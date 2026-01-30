use ringbuf::{Consumer, SharedRb};
use std::sync::Arc;
use tauri::{AppHandle, Emitter};
use tokio::time::{interval, Duration};
use tracing::{info, error};
use tokio::sync::mpsc::Receiver;
use crate::notes::MeetingNote;
use url::Url;
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use futures::{StreamExt, SinkExt};
use serde::Deserialize;
use std::env;

pub enum TranscriptionCommand {
    Stop,
}

#[derive(Debug, Deserialize)]
struct DeepgramResponse {
    channel: Option<DeepgramChannel>,
    is_final: Option<bool>,
}

#[derive(Debug, Deserialize)]
struct DeepgramChannel {
    alternatives: Vec<DeepgramAlternative>,
}

#[derive(Debug, Deserialize)]
struct DeepgramAlternative {
    transcript: String,
}

pub async fn run_transcription_loop(
    mut consumer: Consumer<f32, Arc<SharedRb<f32, Vec<std::mem::MaybeUninit<f32>>>>>,
    input_sample_rate: u32,
    input_channels: u16,
    app_handle: AppHandle,
    mut cmd_rx: Receiver<TranscriptionCommand>,
) {
    info!("Starting transcription loop. Input: {}Hz, {} channels", input_sample_rate, input_channels);
    
    // Load .env if present
    dotenvy::dotenv().ok();
    
    let api_key = env::var("DEEPGRAM_API_KEY").unwrap_or_default();
    info!("Deepgram API Key found: {}", !api_key.is_empty());
    if api_key.is_empty() {
        error!("DEEPGRAM_API_KEY not found in environment variables");
        app_handle.emit("status", "error: missing api key").ok();
        return;
    }

    let mut meeting_note = MeetingNote::new();

    // Connect to Deepgram
    // encoding=linear16 means raw PCM 16-bit signed little-endian
    let url_str = format!(
        "wss://api.deepgram.com/v1/listen?model=nova-2&encoding=linear16&sample_rate={}&channels={}&smart_format=true&interim_results=true",
        input_sample_rate, input_channels
    );
    let url = Url::parse(&url_str).expect("Invalid Deepgram URL");

    use tokio_tungstenite::tungstenite::handshake::client::generate_key;
    
    let host = url.host_str().expect("URL missing host");
    
    let req = tokio_tungstenite::tungstenite::handshake::client::Request::builder()
        .uri(url.as_str())
        .header("Authorization", format!("Token {}", api_key))
        .header("Host", host)
        .header("Connection", "Upgrade")
        .header("Upgrade", "websocket")
        .header("Sec-WebSocket-Version", "13")
        .header("Sec-WebSocket-Key", generate_key())
        .body(())
        .unwrap();

    info!("Connecting to Deepgram...");
    let (ws_stream, _) = match connect_async(req).await {
        Ok(s) => s,
        Err(e) => {
            error!("Failed to connect to Deepgram: {}", e);
            app_handle.emit("status", format!("error: connection failed - {}", e)).ok();
            return;
        }
    };
    info!("Connected to Deepgram.");
    
    let (mut ws_write, mut ws_read) = ws_stream.split();
    
    // Timer to keep pumping audio data
    // 100ms chunks is a good balance for low latency
    let mut ticker = interval(Duration::from_millis(50)); 
    let mut audio_buffer: Vec<i16> = Vec::with_capacity(4096);
    
    let mut active = true;

    while active {
        tokio::select! {
             // Handle Cancellation
            cmd = cmd_rx.recv() => {
                match cmd {
                    Some(TranscriptionCommand::Stop) | None => {
                        info!("Stop command received. Closing connection...");
                        // Send empty frame or Close frame to finish?
                        // Deepgram usually just closes.
                        let _ = ws_write.send(Message::Close(None)).await;
                        
                        match meeting_note.save_to_file(None) {
                             Ok(path) => info!("Meeting notes saved to: {:?}", path),
                             Err(e) => error!("Failed to save meeting notes: {}", e),
                        }
                        active = false;
                    }
                }
            }
            
            // Handle Audio Input
            _ = ticker.tick() => {
                let available = consumer.len();
                if available > 0 {
                     let (head, tail) = consumer.as_slices();
                     let head_len = head.len();
                     let tail_len = tail.len();
                     
                     // Process head
                     for &sample in head {
                         let s = (sample * 32767.0).clamp(-32768.0, 32767.0) as i16;
                         audio_buffer.push(s);
                     }
                     // Process tail
                     for &sample in tail {
                        let s = (sample * 32767.0).clamp(-32768.0, 32767.0) as i16;
                        audio_buffer.push(s);
                     }
                     
                     // Advance consumer
                     unsafe { consumer.advance(head_len + tail_len); }
                     
                     // Only send if we have enough data (e.g. 100ms @ 48kHz = 4800 samples)
                     // This prevents sending tiny packets and respects rate guidelines.
                     if audio_buffer.len() >= 4800 {
                         // Debug: Check signal level
                         let peak = audio_buffer.iter().map(|&s| s.abs()).max().unwrap_or(0);
                         if peak < 50 {
                             info!("Audio buffer contains silence (Peak: {}/32767). Play some audio!", peak);
                         } else {
                             info!("Sending {} samples to Deepgram (Peak: {})", audio_buffer.len(), peak);
                         }

                         // Convert Vec<i16> to Vec<u8> (bytes)
                         let mut byte_data = Vec::with_capacity(audio_buffer.len() * 2);
                         for sample in &audio_buffer {
                             byte_data.extend_from_slice(&sample.to_le_bytes());
                         }
                         
                         match ws_write.send(Message::Binary(byte_data)).await {
                             Ok(_) => {},
                             Err(e) => {
                                 error!("WS Send Error: {}", e);
                             }
                         }
                         audio_buffer.clear();
                     }
                }
            }
            
            // Handle Deepgram Responses
            msg = ws_read.next() => {
                match msg {
                    Some(Ok(Message::Text(text))) => {
                         // Parse JSON
                         if let Ok(response) = serde_json::from_str::<DeepgramResponse>(&text) {
                            if let Some(channel) = response.channel {
                                if let Some(alt) = channel.alternatives.first() {
                                    let transcript = &alt.transcript;
                                    let is_final = response.is_final.unwrap_or(false);
                                    
                                    if !transcript.trim().is_empty() {
                                         let timestamp = chrono::Utc::now().to_rfc3339();
                                         let payload = serde_json::json!({
                                             "text": transcript,
                                             "is_final": is_final,
                                             "timestamp": timestamp
                                         });
                                         
                                         if is_final {
                                             app_handle.emit("transcript_final", &payload).ok();
                                             let display_time = chrono::Local::now().format("%H:%M:%S").to_string();
                                             meeting_note.add_transcript_segment(transcript.clone(), display_time);
                                         } else {
                                             app_handle.emit("transcript_partial", &payload).ok();
                                         }
                                    }
                                }
                            }
                         }
                    }
                    Some(Ok(Message::Close(_))) => {
                        info!("Deepgram connection closed.");
                        break;
                    }
                    Some(Err(e)) => {
                        error!("WS Receive Error: {}", e);
                        // break;
                    }
                    None => {
                        break;
                    }
                    _ => {}
                }
            }
        }
    }
    
    info!("Exiting transcription loop");
}

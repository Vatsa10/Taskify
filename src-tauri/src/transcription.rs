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

    let req = tokio_tungstenite::tungstenite::handshake::client::Request::builder()
        .uri(url.as_str())
        .header("Authorization", format!("Token {}", api_key))
        .body(())
        .unwrap();

    info!("Connecting to Deepgram...");
    let (ws_stream, _) = match connect_async(req).await {
        Ok(s) => s,
        Err(e) => {
            error!("Failed to connect to Deepgram: {}", e);
            app_handle.emit("status", "error: connection failed").ok();
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
                     // We grab chunks
                     // Note: iter() on consumer is not straightforward for slices.
                     // We used unsafe advance which is efficient but we need to READ first.
                     // IMPORTANT: ringbuf `pop_iter` or `pop_slice`.
                     // Since we need to convert to i16, we iterate.
                     
                     // To avoid locking too long, limit chunk size?
                     // 48000Hz * 0.05s = 2400 samples.
                     // let chunk_size = std::cmp::min(available, 4800);
                     
                     // Ideally we pop into a temp buffer.
                     // let mut f32_chunk = vec![0.0; chunk_size];
                     // consumer.pop_slice(&mut f32_chunk);
                     
                     // Better: use iterator directly if possible, or simple loop
                     // Simple loop popping one by one is slow.
                     // Consumer implements iter() that yields items? No.
                     // Use `pop_iter`
                     
                     // Optimization: Use slices if possible.
                     // consumer.as_slices() returns (&[T], &[T]).
                     
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
                     
                     // Send data if buffer is big enough
                     if !audio_buffer.is_empty() {
                         // Convert Vec<i16> to Vec<u8> (bytes)
                         let mut byte_data = Vec::with_capacity(audio_buffer.len() * 2);
                         for sample in &audio_buffer {
                             byte_data.extend_from_slice(&sample.to_le_bytes());
                         }
                         
                         match ws_write.send(Message::Binary(byte_data)).await {
                             Ok(_) => {},
                             Err(e) => {
                                 error!("WS Send Error: {}", e);
                                 // break; // Optionally break or retry
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

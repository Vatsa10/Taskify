use tauri::{AppHandle, State, Emitter};
use std::sync::Mutex;
use tokio::sync::mpsc;
use crate::audio::AudioSystem;
use crate::transcription::{run_transcription_loop, TranscriptionCommand};
use tracing::{info, error};

// cpal::Stream is not Send on Windows because of *mut () raw pointers in WASAPI.
// Since we only hold it to drop it later (not accessing it safely across threads),
// we can wrap it.
pub struct SendStream(pub cpal::Stream);
unsafe impl Send for SendStream {}

pub struct RecordingState {
    pub stream: Option<SendStream>,
    pub cmd_tx: Option<mpsc::Sender<TranscriptionCommand>>,
}

pub struct AppState {
    pub recording: Mutex<RecordingState>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            recording: Mutex::new(RecordingState {
                stream: None,
                cmd_tx: None,
            }),
        }
    }
}

#[tauri::command]
pub async fn start_recording(state: State<'_, AppState>, app: AppHandle) -> Result<(), String> {
    info!("Received start_recording command");
    let mut recording = state.recording.lock().map_err(|e| e.to_string())?;
    
    if recording.stream.is_some() {
        return Err("Already recording".into());
    }

    let (mut audio_sys, consumer) = AudioSystem::new();
    
    // Start audio capture
    let (stream, sample_rate, channels) = audio_sys.start_capture().map_err(|e| e.to_string())?;
    
    // Create command channel
    let (tx, rx) = mpsc::channel(10);

    // Spawn transcription task
    tokio::spawn(run_transcription_loop(consumer, sample_rate, channels, app.clone(), rx));
    
    recording.stream = Some(SendStream(stream));
    recording.cmd_tx = Some(tx);
    
    info!("Recording started successfully");
    
    // Emit status
    app.emit("status", "recording").map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
pub async fn stop_recording(state: State<'_, AppState>, app: AppHandle) -> Result<(), String> {
    info!("Received stop_recording command");
    
    let cmd_tx = {
        let mut recording = state.recording.lock().map_err(|e| e.to_string())?;
        
        // Stop audio
        if let Some(wrapped_stream) = recording.stream.take() {
            drop(wrapped_stream.0); 
        }
        
        recording.cmd_tx.take()
    };

    if let Some(tx) = cmd_tx {
        if let Err(e) = tx.send(TranscriptionCommand::Stop).await {
            error!("Failed to send stop command to transcription task: {}", e);
        }
    }
    
    info!("Recording stopped");
    app.emit("status", "stopped").map_err(|e| e.to_string())?;

    Ok(())
}

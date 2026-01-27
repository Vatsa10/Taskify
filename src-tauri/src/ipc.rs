use tauri::{AppHandle, State, Runtime};
use std::sync::Mutex;
use crate::audio::AudioSystem;
use crate::transcription::run_transcription_loop;
use tracing::{info, error};

pub struct RecordingState {
    pub stream: Option<cpal::Stream>,
    pub abort_handle: Option<tokio::task::AbortHandle>,
}

pub struct AppState {
    pub recording: Mutex<RecordingState>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            recording: Mutex::new(RecordingState {
                stream: None,
                abort_handle: None,
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
    
    // Spawn transcription task
    let handle = tokio::spawn(run_transcription_loop(consumer, sample_rate, channels, app.clone()));
    
    recording.stream = Some(stream);
    recording.abort_handle = Some(handle.abort_handle());
    
    info!("Recording started successfully");
    
    // Emit status
    app.emit("status", "recording").map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
pub async fn stop_recording(state: State<'_, AppState>, app: AppHandle) -> Result<(), String> {
    info!("Received stop_recording command");
    let mut recording = state.recording.lock().map_err(|e| e.to_string())?;
    
    // Stop audio
    if let Some(stream) = recording.stream.take() {
        drop(stream); 
    }
    
    // Stop transcription task
    if let Some(abort_handle) = recording.abort_handle.take() {
        abort_handle.abort();
    }
    
    info!("Recording stopped");
    app.emit("status", "stopped").map_err(|e| e.to_string())?;

    Ok(())
}

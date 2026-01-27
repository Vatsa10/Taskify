pub mod audio;
pub mod transcription;
pub mod notes;
pub mod ipc;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(ipc::AppState::new())
        .invoke_handler(tauri::generate_handler![ipc::start_recording, ipc::stop_recording])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

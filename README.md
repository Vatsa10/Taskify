# Meeting Assistant

A production-ready desktop meeting assistant built with Tauri, Rust, and React. Note: Audio capture only works on Windows (WASAPI Loopback).

## Architecture

### Backend (Rust)
- **Audio Capture (`audio.rs`)**: Uses `cpal` to interface with Windows WASAPI Loopback. It captures system audio (what you hear) and pushes raw F32 samples into a high-performance ring buffer.
- **IPC (`ipc.rs`)**: Manages the application state (`RecordingState`) and exposes `start_recording` and `stop_recording` commands to the frontend.
- **Transcription (`transcription.rs`)**: Runs in a separate async Tokio task. It consumes audio from the ring buffer. Currently, it simulates transcription events. In a production environment, this is where you would pipe audio to a Cloud STT provider (e.g., Deepgram, OpenAI Whisper).
- **Notes (`notes.rs`)**: Structure for storing meeting metadata (stubbed).

### Frontend (React + TypeScript)
- **UI**: A minimal, dark-themed interface built with React.
- **Communication**: Uses Tauri's Event system (`listen`) to receive real-time partial and final transcripts.
- **Styling**: Custom CSS for a premium feel.

## Prerequisites

- **OS**: Windows (strictly required for WASAPI Loopback).
- **Rust**: Stable toolchain installed (`rustup`).
- **Node.js**: LTS version.
- **System Audio**: You must have an active output device (speakers/headphones).

## Setup & Run

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Run in Development Mode**:
   ```bash
   npm run tauri dev
   ```
   - This will compile the Rust backend and start the Vite frontend.
   - The first build may take a few minutes.

3. **Usage**:
   - Click **Start Recording**.
   - Speak or play audio on your system.
   - You will see simulated transcription segments appear in the UI.
   - Click **Stop Recording** to end the session.

## Next Steps

1. **Integrate Real STT**:
   - Edit `src-tauri/src/transcription.rs`.
   - Replace the simulation loop with a `reqwest` multipart upload or websocket connection to an STT provider.
2. **Implement Notes**:
   - Save the transcript to a Markdown file using `std::fs` in `notes.rs` on `stop_recording`.

## Troubleshooting

- **Audio Error**: If `cpal` fails, ensure you have an audio output device enabled.
- **Build Fails**: Ensure Visual Studio C++ Build Tools are installed (standard requirement for Rust on Windows).

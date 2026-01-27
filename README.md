# Meeting Assistant

A production-ready desktop meeting assistant built with Tauri, Rust, and React. 

**Key Features:**
*   **System Audio Capture**: Captures "what you hear" (meetings, videos, calls) using Windows WASAPI Loopback.
*   **Real-time Transcription**: Uses **Deepgram Nova-2** model via secure WebSockets for high-accuracy, low-latency speech-to-text.
*   **Smart Buffering**: Optimizes network traffic by buffering audio into 100ms chunks to respect API rate limits.
*   **Auto-Notes**: Automatically saves meeting transcripts and metadata to Markdown files locally.
*   **Production Architecture**: Thread-safe Rust backend with non-blocking audio pipelines.

## Architecture

### Backend (Rust)
- **Audio Capture (`audio.rs`)**: 
    - Uses `cpal` to interface with Windows WASAPI Loopback.
    - Captures system audio samples (F32).
    - Uses a lock-free **Ring Buffer** to transfer data between the high-priority audio thread and the processing thread without blocking.
- **Transcription (`transcription.rs`)**: 
    - connects to **Deepgram API** (`wss://api.deepgram.com`) using `tokio-tungstenite`.
    - Converts F32 audio to I16 PCM on the fly.
    - Implements a **100ms buffering strategy** (accumulating ~4800 samples) before sending to avoid rate-limiting issues.
    - Handles WebSocket handshakes manually (including `Sec-WebSocket-Key` generation) to ensure robust connectivity.
- **Notes Persistence (`notes.rs`)**: 
    - Accumulates transcript segments in memory during the session.
    - Upon stopping, saves a formatted Markdown file to the `meetings/` directory (e.g., `meetings/meeting_20240127_233000.md`).
- **IPC (`ipc.rs`)**: 
    - Manages application state via `tauri::State`.
    - Exposes `start_recording` and `stop_recording` commands.
    - Handles safe shutdown of async tasks using channels.

### Frontend (React + TypeScript)
- **UI**: A minimal, dark-themed interface built with React.
- **Real-time Updates**: Uses Tauri's Event system (`listen`) to receive `transcript_partial` and `transcript_final` events.
- **State Management**: Handles connection status and live scrolling transcript view.

## Prerequisites

- **OS**: Windows (strictly required for WASAPI Loopback).
- **Rust**: Stable toolchain installed (`rustup`).
- **Node.js**: LTS version.
- **Deepgram API Key**: You need a valid API key from [Deepgram](https://deepgram.com/).

## Configuration

1. Create a `.env` file in the project root:
   ```env
   DEEPGRAM_API_KEY=your_deepgram_api_key_here
   ```
   *Note: Finding the `.env` file depends on the working directory of the executable. In development (`npm run tauri dev`), place it in the project root.*

## Setup & Run

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Run in Development Mode**:
   ```bash
   npm run tauri dev
   ```
   - This compiles the Rust backend and starts the interface.
   - **Note**: The first build handles heavy crates (`tokio`, `tungstenite`, `native-tls`) and might take a few minutes.

3. **Usage**:
   - Click **Start Recording**.
   - Speak or play audio on your system.
   - Watch the live transcript appear.
   - Click **Stop Recording**: The transcript is saved to the `meetings/` folder.

## Troubleshooting

- **"error: connection failed"**: 
    - Check your internet connection.
    - Verify `DEEPGRAM_API_KEY` is correct in `.env`.
    - Ensure your system clock is accurate (required for SSL/TLS handshakes).
- **No Audio Captured**: 
    - Ensure you have an active output device (Speakers/Headphones). WASAPI Loopback captures *output*, so if your system is silent, no data is sent.
- **Build Errors (TLS/SSL)**: 
    - This project uses `native-tls-vendored` to bundle OpenSSL certificates, avoiding common Windows certificate store issues. Ensure you have a clean build storage if issues persist (`cargo clean`).

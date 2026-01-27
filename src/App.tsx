import { useState, useEffect, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import "./App.css";

interface TranscriptSegment {
  text: string;
  is_final: boolean;
  timestamp: string;
}

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState("Ready");
  const [transcript, setTranscript] = useState<TranscriptSegment[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let unlistenPartial: Promise<() => void>;
    let unlistenFinal: Promise<() => void>;
    let unlistenStatus: Promise<() => void>;

    const setupListeners = async () => {
      unlistenPartial = listen("transcript_partial", (event: any) => {
        const payload = event.payload as TranscriptSegment;
        setTranscript((prev) => {
          const last = prev[prev.length - 1];
          // If the last segment is partial, replace it with the new update
          if (last && !last.is_final) {
            return [...prev.slice(0, -1), payload];
          }
          // Otherwise append
          return [...prev, payload];
        });
      });

      unlistenFinal = listen("transcript_final", (event: any) => {
        const payload = event.payload as TranscriptSegment;
        setTranscript((prev) => {
          const last = prev[prev.length - 1];
          // Replace the partial placeholder with the final segment
          if (last && !last.is_final) {
             return [...prev.slice(0, -1), payload];
          }
          return [...prev, payload];
        });
      });
      
      unlistenStatus = listen("status", (event: any) => {
          setStatus(event.payload as string);
          if (event.payload === "stopped") setIsRecording(false);
          if (event.payload === "recording") setIsRecording(true);
      });
    };

    setupListeners();

    return () => {
      if (unlistenPartial) unlistenPartial.then((f) => f());
      if (unlistenFinal) unlistenFinal.then((f) => f());
      if (unlistenStatus) unlistenStatus.then((f) => f());
    };
  }, []);

  useEffect(() => {
      if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
  }, [transcript]);

  async function toggleRecording() {
    if (isRecording) {
      try {
        await invoke("stop_recording");
        // State update handled by listener or optimistic
        setIsRecording(false);
      } catch (e) {
        console.error(e);
      }
    } else {
      try {
        await invoke("start_recording");
        setIsRecording(true);
      } catch (e) {
        console.error(e);
      }
    }
  }

  return (
    <div className="container">
      <header>
        <h1>Meeting Assistant</h1>
        <div className="indicator-wrapper">
            <div className={`indicator ${isRecording ? "active" : ""}`}></div>
            <span>{status}</span>
        </div>
      </header>
      
      <div className="transcript-box" ref={scrollRef}>
        {transcript.length === 0 && <div className="placeholder">Start recording to see live transcription...</div>}
        {transcript.map((seg, i) => (
          <div key={i} className={`segment ${seg.is_final ? "final" : "partial"}`}>
            <span className="timestamp">{new Date(seg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}</span>
            <p className="text">{seg.text}</p>
          </div>
        ))}
      </div>

      <div className="controls">
        <button 
            onClick={toggleRecording}
            className={`record-btn ${isRecording ? "stop" : "start"}`}
        >
          {isRecording ? "Stop Recording" : "Start Recording"}
        </button>
      </div>
    </div>
  );
}

export default App;

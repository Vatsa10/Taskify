import React, { useState, useEffect } from 'react';
import { MeetingControlPanel } from './components/MeetingControlPanel';
import { TranscriptionWindow } from './components/TranscriptionWindow';
import { NotesEditor } from './components/NotesEditor';
import { InsightsDashboard } from './components/InsightsDashboard';
import { useMeetingStore } from './store/meetingStore';
import { useSettingsStore } from './store/settingsStore';

declare global {
  interface Window {
    api: any;
    electronAPI: any;
  }
}

export const App: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [showTranscription, setShowTranscription] = useState(true);
  const [showNotes, setShowNotes] = useState(false);
  const [showInsights, setShowInsights] = useState(false);
  
  const { currentMeeting, startMeeting, endMeeting } = useMeetingStore();
  const { settings } = useSettingsStore();

  useEffect(() => {
    // Set up IPC listeners
    if (window.api) {
      window.api.onToggleNotes(() => setShowNotes(prev => !prev));
      window.api.onToggleTranscription(() => setShowTranscription(prev => !prev));
      
      window.api.onTranscriptionResult((text: string, speaker?: string) => {
        // Handle transcription results
        console.log('Transcription:', text, speaker);
      });
      
      window.api.onAnalysisResult((result: any) => {
        // Handle AI analysis results
        console.log('Analysis:', result);
      });
    }

    return () => {
      if (window.api) {
        window.api.removeAllListeners('toggle-notes');
        window.api.removeAllListeners('toggle-transcription');
        window.api.removeAllListeners('transcription-result');
        window.api.removeAllListeners('analysis-result');
      }
    };
  }, []);

  const handleStartRecording = async () => {
    try {
      if (window.api) {
        await window.api.startAudioCapture();
        await window.api.startTranscription();
        setIsRecording(true);
        startMeeting();
      }
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  };

  const handleStopRecording = async () => {
    try {
      if (window.api) {
        await window.api.stopAudioCapture();
        await window.api.stopTranscription();
        setIsRecording(false);
        endMeeting();
      }
    } catch (error) {
      console.error('Failed to stop recording:', error);
    }
  };

  const handleMinimize = () => {
    if (window.api) {
      window.api.minimizeWindow();
    }
  };

  const handleClose = () => {
    if (window.api) {
      window.api.closeWindow();
    }
  };

  return (
    <div className="h-screen w-screen glass-morphism-dark text-white overflow-hidden">
      {/* Title Bar */}
      <div className="titlebar">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-medium">Meeting Assistant</span>
          {isRecording && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-red-400">Recording</span>
            </div>
          )}
        </div>
        <div className="flex items-center space-x-1">
          <button className="titlebar-button titlebar-minimize" onClick={handleMinimize} />
          <button className="titlebar-button titlebar-close" onClick={handleClose} />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-col h-[calc(100vh-30px)]">
        {/* Control Panel */}
        <MeetingControlPanel
          isRecording={isRecording}
          onStartRecording={handleStartRecording}
          onStopRecording={handleStopRecording}
          showTranscription={showTranscription}
          showNotes={showNotes}
          showInsights={showInsights}
          onToggleTranscription={() => setShowTranscription(!showTranscription)}
          onToggleNotes={() => setShowNotes(!showNotes)}
          onToggleInsights={() => setShowInsights(!showInsights)}
        />

        {/* Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Transcription Window */}
          {showTranscription && (
            <div className="flex-1 p-4">
              <TranscriptionWindow />
            </div>
          )}

          {/* Notes Editor */}
          {showNotes && (
            <div className="w-96 p-4 border-l border-white/10">
              <NotesEditor />
            </div>
          )}

          {/* Insights Dashboard */}
          {showInsights && (
            <div className="w-80 p-4 border-l border-white/10">
              <InsightsDashboard />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;

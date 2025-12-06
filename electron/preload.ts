import { contextBridge, ipcRenderer } from 'electron';
import { electronAPI } from '@electron-toolkit/preload';

const api = {
  // Window management
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  closeWindow: () => ipcRenderer.invoke('close-window'),
  setWindowPosition: (x: number, y: number) => ipcRenderer.invoke('set-window-position', x, y),
  setWindowSize: (width: number, height: number) => ipcRenderer.invoke('set-window-size', width, height),
  setAlwaysOnTop: (alwaysOnTop: boolean) => ipcRenderer.invoke('set-always-on-top', alwaysOnTop),
  setOpacity: (opacity: number) => ipcRenderer.invoke('set-opacity', opacity),

  // System information
  getAudioSources: () => ipcRenderer.invoke('get-audio-sources'),
  getScreenSize: () => ipcRenderer.invoke('get-screen-size'),

  // Event listeners
  onToggleNotes: (callback: () => void) => ipcRenderer.on('toggle-notes', callback),
  onToggleTranscription: (callback: () => void) => ipcRenderer.on('toggle-transcription', callback),

  // Audio capture
  startAudioCapture: () => ipcRenderer.invoke('start-audio-capture'),
  stopAudioCapture: () => ipcRenderer.invoke('stop-audio-capture'),
  onAudioData: (callback: (data: ArrayBuffer) => void) => ipcRenderer.on('audio-data', callback),

  // Speech recognition
  startTranscription: () => ipcRenderer.invoke('start-transcription'),
  stopTranscription: () => ipcRenderer.invoke('stop-transcription'),
  onTranscriptionResult: (callback: (text: string, speaker?: string) => void) => 
    ipcRenderer.on('transcription-result', callback),

  // AI analysis
  analyzeMeeting: (transcript: string) => ipcRenderer.invoke('analyze-meeting', transcript),
  onAnalysisResult: (callback: (result: any) => void) => ipcRenderer.on('analysis-result', callback),

  // Data storage
  saveMeeting: (meeting: any) => ipcRenderer.invoke('save-meeting', meeting),
  getMeetings: () => ipcRenderer.invoke('get-meetings'),
  deleteMeeting: (id: string) => ipcRenderer.invoke('delete-meeting', id),

  // Settings
  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSettings: (settings: any) => ipcRenderer.invoke('save-settings'),

  // Remove all listeners
  removeAllListeners: (channel: string) => ipcRenderer.removeAllListeners(channel)
};

contextBridge.exposeInMainWorld('electronAPI', electronAPI);
contextBridge.exposeInMainWorld('api', api);

export type Api = typeof api;

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Settings } from '@/types';

interface SettingsStore {
  settings: Settings;
  updateSettings: (updates: Partial<Settings>) => void;
  resetSettings: () => void;
  toggleTheme: () => void;
  setOpacity: (opacity: number) => void;
  setApiKey: (apiKey: string) => void;
  updateShortcuts: (shortcuts: Partial<Settings['shortcuts']>) => void;
}

const defaultSettings: Settings = {
  theme: 'dark',
  opacity: 0.8,
  alwaysOnTop: true,
  autoStartRecording: false,
  language: 'en',
  apiKey: '',
  whisperModel: 'base',
  audioQuality: 'medium',
  enableSpeakerDiarization: true,
  enableActionItemDetection: true,
  enableSentimentAnalysis: true,
  enableTopicDetection: true,
  autoSaveNotes: true,
  exportFormat: 'markdown',
  shortcuts: {
    toggleRecording: 'CommandOrControl+Shift+M',
    toggleTranscription: 'CommandOrControl+Shift+T',
    toggleNotes: 'CommandOrControl+Shift+N',
    takeScreenshot: 'CommandOrControl+Shift+S',
    startBreak: 'CommandOrControl+Shift+B'
  }
};

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      settings: defaultSettings,

      updateSettings: (updates) => {
        set(state => ({
          settings: { ...state.settings, ...updates }
        }));
      },

      resetSettings: () => {
        set({ settings: defaultSettings });
      },

      toggleTheme: () => {
        set(state => ({
          settings: {
            ...state.settings,
            theme: state.settings.theme === 'dark' ? 'light' : 'dark'
          }
        }));
      },

      setOpacity: (opacity) => {
        set(state => ({
          settings: { ...state.settings, opacity: Math.max(0.3, Math.min(0.9, opacity)) }
        }));
      },

      setApiKey: (apiKey) => {
        set(state => ({
          settings: { ...state.settings, apiKey }
        }));
      },

      updateShortcuts: (shortcuts) => {
        set(state => ({
          settings: {
            ...state.settings,
            shortcuts: { ...state.settings.shortcuts, ...shortcuts }
          }
        }));
      }
    }),
    {
      name: 'settings-store'
    }
  )
);

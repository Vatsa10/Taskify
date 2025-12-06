import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Meeting, TranscriptEntry, Note, ActionItem, Participant } from '@/types';

interface MeetingStore {
  // State
  currentMeeting: Meeting | null;
  meetings: Meeting[];
  isRecording: boolean;
  transcriptionHistory: TranscriptEntry[];
  currentNotes: Note[];
  currentActionItems: ActionItem[];
  
  // Actions
  startMeeting: (title?: string) => void;
  endMeeting: () => void;
  addTranscriptEntry: (entry: Omit<TranscriptEntry, 'id'>) => void;
  addNote: (note: Omit<Note, 'id'>) => void;
  updateNote: (id: string, updates: Partial<Note>) => void;
  deleteNote: (id: string) => void;
  addActionItem: (actionItem: Omit<ActionItem, 'id' | 'createdAt'>) => void;
  updateActionItem: (id: string, updates: Partial<ActionItem>) => void;
  deleteActionItem: (id: string) => void;
  addParticipant: (participant: Omit<Participant, 'id'>) => void;
  updateParticipant: (id: string, updates: Partial<Participant>) => void;
  
  // Utility
  getMeetingById: (id: string) => Meeting | undefined;
  deleteMeeting: (id: string) => void;
  exportMeeting: (id: string, format: 'markdown' | 'json' | 'pdf') => string;
  clearCurrentMeeting: () => void;
}

export const useMeetingStore = create<MeetingStore>()(
  persist(
    (set, get) => ({
      // Initial state
      currentMeeting: null,
      meetings: [],
      isRecording: false,
      transcriptionHistory: [],
      currentNotes: [],
      currentActionItems: [],

      // Meeting management
      startMeeting: (title = 'New Meeting') => {
        const newMeeting: Meeting = {
          id: generateId(),
          title,
          startTime: new Date(),
          transcript: [],
          notes: [],
          actionItems: [],
          participants: [],
          insights: {
            speakingTimeDistribution: [],
            topicDistribution: [],
            sentiment: { overall: 'neutral', score: 0, breakdown: { positive: 0, neutral: 1, negative: 0 } },
            engagement: { participation: 0, questions: 0, interruptions: 0, consensus: 0 },
            keyDecisions: [],
            followUpRequired: false
          }
        };
        
        set({ currentMeeting: newMeeting, isRecording: true });
      },

      endMeeting: () => {
        const { currentMeeting, transcriptionHistory, currentNotes, currentActionItems } = get();
        
        if (currentMeeting) {
          const completedMeeting: Meeting = {
            ...currentMeeting,
            endTime: new Date(),
            duration: Date.now() - currentMeeting.startTime.getTime(),
            transcript: transcriptionHistory,
            notes: currentNotes,
            actionItems: currentActionItems
          };
          
          set(state => ({
            meetings: [...state.meetings, completedMeeting],
            currentMeeting: null,
            isRecording: false,
            transcriptionHistory: [],
            currentNotes: [],
            currentActionItems: []
          }));
        }
      },

      // Transcription
      addTranscriptEntry: (entry) => {
        const transcriptEntry: TranscriptEntry = {
          ...entry,
          id: generateId()
        };
        
        set(state => ({
          transcriptionHistory: [...state.transcriptionHistory, transcriptEntry]
        }));
      },

      // Notes
      addNote: (note) => {
        const newNote: Note = {
          ...note,
          id: generateId()
        };
        
        set(state => ({
          currentNotes: [...state.currentNotes, newNote]
        }));
      },

      updateNote: (id, updates) => {
        set(state => ({
          currentNotes: state.currentNotes.map(note =>
            note.id === id ? { ...note, ...updates } : note
          )
        }));
      },

      deleteNote: (id) => {
        set(state => ({
          currentNotes: state.currentNotes.filter(note => note.id !== id)
        }));
      },

      // Action items
      addActionItem: (actionItem) => {
        const newActionItem: ActionItem = {
          ...actionItem,
          id: generateId(),
          createdAt: new Date()
        };
        
        set(state => ({
          currentActionItems: [...state.currentActionItems, newActionItem]
        }));
      },

      updateActionItem: (id, updates) => {
        set(state => ({
          currentActionItems: state.currentActionItems.map(item =>
            item.id === id ? { ...item, ...updates } : item
          )
        }));
      },

      deleteActionItem: (id) => {
        set(state => ({
          currentActionItems: state.currentActionItems.filter(item => item.id !== id)
        }));
      },

      // Participants
      addParticipant: (participant) => {
        const newParticipant: Participant = {
          ...participant,
          id: generateId()
        };
        
        set(state => ({
          currentMeeting: state.currentMeeting
            ? { ...state.currentMeeting, participants: [...state.currentMeeting.participants, newParticipant] }
            : null
        }));
      },

      updateParticipant: (id, updates) => {
        set(state => ({
          currentMeeting: state.currentMeeting
            ? {
                ...state.currentMeeting,
                participants: state.currentMeeting.participants.map(p =>
                  p.id === id ? { ...p, ...updates } : p
                )
              }
            : null
        }));
      },

      // Utility
      getMeetingById: (id) => {
        return get().meetings.find(meeting => meeting.id === id);
      },

      deleteMeeting: (id) => {
        set(state => ({
          meetings: state.meetings.filter(meeting => meeting.id !== id)
        }));
      },

      exportMeeting: (id, format) => {
        const meeting = get().getMeetingById(id);
        if (!meeting) return '';
        
        switch (format) {
          case 'json':
            return JSON.stringify(meeting, null, 2);
          case 'markdown':
            return exportToMarkdown(meeting);
          default:
            return JSON.stringify(meeting, null, 2);
        }
      },

      clearCurrentMeeting: () => {
        set({
          currentMeeting: null,
          isRecording: false,
          transcriptionHistory: [],
          currentNotes: [],
          currentActionItems: []
        });
      }
    }),
    {
      name: 'meeting-store',
      partialize: (state) => ({ meetings: state.meetings })
    }
  )
);

// Helper functions
function generateId(): string {
  return Math.random().toString(36).substr(2, 9);
}

function exportToMarkdown(meeting: Meeting): string {
  let markdown = `# ${meeting.title}\n\n`;
  markdown += `**Date:** ${meeting.startTime.toLocaleDateString()}\n`;
  markdown += `**Duration:** ${Math.round((meeting.duration || 0) / 60000)} minutes\n\n`;
  
  if (meeting.participants.length > 0) {
    markdown += `## Participants\n\n`;
    meeting.participants.forEach(p => {
      markdown += `- ${p.name}${p.role ? ` (${p.role})` : ''}\n`;
    });
    markdown += '\n';
  }
  
  if (meeting.transcript.length > 0) {
    markdown += `## Transcript\n\n`;
    meeting.transcript.forEach(entry => {
      markdown += `**${entry.speaker}** (${entry.timestamp.toLocaleTimeString()}):\n`;
      markdown += `${entry.text}\n\n`;
    });
  }
  
  if (meeting.actionItems.length > 0) {
    markdown += `## Action Items\n\n`;
    meeting.actionItems.forEach(item => {
      markdown += `- [ ] ${item.description}`;
      if (item.assignee) markdown += ` - **Assigned to:** ${item.assignee}`;
      if (item.dueDate) markdown += ` - **Due:** ${item.dueDate.toLocaleDateString()}`;
      markdown += '\n';
    });
  }
  
  return markdown;
}

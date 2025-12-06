export interface Meeting {
  id: string;
  title: string;
  startTime: Date;
  endTime?: Date;
  duration?: number;
  transcript: TranscriptEntry[];
  notes: Note[];
  actionItems: ActionItem[];
  participants: Participant[];
  insights: MeetingInsights;
  audioPath?: string;
  summary?: string;
}

export interface TranscriptEntry {
  id: string;
  timestamp: Date;
  speaker: string;
  text: string;
  confidence?: number;
  isActionItem?: boolean;
  topics?: string[];
}

export interface Note {
  id: string;
  content: string;
  timestamp: Date;
  tags: string[];
  isImportant: boolean;
  linkedTranscriptIds?: string[];
}

export interface ActionItem {
  id: string;
  description: string;
  assignee?: string;
  dueDate?: Date;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'in_progress' | 'completed';
  createdAt: Date;
  completedAt?: Date;
}

export interface Participant {
  id: string;
  name: string;
  email?: string;
  role?: string;
  speakingTime: number;
  contributions: number;
}

export interface MeetingInsights {
  speakingTimeDistribution: SpeakerStats[];
  topicDistribution: TopicStats[];
  sentiment: SentimentAnalysis;
  engagement: EngagementMetrics;
  keyDecisions: string[];
  followUpRequired: boolean;
}

export interface SpeakerStats {
  speaker: string;
  speakingTime: number;
  percentage: number;
  wordCount: number;
}

export interface TopicStats {
  topic: string;
  frequency: number;
  duration: number;
  sentiment: 'positive' | 'neutral' | 'negative';
}

export interface SentimentAnalysis {
  overall: 'positive' | 'neutral' | 'negative';
  score: number;
  breakdown: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

export interface EngagementMetrics {
  participation: number;
    questions: number;
    interruptions: number;
    consensus: number;
}

export interface Settings {
  theme: 'light' | 'dark' | 'auto';
  opacity: number;
  alwaysOnTop: boolean;
  autoStartRecording: boolean;
  language: string;
  apiKey: string;
  whisperModel: 'tiny' | 'base' | 'small' | 'medium' | 'large';
  audioQuality: 'low' | 'medium' | 'high';
  enableSpeakerDiarization: boolean;
  enableActionItemDetection: boolean;
  enableSentimentAnalysis: boolean;
  enableTopicDetection: boolean;
  autoSaveNotes: boolean;
  exportFormat: 'markdown' | 'pdf' | 'docx';
  shortcuts: KeyboardShortcuts;
}

export interface KeyboardShortcuts {
  toggleRecording: string;
  toggleTranscription: string;
  toggleNotes: string;
  takeScreenshot: string;
  startBreak: string;
}

export interface AudioSource {
  id: string;
  name: string;
  type: 'microphone' | 'system' | 'application';
}

export interface WindowPosition {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Theme {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    accent: string;
  };
}

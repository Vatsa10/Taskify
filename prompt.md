# Meeting Assistant Electron App - Development Prompt

## Project Overview
Build an Electron-based real-time AI assistant specifically designed for meetings that provides contextual help, note-taking, and follow-up actions during business meetings, video conferences, and collaborative sessions.

## Core Features

### 1. Real-Time Meeting Analysis
- **Speech Recognition**: Transcribe meeting audio in real-time
- **Speaker Identification**: Track and label different speakers
- **Topic Detection**: Identify key discussion topics and agenda items
- **Action Item Extraction**: Automatically detect and highlight action items, decisions, and deadlines

### 2. Smart Note-Taking
- **Auto-Summarization**: Generate concise meeting summaries
- **Key Points Extraction**: Highlight important decisions and insights
- **Timeline-Based Notes**: Organize notes by meeting timeline
- **Tagging System**: Categorize notes by topics, speakers, or action items

### 3. Meeting Enhancement Tools
- **Agenda Tracking**: Monitor agenda progress and time management
- **Question Suggestions**: Provide relevant questions based on context
- **Fact-Checking**: Real-time verification of claims and data
- **Translation Support**: Multi-language meeting support

### 4. Post-Meting Features
- **Meeting Minutes**: Generate professional meeting minutes
- **Follow-Up Tasks**: Create actionable task lists with assignments
- **Email Summaries**: Auto-generate meeting recap emails
- **Calendar Integration**: Schedule follow-ups and reminders

## Technical Architecture

### Frontend (Renderer Process)
- **Framework**: React 18+ with TypeScript
- **UI Components**: Tailwind CSS + shadcn/ui
- **State Management**: Zustand or React Query
- **Real-time Updates**: WebSocket connections

### Backend (Main Process)
- **Audio Processing**: Web Audio API for capture and processing
- **AI Integration**: 
  - OpenAI GPT-4/4T for analysis
  - Whisper for speech-to-text
  - Local processing options (whisper.cpp)
- **Data Storage**: SQLite for local meeting data
- **API Services**: RESTful endpoints for AI services

### Key Modules

#### Audio Capture Module
```javascript
// Multi-platform audio capture system
// Windows: Windows Core Audio API (WASAPI) for system audio
// macOS: AVAudioEngine for system audio + ScreenCaptureKit
// Linux: PulseAudio for system audio capture
// Real-time audio streaming to processing services
// Sample rate: 16kHz for Whisper compatibility
// Format: 16-bit PCM, mono channel
```

#### Audio Capture Technologies
- **Windows**: 
  - Windows: Loopback audio capture
  - WASAPI (Windows Audio Session API) for system audio capture
  - DirectShow for microphone input
  - Loopback recording for application-specific audio
- **macOS**:
  - AVAudioEngine for high-quality audio capture
  - ScreenCaptureKit API for integrated screen+audio
  - Core Audio framework for low-latency processing
- **Linux**:
  - PulseAudio for system audio routing
  - ALSA for direct hardware access
  - PipeWire for modern audio management
- **Cross-platform**:
  - Web Audio API for browser-based capture
  - WebRTC for real-time audio streaming
  - Web Workers for non-blocking audio processing

#### Speech Recognition Module
```javascript
// Integration with Whisper API or local model
// Speaker diarization
// Language detection and translation
```

#### AI Analysis Module
```javascript
// Context analysis using LLM
// Action item extraction
// Summary generation
// Topic categorization
```

#### UI Overlay Module
```javascript
// Transparent overlay window
- Click-through capability
- Minimal interface design
- Keyboard shortcuts for control
```

## Development Roadmap

### Phase 1: Core Infrastructure
1. **Electron App Setup**
   - Configure Electron Forge
   - Set up TypeScript + React
   - Implement basic window management

2. **Audio Capture System**
   - Implement screen recording with audio
   - Add microphone capture
   - Handle permissions across platforms

3. **Basic UI Framework**
   - Create overlay window system
   - Implement basic controls
   - Add keyboard shortcuts

### Phase 2: AI Integration
1. **Speech Recognition**
   - Integrate Whisper API
   - Implement real-time transcription
   - Add speaker identification

2. **Basic AI Analysis**
   - Connect to OpenAI API
   - Implement simple summarization
   - Add action item detection

3. **Note-Taking System**
   - Create note editor
   - Implement auto-save
   - Add export functionality

### Phase 3: Advanced Features
1. **Meeting Intelligence**
   - Advanced topic detection
   - Sentiment analysis
   - Engagement metrics

2. **Integration Features**
   - Calendar integration (Google/Outlook)
   - Task management (Todoist/Asana)
   - Email integration

3. **Collaboration Tools**
   - Real-time note sharing
   - Multi-user support
   - Meeting recording storage

## Technical Requirements

### Dependencies
```json
{
  "main": {
    "electron": "^27.0.0",
    "electron-builder": "^24.0.0"
  },
  "renderer": {
    "react": "^18.0.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.0.0",
    "@radix-ui/react-*": "^1.0.0"
  },
  "ai": {
    "openai": "^4.0.0",
    "@whisper-api/whisper": "^1.0.0"
  },
  "audio": {
    "node-record-lpcm16": "^1.0.0",
    "web-audio-api": "^0.2.0"
  }
}
```

### System Requirements
- **Node.js**: 18+ 
- **Operating Systems**: Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **Memory**: 8GB+ RAM recommended
- **Storage**: 500MB+ for app and local data

### API Keys Required
- **OpenAI API Key**: For GPT-4/Whisper integration
- **Google Calendar API**: For calendar integration
- **Optional**: Local Whisper model for offline processing

## Security & Privacy

### Data Protection
- **Local Processing**: Option for offline transcription
- **Encryption**: Encrypt stored meeting data
- **Data Retention**: User-controlled data deletion
- **Privacy Mode**: Disable recording when needed

### Compliance
- **GDPR Compliance**: User data handling
- **Enterprise Security**: SSO integration options
- **Audit Logs**: Track data access and usage

## UI/UX Design Principles

### Overlay Interface Architecture
- **Glass-morphism Design**: Frosted glass effect with backdrop blur
- **Layered Components**: Multiple z-index layers for depth
- **Adaptive Layout**: Responsive to screen size and content
- **Smart Positioning**: Auto-position to avoid covering important content

### Main UI Components

#### 1. Meeting Control Panel
```typescript
interface MeetingControlPanel {
  // Floating toolbar with essential controls
  position: 'top-right' | 'bottom-left' | 'custom';
  components: {
    RecordButton: boolean;          // Start/stop recording
    TranscriptionToggle: boolean;   // Show/hide live transcription
    NotesPanel: boolean;            // Quick notes access
    SettingsMenu: boolean;          // Configuration options
  };
  styling: {
    background: 'rgba(0, 0, 0, 0.8)';
    backdropFilter: 'blur(10px)';
    borderRadius: '12px';
    padding: '8px';
  };
}
```

#### 2. Live Transcription Window
```typescript
interface TranscriptionWindow {
  // Real-time speech-to-text display
  layout: 'scrolling' | 'paged' | 'minimal';
  features: {
    SpeakerLabels: boolean;         // Color-coded speaker identification
    Timestamps: boolean;            // Automatic timestamp insertion
    ActionItemHighlight: boolean;   // Highlight detected action items
    SearchFunction: boolean;         // Search within transcription
  };
  styling: {
    maxHeight: '300px';
    overflow: 'auto';
    fontSize: '14px';
    lineHeight: '1.5';
  };
}
```

#### 3. Smart Notes Editor
```typescript
interface NotesEditor {
  // AI-enhanced note-taking interface
  layout: 'split-view' | 'overlay' | 'sidebar';
  features: {
    AutoSummarize: boolean;         // AI-powered summaries
    ActionItemExtraction: boolean;  // Detect and tag action items
    TopicCategorization: boolean;   // Auto-categorize by topics
    CollaborationMode: boolean;      // Real-time sharing
  };
  components: {
    RichTextEditor: ReactQuill;      // WYSIWYG editing
    TagSystem: boolean;             // Custom tags and filters
    ExportOptions: boolean;          // PDF, Word, Markdown export
  };
}
```

#### 4. Meeting Insights Dashboard
```typescript
interface InsightsDashboard {
  // Analytics and meeting metrics
  widgets: {
    SpeakingTimeChart: boolean;      // Speaker participation analysis
    TopicDistribution: boolean;      // Meeting topic breakdown
    ActionItemTracker: boolean;      // Progress on action items
    SentimentAnalysis: boolean;      // Meeting tone analysis
  };
  visualizations: {
    DonutCharts: boolean;            // For percentage data
    BarGraphs: boolean;              // For comparisons
    TimelineView: boolean;           // For meeting progression
  };
}
```

### Advanced UI Features

#### 1. Adaptive Window System
```typescript
// Smart window positioning and resizing
interface AdaptiveWindow {
  autoPosition: boolean;            // Avoid covering important UI elements
  screenEdgeDetection: boolean;     // Snap to screen edges
  multiMonitorSupport: boolean;      // Handle multiple displays
  collisionDetection: boolean;      // Avoid overlapping other apps
}
```

#### 2. Gesture and Shortcut System
```typescript
interface InteractionSystem {
  keyboardShortcuts: {
    'Ctrl+Shift+M': 'toggleMeetingMode';
    'Ctrl+Shift+N': 'openNotesPanel';
    'Ctrl+Shift+T': 'toggleTranscription';
    'Ctrl+Shift+S': 'takeScreenshot';
  };
  mouseGestures: {
    'doubleClick': 'maximizeWindow';
    'rightClick+drag': 'repositionWindow';
    'scroll': 'zoomContent';
  };
  voiceCommands: boolean;           // Voice-activated controls
}
```

#### 3. Theme and Customization System
```typescript
interface ThemeSystem {
  themes: {
    dark: 'high-contrast-dark';
    light: 'clean-light';
    auto: 'system-preference';
    custom: 'user-defined';
  };
  customization: {
    opacity: number;                // Window transparency (0.3-0.9)
    fontSize: 'small' | 'medium' | 'large';
    accentColor: string;            // Brand color customization
    layoutDensity: 'compact' | 'comfortable' | 'spacious';
  };
}
```

### Component Library Stack

#### UI Framework
- **React 18+**: Component-based architecture
- **TypeScript**: Type-safe component development
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: Pre-built component library
- **Radix UI**: Accessible component primitives
- **Framer Motion**: Smooth animations and transitions

#### Specialized Components
```typescript
// Custom overlay window component
const OverlayWindow = {
  // Click-through functionality
  clickThrough: boolean;           // Allow mouse events to pass through
  alwaysOnTop: boolean;            // Maintain window visibility
  resizable: boolean;               // User-adjustable window size
  minimizable: boolean;             // Quick hide/show functionality
};

// Real-time data visualization
const DataVisualization = {
  TranscriptionStream: ReactFlow;   // Live transcription flow
  SpeakerTimeline: Chart.js;        // Speaker participation chart
  TopicCloud: WordCloud;            // Meeting topic visualization
};
```

#### Accessibility Features
```typescript
interface Accessibility {
  screenReader: boolean;            // Full NVDA/JAWS compatibility
  keyboardNavigation: boolean;      // Complete keyboard control
  highContrastMode: boolean;        // Enhanced visibility options
  fontSizeScaling: boolean;         // Dynamic text sizing
  colorBlindFriendly: boolean;      // Accessible color schemes
}
```

### Performance Optimization

#### Rendering Strategy
- **Virtual Scrolling**: Handle large transcription texts efficiently
- **React.memo**: Prevent unnecessary re-renders
- **Code Splitting**: Lazy load non-critical components
- **Web Workers**: Offload heavy processing from UI thread

#### Memory Management
```typescript
interface MemoryOptimization {
  transcriptionBuffer: number;      // Max transcription history (1000 lines)
  audioCacheSize: number;           // Audio data cache limit (50MB)
  imageCompression: boolean;        // Compress screenshots
  garbageCollection: boolean;       // Automatic cleanup
}
```

### Responsive Design Breakpoints
```typescript
const breakpoints = {
  mobile: '320px',      // Minimal mobile support
  tablet: '768px',      // Tablet landscape
  laptop: '1024px',     // Small laptop
  desktop: '1440px',    // Standard desktop
  ultrawide: '2560px',  // Ultrawide monitors
};
```

### Animation and Micro-interactions
- **Smooth Transitions**: 200ms ease-in-out animations
- **Loading States**: Skeleton screens for content loading
- **Hover Effects**: Subtle visual feedback
- **Status Indicators**: Real-time connection and processing status
- **Toast Notifications**: Non-intrusive system messages

This comprehensive UI architecture ensures a professional, accessible, and performant meeting assistant that adapts to different user needs and screen configurations.

## Monetization Strategy

### Freemium Model
- **Free Tier**: Basic transcription and notes (5 meetings/month)
- **Pro Tier**: Advanced AI features, unlimited meetings ($9.99/month)
- **Team Tier**: Collaboration features, admin controls ($19.99/user/month)
- **Enterprise**: Custom integrations, on-premise options (custom pricing)

### Value Propositions
- **Time Savings**: Automated note-taking and summaries
- **Better Meetings**: Action item tracking and follow-ups
- **Team Productivity**: Shared notes and collaboration
- **Compliance**: Meeting records and audit trails

## Success Metrics

### User Engagement
- **Daily Active Users**: Target 1,000+ within 6 months
- **Meeting Coverage**: Average 3+ meetings per user per week
- **Feature Adoption**: 80%+ users using AI features
- **Retention Rate**: 70%+ monthly retention

### Business Metrics
- **Conversion Rate**: 15% free-to-paid conversion
- **ARPU**: $8-12 per month average
- **Customer Satisfaction**: 4.5+ star rating
- **Enterprise Sales**: 10+ enterprise customers in year 1

## Development Team Structure

### Core Team (3-4 people)
- **Frontend Developer**: React/Electron specialist
- **Backend Developer**: Node.js/AI integration
- **UI/UX Designer**: Interface and experience design
- **Product Manager**: Feature planning and user feedback

### Extended Team
- **AI/ML Engineer**: Advanced AI features
- **DevOps Engineer**: Infrastructure and deployment
- **QA Engineer**: Testing and quality assurance
- **Customer Support**: User assistance and feedback

## Launch Strategy

### Beta Testing (Months 1-2)
- **Private Beta**: 50 selected users
- **Feedback Collection**: Weekly user interviews
- **Bug Fixes**: Priority issue resolution
- **Feature Refinement**: Based on user feedback

### Public Launch (Month 3)
- **Product Hunt Launch**: Community exposure
- **Content Marketing**: Blog posts and tutorials
- **Social Media**: Targeted LinkedIn and Twitter campaigns
- **Partnerships**: Integration with productivity tools

### Growth Phase (Months 4-6)
- **Feature Expansion**: Advanced AI capabilities
- **Platform Expansion**: Mobile companion app
- **Enterprise Sales**: Targeted B2B outreach
- **Community Building**: User forums and feedback channels

## Competitive Advantages

### Technology
- **Real-time Processing**: Low-latency AI analysis
- **Multi-modal Input**: Screen + audio + text
- **Context Awareness**: Meeting-specific AI models
- **Cross-platform**: Universal compatibility

### User Experience
- **Zero Learning Curve**: Intuitive interface
- **Reliable Performance**: Stable and fast
- **Privacy-first**: User data protection
- **Affordable Pricing**: Competitive value proposition

This comprehensive prompt provides the foundation for building a successful meeting assistant Electron app that combines real-time AI capabilities with practical productivity features.

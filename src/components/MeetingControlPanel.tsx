import React from 'react';
import { Play, Pause, Mic, MicOff, FileText, BarChart3, Settings, Volume2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';

interface MeetingControlPanelProps {
  isRecording: boolean;
  onStartRecording: () => void;
  onStopRecording: () => void;
  showTranscription: boolean;
  showNotes: boolean;
  showInsights: boolean;
  onToggleTranscription: () => void;
  onToggleNotes: () => void;
  onToggleInsights: () => void;
}

export const MeetingControlPanel: React.FC<MeetingControlPanelProps> = ({
  isRecording,
  onStartRecording,
  onStopRecording,
  showTranscription,
  showNotes,
  showInsights,
  onToggleTranscription,
  onToggleNotes,
  onToggleInsights
}) => {
  return (
    <div className="glass-morphism-dark border-b border-white/10 p-4">
      <div className="flex items-center justify-between">
        {/* Recording Controls */}
        <div className="flex items-center space-x-4">
          <Button
            onClick={isRecording ? onStopRecording : onStartRecording}
            variant={isRecording ? "destructive" : "default"}
            size="sm"
            className="flex items-center space-x-2"
          >
            {isRecording ? (
              <>
                <Pause className="w-4 h-4" />
                <span>Stop</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Start</span>
              </>
            )}
          </Button>

          <div className="flex items-center space-x-2">
            {isRecording ? (
              <Mic className="w-4 h-4 text-red-400 animate-pulse" />
            ) : (
              <MicOff className="w-4 h-4 text-gray-400" />
            )}
            <span className="text-sm">
              {isRecording ? 'Recording' : 'Not Recording'}
            </span>
          </div>

          <Separator orientation="vertical" className="h-6" />

          {/* Audio Level Indicator */}
          <div className="flex items-center space-x-2">
            <Volume2 className="w-4 h-4 text-gray-400" />
            <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-green-500 transition-all duration-100"
                style={{ width: isRecording ? '65%' : '0%' }}
              />
            </div>
          </div>
        </div>

        {/* View Toggles */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <Switch
              id="transcription-toggle"
              checked={showTranscription}
              onCheckedChange={onToggleTranscription}
            />
            <Label htmlFor="transcription-toggle" className="text-sm cursor-pointer">
              Transcription
            </Label>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="notes-toggle"
              checked={showNotes}
              onCheckedChange={onToggleNotes}
            />
            <Label htmlFor="notes-toggle" className="text-sm cursor-pointer">
              Notes
            </Label>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="insights-toggle"
              checked={showInsights}
              onCheckedChange={onToggleInsights}
            />
            <Label htmlFor="insights-toggle" className="text-sm cursor-pointer">
              Insights
            </Label>
          </div>

          <Separator orientation="vertical" className="h-6" />

          {/* Quick Actions */}
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm" className="text-gray-300 hover:text-white">
              <FileText className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" className="text-gray-300 hover:text-white">
              <BarChart3 className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" className="text-gray-300 hover:text-white">
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="mt-3 flex items-center justify-between text-xs text-gray-400">
        <div className="flex items-center space-x-4">
          <span>AI: Connected</span>
          <span>Audio: System + Mic</span>
          <span>Quality: High</span>
        </div>
        <div className="flex items-center space-x-4">
          <span>Duration: 00:00:00</span>
          <span>Participants: 3</span>
          <span>Action Items: 2</span>
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect, useRef } from 'react';
import { Search, Download, Copy, Filter, User, Clock, Tag } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useMeetingStore } from '@/store/meetingStore';
import { formatDuration } from '@/lib/utils';
import { TranscriptEntry } from '@/types';

export const TranscriptionWindow: React.FC = () => {
  const { transcriptionHistory } = useMeetingStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSpeaker, setSelectedSpeaker] = useState<string>('all');
  const [showActionItems, setShowActionItems] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new transcription entries are added
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollElement = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollElement) {
        scrollElement.scrollTop = scrollElement.scrollHeight;
      }
    }
  }, [transcriptionHistory]);

  // Get unique speakers
  const speakers = Array.from(new Set(transcriptionHistory.map((entry: TranscriptEntry) => entry.speaker)));

  // Filter transcription entries
  const filteredEntries = transcriptionHistory.filter((entry: TranscriptEntry) => {
    const matchesSearch = entry.text.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSpeaker = selectedSpeaker === 'all' || entry.speaker === selectedSpeaker;
    const matchesActionItems = !showActionItems || entry.isActionItem;
    return matchesSearch && matchesSpeaker && matchesActionItems;
  });

  const handleCopyTranscript = () => {
    const transcript = filteredEntries
      .map((entry: TranscriptEntry) => `[${entry.timestamp.toLocaleTimeString()}] ${entry.speaker}: ${entry.text}`)
      .join('\n\n');
    
    navigator.clipboard.writeText(transcript);
  };

  const handleDownloadTranscript = () => {
    const transcript = filteredEntries
      .map((entry: TranscriptEntry) => `[${entry.timestamp.toLocaleTimeString()}] ${entry.speaker}: ${entry.text}`)
      .join('\n\n');
    
    const blob = new Blob([transcript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcript-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getSpeakerColor = (speaker: string) => {
    const colors = [
      'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-purple-500',
      'bg-pink-500', 'bg-indigo-500', 'bg-red-500', 'bg-orange-500'
    ];
    const index = speakers.indexOf(speaker);
    return colors[index % colors.length];
  };

  return (
    <div className="h-full flex flex-col glass-morphism-dark rounded-lg border border-white/10">
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center space-x-2">
            <Clock className="w-5 h-5" />
            <span>Live Transcription</span>
            <Badge variant="secondary" className="text-xs">
              {filteredEntries.length} entries
            </Badge>
          </h2>
          
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm" onClick={handleCopyTranscript}>
              <Copy className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={handleDownloadTranscript}>
              <Download className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search transcription..."
              value={searchTerm}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
              className="pl-10 bg-white/5 border-white/10 text-white placeholder-gray-400"
            />
          </div>
          
          <select
            value={selectedSpeaker}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedSpeaker(e.target.value)}
            className="bg-white/5 border border-white/10 rounded px-3 py-1 text-white text-sm"
          >
            <option value="all">All Speakers</option>
            {speakers.map((speaker: string) => (
              <option key={speaker} value={speaker}>{speaker}</option>
            ))}
          </select>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="action-items-filter"
              checked={showActionItems}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setShowActionItems(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="action-items-filter" className="text-sm text-gray-300">
              Action Items Only
            </label>
          </div>
        </div>
      </div>

      {/* Transcription Content */}
      <ScrollArea ref={scrollAreaRef} className="flex-1 p-4">
        <div className="space-y-4">
          {filteredEntries.map((entry: TranscriptEntry, index: number) => (
            <div
              key={entry.id || index}
              className={`p-3 rounded-lg border border-white/10 transition-all hover:bg-white/5 ${
                entry.isActionItem ? 'bg-yellow-500/10 border-yellow-500/30' : 'bg-white/5'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${getSpeakerColor(entry.speaker)}`} />
                  <span className="font-medium text-sm">{entry.speaker}</span>
                  <span className="text-xs text-gray-400">
                    {entry.timestamp.toLocaleTimeString()}
                  </span>
                  {entry.confidence && (
                    <span className="text-xs text-gray-400">
                      {Math.round(entry.confidence * 100)}%
                    </span>
                  )}
                </div>
                
                {entry.isActionItem && (
                  <Badge variant="outline" className="text-xs border-yellow-500 text-yellow-400">
                    Action Item
                  </Badge>
                )}
              </div>
              
              <p className="text-sm text-gray-200 leading-relaxed">{entry.text}</p>
              
              {entry.topics && entry.topics.length > 0 && (
                <div className="flex items-center space-x-1 mt-2">
                  <Tag className="w-3 h-3 text-gray-400" />
                  {entry.topics.map((topic: string) => (
                    <Badge key={topic} variant="secondary" className="text-xs">
                      {topic}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          ))}
          
          {filteredEntries.length === 0 && (
            <div className="text-center py-8 text-gray-400">
              <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No transcription entries yet</p>
              <p className="text-sm mt-2">Start recording to see live transcription</p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="p-3 border-t border-white/10 bg-black/20">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center space-x-4">
            <span>Real-time transcription</span>
            <span>•</span>
            <span>Auto-detected speakers</span>
            <span>•</span>
            <span>AI-powered analysis</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span>Live</span>
          </div>
        </div>
      </div>
    </div>
  );
};

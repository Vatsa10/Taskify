import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDuration(milliseconds: number): string {
  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  const displayHours = hours.toString().padStart(2, '0');
  const displayMinutes = (minutes % 60).toString().padStart(2, '0');
  const displaySeconds = (seconds % 60).toString().padStart(2, '0');

  return `${displayHours}:${displayMinutes}:${displaySeconds}`;
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function generateId(): string {
  return Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

export function extractActionItems(text: string): string[] {
  const actionPatterns = [
    /(?:I|we|you|they)\s+(?:will|should|need to|must|have to)\s+(.+?)(?:[.!?]|$)/gi,
    /(?:action|task|todo|item):\s*(.+?)(?:[.!?]|$)/gi,
    /(?:let's|let us)\s+(.+?)(?:[.!?]|$)/gi,
    /(?:please|can you|could you)\s+(.+?)(?:[.!?]|$)/gi
  ];

  const actionItems: string[] = [];
  
  actionPatterns.forEach(pattern => {
    const matches = text.match(pattern);
    if (matches) {
      actionItems.push(...matches.map(match => match.trim()));
    }
  });

  return [...new Set(actionItems)]; // Remove duplicates
}

export function extractTopics(text: string): string[] {
  const topicPatterns = [
    /(?:discuss|talk about|regarding|concerning)\s+(.+?)(?:[.!?]|$)/gi,
    /(?:topic|subject|agenda):\s*(.+?)(?:[.!?]|$)/gi,
    /\b(AI|machine learning|data science|software development|marketing|sales|finance|HR|product|design|research)\b/gi
  ];

  const topics: string[] = [];
  
  topicPatterns.forEach(pattern => {
    const matches = text.match(pattern);
    if (matches) {
      topics.push(...matches.map(match => match.trim()));
    }
  });

  return [...new Set(topics)];
}

export function analyzeSentiment(text: string): 'positive' | 'neutral' | 'negative' {
  const positiveWords = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'perfect', 'best', 'awesome'];
  const negativeWords = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'worst', 'disappointing', 'frustrating', 'annoying', 'problem'];
  
  const words = text.toLowerCase().split(/\s+/);
  let positiveCount = 0;
  let negativeCount = 0;
  
  words.forEach(word => {
    if (positiveWords.includes(word)) positiveCount++;
    if (negativeWords.includes(word)) negativeCount++;
  });
  
  if (positiveCount > negativeCount) return 'positive';
  if (negativeCount > positiveCount) return 'negative';
  return 'neutral';
}

export function createBlobUrl(data: ArrayBuffer, mimeType: string): string {
  const blob = new Blob([data], { type: mimeType });
  return URL.createObjectURL(blob);
}

export function revokeBlobUrl(url: string): void {
  URL.revokeObjectURL(url);
}

export function downloadFile(data: string | ArrayBuffer, filename: string, mimeType?: string): void {
  const blob = new Blob([data], { type: mimeType || 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

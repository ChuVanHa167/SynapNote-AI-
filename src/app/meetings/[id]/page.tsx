"use client";

import { useState } from 'react';
import { Clock } from 'lucide-react';
import { mockMeetingDetail } from '@/lib/mockData';
import { AudioPlayer } from '@/components/meetings/AudioPlayer';
import { TranscriptView } from '@/components/meetings/TranscriptView';
import { AIIntelligencePanel } from '@/components/meetings/AIIntelligencePanel';

export default function MeetingDetailPage() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0); 
  const [currentTime, setCurrentTime] = useState(0); 
  const [tasks, setTasks] = useState(mockMeetingDetail.actionItems);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleTranscriptClick = (seconds: number) => {
    setCurrentTime(seconds);
    setIsPlaying(true);
    setProgress((seconds / 150) * 100); // Mock progress logic based on 150s total length
  };

  const toggleTask = (id: number) => {
    setTasks(tasks.map(t => t.id === id ? { ...t, status: t.status === 'completed' ? 'pending' : 'completed' } : t));
  };

  return (
    <div className="w-full max-w-[1600px] mx-auto p-4 lg:p-8 h-[calc(100vh-6rem)] flex flex-col xl:flex-row gap-6">
      
      {/* LEFT COLUMN: Media & Transcript (60%) */}
      <div className="w-full xl:w-[60%] flex flex-col gap-6 h-full min-h-[600px]">
        {/* Header Info */}
        <div className="animate-in fade-in slide-in-from-left-4 duration-700">
           <div className="flex items-center gap-3 text-xs tracking-widest font-medium uppercase text-foreground/40 mb-3">
             <span className="flex items-center gap-1.5 glass-panel px-3 py-1.5 rounded-full"><Clock size={12} /> {mockMeetingDetail.date}</span>
             <span className="w-1 h-1 rounded-full bg-accent/50"></span>
             <span>Thời lượng: {mockMeetingDetail.duration}</span>
           </div>
           <h1 className="text-3xl lg:text-4xl font-light tracking-tight text-foreground/90">{mockMeetingDetail.title}</h1>
        </div>

        <AudioPlayer 
          isPlaying={isPlaying} 
          onPlayPause={() => setIsPlaying(!isPlaying)}
          progress={progress}
          currentTime={formatTime(currentTime)}
          duration={mockMeetingDetail.duration}
        />

        <TranscriptView 
          transcript={mockMeetingDetail.transcript}
          currentTimeSeconds={currentTime}
          onLineClick={handleTranscriptClick}
        />
      </div>

      {/* RIGHT COLUMN: AI Intelligence Panel (40%) */}
      <div className="w-full xl:w-[40%] flex flex-col h-full animate-in fade-in slide-in-from-right-8 duration-700 delay-500 fill-mode-both">
         <AIIntelligencePanel 
            summary={mockMeetingDetail.summary}
            decisions={mockMeetingDetail.decisions}
            actionItems={tasks}
            onToggleTask={toggleTask}
         />
      </div>

    </div>
  );
}

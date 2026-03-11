"use client";

import { useState, useEffect } from 'react';
import { Clock, Loader2, ArrowLeft } from 'lucide-react';
import { useParams, useRouter } from 'next/navigation';
import { AudioPlayer } from '@/components/meetings/AudioPlayer';
import { TranscriptView } from '@/components/meetings/TranscriptView';
import { AIIntelligencePanel } from '@/components/meetings/AIIntelligencePanel';
import Link from 'next/link';

interface MeetingDetail {
  id: string;
  title: string;
  date: string;
  duration: string;
  summary: string;
  transcript: string;
  decisions: string[];
  action_items: any[];
}

export default function MeetingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  
  const [meeting, setMeeting] = useState<MeetingDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0); 
  const [currentTime, setCurrentTime] = useState(0); 
  const [tasks, setTasks] = useState<any[]>([]);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const response = await fetch(`http://localhost:8000/meetings/${id}`);
        if (response.ok) {
          const data = await response.json();
          setMeeting(data);
          setTasks(data.action_items || []);
        } else {
           console.error("Meeting not found");
        }
      } catch (error) {
        console.error("Failed to fetch meeting detail:", error);
      } finally {
        setIsLoading(false);
      }
    };
    if (id) fetchDetail();
  }, [id]);

  if (isLoading) {
     return (
        <div className="w-full h-screen flex items-center justify-center">
           <Loader2 className="text-accent animate-spin" size={40} />
        </div>
     );
  }

  if (!meeting) {
     return (
        <div className="w-full h-screen flex flex-col items-center justify-center gap-4">
           <h2 className="text-xl font-medium">Không tìm thấy cuộc họp</h2>
           <Link href="/meetings" className="text-accent hover:underline flex items-center gap-2">
              <ArrowLeft size={16} /> Quay lại danh sách
           </Link>
        </div>
     );
  }

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleTranscriptClick = (seconds: number) => {
    setCurrentTime(seconds);
    setIsPlaying(true);
    setProgress((seconds / 150) * 100); 
  };

  const toggleTask = (taskId: string) => {
    setTasks(tasks.map(t => t.id === taskId ? { ...t, status: t.status === 'completed' ? 'pending' : 'completed' } : t));
  };

  // Convert flat transcript string to expected format if needed, 
  // or handle as block text. Current TranscriptView seems to expect an array.
  const transcriptLines = meeting.transcript ? [{ id: '1', time: '00:00', speaker: 'AI', text: meeting.transcript }] : [];

  return (
    <div className="w-full max-w-[1600px] mx-auto p-4 lg:p-8 h-[calc(100vh-6rem)] flex flex-col xl:flex-row gap-6">
      
      {/* LEFT COLUMN: Media & Transcript (60%) */}
      <div className="w-full xl:w-[60%] flex flex-col gap-6 h-full min-h-[600px]">
        {/* Header Info */}
        <div className="animate-in fade-in slide-in-from-left-4 duration-700">
           <div className="flex items-center gap-3 text-xs tracking-widest font-medium uppercase text-foreground/40 mb-3">
              <span className="flex items-center gap-1.5 glass-panel px-3 py-1.5 rounded-full"><Clock size={12} /> {meeting.date}</span>
              <span className="w-1 h-1 rounded-full bg-accent/50"></span>
              <span>Thời lượng: {meeting.duration}</span>
           </div>
           <h1 className="text-3xl lg:text-4xl font-light tracking-tight text-foreground/90">{meeting.title}</h1>
        </div>

        <AudioPlayer 
          isPlaying={isPlaying} 
          onPlayPause={() => setIsPlaying(!isPlaying)}
          progress={progress}
          currentTime={formatTime(currentTime)}
          duration={meeting.duration}
        />

        <TranscriptView 
          transcript={transcriptLines as any}
          currentTimeSeconds={currentTime}
          onLineClick={handleTranscriptClick}
        />
      </div>

      {/* RIGHT COLUMN: AI Intelligence Panel (40%) */}
      <div className="w-full xl:w-[40%] flex flex-col h-full animate-in fade-in slide-in-from-right-8 duration-700 delay-500 fill-mode-both">
         <AIIntelligencePanel 
            summary={meeting.summary || "Đang tạo tóm tắt..."}
            decisions={meeting.decisions || []}
            actionItems={tasks}
            onToggleTask={toggleTask}
         />
      </div>

    </div>
  );
}

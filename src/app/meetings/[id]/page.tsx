"use client";

import { useState, useEffect, useRef } from 'react';
import { Clock, Loader2, ArrowLeft, Link2, ExternalLink } from 'lucide-react';
import { useParams } from 'next/navigation';
import { AudioPlayer } from '@/components/meetings/AudioPlayer';
import { TranscriptView } from '@/components/meetings/TranscriptView';
import { AIIntelligencePanel } from '@/components/meetings/AIIntelligencePanel';
import Link from 'next/link';

interface MeetingDetail {
  id: string;
  title: string;
  date: string;
  duration: string;
  status: string;
  summary: string;
  transcript: string;
  decisions: string[];
  action_items: any[];
  audio_url?: string | null;
  video_url?: string | null;
  link_url?: string | null;
}

export default function MeetingDetailPage() {
  const params = useParams();
  const id = params.id as string;
  
  const [meeting, setMeeting] = useState<MeetingDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0); 
  const [currentTime, setCurrentTime] = useState(0); 
  const [durationSeconds, setDurationSeconds] = useState(0);
  const [volume, setVolume] = useState(0.66);
  const [tasks, setTasks] = useState<any[]>([]);
  const [isReloadingTranscript, setIsReloadingTranscript] = useState(false);
  const [isTranscriptExpanded, setIsTranscriptExpanded] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const fetchDetail = async (options?: { silent?: boolean }) => {
    const silent = options?.silent;
    if (!silent) setIsLoading(true);
    try {
      const response = await fetch(`/api/meetings/${id}`);
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
      if (!silent) setIsLoading(false);
    }
  };

  useEffect(() => {
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

  const syncProgress = () => {
    const audio = audioRef.current;
    if (!audio) return;
    const current = audio.currentTime;
    const dur = audio.duration || durationSeconds || 1;
    setCurrentTime(Math.floor(current));
    setDurationSeconds(isNaN(dur) ? 0 : Math.floor(dur));
    setProgress(Math.min(100, (current / dur) * 100));
  };

  const handlePlayPause = () => {
    const audio = audioRef.current;
    if (!audio || !meeting.audio_url) return;
    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play();
      setIsPlaying(true);
    }
  };

  const handleSeek = (value: number) => {
    const audio = audioRef.current;
    if (!audio || !meeting.audio_url || !durationSeconds) return;
    const target = (value / 100) * (audio.duration || durationSeconds);
    audio.currentTime = target;
    setCurrentTime(Math.floor(target));
    setProgress(value);
  };

  const handleVolumeChange = (value: number) => {
    setVolume(value);
    if (audioRef.current) {
      audioRef.current.volume = value;
    }
  };

  const handleTranscriptClick = (seconds: number) => {
    if (!Number.isFinite(seconds) || seconds < 0 || !meeting.audio_url) return;
    const audio = audioRef.current;
    if (!audio) return;

    const dur = durationSeconds || audio.duration;
    if (!Number.isFinite(dur) || dur <= 0) return;

    const clamped = Math.min(seconds, dur);
    audio.currentTime = clamped;
    setCurrentTime(Math.floor(clamped));
    setProgress((clamped / dur) * 100);
    audio.play();
    setIsPlaying(true);
  };

  const handleReloadTranscript = async () => {
    setIsReloadingTranscript(true);
    try {
      // Gọi API để trigger AI dịch lại transcript
      const response = await fetch(`/api/meetings/${id}/reprocess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        // Polling để chờ kết quả xử lý
        const pollInterval = setInterval(async () => {
          const detailResponse = await fetch(`/api/meetings/${id}`);
          if (detailResponse.ok) {
            const data = await detailResponse.json();
            if (data.status === 'HOÀN THÀNH' || data.status === 'LỖI') {
              clearInterval(pollInterval);
              setMeeting(data);
              setTasks(data.action_items || []);
              setIsReloadingTranscript(false);
            }
          }
        }, 2000); // Check mỗi 2 giây
      } else {
        console.error('Failed to reprocess transcript');
        setIsReloadingTranscript(false);
      }
    } catch (error) {
      console.error('Error reprocessing transcript:', error);
      setIsReloadingTranscript(false);
    }
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
           {/* Meeting Link */}
           {meeting.link_url && (
             <a
               href={meeting.link_url}
               target="_blank"
               rel="noopener noreferrer"
               className="mt-3 inline-flex items-center gap-2 text-sm text-accent hover:text-accent/80 transition-colors group"
             >
               <Link2 size={16} />
               <span className="truncate max-w-md">{meeting.link_url}</span>
               <ExternalLink size={14} className="opacity-0 group-hover:opacity-100 transition-opacity" />
             </a>
           )}
        </div>

        <AudioPlayer 
            isPlaying={isPlaying} 
            onPlayPause={handlePlayPause}
            onSeek={handleSeek}
            progress={progress}
            currentTime={formatTime(currentTime)}
            duration={durationSeconds ? formatTime(Math.max(durationSeconds - currentTime, 0)) : meeting.duration}
            volume={volume}
            onVolumeChange={handleVolumeChange}
            disabled={!meeting.audio_url || !!audioError}
            error={audioError}
        />

          <audio
            ref={audioRef}
            src={`/api/meetings/${id}/stream`}
            onTimeUpdate={syncProgress}
            onLoadedMetadata={syncProgress}
            onEnded={() => setIsPlaying(false)}
            onError={(e) => {
              console.error('Audio error:', e);
              setAudioError('Không thể tải audio. File có thể đang được xử lý hoặc không khả dụng.');
              setIsPlaying(false);
            }}
            className="hidden"
          />

        <TranscriptView 
          transcript={transcriptLines as any}
          currentTimeSeconds={currentTime}
          onLineClick={handleTranscriptClick}
          onReload={handleReloadTranscript}
          reloading={isReloadingTranscript}
          expanded={isTranscriptExpanded}
          onToggleExpand={() => setIsTranscriptExpanded((v) => !v)}
        />
      </div>

      {/* RIGHT COLUMN: AI Intelligence Panel (40%) */}
      <div className="w-full xl:w-[40%] flex flex-col h-full animate-in fade-in slide-in-from-right-8 duration-700 delay-500 fill-mode-both">
         <AIIntelligencePanel
            summary={meeting.summary || "Đang tạo tóm tắt..."}
            decisions={meeting.decisions || []}
            actionItems={tasks}
            onToggleTask={toggleTask}
            meetingId={id}
         />
      </div>

    </div>
  );
}

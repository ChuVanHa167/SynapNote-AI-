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
  status: string;
  summary: string;
  transcript: string;
  audio_url?: string | null;
  video_url?: string | null;
  decisions: string[];
  action_items: any[];
}

import { VideoPlayer } from '@/components/meetings/VideoPlayer';

const API_BASE_URL = "http://localhost:8000";

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
  const [seekTo, setSeekTo] = useState<number | undefined>(undefined);
  // v2.3 FIX - Robust Transcript Parser (Moved to top level to follow Hook rules)
  const [parsedTranscript, setParsedTranscript] = useState<any[]>([]);

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

  useEffect(() => {
    if (!meeting?.transcript) {
      setParsedTranscript([]);
      return;
    }

    try {
      const parsed = JSON.parse(meeting.transcript);
      if (Array.isArray(parsed)) {
        setParsedTranscript(parsed);
        return;
      }
    } catch (e) {}

    const segments = meeting.transcript.split(/\n\s*\n/);
    const result: any[] = [];
    segments.forEach((segment, index) => {
      const timeMatch = segment.match(/\[(\d{2}):(\d{2})\s*-\s*(\d{2}):(\d{2})\]/);
      if (timeMatch) {
        const startSec = parseInt(timeMatch[1]) * 60 + parseInt(timeMatch[2]);
        let content = segment.replace(timeMatch[0], "").trim();
        let speaker = "AI";
        const speakerMatch = content.match(/^\[(.*?)\]:/);
        if (speakerMatch) {
          speaker = speakerMatch[1];
          content = content.replace(speakerMatch[0], "").trim();
        }
        result.push({ id: String(index + 1), time: `${timeMatch[1]}:${timeMatch[2]}`, seconds: startSec, speaker, text: content });
      }
    });

    if (result.length > 0) {
      setParsedTranscript(result);
    } else {
      setParsedTranscript([{ id: '1', time: '00:00', seconds: 0, speaker: 'AI', text: meeting.transcript }]);
    }
  }, [meeting?.transcript]);

  /* v2.2 FIX - DIAGNOSTIC LOGS */
  useEffect(() => {
    if (meeting) {
      console.log("[v2.2] Meeting loaded:", {
        id: meeting.id,
        status: meeting.status,
        video_url: meeting.video_url,
        audio_url: meeting.audio_url
      });
    }
  }, [meeting]);

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
    setSeekTo(seconds);
    setCurrentTime(seconds);
    setIsPlaying(true);
    // Reset seekTo after a short delay
    setTimeout(() => setSeekTo(undefined), 100);
  };

  const toggleTask = (taskId: string) => {
    setTasks(tasks.map(t => t.id === taskId ? { ...t, status: t.status === 'completed' ? 'pending' : 'completed' } : t));
  };

  // Parser hooks moved to top level

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
            <span className="w-1 h-1 rounded-full bg-accent/50"></span>
            <span className={`px-2 py-0.5 rounded-full text-[10px] ${meeting.status === 'HOÀN THÀNH' ? 'bg-emerald-500/10 text-emerald-500' :
                meeting.status === 'LỖI' ? 'bg-red-500/10 text-red-500' :
                  'bg-blue-500/10 text-blue-400 animate-pulse'
              }`}>
              {meeting.status}
            </span>
          </div>
          <h1 className="text-3xl lg:text-4xl font-light tracking-tight text-foreground/90">{meeting.title} <span className="opacity-30 text-xs">[v2.2 FIX]</span></h1>
        </div>

        {meeting.video_url ? (
          <VideoPlayer
            videoUrl={`${API_BASE_URL}${meeting.video_url}`}
            duration={meeting.duration}
            title={meeting.title}
            onTimeUpdate={setCurrentTime}
            seekTo={seekTo}
          />
        ) : (
          <AudioPlayer
            isPlaying={isPlaying}
            onPlayPause={() => setIsPlaying(!isPlaying)}
            progress={progress}
            currentTime={formatTime(currentTime)}
            duration={meeting.duration}
            audioUrl={meeting.audio_url ? `${API_BASE_URL}${meeting.audio_url}` : null}
            onTimeUpdate={setCurrentTime}
            seekTo={seekTo}
          />
        )}

        <TranscriptView
          transcript={parsedTranscript}
          currentTimeSeconds={currentTime}
          onLineClick={handleTranscriptClick}
          status={meeting.status}
        />
      </div>

      {/* RIGHT COLUMN: AI Intelligence Panel (40%) */}
      <div className="w-full xl:w-[40%] flex flex-col h-full animate-in fade-in slide-in-from-right-8 duration-700 delay-500 fill-mode-both">
        <AIIntelligencePanel
          meetingId={meeting.id}
          summary={meeting.summary || "Đang tạo tóm tắt..."}
          decisions={meeting.decisions || []}
          actionItems={tasks}
          onToggleTask={toggleTask}
          status={meeting.status}
        />
      </div>

    </div>
  );
}

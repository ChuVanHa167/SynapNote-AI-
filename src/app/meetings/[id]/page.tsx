"use client";

import { useState, useEffect } from 'react';
import { Clock, Loader2, ArrowLeft, RotateCw, Trash2 } from 'lucide-react';
import { useParams, useRouter } from 'next/navigation';
import { AudioPlayer } from '@/components/meetings/AudioPlayer';
import { TranscriptView } from '@/components/meetings/TranscriptView';
import { AIIntelligencePanel } from '@/components/meetings/AIIntelligencePanel';
import Link from 'next/link';
import { DeleteModal } from '@/components/meetings/DeleteModal';
import { VideoPlayer } from '@/components/meetings/VideoPlayer';

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
  const [parsedTranscript, setParsedTranscript] = useState<any[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/meetings/${id}`);
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
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleTranscriptClick = (seconds: number) => {
    setSeekTo(seconds);
    setCurrentTime(seconds);
    setIsPlaying(true);
    setTimeout(() => setSeekTo(undefined), 100);
  };

  const toggleTask = (taskId: string) => {
    setTasks(tasks.map(t => t.id === taskId ? { ...t, status: t.status === 'completed' ? 'pending' : 'completed' } : t));
  };

  const handleReprocess = async () => {
    if (!id || isLoading) return;
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/meetings/${id}/reprocess`, {
        method: 'POST',
      });
      if (response.ok) {
        const updatedMeeting = await response.json();
        setMeeting(updatedMeeting);
        alert("Đã bắt đầu xử lý lại bản dịch. Vui lòng đợi trong giây lát.");
      } else {
        alert("Không thể yêu cầu xử lý lại.");
      }
    } catch (error) {
      console.error("Reprocess failed:", error);
      alert("Lỗi kết nối khi yêu cầu xử lý lại.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/meetings/${id}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setTimeout(() => {
          router.push('/meetings');
        }, 2100);
      } else {
        throw new Error("Failed to delete");
      }
    } catch (error) {
      console.error("Delete failed:", error);
      throw error;
    }
  };

  return (
    <div className="w-full max-w-[1700px] mx-auto p-4 lg:p-8 h-[calc(100vh-6rem)] flex flex-col xl:flex-row gap-6">

      {/* LEFT COLUMN: Media & Transcript */}
      <div className={`flex flex-col gap-6 h-full min-h-[600px] transition-all duration-700 ${isExpanded ? 'w-full' : 'w-full xl:w-[60%]'}`}>
        <div className="animate-in fade-in slide-in-from-left-4 duration-700 flex items-center justify-between">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3 text-xs tracking-widest font-medium uppercase text-foreground/40">
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
            <h1 className="text-3xl lg:text-4xl font-light tracking-tight text-foreground/90">{meeting.title}</h1>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleReprocess}
              disabled={meeting.status === 'ĐANG XỬ LÝ'}
              className={`group flex items-center gap-2 px-5 py-2.5 rounded-full glass-panel-hover border border-white/5 text-xs font-medium text-foreground/60 transition-all hover:border-accent/20 hover:text-accent ${meeting.status === 'ĐANG XỬ LÝ' ? 'opacity-40 cursor-not-allowed' : ''}`}
            >
              <RotateCw size={14} className={meeting.status === 'ĐANG XỬ LÝ' ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'} />
              <span>Tải lại bản dịch</span>
            </button>

            <button
              onClick={() => setShowDeleteModal(true)}
              className="group flex items-center gap-2 px-5 py-2.5 rounded-full glass-panel-hover border border-white/5 text-xs font-medium text-red-400/60 transition-all hover:border-red-500/20 hover:text-red-500"
            >
              <Trash2 size={14} className="group-hover:scale-110 transition-transform" />
              <span>Xóa</span>
            </button>

            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="group flex items-center gap-2 px-5 py-2.5 rounded-full glass-panel-hover border border-white/5 text-xs font-medium text-foreground/60 transition-all hover:border-accent/20 hover:text-accent"
            >
              <div className={`p-1.5 rounded-lg bg-white/5 group-hover:bg-accent/10 transition-colors`}>
                <svg className={`w-4 h-4 transition-transform duration-500 ${isExpanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isExpanded ? "M11 19l-7-7 7-7m8 14l-7-7 7-7" : "M13 5l7 7-7 7M5 5l7 7-7 7"} />
                </svg>
              </div>
              <span>{isExpanded ? "Thu gọn màn hình" : "Mở rộng bản dịch"}</span>
            </button>
          </div>
        </div>

        <div className={`transition-all duration-700 ${isExpanded ? 'order-2 w-full xl:max-w-2xl self-center' : 'order-1 w-full'}`}>
          {meeting.audio_url ? (
            <AudioPlayer
              isPlaying={isPlaying}
              onPlayPause={() => setIsPlaying(!isPlaying)}
              progress={progress}
              currentTime={formatTime(currentTime)}
              duration={meeting.duration}
              audioUrl={`${API_BASE_URL}${meeting.audio_url}`}
              onTimeUpdate={setCurrentTime}
              seekTo={seekTo}
            />
          ) : meeting.video_url ? (
            <VideoPlayer
              videoUrl={`${API_BASE_URL}${meeting.video_url}`}
              duration={meeting.duration}
              title={meeting.title}
              onTimeUpdate={setCurrentTime}
              seekTo={seekTo}
            />
          ) : (
            <div className="glass-panel rounded-[2rem] h-48 flex items-center justify-center border border-dashed border-border/40">
              <p className="text-foreground/40 text-sm">Đang chuẩn bị file âm thanh...</p>
            </div>
          )}
        </div>

        <div className={`transition-all duration-700 flex flex-col min-h-0 ${isExpanded ? 'order-1 flex-1 h-full' : 'order-2'}`}>
          <TranscriptView
            transcript={parsedTranscript}
            currentTimeSeconds={currentTime}
            onLineClick={handleTranscriptClick}
            status={meeting.status}
          />
        </div>
      </div>

      {!isExpanded && (
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
      )}

      <DeleteModal 
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDelete}
        title="Xác nhận xóa bản ghi"
      />
    </div>
  );
}

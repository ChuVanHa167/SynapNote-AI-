import { FileText, Search, Loader2, Clock } from 'lucide-react';
import { TranscriptLine } from '@/types/meeting';

interface TranscriptViewProps {
  transcript: TranscriptLine[];
  currentTimeSeconds: number;
  onLineClick: (seconds: number) => void;
  status?: string;
}

interface TimeSegment {
  startTime: number;
  endTime: number;
  lines: TranscriptLine[];
}

const formatSegmentTime = (seconds: number) => {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
};

const groupByTimeSegments = (transcript: TranscriptLine[], segmentDuration: number = 30): TimeSegment[] => {
  if (transcript.length === 0) return [];
  
  const segments: TimeSegment[] = [];
  let currentSegmentStart = 0;
  let currentSegment: TranscriptLine[] = [];

  transcript.forEach((line) => {
    const nextSegmentStart = currentSegmentStart + segmentDuration;
    
    if (line.seconds >= nextSegmentStart) {
      if (currentSegment.length > 0) {
        segments.push({
          startTime: currentSegmentStart,
          endTime: currentSegmentStart + segmentDuration,
          lines: currentSegment,
        });
      }
      
      currentSegmentStart = Math.floor(line.seconds / segmentDuration) * segmentDuration;
      currentSegment = [line];
    } else {
      currentSegment.push(line);
    }
  });

  if (currentSegment.length > 0) {
    segments.push({
      startTime: currentSegmentStart,
      endTime: currentSegmentStart + segmentDuration,
      lines: currentSegment,
    });
  }

  return segments;
};

export function TranscriptView({ transcript, currentTimeSeconds, onLineClick, status }: TranscriptViewProps) {
  const segments = groupByTimeSegments(transcript);

  return (
    <div className="glass-panel flex-1 rounded-[2rem] flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-8 duration-700 delay-300 fill-mode-both border border-border">
      <div className="px-8 py-5 border-b border-border flex items-center justify-between bg-card/20 z-10">
        <h3 className="text-sm font-medium tracking-widest uppercase text-foreground/90 flex items-center gap-3">
          <FileText size={16} className="text-accent" />
          Bản dịch
        </h3>
        <button className="text-foreground/80 hover:text-accent transition-colors">
          <Search size={18} strokeWidth={1.5} />
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6 space-y-4 relative scroll-smooth" id="transcript-container">
        {transcript.length > 0 ? (
          segments.map((segment, segmentIndex) => {
            const isSegmentActive = currentTimeSeconds >= segment.startTime && currentTimeSeconds < segment.endTime;
            
            return (
              <div key={`segment-${segmentIndex}`} className="space-y-3">
                {/* Time Segment Header */}
                <div 
                  className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-all duration-500 ${
                    isSegmentActive 
                      ? 'bg-accent/10 border border-accent/30' 
                      : 'bg-card/20 border border-border/30'
                  }`}
                  id={`segment-${segment.startTime}`}
                >
                  <Clock size={14} className={isSegmentActive ? 'text-accent' : 'text-foreground/50'} />
                  <span className={`text-xs font-mono font-semibold tracking-wider ${
                    isSegmentActive ? 'text-accent' : 'text-foreground/60'
                  }`}>
                    {formatSegmentTime(segment.startTime)} - {formatSegmentTime(segment.endTime)}
                  </span>
                  {isSegmentActive && (
                    <span className="ml-auto text-xs text-accent font-medium">Phát hiện</span>
                  )}
                </div>

                {/* Transcript Lines in Segment */}
                {segment.lines.map((line) => {
                  const isActive = currentTimeSeconds >= line.seconds && currentTimeSeconds < line.seconds + 15;
                  return (
                    <div 
                      key={line.id} 
                      id={`transcript-line-${line.id}`}
                      onClick={() => onLineClick(line.seconds)}
                      className={`flex gap-6 p-4 rounded-xl cursor-pointer transition-all duration-500 group ${
                        isActive 
                          ? 'bg-accent/10 border border-accent/30 shadow-[inset_4px_0_0_rgba(212,175,55,1)] scale-[1.01] transform-gpu ml-4' 
                          : 'hover:bg-card/40 border border-transparent opacity-75 hover:opacity-100 ml-2'
                      }`}
                      ref={(el) => {
                        if (isActive && el) {
                          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                      }}
                    >
                      <div className={`text-xs font-mono mt-1 min-w-[45px] transition-colors duration-500 ${
                        isActive ? 'text-accent font-bold' : 'text-foreground/40 group-hover:text-foreground/80'
                      }`}>
                        {line.time}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-foreground/80 mb-1 flex items-center gap-2 text-xs tracking-widest uppercase opacity-80">
                          {line.speaker}
                        </div>
                        <p className={`leading-relaxed text-sm transition-colors duration-500 ${
                          isActive ? 'text-foreground' : 'text-foreground/80'
                        }`}>{line.text}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-foreground/30 gap-4 py-20">
            <Loader2 className={`animate-spin ${status === 'LỖI' ? 'hidden' : ''}`} size={24} />
            <p className="text-sm italic">
              {status === 'HOÀN THÀNH' ? 'Không có nội dung bản dịch.' : 
               status === 'LỖI' ? 'Lỗi khi trích xuất bản dịch.' : 
               'AI đang trích xuất bản dịch, vui lòng đợi...'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

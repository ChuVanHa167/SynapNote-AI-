import { FileText, Search, Loader2 } from 'lucide-react';
import { TranscriptLine } from '@/types/meeting';

interface TranscriptViewProps {
  transcript: TranscriptLine[];
  currentTimeSeconds: number;
  onLineClick: (seconds: number) => void;
  status?: string;
}

export function TranscriptView({ transcript, currentTimeSeconds, onLineClick, status }: TranscriptViewProps) {
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
      
      <div className="flex-1 overflow-y-auto p-6 space-y-2 relative scroll-smooth" id="transcript-container">
        {transcript.length > 0 ? (
          transcript.map((line) => {
            const isActive = currentTimeSeconds >= line.seconds && currentTimeSeconds < line.seconds + 15;
            return (
              <div 
                key={line.id} 
                id={`transcript-line-${line.id}`}
                onClick={() => onLineClick(line.seconds)}
                className={`flex gap-6 p-4 rounded-2xl cursor-pointer transition-all duration-500 group hover:pl-6 ${
                  isActive 
                    ? 'bg-accent/5 border border-accent/20 shadow-[inset_4px_0_0_rgba(212,175,55,1)] scale-[1.02] transform-gpu' 
                    : 'hover:bg-card/40 border border-transparent opacity-60 hover:opacity-100'
                }`}
                ref={(el) => {
                  if (isActive && el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  }
                }}
              >
                <div className={`text-xs font-mono mt-1 min-w-[45px] transition-colors duration-500 ${isActive ? 'text-accent' : 'text-foreground/30 group-hover:text-foreground/90'}`}>
                  {line.time}
                </div>
                <div>
                  <div className="font-medium text-foreground/80 mb-1 flex items-center gap-2 text-sm tracking-wide">
                    {line.speaker}
                  </div>
                  <p className={`leading-relaxed text-sm font-medium transition-colors duration-500 ${isActive ? 'text-foreground/90' : 'text-foreground/90'}`}>{line.text}</p>
                </div>
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

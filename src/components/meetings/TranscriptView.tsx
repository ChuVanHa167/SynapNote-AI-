import { FileText, Search, RefreshCw, Maximize2, Minimize2 } from 'lucide-react';
import { TranscriptLine } from '@/types/meeting';

interface TranscriptViewProps {
  transcript: TranscriptLine[];
  currentTimeSeconds: number;
  onLineClick: (seconds: number) => void;
  onReload: () => void;
  reloading?: boolean;
  expanded?: boolean;
  onToggleExpand?: () => void;
}

export function TranscriptView({ transcript, currentTimeSeconds, onLineClick, onReload, reloading = false, expanded = false, onToggleExpand }: TranscriptViewProps) {
  return (
    <div className={`glass-panel flex-1 rounded-[2rem] flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-8 duration-700 delay-300 fill-mode-both border border-border ${expanded ? 'min-h-[520px]' : ''}`}>
      <div className="px-8 py-5 border-b border-border flex items-center justify-between bg-card/20 z-10 gap-3">
        <h3 className="text-sm font-medium tracking-widest uppercase text-foreground/90 flex items-center gap-3">
          <FileText size={16} className="text-accent" />
          Bản dịch
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={onReload}
            className="text-foreground/80 hover:text-accent transition-colors flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-lg border border-border"
            disabled={reloading}
          >
            <RefreshCw size={14} className={reloading ? 'animate-spin' : ''} />
            {reloading ? 'Đang tải...' : 'Tải lại'}
          </button>
          <button
            onClick={onToggleExpand}
            className="text-foreground/80 hover:text-accent transition-colors p-2 rounded-lg border border-transparent"
          >
            {expanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
          <button className="text-foreground/80 hover:text-accent transition-colors">
            <Search size={18} strokeWidth={1.5} />
          </button>
        </div>
      </div>
      
      <div className={`flex-1 overflow-y-auto p-6 space-y-3 relative scroll-smooth text-base ${expanded ? 'max-h-[70vh]' : ''}`} id="transcript-container">
        {transcript.map((line) => {
          const isActive = currentTimeSeconds >= line.seconds && currentTimeSeconds < line.seconds + 15;
          return (
            <div
              key={line.id}
              id={`transcript-line-${line.id}`}
              onClick={() => onLineClick(line.seconds)}
              className={`flex gap-6 p-4 rounded-2xl cursor-pointer transition-all duration-500 ${
                isActive
                  ? 'bg-accent/5 border border-accent/20 shadow-[inset_4px_0_0_rgba(212,175,55,1)]'
                  : 'border border-transparent opacity-60'
              }`}
              ref={(el) => {
                if (isActive && el) {
                  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
              }}
            >
              <div className="text-xs font-mono mt-1 min-w-[45px] text-foreground/30">
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
        })}
      </div>
    </div>
  );
}

import { Play, Pause, Rewind, FastForward, Volume2 } from 'lucide-react';

interface AudioPlayerProps {
  isPlaying: boolean;
  onPlayPause: () => void;
  progress: number;
  currentTime: string;
  duration: string;
}

export function AudioPlayer({ isPlaying, onPlayPause, progress, currentTime, duration }: AudioPlayerProps) {
  return (
    <div className="glass-panel rounded-[2rem] p-6 lg:p-10 relative overflow-hidden group animate-in fade-in zoom-in-95 duration-700 delay-150 fill-mode-both border border-border">
      <div className="absolute -top-32 -right-32 w-64 h-64 bg-accent/10 rounded-full blur-[80px] group-hover:bg-accent/20 transition-colors duration-700"></div>
      
      <div className="flex items-center justify-between z-10 w-full relative">
        <div className="flex items-center gap-8">
          <button 
            onClick={onPlayPause}
            className="w-16 h-16 rounded-full bg-accent text-accent-foreground flex items-center justify-center hover:scale-105 transition-all duration-500 shadow-[0_0_20px_rgba(212,175,55,0.2)] hover:shadow-[0_0_30px_rgba(212,175,55,0.4)]"
          >
            {isPlaying ? <Pause size={24} fill="currentColor" /> : <Play size={24} fill="currentColor" className="ml-1" />}
          </button>
          
          <div className="flex items-center gap-6 text-foreground/80">
            <button className="hover:text-foreground transition-colors hover:scale-110 duration-300"><Rewind size={20} /></button>
            <button className="hover:text-foreground transition-colors hover:scale-110 duration-300"><FastForward size={20} /></button>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-4 text-foreground/80 glass-panel px-4 py-2 rounded-full">
          <Volume2 size={16} />
          <div className="w-20 h-1 bg-foreground/10 rounded-full overflow-hidden">
            <div className="w-2/3 h-full bg-foreground/50 rounded-full"></div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4 text-xs font-medium z-10 w-full mt-8 relative">
        <span className="text-accent min-w-[40px] tracking-wider">{currentTime}</span>
        <div className="flex-1 h-1.5 bg-foreground/5 rounded-full relative cursor-pointer group shadow-inner overflow-hidden">
          <div className="absolute top-0 left-0 h-full bg-gradient-to-r from-accent/50 to-accent rounded-full transition-all duration-300 relative" style={{ width: `${progress}%` }}>
             <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-3 bg-white rounded-full shadow-[0_0_10px_rgba(255,255,255,0.8)]"></div>
          </div>
        </div>
        <span className="text-foreground/30 min-w-[40px] tracking-wider">-{duration}</span>
      </div>
    </div>
  );
}

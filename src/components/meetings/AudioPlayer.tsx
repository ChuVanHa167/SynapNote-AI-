import { Play, Pause, Rewind, FastForward, Volume2, VolumeX } from 'lucide-react';

interface AudioPlayerProps {
  isPlaying: boolean;
  onPlayPause: () => void;
  onSeek: (value: number) => void;
  progress: number;
  currentTime: string;
  duration: string;
  volume: number;
  onVolumeChange: (value: number) => void;
}

export function AudioPlayer({ isPlaying, onPlayPause, onSeek, progress, currentTime, duration, volume, onVolumeChange }: AudioPlayerProps) {
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
          {volume === 0 ? <VolumeX size={16} /> : <Volume2 size={16} />}
          <input
            type="range"
            min={0}
            max={100}
            value={Math.round(volume * 100)}
            onChange={(e) => onVolumeChange(Number(e.target.value) / 100)}
            className="w-24 h-1 accent-accent/80"
          />
        </div>
      </div>

      <div className="flex items-center gap-4 text-xs font-medium z-10 w-full mt-8 relative">
        <span className="text-accent min-w-[40px] tracking-wider">{currentTime}</span>
        <input
          type="range"
          min={0}
          max={100}
          value={progress}
          onChange={(e) => onSeek(Number(e.target.value))}
          className="flex-1 h-1.5 bg-foreground/5 rounded-full relative cursor-pointer group shadow-inner overflow-hidden accent-accent/80"
        />
        <span className="text-foreground/30 min-w-[40px] tracking-wider">-{duration}</span>
      </div>
    </div>
  );
}

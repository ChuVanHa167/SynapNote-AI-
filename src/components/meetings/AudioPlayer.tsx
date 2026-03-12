import { Play, Pause, Rewind, FastForward, Volume2 } from 'lucide-react';
import { useRef, useEffect, useState } from 'react';

interface AudioPlayerProps {
  isPlaying: boolean;
  onPlayPause: () => void;
  progress: number;
  currentTime: string;
  duration: string;
  audioUrl?: string | null;
}

export function AudioPlayer({ isPlaying, onPlayPause, progress: initialProgress, currentTime: initialCurrentTime, duration, audioUrl }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [progress, setProgress] = useState(initialProgress);
  const [currentTime, setCurrentTime] = useState(initialCurrentTime);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.play().catch(err => console.error("Playback failed:", err));
    } else {
      audio.pause();
    }
  }, [isPlaying]);

  const handleTimeUpdate = () => {
    const audio = audioRef.current;
    if (!audio) return;
    
    const current = audio.currentTime;
    const total = audio.duration || 1;
    setProgress((current / total) * 100);
    
    const m = Math.floor(current / 60).toString().padStart(2, '0');
    const s = Math.floor(current % 60).toString().padStart(2, '0');
    setCurrentTime(`${m}:${s}`);
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percent = Math.max(0, Math.min(100, (x / rect.width) * 100));
    audio.currentTime = (percent / 100) * audio.duration;
  };

  return (
    <div className="glass-panel rounded-[2rem] p-6 lg:p-10 relative overflow-hidden group animate-in fade-in zoom-in-95 duration-700 delay-150 fill-mode-both border border-border">
      {audioUrl && (
        <audio 
          ref={audioRef} 
          src={audioUrl} 
          onTimeUpdate={handleTimeUpdate}
          onEnded={() => { if (isPlaying) onPlayPause(); }}
          onCanPlay={() => setIsReady(true)}
        />
      )}
      
      <div className="absolute -top-32 -right-32 w-64 h-64 bg-accent/10 rounded-full blur-[80px] group-hover:bg-accent/20 transition-colors duration-700"></div>
      
      <div className="flex items-center justify-between z-10 w-full relative">
        <div className="flex items-center gap-8">
          <button 
            onClick={onPlayPause}
            disabled={!audioUrl || !isReady}
            className={`w-16 h-16 rounded-full bg-accent text-accent-foreground flex items-center justify-center hover:scale-105 transition-all duration-500 shadow-[0_0_20px_rgba(212,175,55,0.2)] hover:shadow-[0_0_30px_rgba(212,175,55,0.4)] ${(!audioUrl || !isReady) ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isPlaying ? <Pause size={24} fill="currentColor" /> : <Play size={24} fill="currentColor" className="ml-1" />}
          </button>
          
          <div className="flex items-center gap-6 text-foreground/80">
            <button 
              onClick={() => { if (audioRef.current) audioRef.current.currentTime -= 10; }}
              className="hover:text-foreground transition-colors hover:scale-110 duration-300"
            >
              <Rewind size={20} />
            </button>
            <button 
              onClick={() => { if (audioRef.current) audioRef.current.currentTime += 10; }}
              className="hover:text-foreground transition-colors hover:scale-110 duration-300"
            >
              <FastForward size={20} />
            </button>
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
        <div 
          onClick={handleSeek}
          className="flex-1 h-1.5 bg-foreground/5 rounded-full relative cursor-pointer group shadow-inner overflow-hidden"
        >
          <div className="absolute top-0 left-0 h-full bg-gradient-to-r from-accent/50 to-accent rounded-full transition-all duration-300 relative" style={{ width: `${progress}%` }}>
             <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-3 bg-white rounded-full shadow-[0_0_10px_rgba(255,255,255,0.8)]"></div>
          </div>
        </div>
        <span className="text-foreground/30 min-w-[40px] tracking-wider">{duration}</span>
      </div>
    </div>
  );
}

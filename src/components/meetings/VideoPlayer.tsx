"use client";

import { Play, Pause, Rewind, FastForward, Volume2, VolumeX, Maximize } from 'lucide-react';
import { useRef, useEffect, useState } from 'react';

interface VideoPlayerProps {
  videoUrl: string;
  duration: string;
  title?: string;
  onTimeUpdate?: (seconds: number) => void;
  seekTo?: number;
}

export function VideoPlayer({ videoUrl, duration, title, onTimeUpdate, seekTo }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTimeFormatted, setCurrentTimeFormatted] = useState("00:00");
  const [isReady, setIsReady] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [showControls, setShowControls] = useState(true);
  let controlsTimeout: NodeJS.Timeout;

  const playPromiseRef = useRef<Promise<void> | null>(null);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      if (playPromiseRef.current !== null) {
        playPromiseRef.current.then(() => {
          videoRef.current?.pause();
        }).catch(() => {
          videoRef.current?.pause();
        });
      } else {
        videoRef.current.pause();
      }
    } else {
      playPromiseRef.current = videoRef.current.play();
      playPromiseRef.current.catch(err => {
        if (err.name !== 'AbortError') {
          console.error("Video playback failed:", err);
        }
      });
    }
    setIsPlaying(!isPlaying);
  };

  // Handle seekTo from parent
  useEffect(() => {
    if (videoRef.current && typeof seekTo === 'number') {
      videoRef.current.currentTime = seekTo;
    }
  }, [seekTo]);

  const handleTimeUpdate = () => {
    const video = videoRef.current;
    if (!video) return;

    const current = video.currentTime;
    const total = video.duration || 1;
    setProgress((current / total) * 100);

    const m = Math.floor(current / 60).toString().padStart(2, '0');
    const s = Math.floor(current % 60).toString().padStart(2, '0');
    setCurrentTimeFormatted(`${m}:${s}`);

    if (onTimeUpdate) onTimeUpdate(current);
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    const video = videoRef.current;
    if (!video) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percent = Math.max(0, Math.min(100, (x / rect.width) * 100));
    video.currentTime = (percent / 100) * video.duration;
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
      videoRef.current.muted = newVolume === 0;
      setIsMuted(newVolume === 0);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      const newMuted = !isMuted;
      setIsMuted(newMuted);
      videoRef.current.muted = newMuted;
      if (newMuted) {
        setVolume(0);
      } else {
        setVolume(videoRef.current.volume || 1);
      }
    }
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      containerRef.current.requestFullscreen();
    }
  };

  const handleMouseMove = () => {
    setShowControls(true);
    clearTimeout(controlsTimeout);
    controlsTimeout = setTimeout(() => {
      if (isPlaying) setShowControls(false);
    }, 3000);
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      className="glass-panel rounded-[2rem] overflow-hidden relative group aspect-video bg-black/40 border border-border transition-all duration-700 shadow-2xl"
    >
      <video
        ref={videoRef}
        src={videoUrl}
        className="w-full h-full object-contain cursor-pointer"
        onClick={togglePlay}
        onTimeUpdate={handleTimeUpdate}
        onCanPlay={() => setIsReady(true)}
        onEnded={() => setIsPlaying(false)}
      />

      {/* Overlay Controls */}
      <div className={`absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex flex-col justify-end p-6 lg:p-8 transition-opacity duration-500 ${showControls ? 'opacity-100' : 'opacity-0'}`}>

        <div className="flex flex-col gap-6">
          {/* Progress Bar */}
          <div
            onClick={handleSeek}
            className="w-full h-1.5 bg-white/10 rounded-full relative cursor-pointer group/progress overflow-hidden"
          >
            <div
              className="absolute top-0 left-0 h-full bg-accent rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            >
              <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-[0_0_10px_white] scale-0 group-hover/progress:scale-100 transition-transform"></div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <button
                onClick={togglePlay}
                className="w-12 h-12 rounded-full bg-accent text-accent-foreground flex items-center justify-center hover:scale-110 transition-transform"
              >
                {isPlaying ? <Pause size={20} fill="currentColor" /> : <Play size={20} fill="currentColor" className="ml-0.5" />}
              </button>

              <div className="flex items-center gap-6 text-white/70">
                <button onClick={() => { if (videoRef.current) videoRef.current.currentTime -= 10; }} className="hover:text-white transition-colors"><Rewind size={18} /></button>
                <button onClick={() => { if (videoRef.current) videoRef.current.currentTime += 10; }} className="hover:text-white transition-colors"><FastForward size={18} /></button>
              </div>

              <div className="text-xs font-mono text-white/50 flex items-center gap-2">
                <span className="text-accent">{currentTimeFormatted}</span>
                <span>/</span>
                <span>{duration}</span>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className="flex items-center gap-3 bg-white/5 px-4 py-2 rounded-full">
                <button onClick={toggleMute} className="text-white/60 hover:text-white transition-colors">
                  {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
                </button>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={volume}
                  onChange={handleVolumeChange}
                  className="w-20 h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-accent"
                />
              </div>
              <button onClick={toggleFullscreen} className="text-white/60 hover:text-white transition-colors">
                <Maximize size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Big Play Button Overlay when paused */}
      {!isPlaying && isReady && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-24 h-24 rounded-full bg-accent/20 backdrop-blur-sm border border-accent/30 flex items-center justify-center animate-pulse">
            <Play size={40} className="text-accent ml-2" fill="currentColor" />
          </div>
        </div>
      )}
    </div>
  );
}

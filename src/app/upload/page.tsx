"use client";

import { useState, useCallback, useRef, useEffect } from 'react';
import { UploadCloud, AudioLines, Type, Clock, FileVideo } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { ProcessingOverlay } from '@/components/upload/ProcessingOverlay';
import { useUpload } from '@/context/UploadContext';

export default function Home() {
  const { status, uploadFile, cancelUpload, resetUpload } = useUpload();
  const [isDragActive, setIsDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [currentTime, setCurrentTime] = useState<Date | null>(null);
  const [duration, setDuration] = useState<string>('0m 0s');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  // Handle Client-side only Time
  useEffect(() => {
    setCurrentTime(new Date());
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
  }, []);

  const getFileDuration = (file: File): Promise<string> => {
    return new Promise((resolve) => {
      const element = document.createElement(file.type.startsWith('video') ? 'video' : 'audio');
      element.preload = 'metadata';
      element.onloadedmetadata = () => {
        URL.revokeObjectURL(element.src);
        const seconds = Math.floor(element.duration);
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        resolve(`${minutes}m ${remainingSeconds}s`);
      };
      element.onerror = () => resolve("0m 0s");
      element.src = URL.createObjectURL(file);
    });
  };

  const handleUploadAction = async () => {
    if (!selectedFile) return;
    await uploadFile(selectedFile, title, duration);
  };

  const handleProcessingFinished = () => {
    const mid = status.meetingId;
    resetUpload();
    if (mid) {
      router.push(`/meetings/${mid}`);
    } else {
      router.push('/meetings');
    }
  };

  const handleCancelProcessing = () => {
    cancelUpload();
    setSelectedFile(null);
    setTitle('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      const dur = await getFileDuration(file);
      setDuration(dur);
    }
  }, []);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedFile(file);
      const dur = await getFileDuration(file);
      setDuration(dur);
    }
  };

  const isUploadingOrProcessing = status.isUploading || status.isProcessing;

  return (
    <div className="w-full max-w-7xl mx-auto p-6 lg:p-10 hide-scrollbar flex flex-col gap-10">
      <section className="animate-in fade-in slide-in-from-bottom-4 duration-700">
        <h1 className="text-3xl font-medium tracking-tight mb-2">
          <span className="text-foreground/90">Tải lên cuộc họp</span>
        </h1>
        <p className="text-foreground/80 text-sm tracking-wide">Tải lên file video hoặc audio để AI tự động trích xuất thông tin.</p>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full animate-in fade-in slide-in-from-bottom-8 duration-700 delay-150 fill-mode-both">
        <section className="col-span-1 glass-panel rounded-3xl p-8 border border-border/60 flex flex-col h-full bg-card/20 min-h-[400px]">
          <div className="mb-8 flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center">
              <Type className="text-accent" size={18} />
            </div>
            <h2 className="text-lg font-medium tracking-wide">Thiết lập Bản ghi</h2>
          </div>

          <div className="flex flex-col gap-2 flex-grow">
            <label htmlFor="meeting-title" className="text-sm text-foreground/70 font-medium ml-1">Tên tùy chỉnh</label>
            <input
              type="text"
              id="meeting-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Họp Sprint (Không bắt buộc)"
              className="w-full bg-background border border-border/80 rounded-xl px-4 py-3 text-sm outline-none focus:border-accent/60 transition-all"
              disabled={isUploadingOrProcessing}
            />
          </div>

          <div className="mt-8 pt-8 border-t border-border/40 grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <span className="text-[10px] text-foreground/40 uppercase tracking-widest font-semibold flex items-center gap-1.5"><Clock size={12} /> THỜI GIAN</span>
              <p className="text-sm font-medium text-foreground/80">
                {currentTime ? currentTime.toLocaleTimeString('vi-VN', { hour12: false }) : '--:--:--'}
              </p>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[10px] text-foreground/40 uppercase tracking-widest font-semibold flex items-center gap-1.5"><FileVideo size={12} /> ĐỊNH DẠNG</span>
              <p className="text-xs font-medium text-foreground/80">Audio, Video</p>
            </div>
          </div>

          <button
            className={`w-full mt-8 py-4 rounded-xl font-medium tracking-wide transition-all ${selectedFile && !isUploadingOrProcessing ? 'bg-accent text-accent-foreground shadow-lg hover:bg-accent/90' : 'bg-card/50 text-foreground/30 cursor-not-allowed'}`}
            disabled={!selectedFile || isUploadingOrProcessing}
            onClick={handleUploadAction}
          >
            {status.isUploading ? 'Đang tải lên...' : status.isProcessing ? 'Đang xử lý AI...' : 'Lưu bản ghi'}
          </button>
        </section>

        <section className="col-span-1 lg:col-span-2">
          <div
            className={`w-full glass-panel rounded-3xl border transition-all duration-500 flex flex-col items-center justify-center text-center cursor-pointer min-h-[450px] relative overflow-hidden group ${isDragActive ? 'border-accent scale-[1.01]' : 'border-border/60 hover:border-accent/40 bg-card/10'} ${isUploadingOrProcessing ? 'pointer-events-none opacity-90' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              accept=".mp4,.mov,.mp3,.wav"
              onChange={handleFileChange}
              disabled={isUploadingOrProcessing}
            />

            <div className="relative z-10 flex flex-col items-center p-8">
              {isUploadingOrProcessing ? (
                <div className="flex flex-col items-center">
                  <div className="w-24 h-24 rounded-full border border-accent/50 bg-accent/10 flex items-center justify-center mb-6 relative">
                    <span className="absolute inset-0 rounded-full border-t-2 border-accent animate-spin"></span>
                    <UploadCloud size={32} className="text-accent animate-pulse" />
                  </div>
                  <h3 className="text-2xl font-medium mb-2">{status.isUploading ? 'Tải lên...' : 'Xử lý...'}</h3>
                  <p className="text-accent/80 text-sm">{status.progress}%</p>
                  <button 
                    onClick={(e) => { e.stopPropagation(); handleCancelProcessing(); }}
                    className="mt-6 px-6 py-2 rounded-full border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors text-xs font-medium"
                  >
                    Hủy tải lên
                  </button>
                </div>
              ) : selectedFile ? (
                <div className="flex flex-col items-center">
                  <FileVideo size={36} className="text-accent mb-6" />
                  <h3 className="text-2xl font-medium mb-2 max-w-sm truncate">{selectedFile.name}</h3>
                  <p className="text-foreground/50 text-sm mb-8">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                  <button
                    className="px-6 py-2 rounded-full border border-border/80 text-foreground/60 hover:text-foreground transition-colors text-sm font-medium"
                    onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                  >
                    Hủy chọn
                  </button>
                </div>
              ) : (
                <>
                  <UploadCloud size={32} className="text-accent mb-4 group-hover:-translate-y-1 transition-transform" />
                  <h3 className="text-3xl font-medium mb-4">Kéo thả file vào đây</h3>
                  <p className="text-foreground/60 text-sm mb-12 max-w-sm leading-relaxed">
                    Hỗ trợ MP4, MOV, MP3, WAV. Nhấp để chọn bản ghi.
                  </p>
                  <div className="flex gap-4 text-[11px] font-semibold text-foreground/40 uppercase tracking-[0.15em] bg-background/30 py-3 px-6 rounded-2xl border border-border/40">
                    <span>MP4, MOV</span>
                    <span className="px-4 border-l border-r border-border/50">MP3, WAV</span>
                    <span>Max 1GB</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </section>
      </div>

      <ProcessingOverlay
        isVisible={isUploadingOrProcessing}
        meetingId={status.meetingId || undefined}
        onFinished={handleProcessingFinished}
        onCancel={handleCancelProcessing}
        uploadProgress={status.progress}
        stepOverride={status.step}
      />
    </div>
  );
}

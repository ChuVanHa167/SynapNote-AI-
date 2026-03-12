"use client";

import { useState, useCallback, useRef, useEffect } from 'react';
import { UploadCloud, AudioLines, Type, Clock, FileVideo } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { ProcessingOverlay } from '@/components/upload/ProcessingOverlay';

export default function Home() {
  const [isDragActive, setIsDragActive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [showOverlay, setShowOverlay] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [currentTime, setCurrentTime] = useState<Date | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  // Handle Client-side only Time to prevent hydration errors
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

  const handleUploadAction = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      // Send user's typed title if provided, else it will default in backend
      if (title.trim() !== '') {
        formData.append("title", title);
      }

      const response = await fetch("http://localhost:8000/meetings/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Lỗi khi tải file lên máy chủ");
      }

      const data = await response.json();
      console.log("Upload Success:", data);

      // Show processing overlay
      setShowOverlay(true);
      
    } catch (error) {
      console.error(error);
      alert("Tải lên thất bại. Vui lòng kiểm tra lại kết nối Backend.");
      setIsUploading(false);
    }
  };

  const handleProcessingFinished = () => {
    router.push(`/meetings`);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-6 lg:p-10 hide-scrollbar flex flex-col gap-10">

      {/* Welcome Title */}
      <section className="animate-in fade-in slide-in-from-bottom-4 duration-700">
        <h1 className="text-3xl font-medium tracking-tight mb-2">
          <span className="text-foreground/90">Tải lên cuộc họp</span>
        </h1>
        <p className="text-foreground/80 text-sm tracking-wide">Tải lên file video hoặc audio để AI tự động trích xuất thông tin.</p>
      </section>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full animate-in fade-in slide-in-from-bottom-8 duration-700 delay-150 fill-mode-both">

        {/* Left Column: Details */}
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
              placeholder="Ví dụ: Họp Sprint 4 (Không bắt buộc)"
              className="w-full bg-background border border-border/80 rounded-xl px-4 py-3 text-sm outline-none focus:border-accent/60 focus:ring-1 focus:ring-accent/60 transition-all text-foreground placeholder-foreground/30 shadow-inner"
              disabled={isUploading}
            />
            <p className="text-xs text-foreground/40 mt-1 ml-1 leading-relaxed">
              Nếu để trống, AI trên hệ thống sẽ tự đặt tên theo phân tích nội dung.
            </p>
          </div>

          <div className="mt-8 pt-8 border-t border-border/40 grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <span className="text-[10px] text-foreground/40 uppercase tracking-widest font-semibold flex items-center gap-1.5"><Clock size={12} /> THỜI GIAN UPLOAD</span>
              <p className="text-sm font-medium tracking-wide text-foreground/80 truncate">
                {currentTime ? currentTime.toLocaleTimeString('vi-VN', { hour12: false }) : '--:--:--'}
              </p>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[10px] text-foreground/40 uppercase tracking-widest font-semibold flex items-center gap-1.5"><FileVideo size={12} /> ĐỊNH DẠNG</span>
              <p className="text-xs font-medium tracking-wide text-foreground/80 break-words">Audio, Video</p>
            </div>
          </div>

          <button
            className={`w-full mt-8 py-4 rounded-xl font-medium tracking-wide transition-all ${selectedFile && !isUploading ? 'bg-accent text-accent-foreground shadow-[0_0_20px_rgba(212,175,55,0.3)] hover:bg-accent/90 focus:scale-[0.98]' : 'bg-card/50 text-foreground/30 cursor-not-allowed border border-border/50'}`}
            disabled={!selectedFile || isUploading}
            onClick={handleUploadAction}
          >
            {isUploading ? 'Đang lưu...' : 'Lưu bản ghi'}
          </button>
        </section>

        {/* Right Column: Upload Zone */}
        <section className="col-span-1 lg:col-span-2">
          <div
            className={`w-full glass-panel rounded-3xl border transition-all duration-500 flex flex-col items-center justify-center text-center cursor-pointer min-h-[450px] relative overflow-hidden group ${isDragActive ? 'border-accent shadow-[0_0_30px_rgba(212,175,55,0.15)] scale-[1.01]' : 'border-border/60 hover:border-accent/40 hover:shadow-[0_0_20px_rgba(212,175,55,0.05)] bg-card/10'
              } ${isUploading ? 'pointer-events-none opacity-90' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            {/* Subtle hover gradient */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-accent/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              accept=".mp4,.mov,.mp3,.wav"
              onChange={handleFileChange}
              disabled={isUploading}
            />

            <div className="relative z-10 flex flex-col items-center p-8">
              {isUploading ? (
                <div className="flex flex-col items-center animate-in fade-in zoom-in-95 duration-500">
                  <div className="w-24 h-24 rounded-full border border-accent/50 bg-accent/10 flex items-center justify-center mb-6 relative">
                    <span className="absolute inset-0 rounded-full border-t-2 border-accent animate-spin"></span>
                    <UploadCloud size={32} strokeWidth={1.5} className="text-accent absolute animate-pulse" />
                  </div>
                  <h3 className="text-2xl font-medium tracking-wide mb-2 text-foreground/90">Đang tải lên...</h3>
                  <p className="text-accent/80 text-sm font-medium tracking-wide">Hệ thống AI đang xử lý file của bạn</p>
                </div>
              ) : selectedFile ? (
                <div className="flex flex-col items-center animate-in fade-in zoom-in-95 duration-500">
                  <div className="w-24 h-24 rounded-full border border-accent/40 bg-accent/5 flex items-center justify-center mb-6 shadow-lg shadow-accent/5">
                    <FileVideo size={36} strokeWidth={1} className="text-accent" />
                  </div>
                  <h3 className="text-2xl font-medium tracking-wide mb-2 text-foreground/90 text-center truncate max-w-sm px-4">{selectedFile.name}</h3>
                  <p className="text-foreground/50 text-sm font-medium tracking-wide mb-8">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                  <button
                    className="px-6 py-2 rounded-full border border-border/80 text-foreground/60 hover:text-foreground hover:bg-card/50 transition-colors text-sm font-medium z-20"
                    onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                  >
                    Hủy chọn
                  </button>
                </div>
              ) : (
                <>
                  <div className="w-24 h-24 rounded-full border border-border/80 bg-background/50 flex flex-col items-center justify-center mb-8 relative group-hover:border-accent/30 transition-colors shadow-2xl">
                    <div className="absolute inset-0 bg-accent/10 rounded-full blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                    <UploadCloud size={32} strokeWidth={1} className="text-accent mb-1 group-hover:-translate-y-1 transition-transform duration-500" />
                    <AudioLines size={16} strokeWidth={1.5} className="text-foreground/30 absolute bottom-5" />
                  </div>

                  <h3 className="text-3xl font-medium tracking-wide mb-4 text-foreground/90">Kéo thả file vào đây</h3>
                  <p className="text-foreground/60 text-sm mb-12 max-w-sm leading-relaxed">
                    Hỗ trợ các định dạng tiêu chuẩn. Nhấp hoặc Kéo thả file bất kỳ vào khu vực này để chọn bản ghi.
                  </p>

                  <div className="flex flex-wrap items-center justify-center gap-4 text-[11px] font-semibold text-foreground/40 uppercase tracking-[0.15em] bg-background/30 py-3 px-6 rounded-2xl border border-border/40 backdrop-blur-sm">
                    <span className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-accent/50"></span> MP4, MOV</span>
                    <span className="flex items-center gap-2 px-4 border-l border-r border-border/50"><span className="w-1.5 h-1.5 rounded-full bg-accent/50"></span> MP3, WAV</span>
                    <span className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.3)]"></span> Tối đa 1GB</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </section>

      </div>
      
      <ProcessingOverlay 
        isVisible={showOverlay} 
        onFinished={handleProcessingFinished} 
      />
    </div>
  );
}

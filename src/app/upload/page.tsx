"use client";

import { useState, useCallback, useRef, useEffect } from 'react';
import { UploadCloud, AudioLines, Type, Clock, FileVideo, Globe, X, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

// Progress Bar Component
function UploadProgress({ 
  progress, 
  status, 
  message, 
  totalBytes, 
  downloadedBytes,
  uploadedBytes,
  error 
}: { 
  progress: number; 
  status: string; 
  message: string;
  totalBytes: number;
  downloadedBytes: number;
  uploadedBytes: number;
  error?: string;
}) {
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = () => {
    switch (status) {
      case 'downloading': return 'bg-blue-500';
      case 'uploading': return 'bg-purple-500';
      case 'processing': return 'bg-yellow-500';
      case 'completed': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-accent';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'downloading': return 'Đang tải xuống...';
      case 'uploading': return 'Đang upload lên cloud...';
      case 'processing': return 'Đang xử lý...';
      case 'completed': return 'Hoàn thành!';
      case 'error': return 'Lỗi!';
      default: return 'Đang chờ...';
    }
  };

  return (
    <div className="w-full max-w-md">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {status === 'completed' ? (
            <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center">
              <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          ) : status === 'error' ? (
            <div className="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center">
              <X className="w-4 h-4 text-red-500" />
            </div>
          ) : (
            <Loader2 className="w-5 h-5 text-accent animate-spin" />
          )}
          <span className="text-sm font-medium text-foreground/80">{getStatusText()}</span>
        </div>
        <span className="text-sm font-semibold text-accent">{Math.round(progress)}%</span>
      </div>

      <div className="h-2 bg-background/50 rounded-full overflow-hidden border border-border/30">
        <div 
          className={`h-full transition-all duration-300 ease-out ${getStatusColor()}`}
          style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
        />
      </div>

      <div className="mt-3 space-y-1">
        <p className="text-xs text-foreground/60">{message || getStatusText()}</p>
        {totalBytes > 0 && (
          <div className="flex items-center gap-3 text-xs text-foreground/40">
            {downloadedBytes > 0 && status === 'downloading' && (
              <span>{formatBytes(downloadedBytes)} / {formatBytes(totalBytes)}</span>
            )}
            {uploadedBytes > 0 && status === 'uploading' && (
              <span>{formatBytes(uploadedBytes)} / {formatBytes(totalBytes)}</span>
            )}
            {status === 'completed' && <span>{formatBytes(totalBytes)}</span>}
          </div>
        )}
        {error && <p className="text-xs text-red-400">{error}</p>}
      </div>
    </div>
  );
}

export default function Home() {
  const [isDragActive, setIsDragActive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [currentTime, setCurrentTime] = useState<Date | null>(null);
  const [activeTab, setActiveTab] = useState<'file' | 'url'>('file');
  const [urlInput, setUrlInput] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const [uploadProgress, setUploadProgress] = useState({
    progress: 0,
    status: 'pending',
    message: '',
    totalBytes: 0,
    downloadedBytes: 0,
    uploadedBytes: 0,
    error: undefined as string | undefined,
    jobId: null as string | null,
  });

  const buildSafeUploadFilename = useCallback((originalName: string) => {
    const dotIndex = originalName.lastIndexOf('.');
    const base = dotIndex > 0 ? originalName.slice(0, dotIndex) : originalName;
    const ext = dotIndex > 0 ? originalName.slice(dotIndex) : '';

    const safeBase = base
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-zA-Z0-9._-]+/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_+|_+$/g, '');

    const safeExt = ext
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-zA-Z0-9.]/g, '');

    const fallbackBase = `upload_${Date.now()}`;
    return `${safeBase || fallbackBase}${safeExt}`;
  }, []);

  const eventSourceRef = useRef<EventSource | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const activeJobIdRef = useRef<string | null>(null);
  const redirectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollFailureCountRef = useRef(0);

  const stopTracking = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    if (redirectTimerRef.current) {
      clearTimeout(redirectTimerRef.current);
      redirectTimerRef.current = null;
    }

    pollFailureCountRef.current = 0;
  }, []);

  const applyProgressUpdate = useCallback((jobId: string, data: any) => {
    if (activeJobIdRef.current !== jobId) return;

    setUploadProgress({
      progress: Number(data.progress ?? 0),
      status: String(data.status || 'pending'),
      message: String(data.message || ''),
      totalBytes: Number(data.total_bytes ?? 0),
      downloadedBytes: Number(data.downloaded_bytes ?? 0),
      uploadedBytes: Number(data.uploaded_bytes ?? 0),
      error: data.error ? String(data.error) : undefined,
      jobId,
    });

    if (data.status === 'completed') {
      stopTracking();
      setIsUploading(false);
      redirectTimerRef.current = setTimeout(() => router.push(`/meetings`), 1500);
      return;
    }

    if (data.status === 'error') {
      stopTracking();
      setIsUploading(false);
    }
  }, [router, stopTracking]);

  const pollJobStatus = useCallback((jobId: string) => {
    if (pollIntervalRef.current) return;

    pollIntervalRef.current = setInterval(async () => {
      if (activeJobIdRef.current !== jobId) {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        return;
      }

      try {
        const response = await fetch(`/api/meetings/job-status/${jobId}`);
        if (!response.ok) {
          throw new Error(`status_${response.status}`);
        }

        pollFailureCountRef.current = 0;
        const data = await response.json();
        applyProgressUpdate(jobId, data);
      } catch {
        pollFailureCountRef.current += 1;
        if (pollFailureCountRef.current >= 8) {
          stopTracking();
          setUploadProgress((prev) => ({
            ...prev,
            status: 'error',
            error: 'Không thể lấy tiến độ xử lý. Vui lòng thử lại.',
          }));
          setIsUploading(false);
        }
      }
    }, 1000);
  }, [applyProgressUpdate, stopTracking]);

  const startSSE = useCallback((jobId: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(`/api/meetings/upload-progress/${jobId}`);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const progressData = JSON.parse(event.data);
        applyProgressUpdate(jobId, progressData);
      } catch {
        // Ignore malformed chunk and rely on polling.
      }
    };

    eventSource.onerror = () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      pollJobStatus(jobId);
    };
  }, [applyProgressUpdate, pollJobStatus]);

  useEffect(() => {
    setCurrentTime(new Date());
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    return () => {
      stopTracking();
      activeJobIdRef.current = null;
    };
  }, [stopTracking]);

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
    
    // Reset and initialize progress
    setUploadProgress({
      progress: 5, status: 'processing', message: 'Đang chuẩn bị upload...',
      totalBytes: selectedFile.size, downloadedBytes: 0, uploadedBytes: 0,
      error: undefined, jobId: null,
    });
    
    try {
      const formData = new FormData();
      const safeFilename = buildSafeUploadFilename(selectedFile.name);
      formData.append("file", selectedFile, safeFilename);
      if (title.trim()) formData.append("title", title);

      const response = await fetch("/api/meetings/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Lỗi ${response.status}: ${errorText || "Không rõ lỗi"}`);
      }

      const data = await response.json();
      
      // Check if server returned error
      if (data.status === 'error') {
        throw new Error(data.message || "Lỗi xử lý file");
      }
      
      const job_id = data.job_id;
      if (!job_id) {
        throw new Error("Không nhận được mã tiến trình từ server");
      }

      activeJobIdRef.current = job_id;
      setUploadProgress(prev => ({ ...prev, jobId: job_id }));

      // Run polling and SSE together to avoid stuck loading when SSE is buffered by proxy.
      pollJobStatus(job_id);
      startSSE(job_id);
      
    } catch (error: any) {
      setUploadProgress(prev => ({ 
        ...prev, 
        status: 'error', 
        error: error.message,
        progress: 0 
      }));
      setIsUploading(false);
    }
  };

  const handleUploadFromUrl = async () => {
    if (!urlInput.trim()) {
      alert("Vui lòng nhập URL file");
      return;
    }
    setIsUploading(true);
    setUploadProgress({
      progress: 0, status: 'pending', message: 'Đang khởi tạo...',
      totalBytes: 0, downloadedBytes: 0, uploadedBytes: 0,
      error: undefined, jobId: null,
    });

    try {
      const formData = new FormData();
      formData.append("file_url", urlInput);
      if (title.trim()) formData.append("title", title);

      const startResponse = await fetch("/api/meetings/upload-from-url", {
        method: "POST", body: formData,
      });
      if (!startResponse.ok) throw new Error("Không thể bắt đầu upload");

      const { job_id } = await startResponse.json();
      if (!job_id) {
        throw new Error("Không nhận được mã tiến trình từ server");
      }

      activeJobIdRef.current = job_id;
      setUploadProgress(prev => ({ ...prev, jobId: job_id }));

      pollJobStatus(job_id);
      startSSE(job_id);
    } catch (error: any) {
      setUploadProgress(prev => ({ ...prev, status: 'error', error: error.message }));
      setIsUploading(false);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    if (e.dataTransfer.files?.length > 0) setSelectedFile(e.dataTransfer.files[0]);
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleCancel = () => {
    stopTracking();
    activeJobIdRef.current = null;
    setSelectedFile(null);
    setUrlInput('');
    setUploadProgress({
      progress: 0, status: 'pending', message: '',
      totalBytes: 0, downloadedBytes: 0, uploadedBytes: 0,
      error: undefined, jobId: null,
    });
    setIsUploading(false);
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-6 lg:p-10 hide-scrollbar flex flex-col gap-10">
      <section className="animate-in fade-in slide-in-from-bottom-4 duration-700">
         <h1 className="text-3xl font-medium tracking-tight mb-2">
             <span className="text-foreground/90">Tải lên cuộc họp</span> 
         </h1>
         <p className="text-foreground/80 text-sm tracking-wide">Tải lên file video/audio hoặc nhập link để AI tự động trích xuất thông tin.</p>
      </section>

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
                  type="text" id="meeting-title"
                  value={title} onChange={(e) => setTitle(e.target.value)}
                  placeholder="Ví dụ: Họp Sprint 4"
                  className="w-full bg-background border border-border/80 rounded-xl px-4 py-3 text-sm outline-none focus:border-accent/60 transition-all text-foreground placeholder-foreground/30 shadow-inner"
                  disabled={isUploading}
               />
           </div>

           <div className="mt-8 pt-8 border-t border-border/40 grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1">
                 <span className="text-[10px] text-foreground/40 uppercase tracking-widest font-semibold flex items-center gap-1.5"><Clock size={12}/> THỜI GIAN</span>
                 <p className="text-sm font-medium tracking-wide text-foreground/80 truncate">
                   {currentTime ? currentTime.toLocaleTimeString('vi-VN', { hour12: false }) : '--:--:--'}
                 </p>
              </div>
              <div className="flex flex-col gap-1">
                 <span className="text-[10px] text-foreground/40 uppercase tracking-widest font-semibold flex items-center gap-1.5"><FileVideo size={12}/> ĐỊNH DẠNG</span>
                 <p className="text-xs font-medium tracking-wide text-foreground/80 break-words">Audio, Video, URL</p>
              </div>
           </div>

           <button 
               className={`w-full mt-8 py-4 rounded-xl font-medium tracking-wide transition-all ${
                 (activeTab === 'file' && selectedFile && !isUploading) || (activeTab === 'url' && urlInput.trim() && !isUploading)
                 ? 'bg-accent text-accent-foreground shadow-[0_0_20px_rgba(212,175,55,0.3)] hover:bg-accent/90' 
                 : 'bg-card/50 text-foreground/30 cursor-not-allowed border border-border/50'
               }`}
               disabled={isUploading || (activeTab === 'file' ? !selectedFile : !urlInput.trim())}
               onClick={activeTab === 'file' ? handleUploadAction : handleUploadFromUrl}
           >
              {isUploading ? (activeTab === 'url' ? 'Đang xử lý...' : 'Đang lưu...') : (activeTab === 'url' ? 'Tải từ link' : 'Lưu bản ghi')}
           </button>
        </section>

        {/* Right Column: Upload Zone */}
        <section className="col-span-1 lg:col-span-2">
          {/* Tabs */}
          <div className="flex gap-2 mb-4">
            <button onClick={() => setActiveTab('file')} disabled={isUploading}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-2 ${
                activeTab === 'file' ? 'bg-accent text-accent-foreground' : 'bg-card/30 text-foreground/60 hover:bg-card/50'
              }`}>
              <UploadCloud size={16} /> Tải file lên
            </button>
            <button onClick={() => setActiveTab('url')} disabled={isUploading}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-2 ${
                activeTab === 'url' ? 'bg-accent text-accent-foreground' : 'bg-card/30 text-foreground/60 hover:bg-card/50'
              }`}>
              <Globe size={16} /> Tải từ link
            </button>
          </div>

          {activeTab === 'url' ? (
            <div className={`w-full glass-panel rounded-3xl border transition-all duration-500 flex flex-col items-center justify-center text-center min-h-[450px] p-8 relative overflow-hidden ${
              isUploading ? 'border-accent/50' : 'border-border/60 bg-card/10'
            }`}>
              {isUploading ? (
                <div className="flex flex-col items-center">
                  <div className="w-20 h-20 rounded-full border border-accent/50 bg-accent/10 flex items-center justify-center mb-6 relative">
                    <span className="absolute inset-0 rounded-full border-t-2 border-accent animate-spin"></span>
                    <UploadCloud size={28} className="text-accent absolute animate-pulse" />
                  </div>
                  <h3 className="text-2xl font-medium tracking-wide mb-4 text-foreground/90">Đang xử lý URL...</h3>
                  <UploadProgress 
                    progress={uploadProgress.progress} status={uploadProgress.status} message={uploadProgress.message}
                    totalBytes={uploadProgress.totalBytes} downloadedBytes={uploadProgress.downloadedBytes}
                    uploadedBytes={uploadProgress.uploadedBytes} error={uploadProgress.error}
                  />
                  {uploadProgress.status !== 'completed' && uploadProgress.status !== 'error' && (
                    <button onClick={handleCancel} className="mt-6 px-4 py-2 rounded-full border border-border/80 text-foreground/60 hover:text-foreground hover:bg-card/50 transition-colors text-sm font-medium">
                      Hủy
                    </button>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center w-full max-w-lg">
                  <div className="w-20 h-20 rounded-full border border-accent/40 bg-accent/5 flex items-center justify-center mb-6 shadow-lg shadow-accent/5">
                    <Globe size={32} className="text-accent" />
                  </div>
                  <h3 className="text-2xl font-medium tracking-wide mb-2 text-foreground/90">Nhập link file</h3>
                  <p className="text-foreground/60 text-sm mb-6">Hỗ trợ Google Drive, Dropbox và các link trực tiếp</p>
                  <div className="w-full flex flex-col gap-3">
                    <input type="url" value={urlInput} onChange={(e) => setUrlInput(e.target.value)}
                      placeholder="https://example.com/file.mp4"
                      className="w-full bg-background border border-border/80 rounded-xl px-4 py-4 text-sm outline-none focus:border-accent/60 transition-all text-foreground placeholder-foreground/30 shadow-inner"
                    />
                    <div className="flex flex-wrap items-center justify-center gap-2 text-[11px] font-semibold text-foreground/40 uppercase tracking-[0.15em] bg-background/30 py-3 px-4 rounded-xl border border-border/40">
                      <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-accent/50"></span> Google Drive</span>
                      <span className="flex items-center gap-1.5 px-3 border-l border-r border-border/50"><span className="w-1.5 h-1.5 rounded-full bg-accent/50"></span> Dropbox</span>
                      <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-accent/50"></span> Direct Link</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div 
              className={`w-full glass-panel rounded-3xl border transition-all duration-500 flex flex-col items-center justify-center text-center cursor-pointer min-h-[450px] relative overflow-hidden group ${
                isDragActive ? 'border-accent shadow-[0_0_30px_rgba(212,175,55,0.15)] scale-[1.01]' : 'border-border/60 hover:border-accent/40 bg-card/10'
              } ${isUploading ? 'pointer-events-none opacity-90' : ''}`}
              onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="absolute inset-0 bg-gradient-to-b from-transparent to-accent/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <input type="file" ref={fileInputRef} className="hidden" accept=".mp4,.mov,.mp3,.wav" onChange={handleFileChange} disabled={isUploading} />

              <div className="relative z-10 flex flex-col items-center p-8">
                {isUploading ? (
                   <div className="flex flex-col items-center w-full max-w-md">
                      <div className="w-24 h-24 rounded-full border border-accent/50 bg-accent/10 flex items-center justify-center mb-6 relative">
                         <span className="absolute inset-0 rounded-full border-t-2 border-accent animate-spin"></span>
                         <UploadCloud size={32} className="text-accent absolute animate-pulse" />
                      </div>
                      <h3 className="text-2xl font-medium tracking-wide mb-2 text-foreground/90">
                        {uploadProgress.status === 'completed' ? 'Hoàn thành!' : 'Đang xử lý...'}
                      </h3>
                      <UploadProgress 
                        progress={uploadProgress.progress} 
                        status={uploadProgress.status} 
                        message={uploadProgress.message}
                        totalBytes={uploadProgress.totalBytes} 
                        downloadedBytes={uploadProgress.downloadedBytes}
                        uploadedBytes={uploadProgress.uploadedBytes} 
                        error={uploadProgress.error}
                      />
                      {uploadProgress.status !== 'completed' && uploadProgress.status !== 'error' && (
                        <button onClick={handleCancel} className="mt-6 px-4 py-2 rounded-full border border-border/80 text-foreground/60 hover:text-foreground hover:bg-card/50 transition-colors text-sm font-medium">
                          Hủy
                        </button>
                      )}
                   </div>
                ) : selectedFile ? (
                   <div className="flex flex-col items-center">
                      <div className="w-24 h-24 rounded-full border border-accent/40 bg-accent/5 flex items-center justify-center mb-6 shadow-lg shadow-accent/5">
                         <FileVideo size={36} className="text-accent" />
                      </div>
                      <h3 className="text-2xl font-medium tracking-wide mb-2 text-foreground/90 text-center truncate max-w-sm px-4">{selectedFile.name}</h3>
                      <p className="text-foreground/50 text-sm font-medium tracking-wide mb-8">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                      <button className="px-6 py-2 rounded-full border border-border/80 text-foreground/60 hover:text-foreground hover:bg-card/50 transition-colors text-sm font-medium z-20"
                         onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}>Hủy chọn</button>
                   </div>
                ) : (
                   <>
                      <div className="w-24 h-24 rounded-full border border-border/80 bg-background/50 flex flex-col items-center justify-center mb-8 relative group-hover:border-accent/30 transition-colors shadow-2xl">
                         <div className="absolute inset-0 bg-accent/10 rounded-full blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                         <UploadCloud size={32} className="text-accent mb-1 group-hover:-translate-y-1 transition-transform duration-500" />
                         <AudioLines size={16} className="text-foreground/30 absolute bottom-5" />
                      </div>
                      <h3 className="text-3xl font-medium tracking-wide mb-4 text-foreground/90">Kéo thả file vào đây</h3>
                      <p className="text-foreground/60 text-sm mb-12 max-w-sm leading-relaxed">Hỗ trợ các định dạng tiêu chuẩn. Nhấp hoặc kéo thả file vào đây.</p>
                      <div className="flex flex-wrap items-center justify-center gap-4 text-[11px] font-semibold text-foreground/40 uppercase tracking-[0.15em] bg-background/30 py-3 px-6 rounded-2xl border border-border/40">
                        <span className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-accent/50"></span> MP4, MOV</span>
                        <span className="flex items-center gap-2 px-4 border-l border-r border-border/50"><span className="w-1.5 h-1.5 rounded-full bg-accent/50"></span> MP3, WAV</span>
                        <span className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500/50"></span> Tối đa 1GB</span>
                      </div>
                   </>
                )}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

"use client";

import { useState, useCallback, useRef } from 'react';
import { UploadCloud, AudioLines } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      router.push('/meetings/processing'); // Chuyển hướng ảo
    }
  }, [router]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      router.push('/meetings/processing'); // Chuyển hướng ảo
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-6 lg:p-10 hide-scrollbar flex flex-col gap-10">
      
      {/* Welcome & Upload Title */}
      <section className="animate-in fade-in slide-in-from-bottom-4 duration-700">
         <h1 className="text-3xl font-medium tracking-tight mb-2">
             <span className="text-foreground/90">Tải lên cuộc họp</span> 
         </h1>
         <p className="text-foreground/80 text-sm tracking-wide">Tải lên file video hoặc audio để AI tự động trích xuất thông tin.</p>
      </section>

      {/* Luxury Upload Section */}
      <section className="animate-in fade-in slide-in-from-bottom-8 duration-700 delay-150 fill-mode-both">
         
         <div 
          className={`w-full glass-panel rounded-[2rem] border transition-all duration-500 flex flex-col items-center justify-center text-center cursor-pointer min-h-[400px] relative overflow-hidden group ${
            isDragActive ? 'border-accent shadow-[0_0_30px_rgba(212,175,55,0.15)] scale-[1.01]' : 'border-border hover:border-accent/40 hover:shadow-[0_0_20px_rgba(212,175,55,0.05)]'
          }`}
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
          />

          <div className="relative z-10 flex flex-col items-center">
            <div className="w-24 h-24 rounded-full border border-border bg-card/50 flex flex-col items-center justify-center mb-8 relative group-hover:border-accent/30 transition-colors shadow-xl">
               <div className="absolute inset-0 bg-accent/10 rounded-full blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
               <UploadCloud size={32} strokeWidth={1} className="text-accent mb-1 group-hover:-translate-y-1 transition-transform duration-500" />
               <AudioLines size={16} strokeWidth={1.5} className="text-foreground/30 absolute bottom-5" />
            </div>
            
            <h3 className="text-2xl font-medium tracking-wide mb-3 text-foreground/90">Kéo thả file vào đây</h3>
            <p className="text-foreground/80 text-sm mb-10 max-w-sm">
               Hỗ trợ định dạng Audio và Video. Hệ thống AI của chúng tôi sẽ tự động tạo bản dịch và tổng hợp các công việc cần làm.
            </p>
            
            <div className="flex items-center gap-6 text-[11px] font-semibold text-foreground/30 uppercase tracking-[0.15em]">
              <span className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-accent/50"></span> MP4, MOV</span>
              <span className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-accent/50"></span> MP3, WAV</span>
              <span className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500/50"></span> Tối đa 1GB</span>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
}

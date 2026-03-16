"use client";

import { Loader2, Sparkles, FileVideo, CheckCircle2, UploadCloud } from 'lucide-react';
import { useEffect, useState } from 'react';

interface ProcessingOverlayProps {
  isVisible: boolean;
  meetingId?: string;
  onFinished?: () => void;
  onCancel?: () => void;
  uploadProgress?: number; // 0 to 100
  stepOverride?: number;   // Sync with global steps
}

export function ProcessingOverlay({ 
  isVisible, 
  meetingId, 
  onFinished, 
  onCancel, 
  uploadProgress = 0,
  stepOverride
}: ProcessingOverlayProps) {
  const [step, setStep] = useState(0);
  const [isDone, setIsDone] = useState(false);

  const steps = [
    { icon: UploadCloud, text: "Đang tải file lên hệ thống...", duration: 0 }, // Step 0: Uploading
    { icon: FileVideo, text: "Đang kiểm tra và lưu trữ dữ liệu...", duration: 2000 },
    { icon: Loader2, text: "Đang trích xuất âm thanh chất lượng cao...", duration: 3000 },
    { icon: Sparkles, text: "AI đang phân tích và tóm tắt nội dung...", duration: 4000 },
    { icon: CheckCircle2, text: "Đã hoàn thành bản ghi!", duration: 0 },
  ];

  useEffect(() => {
    if (stepOverride !== undefined && stepOverride !== step) {
      setStep(stepOverride);
      if (stepOverride === 4) setIsDone(true);
    }
  }, [stepOverride, step]);

  useEffect(() => {
    if (!isVisible) {
      setStep(0);
      setIsDone(false);
      return;
    }

    // --- UPLOADING PHASE ---
    if (step === 0 && stepOverride === undefined) {
      if (uploadProgress >= 100) {
        setStep(1);
      }
      return;
    }

    // --- PROCESSING PHASE ---
    if (meetingId && !isDone && stepOverride === undefined) {
      const pollInterval = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8000/meetings/${meetingId}`);
          if (res.ok) {
            const data = await res.json();
            if (data.status === "HOÀN THÀNH") {
              setStep(4);
              setIsDone(true);
              clearInterval(pollInterval);
            } else if (data.status === "LỖI") {
              clearInterval(pollInterval);
            }
          }
        } catch (e) {
          console.error("Polling error:", e);
        }
      }, 2500);

      return () => clearInterval(pollInterval);
    }

    // Fallback simulation
    if (!meetingId && step > 0 && step < 3 && stepOverride === undefined) {
      const timer = setTimeout(() => {
        setStep(step + 1);
      }, steps[step].duration);
      return () => clearTimeout(timer);
    }
    
  }, [isVisible, step, uploadProgress, meetingId, isDone, stepOverride]);

  if (!isVisible) return null;

  const CurrentIcon = steps[step].icon;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background/80 backdrop-blur-xl animate-in fade-in duration-500">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-accent/20 rounded-full blur-[120px] animate-pulse"></div>
        <div className="absolute -bottom-[10%] -right-[10%] w-[40%] h-[40%] bg-accent/10 rounded-full blur-[120px] animate-pulse duration-700"></div>
      </div>

      <div className="relative glass-panel border border-white/10 p-12 lg:p-16 rounded-[3rem] max-w-lg w-full flex flex-col items-center shadow-2xl animate-in zoom-in-95 duration-700">
        <div className="w-24 h-24 rounded-3xl bg-card border border-white/5 flex items-center justify-center mb-10 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-tr from-accent/20 to-transparent"></div>
          <CurrentIcon
            size={40}
            className={`text-accent relative z-10 ${step < 3 ? 'animate-pulse' : 'animate-bounce'}`}
            strokeWidth={1.5}
          />
          {step < 3 && (
            <div className="absolute inset-0 border-2 border-accent/30 rounded-3xl animate-ping opacity-20"></div>
          )}
        </div>

        <div className="text-center space-y-4">
          <h2 className="text-2xl font-medium tracking-tight text-foreground/90">
            {steps[step].text}
          </h2>
          <div className="flex items-center justify-center gap-2">
            {steps.map((_, i) => (
              <div
                key={i}
                className={`h-1 rounded-full transition-all duration-500 ${i === step ? 'w-8 bg-accent' : i < step ? 'w-4 bg-accent/30' : 'w-4 bg-white/5'
                  }`}
              ></div>
            ))}
          </div>
        </div>

        <div className="mt-12 w-full bg-white/5 h-1 rounded-full overflow-hidden relative">
          <div
            className="absolute top-0 left-0 h-full bg-accent transition-all duration-700 ease-out"
            style={{ 
              width: isDone 
                ? '100%' 
                : step === 0 
                  ? `${uploadProgress * 0.2} + 0 %` 
                  : `${20 + (step / (steps.length - 1)) * 80}%` 
            }}
          ></div>
        </div>

        <div className="flex flex-col items-center gap-4 mt-10">
          {isDone ? (
            <button
              onClick={onFinished}
              className="px-8 py-4 rounded-2xl bg-accent text-accent-foreground shadow-[0_0_20px_rgba(212,175,55,0.3)] hover:bg-accent/90 transition-all font-medium flex items-center gap-2 animate-in zoom-in-90 duration-500"
            >
              <span>Xem kết quả Dashboard</span>
            </button>
          ) : (
            <div className="flex flex-col items-center gap-6">
               <button
                onClick={onCancel}
                className="px-8 py-3 rounded-2xl bg-white/5 border border-white/10 text-foreground/60 hover:text-foreground hover:bg-white/10 transition-all text-sm font-medium"
              >
                <span>Hủy và Chờ xử lý ngầm</span>
              </button>
              
              <button 
                onClick={onCancel}
                className="text-[10px] uppercase tracking-widest text-red-400/50 hover:text-red-400 transition-colors font-bold"
              >
                Hủy tải lên toàn bộ
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

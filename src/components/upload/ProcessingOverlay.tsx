"use client";

import { Loader2, Sparkles, FileVideo, CheckCircle2 } from 'lucide-react';
import { useEffect, useState } from 'react';

interface ProcessingOverlayProps {
  isVisible: boolean;
  onFinished?: () => void;
}

export function ProcessingOverlay({ isVisible, onFinished }: ProcessingOverlayProps) {
  const [step, setStep] = useState(0);

  const steps = [
    { icon: FileVideo, text: "Đang tải video lên bộ nhớ tạm...", duration: 2000 },
    { icon: Loader2, text: "Đang trích xuất âm thanh chất lượng cao...", duration: 3000 },
    { icon: Sparkles, text: "AI đang phân tích và tóm tắt nội dung...", duration: 4000 },
    { icon: CheckCircle2, text: "Hoàn tất! Đang chuẩn bị Dashboard...", duration: 1500 },
  ];

  useEffect(() => {
    if (!isVisible) {
      setStep(0);
      return;
    }

    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep < steps.length - 1) {
        currentStep++;
        setStep(currentStep);
      } else {
        clearInterval(interval);
        if (onFinished) onFinished();
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [isVisible, onFinished]);

  if (!isVisible) return null;

  const CurrentIcon = steps[step].icon;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background/80 backdrop-blur-xl animate-in fade-in duration-500">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-accent/20 rounded-full blur-[120px] animate-pulse"></div>
        <div className="absolute -bottom-[10%] -right-[10%] w-[40%] h-[40%] bg-accent/10 rounded-full blur-[120px] animate-pulse duration-700"></div>
      </div>

      <div className="relative glass-panel border border-white/10 p-12 lg:p-16 rounded-[3rem] max-w-lg w-full flex flex-col items-center shadow-2xl animate-in zoom-in-95 slide-in-from-bottom-8 duration-700">
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
          <p className="text-sm text-foreground/40 font-medium tracking-wide uppercase mt-6">
            Vui lòng không đóng trình duyệt
          </p>
        </div>

        {/* Progress percent simulation */}
        <div className="mt-12 w-full bg-white/5 h-1 rounded-full overflow-hidden relative">
          <div
            className="absolute top-0 left-0 h-full bg-accent transition-all duration-[2500ms] linear"
            style={{ width: `${((step + 1) / steps.length) * 100}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
}

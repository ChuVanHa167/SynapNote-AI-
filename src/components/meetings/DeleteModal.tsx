"use client";

import { Trash2, AlertTriangle, CheckCircle, X } from 'lucide-react';
import { useState, useEffect } from 'react';

interface DeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  title?: string;
}

export function DeleteModal({ isOpen, onClose, onConfirm, title = "Xóa bản ghi" }: DeleteModalProps) {
  const [step, setStep] = useState<'confirm' | 'deleting' | 'success' | 'error'>('confirm');
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setStep('confirm');
      setIsAnimating(true);
    } else {
      setIsAnimating(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    setStep('deleting');
    try {
      await onConfirm();
      setStep('success');
      // Auto close after 2 seconds on success
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (error) {
      setStep('error');
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className={`absolute inset-0 bg-background/80 backdrop-blur-sm transition-opacity duration-500 ${isAnimating ? 'opacity-100' : 'opacity-0'}`}
        onClick={step !== 'deleting' ? onClose : undefined}
      />
      
      {/* Modal Content */}
      <div className={`relative w-full max-w-md glass-panel rounded-[2.5rem] border border-white/10 shadow-2xl p-8 transition-all duration-500 transform-gpu ${isAnimating ? 'scale-100 opacity-100 translate-y-0' : 'scale-95 opacity-0 translate-y-8'}`}>
        
        {/* Close Button */}
        {step !== 'deleting' && step !== 'success' && (
          <button 
            onClick={onClose}
            className="absolute right-6 top-6 p-2 rounded-full hover:bg-white/5 text-foreground/40 hover:text-foreground transition-all"
          >
            <X size={20} />
          </button>
        )}

        <div className="flex flex-col items-center text-center gap-6">
          
          {/* Icons Contextual Header */}
          <div className="relative">
            {step === 'confirm' && (
              <div className="w-20 h-20 rounded-[2rem] bg-red-500/10 flex items-center justify-center text-red-500 animate-in zoom-in-50 duration-500">
                <Trash2 size={40} strokeWidth={1.5} />
                <div className="absolute -top-1 -right-1 w-8 h-8 rounded-full bg-background border border-red-500/20 flex items-center justify-center text-red-500">
                  <AlertTriangle size={16} />
                </div>
              </div>
            )}
            
            {step === 'deleting' && (
              <div className="w-20 h-20 rounded-[2rem] bg-accent/10 flex items-center justify-center text-accent animate-pulse">
                <Trash2 size={40} strokeWidth={1.5} className="animate-bounce" />
              </div>
            )}
            
            {step === 'success' && (
              <div className="w-20 h-20 rounded-[2rem] bg-emerald-500/10 flex items-center justify-center text-emerald-500 animate-in zoom-in-50 duration-500">
                <CheckCircle size={40} strokeWidth={1.5} />
              </div>
            )}
            
            {step === 'error' && (
              <div className="w-20 h-20 rounded-[2rem] bg-red-500/10 flex items-center justify-center text-red-500 animate-in zoom-in-50 duration-500">
                <X size={40} strokeWidth={1.5} />
              </div>
            )}
          </div>

          {/* Text Content */}
          <div className="space-y-2">
            <h3 className="text-2xl font-light tracking-tight text-foreground/90">
              {step === 'confirm' && title}
              {step === 'deleting' && "Đang xóa..."}
              {step === 'success' && "Đã xóa thành công!"}
              {step === 'error' && "Lỗi khi xóa"}
            </h3>
            <p className="text-sm text-foreground/60 leading-relaxed max-w-[280px]">
              {step === 'confirm' && "Bản ghi này sẽ bị xóa vĩnh viễn và không thể khôi phục lại. Bạn có chắc chắn không?"}
              {step === 'deleting' && "Hệ thống đang gỡ bỏ dữ liệu và các file liên quan từ bộ nhớ."}
              {step === 'success' && "Dữ liệu bản ghi đã được dọn dẹp sạch sẽ khỏi hệ thống."}
              {step === 'error' && "Đã có lỗi xảy ra trong quá trình xóa. Vui lòng thử lại sau."}
            </p>
          </div>

          {/* Actions */}
          <div className="flex flex-col w-full gap-3 mt-4">
            {step === 'confirm' && (
              <>
                <button 
                  onClick={handleConfirm}
                  className="w-full py-4 rounded-2xl bg-red-500/10 hover:bg-red-500/20 text-red-500 font-medium transition-all border border-red-500/20 shadow-lg shadow-red-500/5 active:scale-[0.98]"
                >
                  Xác nhận xóa
                </button>
                <button 
                  onClick={onClose}
                  className="w-full py-4 rounded-2xl hover:bg-white/5 text-foreground/40 hover:text-foreground transition-all text-sm"
                >
                  Hủy bỏ
                </button>
              </>
            )}
            
            {step === 'error' && (
              <button 
                onClick={() => setStep('confirm')}
                className="w-full py-4 rounded-2xl glass-panel text-foreground/80 hover:text-accent font-medium transition-all"
              >
                Thử lại
              </button>
            )}
            
            {(step === 'success' || step === 'deleting') && (
              <div className="h-[104px] flex items-center justify-center">
                 {step === 'deleting' && <div className="w-12 h-1 bg-white/10 rounded-full overflow-hidden relative">
                    <div className="absolute inset-0 bg-accent animate-progress-indefinite rounded-full" />
                 </div>}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

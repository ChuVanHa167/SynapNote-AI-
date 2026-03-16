"use client";

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { APP_CONFIG } from '@/config/constants';
import { UserProvider } from '@/context/UserContext';
import { UploadProvider, useUpload } from '@/context/UploadContext';
import { Loader2, CheckCircle2 } from 'lucide-react';

function AppContent({ children }: { children: React.ReactNode }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const pathname = usePathname();
  const { status } = useUpload();
  
  const isAuthPage = pathname === '/login' || pathname === '/register';
  const isUploadPage = pathname === '/upload';
  const showGlobalIndicator = (status.isUploading || status.isProcessing) && !isUploadPage;

  return (
    <div className="min-h-screen bg-background text-foreground flex overflow-hidden">
      {/* Dynamic Background Effects */}
      <div className="fixed inset-0 pointer-events-none z-[-1] overflow-hidden">
         <div className="absolute top-[-10%] left-[-5%] w-[40%] h-[40%] bg-accent/5 rounded-full blur-[120px] mix-blend-screen opacity-50"></div>
         <div className="absolute bottom-[-10%] right-[-5%] w-[35%] h-[35%] bg-accent/5 rounded-full blur-[100px] mix-blend-screen opacity-50"></div>
         <div className="absolute inset-0 opacity-[0.015]" style={{ backgroundImage: `url("${APP_CONFIG.urls.noiseBackground}")` }}></div>
      </div>

      {!isAuthPage && (
        <Sidebar 
          isOpen={isSidebarOpen} 
          onClose={() => setIsSidebarOpen(false)} 
        />
      )}
      
      <div className={`flex-1 flex flex-col min-h-screen transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] ${!isAuthPage ? 'lg:pl-[280px]' : ''}`}>
        {!isAuthPage && <Header onMenuClick={() => setIsSidebarOpen(true)} />}
        
        <main className="flex-1 overflow-x-hidden overflow-y-auto">
          <div className={`mx-auto w-full transition-all duration-500 ${!isAuthPage ? 'min-h-[calc(100vh-6rem)]' : 'min-h-screen'}`}>
            {children}
          </div>
        </main>
      </div>

      {/* Global Background Upload Indicator */}
      {showGlobalIndicator && (
        <div className="fixed bottom-6 right-6 z-[100] animate-in fade-in slide-in-from-right-4 duration-500">
          <div className="glass-panel border border-accent/20 px-4 py-3 rounded-2xl flex items-center gap-4 bg-background/50 backdrop-blur-md shadow-2xl">
            <div className="relative">
              {status.isUploading ? (
                <div className="w-8 h-8 rounded-full border-2 border-accent/20 border-t-accent animate-spin" />
              ) : (
                <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center">
                  <Loader2 className="text-accent animate-pulse" size={16} />
                </div>
              )}
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-accent mb-0.5">
                {status.isUploading ? 'Đang tải lên' : 'AI Đang xử lý'}
              </p>
              <p className="text-xs font-medium text-foreground/80 truncate max-w-[150px]">
                {status.fileName}
              </p>
            </div>
            <div className="h-8 w-[1px] bg-border/50" />
            <div className="text-right min-w-[3rem]">
              <p className="text-xs font-mono font-bold text-accent">
                {status.isUploading ? `${status.progress}%` : 'Xử lý...'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Global Completion Notification */}
      {status.step === 4 && !isUploadPage && (
        <div className="fixed bottom-6 right-6 z-[100] animate-in fade-in slide-in-from-bottom-4 duration-500">
             <div className="glass-panel border border-emerald-500/30 px-5 py-4 rounded-2xl flex items-center gap-4 bg-emerald-500/5 backdrop-blur-md shadow-2xl">
                <div className="h-10 w-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                   <CheckCircle2 className="text-emerald-500" size={20} />
                </div>
                <div>
                   <p className="text-sm font-semibold text-foreground/90 leading-tight">Xử lý hoàn tất!</p>
                   <p className="text-xs text-foreground/60">{status.fileName}</p>
                </div>
                <button 
                   onClick={() => window.location.href = `/meetings/${status.meetingId}`}
                   className="ml-2 px-3 py-1.5 rounded-lg bg-emerald-500 text-white text-[10px] font-bold uppercase tracking-wider"
                >
                   Xem
                </button>
             </div>
        </div>
      )}
    </div>
  );
}

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <UserProvider>
      <UploadProvider>
        <AppContent>
          {children}
        </AppContent>
      </UploadProvider>
    </UserProvider>
  );
}

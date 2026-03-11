"use client";

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { APP_CONFIG } from '@/config/constants';

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const pathname = usePathname();
  const isAuthPage = pathname === '/login' || pathname === '/register';

  return (
    <div className="min-h-screen bg-background text-foreground flex overflow-hidden">
      {/* Dynamic Background Effects */}
      <div className="fixed inset-0 pointer-events-none z-[-1] overflow-hidden">
         {/* Subtle glowing orbs */}
         <div className="absolute top-[-10%] left-[-5%] w-[40%] h-[40%] bg-accent/5 rounded-full blur-[120px] mix-blend-screen opacity-50"></div>
         <div className="absolute bottom-[-10%] right-[-5%] w-[35%] h-[35%] bg-accent/5 rounded-full blur-[100px] mix-blend-screen opacity-50"></div>
         
         {/* Subtle noise texture overlay */}
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
    </div>
  );
}

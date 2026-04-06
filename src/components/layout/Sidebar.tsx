"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Settings, X, UploadCloud, MessageSquareText, Presentation } from 'lucide-react';
import { APP_CONFIG } from '@/config/constants';

const menuItems = [
  { name: 'Tổng quan', icon: LayoutDashboard, href: '/' },
  { name: 'Tải lên âm thanh', icon: UploadCloud, href: '/upload' },
  { name: 'Danh sách cuộc họp', icon: Presentation, href: '/meetings' },
  { name: 'Trợ lý AI', icon: MessageSquareText, href: '/ai-chat' },
  { name: 'Cài đặt', icon: Settings, href: '/settings' },
];

export function Sidebar({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const pathname = usePathname();

  return (
    <>
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/80 z-40 lg:hidden backdrop-blur-md transition-opacity"
          onClick={onClose}
        />
      )}

      <aside className={`fixed top-0 left-0 z-50 h-screen w-72 bg-card/60 backdrop-blur-2xl border-r border-border transform transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] lg:translate-x-0 lg:w-[280px] ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        
        {/* LOGO AREA */}
        <div className="flex items-center justify-between h-24 px-8">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full border border-accent flex items-center justify-center relative shadow-[0_0_15px_rgba(212,175,55,0.2)] overflow-hidden">
               <div className="absolute inset-0 bg-accent/20"></div>
               <div className="w-2.5 h-2.5 rounded-full bg-accent z-10"></div>
            </div>
            <span className="text-foreground font-medium text-lg tracking-widest uppercase">{APP_CONFIG.branding.appName}</span>
          </Link>
          <button onClick={onClose} className="lg:hidden text-foreground/90 hover:text-foreground transition-colors">
            <X size={20} strokeWidth={1.5} />
          </button>
        </div>

        {/* NAVIGATION */}
        <nav className="p-6 space-y-1 mt-4 flex-1">
          <div className="px-4 mb-8">
            <div className="relative inline-flex overflow-hidden rounded-xl p-[1px] group shadow-[0_0_20px_rgba(212,175,55,0.1)]">
              <span className="absolute inset-[-1000%] animate-[spin_3s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,transparent_0%,#D4AF37_50%,transparent_100%)] opacity-80 group-hover:opacity-100 transition-opacity" />
              <div className="inline-flex h-full w-full items-center justify-center rounded-xl bg-background px-6 py-2.5 text-xs font-bold text-foreground uppercase tracking-[0.25em] backdrop-blur-3xl">
                Menu
              </div>
            </div>
          </div>
          {menuItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/' && pathname?.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-4 px-4 py-3.5 rounded-xl transition-all duration-300 group relative overflow-hidden ${
                  isActive 
                    ? 'text-accent font-medium' 
                    : 'text-foreground/90 hover:text-foreground'
                }`}
                onClick={() => { if (typeof window !== 'undefined' && window.innerWidth < 1024) onClose() }}
              >
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-1/2 bg-accent rounded-r-full shadow-[0_0_10px_rgba(212,175,55,0.8)]"></div>
                )}
                {isActive && (
                  <div className="absolute inset-0 bg-accent/5 pointer-events-none"></div>
                )}

                <item.icon size={20} strokeWidth={1.5} className={`transition-all duration-300 ${isActive ? 'text-accent' : 'text-foreground/80 group-hover:text-foreground/80 group-hover:scale-110'}`} />
                <span className="text-sm tracking-wide">{item.name}</span>
              </Link>
            );
          })}
        </nav>
        
        {/* BOTTOM AREA */}
        <div className="p-8 absolute bottom-0 left-0 right-0">
          <div className="glass-panel p-4 rounded-2xl flex items-center justify-between border border-white/5 relative overflow-hidden group hover:border-accent/30 transition-colors cursor-pointer">
             <div className="absolute inset-0 bg-gradient-to-tr from-accent/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
             <div>
                <p className="text-xs text-foreground/80 font-medium tracking-wider uppercase mb-1">Nâng cấp gói</p>
                <p className="text-sm text-foreground/90 font-medium">Pro Workspace</p>
             </div>
             <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center text-accent">
                →
             </div>
          </div>
        </div>
      </aside>
    </>
  );
}

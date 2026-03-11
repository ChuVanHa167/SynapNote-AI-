"use client";

import { Search, Menu, Bell, Loader2 } from 'lucide-react';
import { useState } from 'react';
import Link from 'next/link';
import { APP_CONFIG } from '@/config/constants';

export function Header({ onMenuClick }: { onMenuClick: () => void }) {
  const [isSearching, setIsSearching] = useState(false);

  return (
    <header className="h-24 px-8 lg:px-12 flex items-center justify-between w-full bg-background/40 backdrop-blur-[20px] sticky top-0 z-30 border-b border-border transition-all duration-300">
      <div className="flex items-center gap-6 w-full max-w-2xl">
        <button 
          onClick={onMenuClick}
          className="lg:hidden p-2 -ml-2 text-foreground/90 hover:text-foreground transition-colors"
        >
          <Menu size={22} strokeWidth={1.5} />
        </button>
        
        {/* Minimal Search Bar */}
        <div className={`hidden md:flex items-center relative flex-1 transition-all duration-500 overflow-hidden rounded-full border ${isSearching ? 'border-accent/50 bg-card/80 shadow-[0_0_20px_rgba(212,175,55,0.05)]' : 'border-border bg-card/40 hover:bg-card/60'}`}>
          <div className="pl-5 pr-3 text-foreground/80 flex items-center justify-center">
             <Search size={18} strokeWidth={1.5} className={isSearching ? 'text-accent' : ''} />
          </div>
          <input 
            type="text" 
            placeholder="Tìm kiếm bản dịch, cuộc họp, nội dung..." 
            onFocus={() => setIsSearching(true)}
            onBlur={() => setIsSearching(false)}
            className="w-full bg-transparent h-12 pr-6 text-sm text-foreground placeholder:text-foreground/30 focus:outline-none transition-all"
          />
          {isSearching && (
            <div className="absolute right-4 text-accent animate-spin w-4 h-4">
              <Loader2 size={16} strokeWidth={2} />
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-6 lg:gap-8 min-w-max">
        {/* Luxury Notification Bell */}
        <button className="relative text-foreground/80 hover:text-accent transition-colors p-2 group">
          <Bell size={20} strokeWidth={1.5} className="group-hover:scale-110 transition-transform" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-accent rounded-full border-2 border-background shadow-[0_0_8px_rgba(212,175,55,0.8)]"></span>
        </button>
        
        {/* Minimal User Avatar */}
        <Link href="/login" title="Đăng xuất / Đăng nhập" className="flex items-center gap-4 pl-6 border-l border-border hover:opacity-80 transition-opacity">
          <div className="hidden md:flex flex-col items-end justify-center">
            <span className="text-sm font-medium text-foreground/90 tracking-wide">Alexander</span>
            <span className="text-[10px] text-accent font-semibold tracking-widest uppercase mt-0.5">Quản trị viên</span>
          </div>
          <div className="w-10 h-10 rounded-full cursor-pointer hover:scale-105 transition-transform overflow-hidden border border-white/10 relative p-0.5">
            <div className="absolute inset-0 bg-gradient-to-tr from-accent/40 to-transparent opacity-50"></div>
            <img src={`${APP_CONFIG.urls.defaultAvatarGenerator}?seed=Alex&backgroundColor=transparent`} alt="Avatar" className="w-full h-full object-cover rounded-full bg-[#1F1F22] z-10 relative" />
          </div>
        </Link>
      </div>
    </header>
  );
}

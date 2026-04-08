"use client";

import { Search, Menu, Bell, Loader2, LogOut, Sun, Moon } from 'lucide-react';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { APP_CONFIG } from '@/config/constants';
import { useUser } from '@/context/UserContext';
import { useTheme } from '@/context/ThemeContext';

const API_BASE_URL = '/api';

export function Header({ onMenuClick }: { onMenuClick: () => void }) {
  const [isSearching, setIsSearching] = useState(false);
  const router = useRouter();
  const { user, logout } = useUser();
  const { theme, toggleTheme } = useTheme();
  const userName = user?.display_name || "Alexander";
  const userTitle = user?.title || "Quản trị viên";
  const avatarUrl = user?.avatar_url || `${APP_CONFIG.urls.defaultAvatarGenerator}?seed=Alex&backgroundColor=transparent`;

  const handleLogout = async () => {
    try {
      // 1. Call backend logout
      await fetch(`${API_BASE_URL}/auth/logout`, { method: 'POST' });
      
      // 2. Clear session cookie (Important for Middleware)
      document.cookie = "synap_session=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;";
      
      // 3. Clear global state & Redirect
      logout();
      router.push('/login');
    } catch (error) {
      console.error("Logout failed:", error);
      document.cookie = "synap_session=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;";
      logout();
      router.push('/login');
    }
  };

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
            name="global_search"
            autoComplete="off"
            spellCheck="false"
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

      <div className="flex items-center gap-5 lg:gap-7 min-w-max">
        {/* Luxury Notification Bell */}
        <button className="relative text-foreground/80 hover:text-accent transition-colors p-2 group">
          <Bell size={20} strokeWidth={1.5} className="group-hover:scale-110 transition-transform" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-accent rounded-full border-2 border-background shadow-[0_0_8px_rgba(212,175,55,0.8)]"></span>
        </button>

        {/* Theme Toggle Button */}
        <button 
          onClick={toggleTheme}
          className="relative text-foreground/80 hover:text-accent transition-colors p-2 group"
          title={theme === 'dark' ? 'Chuyển sang chế độ sáng' : 'Chuyển sang chế độ tối'}
        >
          {theme === 'dark' ? (
            <Sun size={20} strokeWidth={1.5} className="group-hover:scale-110 transition-transform" />
          ) : (
            <Moon size={20} strokeWidth={1.5} className="group-hover:scale-110 transition-transform" />
          )}
        </button>
        
        {/* Minimal User Avatar & Info */}
        <div className="flex items-center gap-4 pl-5 border-l border-border h-12">
          <div className="hidden md:flex flex-col items-end justify-center">
            <span className="text-sm font-medium text-foreground/90 tracking-wide">{userName}</span>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[10px] text-accent font-semibold tracking-widest uppercase">{userTitle}</span>
              <button 
                onClick={handleLogout}
                className="text-[10px] text-red-400 hover:text-red-300 font-bold uppercase tracking-tighter transition-colors flex items-center gap-1 group/logout"
              >
                <LogOut size={10} className="group-hover/logout:-translate-x-0.5 transition-transform" />
                Đăng xuất
              </button>
            </div>
          </div>
          <Link href="/settings" className="w-10 h-10 rounded-full cursor-pointer hover:scale-105 transition-transform overflow-hidden border border-white/10 relative p-0.5">
            <div className="absolute inset-0 bg-gradient-to-tr from-accent/40 to-transparent opacity-50"></div>
            <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover rounded-full bg-[#1F1F22] z-10 relative" />
          </Link>
        </div>
      </div>
    </header>
  );
}

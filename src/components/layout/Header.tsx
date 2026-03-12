"use client";

import { Search, Menu, Bell, Loader2 } from 'lucide-react';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { APP_CONFIG } from '@/config/constants';
import { useUser } from '@/context/UserContext';

export function Header({ onMenuClick }: { onMenuClick: () => void }) {
  const [isSearching, setIsSearching] = useState(false);
  const [searchValue, setSearchValue] = useState("");
  const { user } = useUser();
  const router = useRouter();

  const handleSearch = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && searchValue.trim()) {
      router.push(`/meetings?search=${encodeURIComponent(searchValue.trim())}`);
      setSearchValue("");
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
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onFocus={() => setIsSearching(true)}
            onBlur={() => setIsSearching(false)}
            onKeyDown={handleSearch}
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
        
        {/* Minimal User Avatar with Logout logic */}
        <div className="flex items-center gap-4 pl-6 border-l border-border transition-all">
          <div className="hidden md:flex flex-col items-end justify-center">
            <span className="text-sm font-medium text-foreground/90 tracking-wide">{user?.display_name || "Alexander"}</span>
            <span className="text-[10px] text-accent font-semibold tracking-widest uppercase mt-0.5">{user?.title || "Quản trị viên"}</span>
          </div>
          
          <div className="relative group/avatar">
            <div className="w-10 h-10 rounded-full cursor-pointer hover:scale-105 transition-transform overflow-hidden border border-white/10 relative p-0.5 shadow-lg group-hover/avatar:border-accent/40">
              <div className="absolute inset-0 bg-gradient-to-tr from-accent/40 to-transparent opacity-50"></div>
              <img 
                src={user?.avatar_url || `${APP_CONFIG.urls.defaultAvatarGenerator}?seed=${user?.display_name || 'Alex'}&backgroundColor=transparent`} 
                alt="Avatar" 
                className="w-full h-full object-cover rounded-full bg-[#1F1F22] z-10 relative" 
              />
            </div>
            
            {/* Minimal Dropdown */}
            <div className="absolute top-full right-0 mt-3 w-48 bg-card/90 backdrop-blur-xl border border-border rounded-2xl p-2 opacity-0 invisible group-hover/avatar:opacity-100 group-hover/avatar:visible transition-all duration-300 shadow-2xl z-50 translate-y-2 group-hover/avatar:translate-y-0">
              <Link 
                href="/login" 
                onClick={() => {
                  // Xóa cookie session
                  document.cookie = "synap_session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
                }}
                className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 text-sm text-foreground/80 hover:text-accent transition-colors"
              >
                Đăng xuất
              </Link>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

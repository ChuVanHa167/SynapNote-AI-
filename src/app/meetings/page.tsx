"use client";

import { useState, useEffect } from 'react';
import { Search, Filter, Clock, MoreHorizontal, FileVideo, Plus, Loader2, Trash2, X } from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

interface Meeting {
  id: string;
  title: string;
  date: string;
  duration: string;
  participants: number;
  status: string;
  created_at?: string;
}

// Separate the content to use useSearchParams safely
function MeetingsContent() {
  const searchParams = useSearchParams();
  const [searchQuery, setSearchQuery] = useState("");
  const [timeFilter, setTimeFilter] = useState<'all' | 'today' | 'week' | 'month'>('all');
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeMenu, setActiveMenu] = useState<string | null>(null);

  useEffect(() => {
    const search = searchParams.get('search');
    if (search) {
      setSearchQuery(search);
    }
  }, [searchParams]);

  useEffect(() => {
    const fetchMeetings = async () => {
      try {
        const response = await fetch("http://localhost:8000/meetings");
        if (response.ok) {
          const data = await response.json();
          setMeetings(data);
        }
      } catch (error) {
        console.error("Failed to fetch meetings:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchMeetings();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Bạn có chắc chắn muốn xóa cuộc họp này không?")) return;
    
    try {
      const response = await fetch(`http://localhost:8000/meetings/${id}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setMeetings(prev => prev.filter(m => m.id !== id));
        setActiveMenu(null);
      } else {
        alert("Xóa cuộc họp thất bại.");
      }
    } catch (error) {
      console.error("Error deleting meeting:", error);
    }
  };

  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'HOÀN THÀNH':
        return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
      case 'ĐANG XỬ LÝ':
        return "text-amber-500 bg-amber-500/10 border-amber-500/20";
      case 'LỖI':
        return "text-red-500 bg-red-500/10 border-red-500/20";
      default:
        return "text-foreground/40 bg-card/10 border-border/20";
    }
  };

  const filteredMeetings = meetings.filter(m => {
    const matchesSearch = m.title.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (timeFilter === 'all') return matchesSearch;
    
    if (!m.created_at) return matchesSearch; // Fallback for old data
    
    const createdDate = new Date(m.created_at);
    const now = new Date();
    
    if (timeFilter === 'today') {
      return matchesSearch && createdDate.toDateString() === now.toDateString();
    }
    
    if (timeFilter === 'week') {
      const oneWeekAgo = new Date();
      oneWeekAgo.setDate(now.getDate() - 7);
      return matchesSearch && createdDate >= oneWeekAgo;
    }
    
    if (timeFilter === 'month') {
      const oneMonthAgo = new Date();
      oneMonthAgo.setMonth(now.getMonth() - 1);
      return matchesSearch && createdDate >= oneMonthAgo;
    }
    
    return matchesSearch;
  });

  const timeFilterLabels = {
    all: 'Tất cả thời gian',
    today: 'Hôm nay',
    week: 'Tuần này',
    month: 'Tháng này'
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-6 lg:p-10 hide-scrollbar flex flex-col gap-8 h-full">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 animate-in fade-in slide-in-from-top-4 duration-500">
         <div>
            <h1 className="text-3xl font-medium tracking-tight text-foreground/90">Cuộc họp của bạn</h1>
            <p className="text-foreground/80 text-sm tracking-wide mt-2">Quản lý và xem lại tất cả bản ghi âm và tóm tắt cuộc họp.</p>
         </div>
         <Link href="/upload" className="glass-panel px-5 py-2.5 rounded-xl text-sm font-medium hover:border-accent/50 hover:text-accent transition-all flex items-center gap-2 border border-border w-fit">
             <Plus size={16} />
             Tải cuộc họp lên
         </Link>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-150 fill-mode-both">
         <div className="relative flex-1 max-w-md">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-foreground/80" />
            <input 
               type="text" 
               placeholder="Tìm kiếm cuộc họp theo tên, từ khóa..." 
               value={searchQuery}
               onChange={(e) => setSearchQuery(e.target.value)}
               className="w-full bg-card/40 border border-border focus:border-accent/50 rounded-xl py-3 pl-11 pr-10 text-sm focus:outline-none transition-all shadow-inner"
            />
            {searchQuery && (
               <button 
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-foreground/40 hover:text-foreground transition-colors"
               >
                  <X size={16} />
               </button>
            )}
         </div>
         <div className="relative">
            <button 
               onClick={() => setShowFilterDropdown(!showFilterDropdown)}
               className={`glass-panel px-4 py-3 rounded-xl border transition-colors flex items-center gap-2 text-sm ${showFilterDropdown ? 'border-accent text-accent' : 'border-border text-foreground/80 hover:border-accent/30 hover:text-accent'}`}
            >
               <Filter size={16} />
               {timeFilter === 'all' ? 'Lọc theo thời gian' : timeFilterLabels[timeFilter]}
            </button>
            
            {showFilterDropdown && (
               <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowFilterDropdown(false)}></div>
                  <div className="absolute right-0 sm:left-0 top-full mt-2 w-48 glass-panel rounded-xl border border-border shadow-2xl z-50 py-2 animate-in fade-in zoom-in-95 duration-200">
                     {(['all', 'today', 'week', 'month'] as const).map((filter) => (
                        <button
                           key={filter}
                           onClick={() => {
                              setTimeFilter(filter);
                              setShowFilterDropdown(false);
                           }}
                           className={`w-full text-left px-4 py-2 text-xs font-medium transition-colors hover:bg-card/60 ${timeFilter === filter ? 'text-accent' : 'text-foreground/80'}`}
                        >
                           {timeFilterLabels[filter]}
                        </button>
                     ))}
                  </div>
               </>
            )}
         </div>
      </div>

      {/* Meetings List */}
      <div className="glass-panel rounded-[2rem] border border-border overflow-hidden flex-1 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-300 fill-mode-both">
         <div className="overflow-x-auto h-full min-h-[400px]">
            {isLoading ? (
               <div className="w-full h-full flex items-center justify-center p-20">
                  <Loader2 className="text-accent animate-spin" size={32} />
               </div>
            ) : filteredMeetings.length === 0 ? (
               <div className="w-full h-full flex flex-col items-center justify-center p-20 opacity-40">
                  <FileVideo size={48} strokeWidth={1} className="mb-4" />
                  <p className="text-sm font-medium">Chưa có bản ghi nào được tìm thấy.</p>
               </div>
            ) : (
               <table className="w-full text-sm text-left">
                  <thead className="text-[10px] uppercase tracking-widest text-foreground/80 bg-card/20 border-b border-border sticky top-0 z-10">
                     <tr>
                        <th className="px-8 py-5 font-medium">Tên cuộc họp</th>
                        <th className="px-8 py-5 font-medium">Thời gian</th>
                        <th className="px-8 py-5 font-medium">Thời lượng</th>
                        <th className="px-8 py-5 font-medium text-center">Người tham gia</th>
                        <th className="px-8 py-5 font-medium text-right">Trạng thái</th>
                        <th className="px-8 py-5 text-right"></th>
                     </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                     {filteredMeetings.map((item) => (
                        <tr key={item.id} className="hover:bg-card/40 transition-colors group">
                           <td className="px-8 py-5">
                              <Link href={`/meetings/${item.id}`} className="flex items-center gap-4">
                                 <div className="w-10 h-10 rounded-xl bg-card border border-white/5 flex items-center justify-center text-foreground/90 group-hover:text-accent group-hover:border-accent/20 transition-all">
                                    <FileVideo size={20} strokeWidth={1.5} />
                                 </div>
                                 <span className="font-medium text-foreground/90 group-hover:text-accent transition-colors">
                                    {item.title}
                                 </span>
                              </Link>
                           </td>
                           <td className="px-8 py-5 text-foreground/90">
                              <div className="flex items-center gap-2">
                                 <Clock size={14} className="text-foreground/80" />
                                 {item.date}
                              </div>
                           </td>
                           <td className="px-8 py-5 text-foreground/90 font-mono text-xs">{item.duration}</td>
                           <td className="px-8 py-5 text-center text-foreground/90">{item.participants}</td>
                           <td className="px-8 py-5 text-right">
                              <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-semibold tracking-wider border ${getStatusStyle(item.status)}`}>
                                 {item.status}
                              </span>
                           </td>
                           <td className="px-8 py-5 text-right relative">
                              <button 
                                 onClick={() => setActiveMenu(activeMenu === item.id ? null : item.id)}
                                 className="hover:text-foreground transition-colors p-2 text-foreground/30 group-hover:text-foreground/60"
                              >
                                 <MoreHorizontal size={16} />
                              </button>
                              
                              {activeMenu === item.id && (
                                 <div className="absolute right-8 top-12 w-48 glass-panel rounded-xl border border-border shadow-2xl z-50 py-2 animate-in fade-in zoom-in-95 duration-200">
                                    <button 
                                       onClick={() => handleDelete(item.id)}
                                       className="w-full text-left px-4 py-2 text-red-400 hover:bg-red-500/10 transition-colors flex items-center gap-2 text-xs font-medium"
                                    >
                                       <Trash2 size={14} />
                                       Xóa cuộc họp
                                    </button>
                                 </div>
                              )}
                           </td>
                        </tr>
                     ))}
                  </tbody>
               </table>
            )}
         </div>
      </div>

    </div>
  );
}

export default function MeetingsPage() {
  return (
    <Suspense fallback={
       <div className="w-full h-full flex items-center justify-center p-20">
          <Loader2 className="text-accent animate-spin" size={32} />
       </div>
    }>
      <MeetingsContent />
    </Suspense>
  );
}

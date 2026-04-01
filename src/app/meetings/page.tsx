"use client";

import { useState, useEffect } from 'react';
import { Search, Filter, Clock, FileVideo, Plus, Loader2, Trash2 } from 'lucide-react';
import Link from 'next/link';

interface Meeting {
  id: string;
  title: string;
  date: string;
  duration: string;
  participants: number;
  status: string;
}

export default function MeetingsPage() {
   const [searchQuery, setSearchQuery] = useState("");
   const [meetings, setMeetings] = useState<Meeting[]>([]);
   const [isLoading, setIsLoading] = useState(true);
   const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    const fetchMeetings = async () => {
      try {
        const response = await fetch("/api/meetings");
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

  const filteredMeetings = meetings.filter(m => 
    m.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

   const handleDelete = async (id: string) => {
      if (deletingId) return;
      const confirmed = window.confirm("Bạn có chắc muốn xóa cuộc họp này?");
      if (!confirmed) return;

      setDeletingId(id);
      try {
         const response = await fetch(`/api/meetings/${id}`, { method: "DELETE" });
         if (!response.ok) {
            throw new Error("Failed to delete meeting");
         }
         setMeetings((prev) => prev.filter((m) => m.id !== id));
      } catch (error) {
         console.error("Failed to delete meeting:", error);
         alert("Không thể xóa cuộc họp. Vui lòng thử lại.");
      } finally {
         setDeletingId(null);
      }
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
               className="w-full bg-card/40 border border-border focus:border-accent/50 rounded-xl py-3 pl-11 pr-4 text-sm focus:outline-none transition-all shadow-inner"
            />
         </div>
         <button className="glass-panel px-4 py-3 rounded-xl border border-border hover:border-accent/30 hover:text-accent transition-colors flex items-center gap-2 text-sm text-foreground/80">
            <Filter size={16} />
            Lọc theo thời gian
         </button>
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
                           <td className="px-8 py-5 text-right">
                              <button
                                 className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-red-500/40 text-red-400 hover:text-red-300 hover:border-red-400 transition-colors disabled:opacity-60"
                                 onClick={() => handleDelete(item.id)}
                                 disabled={deletingId === item.id}
                              >
                                 {deletingId === item.id ? (
                                    <Loader2 size={16} className="animate-spin" />
                                 ) : (
                                    <Trash2 size={16} />
                                 )}
                                 <span>Xóa</span>
                              </button>
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

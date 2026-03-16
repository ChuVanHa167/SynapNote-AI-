"use client";

import { useState, useEffect } from 'react';
import { FileVideo, Clock, Sparkles, MoveUpRight, MoreHorizontal, ArrowRight, Loader2, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useUser } from '@/context/UserContext';
import { DeleteModal } from '@/components/meetings/DeleteModal';

interface Meeting {
   id: string;
   title: string;
   date: string;
   duration: string;
   participants: number;
   status: string;
}

export default function Dashboard() {
   const { user } = useUser();
   const [meetings, setMeetings] = useState<Meeting[]>([]);
   const [isLoading, setIsLoading] = useState(true);
   const [activeMenu, setActiveMenu] = useState<string | null>(null);
   const [meetingToDelete, setMeetingToDelete] = useState<string | null>(null);
   const [showDeleteModal, setShowDeleteModal] = useState(false);

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

   const handleDelete = async () => {
      if (!meetingToDelete) return;
      
      try {
         const response = await fetch(`http://localhost:8000/meetings/${meetingToDelete}`, {
            method: 'DELETE',
         });
         if (response.ok) {
            setMeetings(prev => prev.filter(m => m.id !== meetingToDelete));
            setActiveMenu(null);
            setMeetingToDelete(null);
         } else {
            throw new Error("Xóa cuộc họp thất bại.");
         }
      } catch (error) {
         console.error("Error deleting meeting:", error);
         throw error;
      }
   };

   // Compute stats
   const totalMeetings = meetings.length;

   const toReviewCount = meetings.filter(
      (m) => m.status === 'HOÀN THÀNH'
   ).length;

   const processingCount = meetings.filter(
      (m) => m.status === 'ĐANG XỬ LÝ' || m.status === 'PENDING'
   ).length;

   const totalHoursSaved = meetings
      .filter((m) => m.status === 'HOÀN THÀNH')
      .reduce((acc, current) => {
         // Tries to parse duration roughly e.g "1h 30m" or "45m"
         let hours = 0;
         let minutes = 0;
         const durationStr = current.duration || "";
         const hMatch = durationStr.match(/(\d+)h/);
         const mMatch = durationStr.match(/(\d+)m/);

         if (hMatch) hours = parseInt(hMatch[1]);
         if (mMatch) minutes = parseInt(mMatch[1]);

         return acc + hours + (minutes / 60);
      }, 0).toFixed(1);

   const stats = [
      { label: "Tổng cuộc họp", value: totalMeetings.toString(), trend: "+12%", isUp: true, icon: FileVideo, color: "text-accent" },
      { label: "Giờ tiết kiệm", value: `${totalHoursSaved}h`, trend: "+4.1h", isUp: true, icon: Clock, color: "text-emerald-400" },
      { label: "Đang xử lý", value: processingCount.toString(), trend: "AI", isUp: true, icon: Sparkles, color: "text-purple-400" },
      { label: "Chờ xem lại", value: toReviewCount.toString(), trend: "Cần xem", isUp: false, icon: Clock, color: "text-amber-400" }
   ];

   const recentMeetings = [...meetings].reverse().slice(0, 3);

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

   return (
      <div className="w-full max-w-7xl mx-auto p-6 lg:p-10 hide-scrollbar flex flex-col gap-10">

         {/* Welcome Section */}
         <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
                <h1 className="text-3xl font-medium tracking-tight mb-2 flex items-center gap-3">
                   <span className="text-foreground/90">Chào buổi tối,</span>
                   <span className="font-semibold bg-gradient-to-r from-accent to-amber-200 bg-clip-text text-transparent">
                      {user?.display_name || "Alexander"}
                   </span>
                </h1>
               <p className="text-foreground/80 text-sm tracking-wide">Bạn có {toReviewCount} bản tóm tắt đã sẵn sàng để xem lại hôm nay.</p>
            </div>
            <Link href="/upload" className="glass-panel px-6 py-3 rounded-xl text-sm font-medium hover:border-accent/50 hover:text-accent transition-all flex items-center gap-2 group border border-border">
               <span className="w-2 h-2 rounded-full bg-accent animate-pulse"></span>
               Tạo cuộc họp mới
               <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </Link>
         </section>

         {/* Stats Cards Overview */}
         <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-150 fill-mode-both">
            {stats.map((stat, i) => (
               <div key={i} className="glass-panel rounded-2xl p-6 relative overflow-hidden group border border-border hover:border-accent/20 transition-colors">
                  <div className="flex justify-between items-start mb-4">
                     <div className={`p-2.5 rounded-xl bg-card border border-white/5 ${stat.color}`}>
                        <stat.icon size={20} strokeWidth={1.5} />
                     </div>
                     <span className={`text-xs font-medium flex items-center gap-1 ${stat.isUp ? 'text-emerald-500' : 'text-amber-500'}`}>
                        {stat.isUp && <MoveUpRight size={12} />} {stat.trend}
                     </span>
                  </div>
                  <p className="text-3xl font-medium tracking-tight mb-1">
                     {isLoading ? <Loader2 className="animate-spin w-8 h-8 opacity-50 my-1" /> : stat.value}
                  </p>
                  <p className="text-xs font-medium text-foreground/80 uppercase tracking-widest">{stat.label}</p>
               </div>
            ))}
         </section>

         {/* Recent Activity */}
         <section className="animate-in fade-in slide-in-from-bottom-12 duration-700 delay-300 fill-mode-both">
            <div className="flex items-center justify-between mb-6">
               <h2 className="text-lg font-medium tracking-wide">Hoạt động gần đây</h2>
               <Link href="/meetings" className="text-sm text-foreground/80 hover:text-accent transition-colors flex items-center gap-1">
                  Xem tất cả <ArrowRight size={14} />
               </Link>
            </div>

            <div className="glass-panel rounded-[2rem] border border-border overflow-hidden">
               <div className="overflow-x-auto min-h-[200px] flex flex-col justify-center">
                  {isLoading ? (
                     <div className="flex justify-center p-10"><Loader2 className="animate-spin text-accent w-8 h-8" /></div>
                  ) : recentMeetings.length === 0 ? (
                     <div className="flex flex-col items-center justify-center p-10 opacity-50">
                        <FileVideo className="w-10 h-10 mb-2" />
                        <p className="text-sm">Chưa có hoạt động nào.</p>
                     </div>
                  ) : (
                     <table className="w-full text-sm text-left border-collapse">
                        <thead className="text-[10px] uppercase tracking-widest text-foreground/80 bg-card/20 border-b border-border">
                           <tr>
                              <th className="px-8 py-5 font-medium">Cuộc họp</th>
                              <th className="px-8 py-5 font-medium">Thời gian</th>
                              <th className="px-8 py-5 font-medium">Độ dài</th>
                              <th className="px-8 py-5 font-medium text-right">Trạng thái</th>
                              <th className="px-8 py-5 text-right"></th>
                           </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                           {recentMeetings.map((item, i) => (
                              <tr key={i} className="hover:bg-card/40 transition-colors group">
                                 <td className="px-8 py-5">
                                    <Link href={`/meetings/${item.id}`} className="font-medium text-foreground/90 group-hover:text-accent transition-colors">
                                       {item.title}
                                    </Link>
                                 </td>
                                 <td className="px-8 py-5 text-foreground/90">{item.date}</td>
                                 <td className="px-8 py-5 text-foreground/90 font-mono text-xs">{item.duration}</td>
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
                                        <div className="absolute right-8 top-12 w-48 glass-panel rounded-xl border border-border shadow-2xl z-50 py-2 animate-in fade-in zoom-in-95 duration-200 text-left">
                                           <button 
                                              onClick={() => setMeetingToDelete(item.id)}
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
         </section>

         <DeleteModal 
            isOpen={!!meetingToDelete}
            onClose={() => setMeetingToDelete(null)}
            onConfirm={handleDelete}
            title="Xác nhận xóa bản ghi"
         />
      </div>
   );
}

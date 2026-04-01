"use client";

import { FileVideo, Clock, Sparkles, MoveUpRight, MoreHorizontal, ArrowRight, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { useState, useEffect } from 'react';

interface Meeting {
  id: string;
  title: string;
  date: string;
  duration: string;
  status: string;
}

export default function Dashboard() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);

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

  return (
    <div className="w-full max-w-7xl mx-auto p-6 lg:p-10 hide-scrollbar flex flex-col gap-10">

      {/* Welcome Section */}
      <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 flex flex-col md:flex-row md:items-end justify-between gap-6">
         <div>
            <h1 className="text-3xl font-medium tracking-tight mb-2 flex items-center gap-3">
                <span className="text-foreground/90">Chào buổi tối,</span>
                <span className="font-semibold bg-gradient-to-r from-accent to-amber-200 bg-clip-text text-transparent">Alexander</span>
            </h1>
            <p className="text-foreground/80 text-sm tracking-wide">Quản lý và xem lại tất cả cuộc họp của bạn.</p>
         </div>
         <Link href="/upload" className="glass-panel px-6 py-3 rounded-xl text-sm font-medium hover:border-accent/50 hover:text-accent transition-all flex items-center gap-2 group border border-border">
             <span className="w-2 h-2 rounded-full bg-accent animate-pulse"></span>
             Tạo cuộc họp mới
             <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
         </Link>
      </section>

      {/* Stats Cards Overview */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-150 fill-mode-both">
         {[
            { label: "Tổng cuộc họp", value: meetings.length.toString(), trend: "Real data", isUp: true, icon: FileVideo, color: "text-accent" },
            { label: "Giờ tiết kiệm", value: "0h", trend: "-", isUp: true, icon: Clock, color: "text-emerald-400" },
            { label: "Phân tích AI", value: "0", trend: "-", isUp: true, icon: Sparkles, color: "text-purple-400" },
            { label: "Chờ xử lý", value: meetings.filter(m => m.status === 'ĐANG XỬ LÝ').length.toString(), trend: "Real time", isUp: false, icon: Clock, color: "text-amber-400" }
         ].map((stat, i) => (
            <div key={i} className="glass-panel rounded-2xl p-6 relative overflow-hidden group border border-border hover:border-accent/20 transition-colors">
               <div className="flex justify-between items-start mb-4">
                  <div className={`p-2.5 rounded-xl bg-card border border-white/5 ${stat.color}`}>
                     <stat.icon size={20} strokeWidth={1.5} />
                  </div>
               </div>
               <p className="text-3xl font-medium tracking-tight mb-1">{stat.value}</p>
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
            <div className="overflow-x-auto">
               {isLoading ? (
                 <div className="w-full h-48 flex items-center justify-center">
                   <Loader2 className="text-accent animate-spin" size={32} />
                 </div>
               ) : meetings.length === 0 ? (
                 <div className="w-full h-48 flex flex-col items-center justify-center text-foreground/40">
                   <FileVideo size={48} strokeWidth={1} className="mb-4" />
                   <p className="text-sm font-medium">Chưa có cuộc họp nào</p>
                 </div>
               ) : (
               <table className="w-full text-sm text-left">
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
                     {meetings.slice(0, 3).map((item, i) => (
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
                           <td className="px-8 py-5 text-right text-foreground/30">
                              <button className="hover:text-foreground transition-colors p-2"><MoreHorizontal size={16} /></button>
                           </td>
                        </tr>
                     ))}
                  </tbody>
               </table>
               )}
            </div>
         </div>
      </section>

    </div>
  );
}

"use client";

import { useState } from 'react';
import { User, Bell, Shield, CreditCard, Sparkles, Sliders, Globe, Copy, CheckCircle2 } from 'lucide-react';
import { APP_CONFIG } from '@/config/constants';

type Tab = 'profile' | 'notifications' | 'security' | 'billing' | 'integrations';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('profile');
  const [copied, setCopied] = useState(false);

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'profile', label: 'Hồ sơ cá nhân', icon: User },
    { id: 'notifications', label: 'Thông báo', icon: Bell },
    { id: 'security', label: 'Bảo mật', icon: Shield },
    { id: 'billing', label: 'Gói & Thanh toán', icon: CreditCard },
    { id: 'integrations', label: 'Tích hợp', icon: Sliders },
  ];

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full max-w-[1200px] mx-auto p-6 lg:p-10 h-full flex flex-col gap-8">
      
      {/* Header */}
      <div className="animate-in fade-in slide-in-from-top-4 duration-500">
         <h1 className="text-3xl lg:text-4xl font-medium tracking-tight text-foreground/90">Cài đặt Hệ thống</h1>
         <p className="text-foreground/80 text-sm tracking-wide mt-2">Quản lý tài khoản, tuỳ chọn thông báo và tích hợp ứng dụng của bạn.</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8 lg:gap-12 flex-1 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-150 fill-mode-both">
         
         {/* Sidebar Navigation */}
         <div className="w-full lg:w-64 shrink-0 flex flex-col gap-2">
            {tabs.map((tab) => {
               const isActive = activeTab === tab.id;
               return (
                  <button
                     key={tab.id}
                     onClick={() => setActiveTab(tab.id)}
                     className={`flex items-center gap-3 w-full text-left px-4 py-3 rounded-2xl transition-all duration-300 text-sm font-medium relative overflow-hidden group border ${
                        isActive 
                           ? 'bg-accent/10 text-accent border-accent/20 shadow-sm' 
                           : 'bg-transparent text-foreground/90 border-transparent hover:bg-card/40 hover:text-foreground/80'
                     }`}
                  >
                     {isActive && (
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-1/2 bg-accent rounded-r-full shadow-[0_0_10px_rgba(212,175,55,0.8)]"></div>
                     )}
                     <tab.icon size={18} className={isActive ? 'text-accent' : 'text-foreground/80 group-hover:text-foreground/90 transition-colors'} />
                     {tab.label}
                  </button>
               );
            })}
         </div>

         {/* Content Area */}
         <div className="flex-1 glass-panel rounded-[2rem] border border-border p-8 lg:p-12 relative overflow-hidden min-h-[500px]">
            {/* Background Glow */}
            <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-accent/5 rounded-full blur-[100px] pointer-events-none -translate-y-1/2 translate-x-1/2"></div>
            
            <div className="max-w-2xl relative z-10">
               
               {/* 1. PROFILE SETTINGS */}
               {activeTab === 'profile' && (
                  <div className="space-y-10 animate-in fade-in duration-500">
                     <div className="border-b border-border pb-6 flex items-center justify-between">
                        <div>
                           <h2 className="text-xl font-medium text-foreground/90 mb-1">Hồ sơ cá nhân</h2>
                           <p className="text-sm text-foreground/80">Cập nhật thông tin cá nhân và ảnh đại diện của bạn.</p>
                        </div>
                     </div>

                     <div className="flex gap-8 items-start">
                        <div className="w-24 h-24 rounded-full border border-white/10 relative overflow-hidden shrink-0 group cursor-pointer bg-card">
                           <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center z-20">
                              <span className="text-xs font-medium text-white shadow-sm">Thay đổi</span>
                           </div>
                           <img src={`${APP_CONFIG.urls.defaultAvatarGenerator}?seed=Alex&backgroundColor=transparent`} alt="Avatar" className="w-full h-full object-cover z-10 relative" />
                        </div>
                        <div className="flex-1 space-y-5">
                           <div className="space-y-2">
                              <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Tên hiển thị</label>
                              <input type="text" defaultValue="Alexander" className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 text-sm focus:outline-none transition-all shadow-inner" />
                           </div>
                           <div className="space-y-2">
                              <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Email</label>
                              <input type="email" defaultValue="alexander@company.com" disabled className="w-full opacity-60 bg-background border border-border rounded-xl py-3 px-4 text-sm focus:outline-none shadow-inner" />
                           </div>
                           <div className="space-y-2">
                              <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Chức danh</label>
                              <input type="text" defaultValue="Giám đốc Sản phẩm" className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 text-sm focus:outline-none transition-all shadow-inner" />
                           </div>
                        </div>
                     </div>
                  </div>
               )}

               {/* 2. SECURITY SETTINGS */}
               {activeTab === 'security' && (
                  <div className="space-y-10 animate-in fade-in duration-500">
                     <div className="border-b border-border pb-6">
                        <h2 className="text-xl font-medium text-foreground/90 mb-1">Đổi mật khẩu</h2>
                        <p className="text-sm text-foreground/80">Đảm bảo tài khoản của bạn đang sử dụng mật khẩu mạnh và an toàn.</p>
                     </div>

                     <div className="space-y-5">
                        <div className="space-y-2">
                           <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Mật khẩu hiện tại</label>
                           <input type="password" placeholder="••••••••" className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 text-sm focus:outline-none transition-all shadow-inner" />
                        </div>
                        <div className="space-y-2">
                           <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Mật khẩu mới</label>
                           <input type="password" placeholder="••••••••" className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 text-sm focus:outline-none transition-all shadow-inner" />
                        </div>
                        <div className="space-y-2">
                           <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Xác nhận mật khẩu mới</label>
                           <input type="password" placeholder="••••••••" className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 text-sm focus:outline-none transition-all shadow-inner" />
                        </div>
                     </div>
                  </div>
               )}

               {/* 3. INTEGRATIONS */}
               {activeTab === 'integrations' && (
                  <div className="space-y-10 animate-in fade-in duration-500">
                     <div className="border-b border-border pb-6">
                        <h2 className="text-xl font-medium text-foreground/90 mb-1">Tích hợp ứng dụng</h2>
                        <p className="text-sm text-foreground/80">Kết nối các công cụ làm việc của bạn để đồng bộ hoá cuộc họp và nhiệm vụ.</p>
                     </div>

                     <div className="space-y-4">
                        
                        <div className="flex items-center justify-between p-5 rounded-2xl border border-white/5 bg-background/40 hover:bg-card/40 transition-colors">
                           <div className="flex items-center gap-4">
                              <div className="w-10 h-10 rounded-xl bg-card border border-border flex items-center justify-center p-2.5">
                                 <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" className="text-[#00C4CC]"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="m15 13-3 3-3-3"></path><path d="M12 16V10"></path></svg>
                              </div>
                              <div>
                                 <h3 className="text-sm font-medium text-foreground/90 leading-tight">Zoom Video Communications</h3>
                                 <p className="text-xs text-foreground/80 mt-0.5">Tự động lấy bản ghi âm từ Zoom Cloud.</p>
                              </div>
                           </div>
                           <button className="px-4 py-2 rounded-xl text-xs font-medium border border-border bg-card hover:bg-card/80 text-foreground transition-colors">Kết nối</button>
                        </div>

                        <div className="flex items-center justify-between p-5 rounded-2xl border border-accent/20 bg-accent/5 transition-colors">
                           <div className="flex items-center gap-4">
                              <div className="w-10 h-10 rounded-xl bg-card border border-white/10 flex items-center justify-center p-2.5">
                                 <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" className="text-[#36C5F0]"><path d="M22.54 6.42a2.78 2.78 0 0 0-4.08 2.18v4.36a2.78 2.78 0 0 0 4.08 2.18V6.42Z"></path><path d="M4.08 17.58a2.78 2.78 0 0 0-2.18-4.08h4.36a2.78 2.78 0 0 0 2.18 4.08v-4.36A2.78 2.78 0 0 0 4.08 17.58Z"></path><path d="M8.44 6.42a2.78 2.78 0 0 0 4.08-2.18v4.36A2.78 2.78 0 0 0 8.44 6.42Z"></path><path d="M19.92 17.58a2.78 2.78 0 0 0 2.18-4.08h-4.36a2.78 2.78 0 0 0-2.18 4.08v-4.36A2.78 2.78 0 0 0 19.92 17.58Z"></path></svg>
                              </div>
                              <div>
                                 <h3 className="text-sm font-medium text-foreground/90 leading-tight flex items-center gap-2">Slack <span className="bg-emerald-500/20 text-emerald-500 text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wider font-semibold border border-emerald-500/20">Đã kết nối</span></h3>
                                 <p className="text-xs text-foreground/80 mt-0.5">Gửi thông báo tóm tắt cuộc họp thẳng vào Slack.</p>
                              </div>
                           </div>
                           <button className="px-4 py-2 rounded-xl text-xs font-medium border border-red-500/20 text-red-400 hover:bg-red-500/10 transition-colors">Ngắt kết nối</button>
                        </div>
                        
                        <div className="flex items-center justify-between p-5 rounded-2xl border border-white/5 bg-background/40 hover:bg-card/40 transition-colors">
                           <div className="flex items-center gap-4">
                              <div className="w-10 h-10 rounded-xl bg-card border border-border flex items-center justify-center p-2.5">
                                 <Globe className="text-[#0079BF]" />
                              </div>
                              <div>
                                 <h3 className="text-sm font-medium text-foreground/90 leading-tight">Khác (API Key)</h3>
                                 <p className="text-xs text-foreground/80 mt-0.5">Tạo Token API để tích hợp tuỳ chỉnh qua Zapier/Make.</p>
                              </div>
                           </div>
                           <div className="flex bg-background border border-border rounded-xl px-2 py-1 items-center gap-2">
                             <span className="text-xs font-mono text-foreground/90 pl-2 select-none">sk_live_...x891</span>
                             <button onClick={() => copyToClipboard('sk_live_test_api_key_123')} className="p-1.5 hover:bg-card rounded-lg text-foreground/90 hover:text-accent transition-colors">
                                {copied ? <CheckCircle2 size={14} className="text-emerald-500" /> : <Copy size={14} />}
                             </button>
                           </div>
                        </div>
                     </div>
                  </div>
               )}

               {/* OTHER TABS */}
               {(activeTab === 'notifications' || activeTab === 'billing') && (
                  <div className="space-y-10 animate-in fade-in duration-500 flex flex-col items-center justify-center text-center py-20 opacity-50">
                     <Sparkles size={40} className="text-accent mb-4" strokeWidth={1} />
                     <h2 className="text-xl font-medium">Tính năng đang phát triển</h2>
                     <p className="text-sm mt-2 max-w-sm">Phần này đang được đội ngũ của chúng tôi hoàn thiện và sẽ sớm ra mắt trong bản cập nhật kế tiếp.</p>
                  </div>
               )}

               {/* Global Save Button for forms */}
               {(activeTab === 'profile' || activeTab === 'security') && (
                  <div className="pt-8 mt-10 border-t border-border flex justify-end">
                     <button className="bg-accent text-accent-foreground px-8 py-3 rounded-xl font-medium text-sm hover:scale-[1.02] transition-transform shadow-[0_4px_14px_rgba(212,175,55,0.2)]">Lưu thay đổi</button>
                  </div>
               )}

            </div>
         </div>

      </div>
    </div>
  );
}

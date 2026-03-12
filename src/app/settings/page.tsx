"use client";

import { useState, useEffect } from 'react';
import { User, Bell, Shield, CreditCard, Sliders, Globe, Copy, CheckCircle2, Eye, EyeOff, Star, Zap, Crown, CreditCard as CardIcon, Loader2, X, Search } from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import { APP_CONFIG } from '@/config/constants';
import { useUser } from '@/context/UserContext';
import { Suspense } from 'react';

type Tab = 'profile' | 'notifications' | 'security' | 'billing' | 'integrations';

function SettingsContent() {
  const searchParams = useSearchParams();
  const [activeTab, setActiveTab] = useState<Tab>('profile');
  const [copied, setCopied] = useState(false);
  const { user, updateUser, refreshUser } = useUser();

  // Profile Form States
  const [displayName, setDisplayName] = useState("");
  const [title, setTitle] = useState("");
  const [userEmail, setUserEmail] = useState("admin@synapnote.com");

  // Security Form States
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Security Visibility States
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // Notification States
  const [emailSummaries, setEmailSummaries] = useState(true);
  const [actionItemAlerts, setActionItemAlerts] = useState(true);
  const [productUpdates, setProductUpdates] = useState(false);

  // Billing & Payment States
  const [showPricing, setShowPricing] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<{name: string, price: string} | null>(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(false);

  // Integrations States
  const [searchIntegration, setSearchIntegration] = useState("");
  const [integrationFilter, setIntegrationFilter] = useState<'all' | 'comm' | 'prod'>('all');
  const [revealApiKey, setRevealApiKey] = useState(false);
  const [connectedServices, setConnectedServices] = useState<string[]>(['slack']); // Mock Slack as already connected
  const [showAuthModal, setShowAuthModal] = useState<{name: string, icon: any, color: string} | null>(null);
  const [authLoading, setAuthLoading] = useState(false);

  // UI States
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  const handleToggleConnection = (id: string, name: string, icon: any, color: string) => {
    const isConnected = connectedServices.includes(id);
    
    if (isConnected) {
      // Disconnect directly
      setConnectedServices(connectedServices.filter(item => item !== id));
      setMessage({ type: 'success', text: `Đã ngắt kết nối với ${name}` });
      setTimeout(() => setMessage(null), 3000);
    } else {
      // Show Auth Modal for connection
      setShowAuthModal({ name, icon, color });
    }
  };

  const completeConnection = () => {
    if (!showAuthModal) return;
    
    setAuthLoading(true);
    // Simulate OAuth handshake
    setTimeout(() => {
      setConnectedServices([...connectedServices, showAuthModal.name.toLowerCase().replace(' ', '')]);
      setAuthLoading(false);
      setShowAuthModal(null);
      setMessage({ type: 'success', text: `Kết nối thành công với ${showAuthModal.name}!` });
      setTimeout(() => setMessage(null), 3000);
    }, 2500);
  };

  useEffect(() => {
    const tabParam = searchParams.get('tab') as Tab;
    if (tabParam && ['profile', 'notifications', 'security', 'billing', 'integrations'].includes(tabParam)) {
      setActiveTab(tabParam);
      if (tabParam === 'billing') {
        setShowPricing(true);
      }
    }
  }, [searchParams]);

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name);
      setTitle(user.title || "");
      setUserEmail(user.email);
      setEmailSummaries(user.email_summaries);
      setActionItemAlerts(user.action_item_alerts);
      setProductUpdates(user.product_updates);
    }
  }, [user]);

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

  const handleSave = async () => {
    setMessage(null);
    setLoading(true);
    
    try {
      if (activeTab === 'profile') {
        const res = await fetch(`http://localhost:8000/auth/profile?email=${userEmail}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ display_name: displayName, title: title })
        });
        if (!res.ok) {
           const data = await res.json();
           throw new Error(data.detail || "Không thể cập nhật hồ sơ");
        }
        
        // Refresh global user state
        await refreshUser(userEmail);
        
        setMessage({ type: 'success', text: 'Tuyệt vời! Thông tin hồ sơ của bạn đã được cập nhật.' });
      } else if (activeTab === 'security') {
        if (!currentPassword) throw new Error("Vui lòng nhập mật khẩu hiện tại");
        if (!newPassword) throw new Error("Vui lòng nhập mật khẩu mới");
        if (newPassword.length < 6) throw new Error("Mật khẩu mới phải có ít nhất 6 ký tự");
        if (newPassword !== confirmPassword) {
           throw new Error("Mật khẩu xác nhận không khớp với mật khẩu mới");
        }

        const res = await fetch(`http://localhost:8000/auth/password?email=${userEmail}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
        });
        
        if (!res.ok) {
           const data = await res.json();
           if (res.status === 400) throw new Error("Mật khẩu hiện tại không chính xác");
           throw new Error(data.detail || "Lỗi khi cập nhật mật khẩu");
        }
        
        setMessage({ type: 'success', text: 'Cập nhật mật khẩu thành công! Hãy ghi nhớ mật khẩu mới của bạn.' });
        setCurrentPassword(""); 
        setNewPassword(""); 
        setConfirmPassword("");
        setShowCurrentPassword(false);
        setShowNewPassword(false);
        setShowConfirmPassword(false);
      } else if (activeTab === 'notifications') {
        const res = await fetch(`http://localhost:8000/auth/profile?email=${userEmail}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            email_summaries: emailSummaries, 
            action_item_alerts: actionItemAlerts, 
            product_updates: productUpdates 
          })
        });
        if (!res.ok) {
           const data = await res.json();
           throw new Error(data.detail || "Không thể cập nhật cài đặt thông báo");
        }
        
        await refreshUser(userEmail);
        setMessage({ type: 'success', text: 'Cài đặt thông báo của bạn đã được lưu!' });
      }
    } catch (err: any) {
       setMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
      // Keep success message longer, clear error faster if desired, but user said "rõ ràng hơn"
      setTimeout(() => setMessage(null), 5000);
    }
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
                           <input 
                              type="file" 
                              accept="image/*" 
                              className="absolute inset-0 opacity-0 cursor-pointer z-30" 
                              onChange={async (e) => {
                                 const file = e.target.files?.[0];
                                 if (!file) return;
                                 
                                 const formData = new FormData();
                                 formData.append('file', file);
                                 
                                 try {
                                    setLoading(true);
                                    const res = await fetch(`http://localhost:8000/auth/upload-avatar?email=${userEmail}`, {
                                       method: 'POST',
                                       body: formData,
                                    });
                                    if (!res.ok) throw new Error("Lỗi khi tải ảnh lên");
                                    await refreshUser(userEmail);
                                    setMessage({ type: 'success', text: 'Cập nhật ảnh đại diện thành công!' });
                                 } catch (err: any) {
                                    setMessage({ type: 'error', text: err.message });
                                 } finally {
                                    setLoading(false);
                                    setTimeout(() => setMessage(null), 3000);
                                 }
                              }}
                           />
                           <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center z-20">
                              <span className="text-xs font-medium text-white shadow-sm">Thay đổi</span>
                           </div>
                           <img 
                              src={user?.avatar_url || `${APP_CONFIG.urls.defaultAvatarGenerator}?seed=${user?.display_name || 'Alex'}&backgroundColor=transparent`} 
                              alt="Avatar" 
                              className="w-full h-full object-cover z-10 relative" 
                           />
                        </div>
                        <div className="flex-1 space-y-5">
                           <div className="space-y-2">
                              <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Tên hiển thị</label>
                              <input type="text" value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 text-sm focus:outline-none transition-all shadow-inner" />
                           </div>
                           <div className="space-y-2">
                              <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Email</label>
                              <input type="email" value={userEmail} disabled className="w-full opacity-60 bg-background border border-border rounded-xl py-3 px-4 text-sm focus:outline-none shadow-inner" />
                           </div>
                           <div className="space-y-2">
                              <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Chức danh</label>
                              <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 text-sm focus:outline-none transition-all shadow-inner" />
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
                           <div className="relative group">
                              <input 
                                 type={showCurrentPassword ? "text" : "password"} 
                                 value={currentPassword} 
                                 onChange={(e) => setCurrentPassword(e.target.value)} 
                                 placeholder="••••••••" 
                                 className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 pr-12 text-sm focus:outline-none transition-all shadow-inner" 
                              />
                              <button 
                                 type="button"
                                 onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                                 className="absolute right-4 top-1/2 -translate-y-1/2 text-foreground/40 hover:text-accent transition-colors"
                              >
                                 {showCurrentPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                              </button>
                           </div>
                        </div>
                        <div className="space-y-2">
                           <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Mật khẩu mới</label>
                           <div className="relative group">
                              <input 
                                 type={showNewPassword ? "text" : "password"} 
                                 value={newPassword} 
                                 onChange={(e) => setNewPassword(e.target.value)} 
                                 placeholder="••••••••" 
                                 className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 pr-12 text-sm focus:outline-none transition-all shadow-inner" 
                              />
                              <button 
                                 type="button"
                                 onClick={() => setShowNewPassword(!showNewPassword)}
                                 className="absolute right-4 top-1/2 -translate-y-1/2 text-foreground/40 hover:text-accent transition-colors"
                              >
                                 {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                              </button>
                           </div>
                        </div>
                        <div className="space-y-2">
                           <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Xác nhận mật khẩu mới</label>
                           <div className="relative group">
                              <input 
                                 type={showConfirmPassword ? "text" : "password"} 
                                 value={confirmPassword} 
                                 onChange={(e) => setConfirmPassword(e.target.value)} 
                                 placeholder="••••••••" 
                                 className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 pr-12 text-sm focus:outline-none transition-all shadow-inner" 
                              />
                              <button 
                                 type="button"
                                 onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                 className="absolute right-4 top-1/2 -translate-y-1/2 text-foreground/40 hover:text-accent transition-colors"
                              >
                                 {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                              </button>
                           </div>
                        </div>
                     </div>
                  </div>
               )}

               {/* 3. INTEGRATIONS */}
               {activeTab === 'integrations' && (
                  <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                     <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 overflow-hidden">
                        <div>
                           <h2 className="text-xl font-medium text-foreground/90 mb-1">Tích hợp ứng dụng</h2>
                           <p className="text-sm text-foreground/80">Kết nối các công cụ làm việc của bạn để đồng bộ hoá cuộc họp và nhiệm vụ.</p>
                        </div>
                        
                        <div className="flex items-center gap-3 bg-card/40 border border-white/5 p-1.5 rounded-2xl w-full md:w-fit shadow-lg shadow-black/20">
                           <div className="relative flex-1 md:w-64">
                              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground/40" />
                              <input 
                                 type="text" 
                                 placeholder="Tìm kiếm ứng dụng..." 
                                 value={searchIntegration}
                                 onChange={(e) => setSearchIntegration(e.target.value)}
                                 className="w-full bg-background/40 border border-transparent focus:border-accent/30 rounded-xl py-2 pl-10 pr-4 text-xs focus:outline-none transition-all shadow-inner"
                              />
                           </div>
                        </div>
                     </div>

                     {/* Filter Tabs */}
                     <div className="flex items-center gap-2 p-1 bg-white/5 border border-white/5 rounded-xl w-fit">
                        {[
                           { id: 'all', label: 'Tất cả' },
                           { id: 'comm', label: 'Truyền thông' },
                           { id: 'prod', label: 'Năng suất' }
                        ].map((tab) => (
                           <button
                              key={tab.id}
                              onClick={() => setIntegrationFilter(tab.id as any)}
                              className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${integrationFilter === tab.id ? 'bg-accent text-accent-foreground shadow-lg shadow-accent/20' : 'text-foreground/60 hover:text-foreground hover:bg-white/5'}`}
                           >
                              {tab.label}
                           </button>
                        ))}
                     </div>

                     <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Zoom Card */}
                        {(searchIntegration === "" || "zoom".includes(searchIntegration.toLowerCase())) && (integrationFilter === 'all' || integrationFilter === 'comm') && (
                           <div className={`glass-panel p-6 rounded-[2rem] border transition-all group overflow-hidden relative ${connectedServices.includes('zoom') ? 'border-accent/20 bg-accent/5' : 'border-white/5 hover:border-accent/20'}`}>
                              <div className="absolute top-0 right-0 w-32 h-32 bg-[#00C4CC]/5 rounded-full blur-[40px] pointer-events-none -translate-y-1/2 translate-x-1/2 group-hover:bg-[#00C4CC]/10 transition-colors"></div>
                              <div className="flex items-start justify-between relative z-10">
                                 <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-2xl bg-card border border-border flex items-center justify-center p-3 shadow-lg group-hover:scale-110 transition-transform">
                                       <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" className="text-[#00C4CC]"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="m15 13-3 3-3-3"></path><path d="M12 16V10"></path></svg>
                                    </div>
                                    <div>
                                       <div className="flex items-center gap-2">
                                          <h3 className="text-sm font-semibold text-foreground/90">Zoom Video</h3>
                                          {connectedServices.includes('zoom') && <span className="bg-emerald-500/20 text-emerald-500 text-[8px] px-1.5 py-0.5 rounded-md uppercase tracking-wider font-bold border border-emerald-500/20 shadow-sm">Connected</span>}
                                       </div>
                                       <p className="text-[10px] text-foreground/50 mt-1 uppercase tracking-wider font-bold">Truyền thông</p>
                                    </div>
                                 </div>
                                 <button 
                                    onClick={() => handleToggleConnection('zoom', 'Zoom Video', <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" className="text-[#00C4CC]"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="m15 13-3 3-3-3"></path><path d="M12 16V10"></path></svg>, '#00C4CC')}
                                    className={`px-4 py-2 rounded-xl text-xs font-medium border transition-all translate-y-0 group-hover:-translate-y-1 shadow-md ${connectedServices.includes('zoom') ? 'border-red-500/20 text-red-500/70 hover:bg-red-500/10' : 'bg-white/5 hover:bg-accent hover:text-accent-foreground border-white/10'}`}
                                 >
                                    {connectedServices.includes('zoom') ? 'Ngắt kết nối' : 'Kết nối'}
                                 </button>
                              </div>
                              <p className="mt-4 text-xs text-foreground/70 leading-relaxed max-w-[90%]">Tự động lấy bản ghi âm từ Zoom Cloud ngay sau khi cuộc họp kết thúc.</p>
                           </div>
                        )}

                        {/* Slack Card */}
                        {(searchIntegration === "" || "slack".includes(searchIntegration.toLowerCase())) && (integrationFilter === 'all' || integrationFilter === 'comm') && (
                           <div className={`glass-panel p-6 rounded-[2rem] border transition-all group overflow-hidden relative shadow-[0_0_30px_rgba(212,175,55,0.05)] ${connectedServices.includes('slack') ? 'border-accent/20 bg-accent/5' : 'border-white/5 hover:border-accent/20'}`}>
                              <div className="absolute top-0 right-0 w-32 h-32 bg-accent/10 rounded-full blur-[40px] pointer-events-none -translate-y-1/2 translate-x-1/2 text-emerald-500"></div>
                              <div className="flex items-start justify-between relative z-10">
                                 <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-2xl bg-card border border-white/10 flex items-center justify-center p-3 shadow-lg group-hover:rotate-6 transition-transform">
                                       <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" className="text-[#36C5F0]"><path d="M22.54 6.42a2.78 2.78 0 0 0-4.08 2.18v4.36a2.78 2.78 0 0 0 4.08 2.18V6.42Z"></path><path d="M4.08 17.58a2.78 2.78 0 0 0-2.18-4.08h4.36a2.78 2.78 0 0 0 2.18 4.08v-4.36A2.78 2.78 0 0 0 4.08 17.58Z"></path><path d="M8.44 6.42a2.78 2.78 0 0 0 4.08-2.18v4.36A2.78 2.78 0 0 0 8.44 6.42Z"></path><path d="M19.92 17.58a2.78 2.78 0 0 0 2.18-4.08h-4.36a2.78 2.78 0 0 0-2.18 4.08v-4.36A2.78 2.78 0 0 0 19.92 17.58Z"></path></svg>
                                    </div>
                                    <div>
                                       <div className="flex items-center gap-2">
                                          <h3 className="text-sm font-semibold text-foreground/90">Slack</h3>
                                          {connectedServices.includes('slack') && <span className="bg-emerald-500/20 text-emerald-500 text-[8px] px-1.5 py-0.5 rounded-md uppercase tracking-wider font-bold border border-emerald-500/20 shadow-sm animate-pulse">Connected</span>}
                                       </div>
                                       <p className="text-[10px] text-foreground/50 mt-1 uppercase tracking-wider font-bold">Truyền thông</p>
                                    </div>
                                 </div>
                                 <button 
                                    onClick={() => handleToggleConnection('slack', 'Slack', <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" className="text-[#36C5F0]"><path d="M22.54 6.42a2.78 2.78 0 0 0-4.08 2.18v4.36a2.78 2.78 0 0 0 4.08 2.18V6.42Z"></path><path d="M4.08 17.58a2.78 2.78 0 0 0-2.18-4.08h4.36a2.78 2.78 0 0 0 2.18 4.08v-4.36A2.78 2.78 0 0 0 4.08 17.58Z"></path><path d="M8.44 6.42a2.78 2.78 0 0 0 4.08-2.18v4.36A2.78 2.78 0 0 0 8.44 6.42Z"></path><path d="M19.92 17.58a2.78 2.78 0 0 0 2.18-4.08h-4.36a2.78 2.78 0 0 0-2.18 4.08v-4.36A2.78 2.78 0 0 0 19.92 17.58Z"></path></svg>, '#36C5F0')}
                                    className={`px-4 py-2 rounded-xl text-xs font-medium border transition-all shadow-sm ${connectedServices.includes('slack') ? 'border-red-500/20 text-red-500/70 hover:bg-red-500/10' : 'bg-white/5 hover:bg-accent hover:text-accent-foreground border-white/10'}`}
                                 >
                                    {connectedServices.includes('slack') ? 'Ngắt kết nối' : 'Kết nối'}
                                 </button>
                              </div>
                              <p className="mt-4 text-xs text-foreground/70 leading-relaxed max-w-[90%]">Gửi thông báo tóm tắt cuộc họp và danh sách Action Items thẳng vào kênh Slack.</p>
                           </div>
                        )}

                        {/* Google Drive Card */}
                        {(searchIntegration === "" || "google drive".includes(searchIntegration.toLowerCase())) && (integrationFilter === 'all' || integrationFilter === 'prod') && (
                           <div className={`glass-panel p-6 rounded-[2rem] border transition-all group overflow-hidden relative ${connectedServices.includes('googledrive') ? 'border-accent/20 bg-accent/5' : 'border-white/5 hover:border-accent/20'}`}>
                              <div className="absolute top-0 right-0 w-32 h-32 bg-[#34A853]/5 rounded-full blur-[40px] pointer-events-none -translate-y-1/2 translate-x-1/2 group-hover:bg-[#34A853]/10 transition-colors"></div>
                              <div className="flex items-start justify-between relative z-10">
                                 <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-2xl bg-card border border-border flex items-center justify-center p-3 shadow-lg group-hover:scale-110 transition-transform">
                                       <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#34A853]"><path d="M12 2L4.5 15.5H19.5L12 2Z" /><path d="M12 2L2 20H12H22L12 2Z" /></svg>
                                    </div>
                                    <div>
                                       <div className="flex items-center gap-2">
                                          <h3 className="text-sm font-semibold text-foreground/90">Google Drive</h3>
                                          {connectedServices.includes('googledrive') && <span className="bg-emerald-500/20 text-emerald-500 text-[8px] px-1.5 py-0.5 rounded-md uppercase tracking-wider font-bold border border-emerald-500/20 shadow-sm">Connected</span>}
                                       </div>
                                       <p className="text-[10px] text-foreground/50 mt-1 uppercase tracking-wider font-bold">Năng suất</p>
                                    </div>
                                 </div>
                                 <button 
                                    onClick={() => handleToggleConnection('googledrive', 'Google Drive', <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#34A853]"><path d="M12 2L4.5 15.5H19.5L12 2Z" /><path d="M12 2L2 20H12H22L12 2Z" /></svg>, '#34A853')}
                                    className={`px-4 py-2 rounded-xl text-xs font-medium border transition-all shadow-md ${connectedServices.includes('googledrive') ? 'border-red-500/20 text-red-500/70 hover:bg-red-500/10' : 'bg-white/5 hover:bg-accent hover:text-accent-foreground border-white/10'}`}
                                 >
                                    {connectedServices.includes('googledrive') ? 'Ngắt kết nối' : 'Kết nối'}
                                 </button>
                              </div>
                              <p className="mt-4 text-xs text-foreground/70 leading-relaxed max-w-[90%]">Lưu trữ biên bản họp và tài liệu Action Items trực tiếp vào Google Drive của bạn.</p>
                           </div>
                        )}

                        {/* Notion Card */}
                        {(searchIntegration === "" || "notion".includes(searchIntegration.toLowerCase())) && (integrationFilter === 'all' || integrationFilter === 'prod') && (
                           <div className={`glass-panel p-6 rounded-[2rem] border transition-all group overflow-hidden relative ${connectedServices.includes('notion') ? 'border-accent/20 bg-accent/5' : 'border-white/5 hover:border-accent/20'}`}>
                              <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-[40px] pointer-events-none -translate-y-1/2 translate-x-1/2 group-hover:bg-white/10 transition-colors"></div>
                              <div className="flex items-start justify-between relative z-10">
                                 <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-2xl bg-card border border-border flex items-center justify-center p-3 shadow-lg group-hover:-rotate-3 transition-transform">
                                       <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" className="text-foreground"><path d="M4.459 4.218c.41-.334.908-.517 1.417-.518h11.967c.508.001 1.006.184 1.417.518.411.334.686.793.774 1.293L20 18.067c.088.5-.027 1.018-.323 1.433-.296.415-.742.684-1.25.75L6.46 20.25c-.508-.066-.954-.335-1.25-.75-.296-.415-.411-.933-.323-1.433l.793-12.556c.088-.5.363-.959.774-1.293zM6.46 18.75l11.08-.25L16.747 5.75H7.253L6.46 18.75zM10 8.5h4v1.5h-4v-1.5zm0 3.5h4v1.5h-4V12zm0 3.5h4v1.5h-4v-1.5z" /></svg>
                                    </div>
                                    <div>
                                       <div className="flex items-center gap-2">
                                          <h3 className="text-sm font-semibold text-foreground/90">Notion</h3>
                                          {connectedServices.includes('notion') && <span className="bg-emerald-500/20 text-emerald-500 text-[8px] px-1.5 py-0.5 rounded-md uppercase tracking-wider font-bold border border-emerald-500/20 shadow-sm">Connected</span>}
                                       </div>
                                       <p className="text-[10px] text-foreground/50 mt-1 uppercase tracking-wider font-bold">Năng suất</p>
                                    </div>
                                 </div>
                                 <button 
                                    onClick={() => handleToggleConnection('notion', 'Notion', <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" className="text-foreground"><path d="M4.459 4.218c.41-.334.908-.517 1.417-.518h11.967c.508.001 1.006.184 1.417.518.411.334.686.793.774 1.293L20 18.067c.088.5-.027 1.018-.323 1.433-.296.415-.742.684-1.25.75L6.46 20.25c-.508-.066-.954-.335-1.25-.75-.296-.415-.411-.933-.323-1.433l.793-12.556c.088-.5.363-.959.774-1.293zM6.46 18.75l11.08-.25L16.747 5.75H7.253L6.46 18.75zM10 8.5h4v1.5h-4v-1.5zm0 3.5h4v1.5h-4V12zm0 3.5h4v1.5h-4v-1.5z" /></svg>, '#000000')}
                                    className={`px-4 py-2 rounded-xl text-xs font-medium border transition-all shadow-md ${connectedServices.includes('notion') ? 'border-red-500/20 text-red-500/70 hover:bg-red-500/10' : 'bg-white/5 hover:bg-accent hover:text-accent-foreground border-white/10'}`}
                                 >
                                    {connectedServices.includes('notion') ? 'Ngắt kết nối' : 'Kết nối'}
                                 </button>
                              </div>
                              <p className="mt-4 text-xs text-foreground/70 leading-relaxed max-w-[90%]">Đồng bộ Action Items thành database trong workspace Notion của bạn.</p>
                           </div>
                        )}
                     </div>

                     {/* API KEY SECTION */}
                     <div className="glass-panel p-8 rounded-[2.5rem] border border-white/5 bg-background/20 relative overflow-hidden group">
                        <div className="absolute inset-0 bg-gradient-to-r from-accent/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                        <div className="relative z-10">
                           <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                              <div>
                                 <div className="flex items-center gap-3 mb-2">
                                    <div className="p-2.5 bg-card border border-border rounded-2xl shadow-inner">
                                       <Globe size={18} className="text-[#0079BF]" />
                                    </div>
                                    <h3 className="text-lg font-medium text-foreground/90 tracking-tight">Khác (API Key)</h3>
                                 </div>
                                 <p className="text-sm text-foreground/60 max-w-sm">Sử dụng Token API để xây dựng các tích hợp tuỳ chỉnh hoặc kết nối qua Zapier, Make.</p>
                              </div>
                              
                              <div className="flex flex-col gap-3 min-w-[320px]">
                                 <div className="flex bg-background border border-white/5 rounded-[1.25rem] p-1.5 items-center gap-1 shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)] focus-within:border-accent/40 transition-all">
                                    <div className="flex-1 px-4 py-2 font-mono text-xs text-foreground/90 select-none overflow-hidden text-ellipsis whitespace-nowrap tracking-wide">
                                       {revealApiKey ? 'sk_live_test_api_key_123_full_secret' : 'sk_live_••••••••••••••••x891'}
                                    </div>
                                    <button 
                                       onClick={() => setRevealApiKey(!revealApiKey)}
                                       className="p-2.5 hover:bg-white/5 rounded-xl text-foreground/40 hover:text-accent transition-colors"
                                       title={revealApiKey ? "Hide key" : "Show key"}
                                    >
                                       {revealApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                                    </button>
                                    <button 
                                       onClick={() => copyToClipboard('sk_live_test_api_key_123_full_secret')} 
                                       className="p-2.5 hover:bg-white/5 rounded-xl text-foreground/40 hover:text-accent transition-colors relative"
                                       title="Copy key"
                                    >
                                       {copied ? (
                                          <>
                                             <CheckCircle2 size={16} className="text-emerald-500 animate-in zoom-in" />
                                             <span className="absolute -top-12 left-1/2 -translate-x-1/2 bg-emerald-500 text-white text-[10px] px-2.5 py-1.5 rounded-lg shadow-xl font-bold animate-in fade-in slide-in-from-bottom-2 z-20 whitespace-nowrap">Đã sao chép!</span>
                                          </>
                                       ) : <Copy size={16} />}
                                    </button>
                                 </div>
                                 <p className="text-[10px] text-center text-foreground/40 px-4 font-medium tracking-tight">Đừng bao giờ chia sẻ API Key của bạn cho bất kỳ ai.</p>
                              </div>
                           </div>
                        </div>
                     </div>
                  </div>
               )}

               {/* 4. NOTIFICATIONS SETTINGS */}
               {activeTab === 'notifications' && (
                  <div className="space-y-10 animate-in fade-in duration-500">
                     <div className="border-b border-border pb-6">
                        <h2 className="text-xl font-medium text-foreground/90 mb-1">Cài đặt Thông báo</h2>
                        <p className="text-sm text-foreground/80">Chọn cách thức và thời điểm bạn muốn nhận thông báo từ hệ thống.</p>
                     </div>

                     <div className="space-y-6">
                        <div className="flex items-center justify-between p-5 rounded-2xl border border-white/5 bg-background/40 hover:bg-card/40 transition-colors">
                           <div className="flex-1 pr-4">
                              <h3 className="text-sm font-medium text-foreground/90 mb-1">Tóm tắt cuộc họp qua Email</h3>
                              <p className="text-xs text-foreground/60 leading-relaxed">Nhận email tóm tắt chi tiết ngay sau khi AI xử lý xong bản ghi âm cuộc họp của bạn.</p>
                           </div>
                           <label className="relative inline-flex items-center cursor-pointer">
                              <input 
                                 type="checkbox" 
                                 className="sr-only peer" 
                                 checked={emailSummaries} 
                                 onChange={(e) => setEmailSummaries(e.target.checked)} 
                              />
                              <div className="w-11 h-6 bg-card border border-border rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-foreground/50 peer-checked:after:bg-foreground/90 after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent peer-checked:border-accent"></div>
                           </label>
                        </div>
                        
                        <div className="flex items-center justify-between p-5 rounded-2xl border border-white/5 bg-background/40 hover:bg-card/40 transition-colors">
                           <div className="flex-1 pr-4">
                              <h3 className="text-sm font-medium text-foreground/90 mb-1">Cảnh báo hành động (Action Items)</h3>
                              <p className="text-xs text-foreground/60 leading-relaxed">Thông báo đẩy khi bạn được phân công một công việc mới trong biên bản họp.</p>
                           </div>
                           <label className="relative inline-flex items-center cursor-pointer">
                              <input 
                                 type="checkbox" 
                                 className="sr-only peer" 
                                 checked={actionItemAlerts} 
                                 onChange={(e) => setActionItemAlerts(e.target.checked)} 
                              />
                              <div className="w-11 h-6 bg-card border border-border rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-foreground/50 peer-checked:after:bg-foreground/90 after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent peer-checked:border-accent"></div>
                           </label>
                        </div>

                        <div className="flex items-center justify-between p-5 rounded-2xl border border-white/5 bg-background/40 hover:bg-card/40 transition-colors">
                           <div className="flex-1 pr-4">
                              <h3 className="text-sm font-medium text-foreground/90 mb-1">Cập nhật Sản phẩm & Ưu đãi</h3>
                              <p className="text-xs text-foreground/60 leading-relaxed">Nhận email định kỳ về các tính năng mới và chương trình nâng cấp gói.</p>
                           </div>
                           <label className="relative inline-flex items-center cursor-pointer">
                              <input 
                                 type="checkbox" 
                                 className="sr-only peer" 
                                 checked={productUpdates} 
                                 onChange={(e) => setProductUpdates(e.target.checked)} 
                              />
                              <div className="w-11 h-6 bg-card border border-border rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-foreground/50 peer-checked:after:bg-foreground/90 after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent peer-checked:border-accent"></div>
                           </label>
                        </div>
                     </div>
                  </div>
               )}

               {/* 5. BILLING SETTINGS */}
               {activeTab === 'billing' && (
                  <div className="space-y-10 animate-in fade-in duration-500">
                     <div className="border-b border-border pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div>
                           <h2 className="text-xl font-medium text-foreground/90 mb-1">Gói & Thanh toán</h2>
                           <p className="text-sm text-foreground/80">Quản lý gói đăng ký hiện tại và nâng cấp không gian làm việc của bạn.</p>
                        </div>
                        <button 
                           onClick={() => setShowPricing(!showPricing)}
                           className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all border ${showPricing ? 'bg-accent text-accent-foreground border-accent' : 'bg-white/5 hover:bg-white/10 border-white/10 text-foreground/90'}`}
                        >
                           {showPricing ? 'Xem gói hiện tại' : 'Nâng cấp gói'}
                        </button>
                     </div>

                     {!showPricing ? (
                        <>
                           {/* Current Plan Card */}
                           <div className="relative overflow-hidden rounded-[2rem] border border-accent/20 bg-accent/5 p-8 shadow-inner">
                              <div className="absolute top-0 right-0 w-64 h-64 bg-accent/10 rounded-full blur-[60px] pointer-events-none -translate-y-1/2 translate-x-1/2"></div>
                              
                              <div className="relative z-10">
                                 <div className="flex items-center justify-between mb-8">
                                    <div>
                                       <h3 className="text-lg font-medium tracking-wide flex items-center gap-3">
                                          Pro Workspace 
                                          <span className="text-[10px] uppercase tracking-widest bg-accent/20 text-accent px-2 py-0.5 rounded-full border border-accent/20">Đang sử dụng</span>
                                       </h3>
                                       <p className="text-sm text-foreground/60 mt-1">Chu kỳ thanh toán tiếp theo: 15/04/2026</p>
                                    </div>
                                    <div className="text-right">
                                       <span className="text-3xl font-medium tracking-tight">$29</span>
                                       <span className="text-sm text-foreground/60">/tháng</span>
                                    </div>
                                 </div>

                                 {/* Usage Bar */}
                                 <div className="space-y-3">
                                    <div className="flex justify-between text-sm">
                                       <span className="font-medium text-foreground/80">Thời lượng giải mã AI</span>
                                       <span className="text-foreground/60">42 / 100 giờ</span>
                                    </div>
                                    <div className="w-full bg-background/50 border border-white/5 rounded-full h-2.5 overflow-hidden">
                                       <div className="bg-gradient-to-r from-accent/80 to-accent h-full rounded-full w-[42%] shadow-[0_0_10px_rgba(212,175,55,0.5)]"></div>
                                    </div>
                                    <p className="text-xs text-foreground/50">Đã làm mới vào 15/03/2026</p>
                                 </div>
                              </div>
                           </div>

                           {/* Invoices */}
                           <div className="space-y-4">
                              <h3 className="text-sm font-medium tracking-wide uppercase text-foreground/80 mb-4">Lịch sử giao dịch</h3>
                              <div className="border border-white/5 rounded-2xl overflow-hidden bg-background/20">
                                 <table className="w-full text-sm text-left">
                                    <thead className="bg-card/40 text-foreground/60 text-xs uppercase tracking-wider">
                                       <tr>
                                          <th className="px-6 py-4 font-medium">Hóa đơn</th>
                                          <th className="px-6 py-4 font-medium hidden md:table-cell">Trạng thái</th>
                                          <th className="px-6 py-4 font-medium">Số tiền</th>
                                          <th className="px-6 py-4 font-medium text-right">Tải xuống</th>
                                       </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/5">
                                       <tr className="hover:bg-card/20 transition-colors">
                                          <td className="px-6 py-4 font-medium text-foreground/90">Tháng 3, 2026</td>
                                          <td className="px-6 py-4 hidden md:table-cell"><span className="text-emerald-400 bg-emerald-400/10 px-2.5 py-1 rounded-full text-xs">Thành công</span></td>
                                          <td className="px-6 py-4 font-medium">$29.00</td>
                                          <td className="px-6 py-4 text-right"><button className="text-accent hover:text-accent/80 text-xs font-medium uppercase tracking-wider">PDF</button></td>
                                       </tr>
                                       <tr className="hover:bg-card/20 transition-colors">
                                          <td className="px-6 py-4 font-medium text-foreground/90">Tháng 2, 2026</td>
                                          <td className="px-6 py-4 hidden md:table-cell"><span className="text-emerald-400 bg-emerald-400/10 px-2.5 py-1 rounded-full text-xs">Thành công</span></td>
                                          <td className="px-6 py-4 font-medium">$29.00</td>
                                          <td className="px-6 py-4 text-right"><button className="text-accent hover:text-accent/80 text-xs font-medium uppercase tracking-wider">PDF</button></td>
                                       </tr>
                                    </tbody>
                                 </table>
                              </div>
                           </div>
                        </>
                     ) : (
                        /* Pricing Plans UI */
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in slide-in-from-bottom-8 duration-700">
                           {/* Starter Plan */}
                           <div className="glass-panel p-8 rounded-[2rem] border border-border flex flex-col hover:border-accent/20 transition-all group">
                              <div className="mb-6">
                                 <div className="w-12 h-12 rounded-2xl bg-card border border-white/5 flex items-center justify-center text-foreground/60 mb-4 group-hover:text-accent transition-colors">
                                    <Star size={24} strokeWidth={1.5} />
                                 </div>
                                 <h3 className="text-lg font-medium tracking-wide">Starter</h3>
                                 <p className="text-xs text-foreground/60 mt-1">Dành cho cá nhân mới bắt đầu.</p>
                              </div>
                              <div className="mb-8">
                                 <span className="text-4xl font-medium tracking-tight">$9</span>
                                 <span className="text-sm text-foreground/50">/tháng</span>
                              </div>
                              <ul className="space-y-4 mb-10 flex-1">
                                 {['10 giờ giải mã AI', '5 cuộc họp mỗi tháng', 'Tóm tắt cơ bản', 'Lưu trữ 30 ngày'].map((item) => (
                                    <li key={item} className="flex items-center gap-3 text-sm text-foreground/80">
                                       <CheckCircle2 size={16} className="text-accent" />
                                       {item}
                                    </li>
                                 ))}
                              </ul>
                              <button 
                                 onClick={() => { setSelectedPlan({name: 'Starter', price: '$9'}); setShowPaymentModal(true); }}
                                 className="w-full py-3.5 rounded-xl border border-border hover:border-accent hover:text-accent transition-all text-sm font-medium"
                              >
                                 Chọn gói Starter
                              </button>
                           </div>

                           {/* Pro Plan */}
                           <div className="glass-panel p-8 rounded-[2rem] border border-accent/40 bg-accent/5 flex flex-col relative overflow-hidden transform lg:scale-105 shadow-[0_0_40px_rgba(212,175,55,0.1)]">
                              <div className="absolute top-0 right-0 px-4 py-1.5 bg-accent text-accent-foreground text-[10px] font-bold tracking-[0.2em] uppercase rounded-bl-2xl">Phổ biến</div>
                              <div className="mb-6">
                                 <div className="w-12 h-12 rounded-2xl bg-accent/20 border border-accent/20 flex items-center justify-center text-accent mb-4">
                                    <Zap size={24} strokeWidth={1.5} />
                                 </div>
                                 <h3 className="text-lg font-medium tracking-wide text-foreground">Pro Workspace</h3>
                                 <p className="text-xs text-foreground/70 mt-1">Tối ưu cho chuyên gia và nhóm nhỏ.</p>
                              </div>
                              <div className="mb-8">
                                 <span className="text-4xl font-medium tracking-tight text-foreground">$19</span>
                                 <span className="text-sm text-foreground/60">/tháng</span>
                              </div>
                              <ul className="space-y-4 mb-10 flex-1">
                                 {['50 giờ giải mã AI', 'Không giới hạn cuộc họp', 'Phân tích Action Items', 'Lưu trữ không giới hạn', 'Hỗ trợ ưu tiên'].map((item) => (
                                    <li key={item} className="flex items-center gap-3 text-sm text-foreground">
                                       <CheckCircle2 size={16} className="text-accent" />
                                       {item}
                                    </li>
                                 ))}
                              </ul>
                              <button 
                                 onClick={() => { setSelectedPlan({name: 'Pro Workspace', price: '$19'}); setShowPaymentModal(true); }}
                                 className="w-full py-3.5 rounded-xl bg-accent text-accent-foreground font-semibold text-sm hover:scale-[1.02] transition-all shadow-lg"
                              >
                                 Chọn gói Pro
                              </button>
                           </div>

                           {/* Enterprise Plan */}
                           <div className="glass-panel p-8 rounded-[2rem] border border-border flex flex-col hover:border-accent/20 transition-all group">
                              <div className="mb-6">
                                 <div className="w-12 h-12 rounded-2xl bg-card border border-white/5 flex items-center justify-center text-foreground/60 mb-4 group-hover:text-accent transition-colors">
                                    <Crown size={24} strokeWidth={1.5} />
                                 </div>
                                 <h3 className="text-lg font-medium tracking-wide">Enterprise</h3>
                                 <p className="text-xs text-foreground/60 mt-1">Dành cho tổ chức lớn và yêu cầu tùy chỉnh.</p>
                              </div>
                              <div className="mb-8">
                                 <span className="text-4xl font-medium tracking-tight">$29</span>
                                 <span className="text-sm text-foreground/50">/tháng</span>
                              </div>
                              <ul className="space-y-4 mb-10 flex-1">
                                 {['Không giới hạn thời lượng', 'Tùy chỉnh mô hình AI', 'Đội ngũ hỗ trợ 24/7', 'Bảo mật nâng cao', 'API Access'].map((item) => (
                                    <li key={item} className="flex items-center gap-3 text-sm text-foreground/80">
                                       <CheckCircle2 size={16} className="text-accent" />
                                       {item}
                                    </li>
                                 ))}
                              </ul>
                              <button 
                                 onClick={() => { setSelectedPlan({name: 'Enterprise', price: '$29'}); setShowPaymentModal(true); }}
                                 className="w-full py-3.5 rounded-xl border border-border hover:border-accent hover:text-accent transition-all text-sm font-medium"
                               >
                                 Liên hệ Sale
                              </button>
                           </div>
                        </div>
                     )}
                  </div>
               )}

               {/* PAYMENT MODAL */}
               {showPaymentModal && (
                  <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
                     <div className="absolute inset-0 bg-background/80 backdrop-blur-xl animate-in fade-in duration-300" onClick={() => setShowPaymentModal(false)}></div>
                     <div className="relative w-full max-w-md glass-panel rounded-[2rem] border border-white/10 shadow-2xl p-0 overflow-hidden animate-in zoom-in-95 duration-300">
                        {paymentSuccess ? (
                           <div className="p-10 text-center space-y-6">
                              <div className="w-20 h-20 bg-emerald-500/20 text-emerald-500 rounded-full flex items-center justify-center mx-auto mb-6">
                                 <CheckCircle2 size={40} />
                              </div>
                              <h3 className="text-2xl font-medium tracking-tight">Thanh toán thành công!</h3>
                              <p className="text-foreground/70 text-sm">Cảm ơn bạn đã nâng cấp không gian làm việc. Gói {selectedPlan?.name} của bạn đã sẵn sàng.</p>
                              <button 
                                 onClick={() => { setShowPaymentModal(false); setShowPricing(false); setPaymentSuccess(false); }}
                                 className="w-full py-3.5 rounded-xl bg-accent text-accent-foreground font-semibold text-sm hover:scale-[1.02] transition-all"
                              >
                                 Quay lại Cài đặt
                              </button>
                           </div>
                        ) : (
                           <>
                              <div className="p-8 border-b border-white/5 bg-card/40 flex items-center justify-between">
                                 <div>
                                    <h3 className="text-lg font-medium tracking-wide">Thanh toán</h3>
                                    <p className="text-xs text-foreground/60 mt-0.5">Nâng cấp lên gói {selectedPlan?.name}</p>
                                 </div>
                                 <button onClick={() => setShowPaymentModal(false)} className="text-foreground/40 hover:text-foreground transition-colors p-2">
                                    <X size={20} />
                                 </button>
                              </div>
                              <div className="p-8 space-y-6">
                                 <div className="space-y-4">
                                    <div className="relative group">
                                       <CardIcon size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-foreground/40 group-focus-within:text-accent transition-colors" />
                                       <input 
                                          type="text" 
                                          placeholder="Số thẻ" 
                                          className="w-full bg-background/40 border border-white/5 focus:border-accent/40 rounded-xl py-3.5 pl-12 pr-4 text-sm focus:outline-none transition-all shadow-inner"
                                       />
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                       <input 
                                          type="text" 
                                          placeholder="MM / YY" 
                                          className="w-full bg-background/40 border border-white/5 focus:border-accent/40 rounded-xl py-3.5 px-4 text-sm focus:outline-none transition-all shadow-inner"
                                       />
                                       <input 
                                          type="text" 
                                          placeholder="CVC" 
                                          className="w-full bg-background/40 border border-white/5 focus:border-accent/40 rounded-xl py-3.5 px-4 text-sm focus:outline-none transition-all shadow-inner"
                                       />
                                    </div>
                                 </div>

                                 <div className="bg-card/40 rounded-2xl p-4 border border-white/5 space-y-3">
                                    <div className="flex justify-between text-xs text-foreground/70">
                                       <span>Gói Đăng ký</span>
                                       <span>{selectedPlan?.price}/tháng</span>
                                    </div>
                                    <div className="flex justify-between text-xs text-foreground/70">
                                       <span>Thuế (0%)</span>
                                       <span>$0.00</span>
                                    </div>
                                    <div className="pt-3 border-t border-white/5 flex justify-between text-sm font-semibold">
                                       <span>Tổng cộng</span>
                                       <span className="text-accent">{selectedPlan?.price}</span>
                                    </div>
                                 </div>

                                 <button 
                                    onClick={() => {
                                       setPaymentLoading(true);
                                       setTimeout(() => {
                                          setPaymentLoading(false);
                                          setPaymentSuccess(true);
                                       }, 2000);
                                    }}
                                    disabled={paymentLoading}
                                    className="w-full py-4 rounded-xl bg-accent text-accent-foreground font-semibold text-sm hover:scale-[1.02] transition-all shadow-lg flex items-center justify-center gap-3 disabled:opacity-70"
                                 >
                                    {paymentLoading ? (
                                       <>
                                          <Loader2 size={18} className="animate-spin" />
                                          Đang xử lý...
                                       </>
                                    ) : (
                                       `Thanh toán ${selectedPlan?.price}`
                                    )}
                                 </button>
                                 <p className="text-[10px] text-center text-foreground/40 px-4">Bằng việc thanh toán, bạn đồng ý với Điều khoản dịch vụ và Chính sách bảo mật của chúng tôi.</p>
                              </div>
                           </>
                        )}
                     </div>
                  </div>
               )}

               {/* AUTH MODAL (Simulation) */}
               {showAuthModal && (
                  <div className="fixed inset-0 z-[110] flex items-center justify-center p-6">
                     <div className="absolute inset-0 bg-background/90 backdrop-blur-2xl animate-in fade-in duration-500" onClick={() => !authLoading && setShowAuthModal(null)}></div>
                     <div className="relative w-full max-w-sm glass-panel rounded-[2.5rem] border border-white/10 shadow-2xl p-0 overflow-hidden animate-in zoom-in-95 duration-400">
                        <div className="p-10 text-center space-y-8">
                           <div className="flex items-center justify-center gap-6 relative">
                              <div className="w-16 h-16 rounded-2xl bg-card border border-white/5 flex items-center justify-center p-4 shadow-xl">
                                 <img src="/logo.png" alt="SynapNote" className="w-full h-full object-contain opacity-80" onError={(e) => (e.currentTarget.src = 'https://cdn-icons-png.flaticon.com/512/2099/2099058.png')} />
                              </div>
                              <div className="flex flex-col items-center gap-1">
                                 <div className="flex gap-1">
                                    <div className={`w-1.5 h-1.5 rounded-full bg-accent ${authLoading ? 'animate-bounce' : 'opacity-40'}`}></div>
                                    <div className={`w-1.5 h-1.5 rounded-full bg-accent ${authLoading ? 'animate-bounce [animation-delay:0.2s]' : 'opacity-40'}`}></div>
                                    <div className={`w-1.5 h-1.5 rounded-full bg-accent ${authLoading ? 'animate-bounce [animation-delay:0.4s]' : 'opacity-40'}`}></div>
                                 </div>
                              </div>
                              <div className="w-16 h-16 rounded-2xl bg-card border border-white/5 flex items-center justify-center p-4 shadow-xl overflow-hidden">
                                 <div className="w-full h-full flex items-center justify-center" style={{ color: showAuthModal.color }}>
                                    {showAuthModal.icon}
                                 </div>
                              </div>
                           </div>
                           
                           <div className="space-y-3">
                              <h3 className="text-xl font-medium tracking-tight">Ủy quyền ứng dụng</h3>
                              <p className="text-sm text-foreground/60 leading-relaxed px-4">
                                 {authLoading 
                                    ? `Đang thiết lập kết nối bảo mật với ${showAuthModal.name}...` 
                                    : `Cho phép SynapNote AI truy cập vào tài khoản ${showAuthModal.name} của bạn để đồng bộ dữ liệu.`}
                              </p>
                           </div>

                           <div className="grid grid-cols-1 gap-3 pt-4">
                              <button 
                                 onClick={completeConnection}
                                 disabled={authLoading}
                                 className="w-full py-4 rounded-2xl bg-accent text-accent-foreground font-semibold text-sm hover:scale-[1.02] active:scale-[0.98] transition-all shadow-lg shadow-accent/20 flex items-center justify-center gap-3 disabled:opacity-70"
                              >
                                 {authLoading ? (
                                    <>
                                       <Loader2 size={18} className="animate-spin" />
                                       Đang xác thực...
                                    </>
                                 ) : (
                                    `Chấp nhận kết nối`
                                 )}
                              </button>
                              {!authLoading && (
                                 <button 
                                    onClick={() => setShowAuthModal(null)}
                                    className="w-full py-4 rounded-2xl border border-white/5 bg-white/5 hover:bg-white/10 text-foreground/60 text-sm font-medium transition-all"
                                 >
                                    Hủy bỏ
                                 </button>
                              )}
                           </div>
                           
                           <p className="text-[10px] text-foreground/40 font-medium">Bằng việc tiếp tục, bạn đồng ý cấp quyền truy cập dữ liệu cho SynapNote.</p>
                        </div>
                     </div>
                  </div>
               )}

               {/* Global Save Button for forms */}
               {(activeTab === 'profile' || activeTab === 'security' || activeTab === 'notifications') && (
                  <div className="pt-8 mt-10 border-t border-border flex items-center justify-between">
                     <div className="flex-1">
                        {message && (
                           <span className={`text-sm font-medium ${message.type === 'success' ? 'text-emerald-500' : 'text-red-400'}`}>
                              {message.text}
                           </span>
                        )}
                     </div>
                     <button 
                        onClick={handleSave}
                        disabled={loading}
                        className={`bg-accent text-accent-foreground px-8 py-3 rounded-xl font-medium text-sm transition-all ${loading ? 'opacity-70 cursor-wait' : 'hover:scale-[1.02] shadow-[0_4px_14px_rgba(212,175,55,0.2)]'}`}
                     >
                        {loading ? 'Đang lưu...' : 'Lưu thay đổi'}
                     </button>
                  </div>
               )}

            </div>
         </div>

      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Suspense fallback={
       <div className="w-full h-full flex items-center justify-center p-20">
          <Loader2 className="text-accent animate-spin" size={32} />
       </div>
    }>
      <SettingsContent />
    </Suspense>
  );
}

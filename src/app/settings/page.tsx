"use client";

import { useState, useEffect, useRef } from 'react';
import { User, Bell, Shield, CreditCard, Sparkles, Sliders, Copy, CheckCircle2, Camera, Loader2 } from 'lucide-react';
import { APP_CONFIG } from '@/config/constants';
import { useUser } from '@/context/UserContext';
import { BillingTab } from './BillingTab';
import { IntegrationsTab } from './IntegrationsTab';

const API_BASE_URL = '/api';

type Tab = 'profile' | 'notifications' | 'security' | 'billing' | 'integrations';

export default function SettingsPage() {
   const [activeTab, setActiveTab] = useState<Tab>('profile');
   const [copied, setCopied] = useState(false);
   const { user, updateUser, loading: contextLoading } = useUser();
   const fileInputRef = useRef<HTMLInputElement>(null);

   const [displayName, setDisplayName] = useState('');
   const [title, setTitle] = useState('');
   const [avatarPreview, setAvatarPreview] = useState('');

   // Notification states
   const [emailSummaries, setEmailSummaries] = useState(true);
   const [actionItemAlerts, setActionItemAlerts] = useState(true);
   const [productUpdates, setProductUpdates] = useState(false);

   // Security states
   const [currentPassword, setCurrentPassword] = useState('');
   const [newPassword, setNewPassword] = useState('');
   const [confirmPassword, setConfirmPassword] = useState('');

   const [isSaving, setIsSaving] = useState(false);
   const [isUploading, setIsUploading] = useState(false);
   const [message, setMessage] = useState({ type: '', text: '' });

   useEffect(() => {
      if (user) {
         setDisplayName(user.display_name || '');
         setTitle(user.title || '');
         setAvatarPreview(user.avatar_url || `${APP_CONFIG.urls.defaultAvatarGenerator}?seed=${user.display_name || 'Alex'}&backgroundColor=transparent`);

         // Init notifications
         setEmailSummaries(!!user.email_summaries);
         setActionItemAlerts(!!user.action_item_alerts);
         setProductUpdates(!!user.product_updates);
      }
   }, [user]);

   const handleAvatarClick = () => {
      fileInputRef.current?.click();
   };

   const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file || !user) return;

      // 1. Show local preview
      const reader = new FileReader();
      reader.onloadend = () => {
         setAvatarPreview(reader.result as string);
      };
      reader.readAsDataURL(file);

      // 2. Upload to server
      setIsUploading(true);
      const formData = new FormData();
      formData.append('file', file);

      try {
         const response = await fetch(`${API_BASE_URL}/auth/upload-avatar?email=${user.email}`, {
            method: 'POST',
            body: formData,
         });

         if (response.ok) {
            const updatedUser = await response.json();
            updateUser({ avatar_url: updatedUser.avatar_url });
            setMessage({ type: 'success', text: 'Tải ảnh đại diện thành công!' });
         } else {
            setMessage({ type: 'error', text: 'Lỗi khi tải ảnh đại diện.' });
         }
      } catch (error) {
         setMessage({ type: 'error', text: 'Lỗi kết nối máy chủ.' });
      } finally {
         setIsUploading(false);
         setTimeout(() => setMessage({ type: '', text: '' }), 3000);
      }
   };

   const handleSave = async () => {
      if (!user) return;

      // Basic validation for security tab
      if (activeTab === 'security') {
         if (!currentPassword) {
            setMessage({ type: 'error', text: 'Vui lòng nhập mật khẩu hiện tại.' });
            return;
         }
         if (newPassword !== confirmPassword) {
            setMessage({ type: 'error', text: 'Mật khẩu mới không khớp.' });
            return;
         }
         if (newPassword.length < 6) {
            setMessage({ type: 'error', text: 'Mật khẩu mới phải từ 6 ký tự.' });
            return;
         }
      }

      setIsSaving(true);
      try {
         let response;
         let body;

         if (activeTab === 'profile' || activeTab === 'notifications') {
            body = {
               display_name: displayName,
               title: title,
               email_summaries: emailSummaries,
               action_item_alerts: actionItemAlerts,
               product_updates: productUpdates,
            };
            response = await fetch(`${API_BASE_URL}/auth/profile?email=${user.email}`, {
               method: 'PUT',
               headers: { 'Content-Type': 'application/json' },
               body: JSON.stringify(body),
            });
         } else if (activeTab === 'security') {
            body = {
               current_password: currentPassword,
               new_password: newPassword,
            };
            response = await fetch(`${API_BASE_URL}/auth/password?email=${user.email}`, {
               method: 'PUT',
               headers: { 'Content-Type': 'application/json' },
               body: JSON.stringify(body),
            });
         }

         if (response && response.ok) {
            const data = await response.json();
            if (activeTab !== 'security') {
               updateUser(data);
            } else {
               // Clear password fields on success
               setCurrentPassword('');
               setNewPassword('');
               setConfirmPassword('');
            }
            setMessage({ type: 'success', text: activeTab === 'security' ? 'Đổi mật khẩu thành công!' : 'Cập nhật thành công!' });
         } else {
            const errorData = await response?.json();
            setMessage({ type: 'error', text: errorData?.detail || 'Đã có lỗi xảy ra.' });
         }
      } catch (error) {
         setMessage({ type: 'error', text: 'Lỗi kết nối máy chủ.' });
      } finally {
         setIsSaving(false);
         setTimeout(() => setMessage({ type: '', text: '' }), 3000);
      }
   };

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

   if (contextLoading && !user) {
      return (
         <div className="flex items-center justify-center min-h-[500px]">
            <Loader2 className="w-10 h-10 text-accent animate-spin" />
         </div>
      );
   }

   return (
      <div className="w-full max-w-[1200px] mx-auto p-6 lg:p-10 h-full flex flex-col gap-8">

         {/* Header */}
         <div className="animate-in fade-in slide-in-from-top-4 duration-500">
            <h1 className="text-3xl lg:text-4xl font-medium tracking-tight text-foreground/90">Cài đặt Hệ thống</h1>
            <p className="text-foreground/80 text-sm tracking-wide mt-2">Quản lý tài khoản, tuỳ chọn thông báo và tích hợp ứng dụng của bạn.</p>
         </div>

         {message.text && (
            <div className={`fixed top-24 right-10 z-[100] px-6 py-4 rounded-2xl border animate-in slide-in-from-right-10 duration-300 shadow-2xl backdrop-blur-md ${message.type === 'success'
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                  : 'bg-red-500/10 border-red-500/20 text-red-400'
               }`}>
               <div className="flex items-center gap-3">
                  {message.type === 'success' ? <CheckCircle2 size={18} /> : <Sparkles size={18} />}
                  <span className="text-sm font-medium">{message.text}</span>
               </div>
            </div>
         )}

         <div className="flex flex-col lg:flex-row gap-8 lg:gap-12 flex-1 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-150 fill-mode-both">

            {/* Sidebar Navigation */}
            <div className="w-full lg:w-64 shrink-0 flex flex-col gap-2">
               {tabs.map((tab) => {
                  const isActive = activeTab === tab.id;
                  return (
                     <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-3 w-full text-left px-4 py-3 rounded-2xl transition-all duration-300 text-sm font-medium relative overflow-hidden group border ${isActive
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
                           <div className="w-24 h-24 rounded-full border border-white/10 relative overflow-hidden shrink-0 group cursor-pointer bg-card" onClick={handleAvatarClick}>
                              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center z-20">
                                 <Camera size={20} className="text-white mb-1" />
                                 <span className="text-[10px] font-medium text-white shadow-sm uppercase tracking-tight">Thay đổi</span>
                              </div>
                              {isUploading && (
                                 <div className="absolute inset-0 bg-black/40 flex items-center justify-center z-30 backdrop-blur-[2px]">
                                    <Loader2 className="w-6 h-6 text-accent animate-spin" />
                                 </div>
                              )}
                              {avatarPreview && <img src={avatarPreview} alt="Avatar" className="w-full h-full object-cover z-10 relative" />}
                              <input
                                 type="file"
                                 ref={fileInputRef}
                                 onChange={handleFileChange}
                                 className="hidden"
                                 accept="image/*"
                              />
                           </div>
                           <div className="flex-1 space-y-5">
                              <div className="space-y-2">
                                 <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Tên hiển thị</label>
                                 <input
                                    type="text"
                                    value={displayName}
                                    onChange={(e) => setDisplayName(e.target.value)}
                                    className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 text-sm focus:outline-none transition-all shadow-inner"
                                 />
                              </div>
                              <div className="space-y-2">
                                 <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Email</label>
                                 <input
                                    type="email"
                                    value={user?.email || ''}
                                    disabled
                                    className="w-full opacity-60 bg-background border border-border rounded-xl py-3 px-4 text-sm focus:outline-none shadow-inner"
                                 />
                              </div>
                              <div className="space-y-2">
                                 <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Chức danh</label>
                                 <input
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 text-sm focus:outline-none transition-all shadow-inner"
                                 />
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
                              <input
                                 type="password"
                                 placeholder="••••••••"
                                 value={currentPassword}
                                 onChange={(e) => setCurrentPassword(e.target.value)}
                                 className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 text-sm focus:outline-none transition-all shadow-inner"
                              />
                           </div>
                           <div className="space-y-2">
                              <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Mật khẩu mới</label>
                              <input
                                 type="password"
                                 placeholder="••••••••"
                                 value={newPassword}
                                 onChange={(e) => setNewPassword(e.target.value)}
                                 className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 text-sm focus:outline-none transition-all shadow-inner"
                              />
                           </div>
                           <div className="space-y-2">
                              <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Xác nhận mật khẩu mới</label>
                              <input
                                 type="password"
                                 placeholder="••••••••"
                                 value={confirmPassword}
                                 onChange={(e) => setConfirmPassword(e.target.value)}
                                 className="w-full bg-background border border-border focus:border-accent/50 rounded-xl py-3 px-4 text-sm focus:outline-none transition-all shadow-inner"
                              />
                           </div>
                        </div>
                     </div>
                  )}

                  {/* 3. INTEGRATIONS - WITH REAL API */}
                  {activeTab === 'integrations' && (
                     <IntegrationsTab userId={user?.id} />
                  )}

                  {/* 4. NOTIFICATION SETTINGS */}
                  {activeTab === 'notifications' && (
                     <div className="space-y-10 animate-in fade-in duration-500">
                        <div className="border-b border-border pb-6">
                           <h2 className="text-xl font-medium text-foreground/90 mb-1">Cấu hình thông báo</h2>
                           <p className="text-sm text-foreground/80">Kiểm soát cách thức và tần suất bạn nhận được thông báo từ hệ thống.</p>
                        </div>

                        <div className="space-y-6">
                           {/* Email Summary */}
                           <div className="flex items-center justify-between p-2">
                              <div className="space-y-0.5">
                                 <h3 className="text-sm font-medium text-foreground/90">Tóm tắt cuộc họp qua Email</h3>
                                 <p className="text-xs text-foreground/80">Nhận bản tóm tắt và hành động ngay sau khi cuộc họp kết thúc.</p>
                              </div>
                              <button
                                 onClick={() => setEmailSummaries(!emailSummaries)}
                                 className={`w-11 h-6 rounded-full transition-colors relative ${emailSummaries ? 'bg-accent' : 'bg-border'}`}
                              >
                                 <div className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${emailSummaries ? 'translate-x-5' : 'translate-x-0'}`} />
                              </button>
                           </div>

                           {/* Action Item Alerts */}
                           <div className="flex items-center justify-between p-2">
                              <div className="space-y-0.5">
                                 <h3 className="text-sm font-medium text-foreground/90">Nhắc nhở hành động</h3>
                                 <p className="text-xs text-foreground/80">Thông báo khi có nhiệm vụ mới được giao cho bạn.</p>
                              </div>
                              <button
                                 onClick={() => setActionItemAlerts(!actionItemAlerts)}
                                 className={`w-11 h-6 rounded-full transition-colors relative ${actionItemAlerts ? 'bg-accent' : 'bg-border'}`}
                              >
                                 <div className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${actionItemAlerts ? 'translate-x-5' : 'translate-x-0'}`} />
                              </button>
                           </div>

                           {/* Product Updates */}
                           <div className="flex items-center justify-between p-2">
                              <div className="space-y-0.5">
                                 <h3 className="text-sm font-medium text-foreground/90">Cập nhật sản phẩm</h3>
                                 <p className="text-xs text-foreground/80">Nhận tin tức về các tính năng mới và cải tiến sản phẩm.</p>
                              </div>
                              <button
                                 onClick={() => setProductUpdates(!productUpdates)}
                                 className={`w-11 h-6 rounded-full transition-colors relative ${productUpdates ? 'bg-accent' : 'bg-border'}`}
                              >
                                 <div className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${productUpdates ? 'translate-x-5' : 'translate-x-0'}`} />
                              </button>
                           </div>
                        </div>
                     </div>
                  )}

                  {/* 5. BILLING & SUBSCRIPTION - WITH REAL API */}
                  {activeTab === 'billing' && (
                     <BillingTab userId={user?.id} />
                  )}

                  {/* Global Save Button for forms */}
                  {(activeTab === 'profile' || activeTab === 'security' || activeTab === 'notifications') && (
                     <div className="pt-8 mt-10 border-t border-border flex justify-end">
                        <button
                           onClick={handleSave}
                           disabled={isSaving}
                           className="bg-accent text-accent-foreground px-8 py-3 rounded-xl font-medium text-sm hover:scale-[1.02] transition-transform shadow-[0_4px_14px_rgba(212,175,55,0.2)] flex items-center gap-2 disabled:opacity-70 disabled:hover:scale-100"
                        >
                           {isSaving && <Loader2 size={16} className="animate-spin" />}
                           {isSaving ? 'Đang lưu...' : 'Lưu thay đổi'}
                        </button>
                     </div>
                  )}

               </div>
            </div>

         </div>
      </div>
   );
}

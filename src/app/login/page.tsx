"use client";

import { useState } from 'react';
import { ArrowRight, Mail, Lock, Github } from 'lucide-react';
import { APP_CONFIG } from '@/config/constants';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate auth logic
    console.log("Submit", { email, password });
    window.location.href = '/'; 
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background relative overflow-hidden">
      
      {/* Abstract Background Elements */}
      <div className="fixed inset-0 pointer-events-none z-0">
         <div className="absolute inset-0 bg-background/90 z-10"></div>
         <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-accent/10 rounded-full blur-[150px] mix-blend-screen opacity-50 animate-pulse duration-10000 z-10"></div>
         <div className="absolute bottom-[-20%] right-[-10%] w-[45%] h-[45%] bg-accent/5 rounded-full blur-[120px] mix-blend-screen opacity-50 z-10"></div>
         <div className="absolute inset-0 opacity-[0.05] mix-blend-overlay z-20" style={{ backgroundImage: `url("${APP_CONFIG.urls.noiseBackground}")` }}></div>
         
         {/* Full Screen Image Background with overlay */}
         <img 
            src="https://images.unsplash.com/photo-1552664730-d307ca884978?q=80&w=2940&auto=format&fit=crop" 
            alt="Professional Meeting" 
            className="absolute inset-0 w-full h-full object-cover opacity-20"
         />
      </div>

      <div className="w-full max-w-[1000px] grid grid-cols-1 lg:grid-cols-2 gap-8 p-6 lg:p-10 z-10">
         
         {/* Branding / Info Side */}
         <div className="hidden lg:flex flex-col justify-between p-10">
            <div className="flex items-center gap-3">
               <div className="w-10 h-10 rounded-full border border-accent flex items-center justify-center relative shadow-[0_0_20px_rgba(212,175,55,0.2)]">
                  <div className="absolute inset-0 bg-accent/20 rounded-full"></div>
                  <div className="w-3 h-3 rounded-full bg-accent z-10"></div>
               </div>
               <span className="text-foreground font-medium text-xl tracking-widest uppercase">{APP_CONFIG.branding.appName}</span>
            </div>
            
            <div className="animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300 fill-mode-both">
               <h1 className="text-4xl lg:text-5xl font-medium tracking-tight mb-6 text-foreground/90">
                  Ghi chú <br />
                  <span className="font-semibold bg-gradient-to-r from-accent to-amber-200 bg-clip-text text-transparent">Thông minh hơn.</span>
               </h1>
               <p className="text-foreground/90 text-base max-w-sm leading-relaxed font-medium">
                  Nền tảng trí tuệ nhân tạo tự động trích xuất, tóm tắt và tự động hóa các quyết định từ cuộc họp của bạn.
               </p>
            </div>

            <div className="text-xs font-semibold tracking-widest uppercase text-foreground/30">
               © <span suppressHydrationWarning>{new Date().getFullYear()}</span> {APP_CONFIG.branding.appName}. All rights reserved.
            </div>
         </div>

         {/* Form Side */}
         <div className="relative group col-span-1 lg:col-start-2 w-full max-w-md mx-auto z-20">
            {/* Animated Gold Border Container */}
            <div className="absolute -inset-[2px] rounded-[2.2rem] bg-gradient-to-r from-accent/20 via-accent/60 to-accent/20 opacity-70 group-hover:opacity-100 blur-[2px] transition-opacity duration-500 animate-[pulse_4s_cubic-bezier(0.4,0,0.6,1)_infinite]"></div>
            
            <div className="glass-panel rounded-[2rem] p-8 lg:p-12 border border-border relative overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-700 bg-card/80 backdrop-blur-xl w-full h-full">
            {/* Header Login */}
            <div className="mb-10 w-full relative z-10 text-center">
                <h2 className="text-2xl font-medium text-foreground/90 mb-2">Đăng nhập</h2>
                <p className="text-sm text-foreground/80">Vui lòng đăng nhập để tiếp tục</p>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-5 relative z-10">


               <div className="space-y-1.5">
                  <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80 pl-1">Email</label>
                  <div className="relative group">
                     <Mail size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-foreground/30 group-focus-within:text-accent transition-colors" />
                     <input 
                        type="email" 
                        required
                        placeholder="you@company.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full bg-background border border-border focus:border-accent/50 rounded-2xl py-3.5 pl-12 pr-4 text-sm focus:outline-none transition-all shadow-inner hover:bg-card/40 focus:bg-background"
                     />
                  </div>
               </div>

               <div className="space-y-1.5">
                  <div className="flex items-center justify-between pl-1">
                     <label className="text-xs font-semibold uppercase tracking-wider text-foreground/80">Mật khẩu</label>
                     <a href="#" className="text-xs text-accent hover:underline">Quên mật khẩu?</a>
                  </div>
                  <div className="relative group">
                     <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-foreground/30 group-focus-within:text-accent transition-colors" />
                     <input 
                        type="password"
                        required 
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full bg-background border border-border focus:border-accent/50 rounded-2xl py-3.5 pl-12 pr-4 text-sm focus:outline-none transition-all shadow-inner hover:bg-card/40 focus:bg-background"
                     />
                  </div>
               </div>

               <button 
                  type="submit"
                  className="w-full bg-accent text-accent-foreground py-3.5 rounded-2xl font-medium tracking-wide hover:scale-[1.02] hover:shadow-[0_0_20px_rgba(212,175,55,0.3)] transition-all duration-300 mt-4 flex items-center justify-center gap-2 group"
               >
                  Đăng nhập vào hệ thống
                  <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
               </button>
            </form>

            <div className="mt-8 flex items-center justify-center gap-4 relative z-10">
               <div className="h-px bg-border flex-1"></div>
               <span className="text-xs uppercase tracking-widest text-foreground/30 font-semibold mb-[-2px]">Hoặc</span>
               <div className="h-px bg-border flex-1"></div>
            </div>

            <div className="mt-8 relative z-10 flex gap-4">
               <button className="flex-1 bg-card hover:bg-card/60 border border-border py-3 rounded-2xl flex items-center justify-center gap-3 transition-colors text-sm font-medium">
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                     <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                     <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                     <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                     <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                  </svg>
                  Google
               </button>
               <button className="flex-1 bg-card hover:bg-card/60 border border-border py-3 rounded-2xl flex items-center justify-center gap-3 transition-colors text-sm font-medium">
                  <Github size={20} className="text-foreground/80" />
                  GitHub
               </button>
            </div>

         </div>
         </div>

      </div>
    </div>
  );
}

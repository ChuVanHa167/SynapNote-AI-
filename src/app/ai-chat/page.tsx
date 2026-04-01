"use client";

import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Bot, Search, Briefcase, FileText, ChevronDown, Paperclip, Loader2 } from 'lucide-react';

interface Message {
  role: 'assistant' | 'user';
  content: string;
}

interface MeetingFile {
  id: string;
  name: string;
  subtitle: string;
}

interface ChatResponse {
  role: string;
  content: string;
}

const API_BASE_URL = 'http://localhost:8000';

export default function AIChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Xin chào, tôi là trợ lý AI của bạn. Tôi có thể giúp bạn tóm tắt cuộc họp, tìm kiếm thông tin trong các bản ghi âm cũ, và đưa ra các đề xuất chiến lược dựa trên dữ liệu hiện có.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [availableFiles, setAvailableFiles] = useState<MeetingFile[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch meetings on mount
  useEffect(() => {
    fetchMeetings();
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchMeetings = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/meetings`);
      if (response.ok) {
        const meetings = await response.json();
        const formattedFiles = meetings.map((m: any) => ({
          id: m.id,
          name: m.title,
          subtitle: 'File ghi âm & Trích xuất'
        }));
        setAvailableFiles(formattedFiles);
      }
    } catch (error) {
      console.error('Failed to fetch meetings:', error);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          meeting_id: selectedFile || null,
        }),
      });

      if (response.ok) {
        const data: ChatResponse = await response.json();
        setMessages(prev => [...prev, { role: 'assistant', content: data.content }]);
      } else {
        const errorData = await response.json().catch(() => ({}));
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Có lỗi xảy ra: ${errorData.detail || 'Không thể kết nối với server AI'}`
        }]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Không thể kết nối với server. Vui lòng kiểm tra kết nối mạng.'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const suggestions = [
    { text: "Tóm tắt các quyết định quan trọng tuần này", icon: FileText },
    { text: "Đề xuất chiến lược dựa trên cuộc họp gần nhất", icon: Briefcase },
    { text: "Tìm các task đang quá hạn", icon: Search }
  ];

  return (
    <div className="w-full max-w-5xl mx-auto p-6 lg:p-10 h-[calc(100vh-6rem)] flex flex-col gap-6 relative">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
         <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-accent flex items-center justify-center shadow-lg shadow-accent/20">
               <Bot size={24} className="text-white" />
            </div>
            <div>
               <h1 className="text-2xl font-medium tracking-tight text-foreground/90">Trợ lý AI Thông minh</h1>
               <p className="text-foreground/80 text-sm tracking-wide">Tra cứu, phân tích và đưa ra đề xuất từ dữ liệu cuộc họp.</p>
            </div>
         </div>

         {/* Context File Selection */}
         <div className="relative">
            <div className="text-xs font-semibold uppercase tracking-wider text-foreground/80 mb-1.5 ml-1">Nguồn dữ liệu hỏi đáp</div>
            <button 
               onClick={() => setIsDropdownOpen(!isDropdownOpen)}
               className={`flex items-center justify-between w-full md:w-[300px] px-4 py-3 border rounded-2xl transition-all font-medium text-sm ${
                  selectedFile 
                     ? 'border-accent/40 bg-accent/5 text-foreground/90 shadow-[0_0_15px_rgba(212,175,55,0.05)]' 
                     : 'border-border bg-card/50 text-foreground/80 hover:border-accent/30 hover:bg-card/80'
               }`}
            >
               <div className="flex items-center gap-3 overflow-hidden">
                  <Paperclip size={16} className={selectedFile ? 'text-accent' : 'text-foreground/80'} />
                  <span className="truncate">
                     {selectedFile ? availableFiles.find(f => f.id === selectedFile)?.name : "Chọn file cuộc họp..."}
                  </span>
               </div>
               <ChevronDown size={14} className={`shrink-0 ml-2 transition-transform duration-300 ${isDropdownOpen ? 'rotate-180 text-accent' : 'text-foreground/80'}`} />
            </button>
            
         {/* Dropdown Menu */}
            {isDropdownOpen && (
               <>
                  <div className="fixed inset-0 z-10" onClick={() => setIsDropdownOpen(false)}></div>
                  <div className="absolute top-full right-0 mt-2 w-full md:w-[300px] bg-card/90 backdrop-blur-xl border border-border rounded-2xl shadow-2xl z-20 overflow-hidden animate-in fade-in slide-in-from-top-2">
                     <div className="max-h-[250px] overflow-y-auto custom-scrollbar p-2">
                        <button
                           onClick={() => { setSelectedFile(null); setIsDropdownOpen(false); }}
                           className={`w-full text-left px-4 py-3 rounded-xl text-sm transition-colors mb-1 ${
                              selectedFile === null ? 'bg-accent/10 text-accent font-medium' : 'text-foreground/90 hover:bg-card hover:text-foreground'
                           }`}
                        >
                           Tất cả dữ liệu chung
                        </button>
                        <div className="h-px bg-border/50 mx-2 my-1"></div>
                        {availableFiles.length === 0 ? (
                           <div className="px-4 py-6 text-center text-sm text-foreground/50">
                              Chưa có cuộc họp nào
                           </div>
                        ) : (
                           availableFiles.map(file => (
                              <button
                                 key={file.id}
                                 onClick={() => { setSelectedFile(file.id); setIsDropdownOpen(false); }}
                                 className={`w-full text-left px-4 py-3 rounded-xl text-sm transition-colors flex flex-col gap-1 ${
                                    selectedFile === file.id ? 'bg-accent/10 text-accent font-medium' : 'text-foreground/90 hover:bg-card hover:text-foreground'
                                 }`}
                              >
                                 <span className="truncate">{file.name}</span>
                                 <span className="text-[10px] text-foreground/80 font-medium">{file.subtitle}</span>
                              </button>
                           ))
                        )}
                     </div>
                  </div>
               </>
            )}
         </div>
      </div>

      {/* Chat Area */}
      <div className="glass-panel flex-1 rounded-[2rem] border border-border overflow-hidden flex flex-col relative animate-in fade-in slide-in-from-bottom-8 duration-700 delay-150 fill-mode-both">
         
         <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-accent/5 rounded-full blur-[100px] pointer-events-none"></div>

         <div className="flex-1 overflow-y-auto p-6 lg:p-10 space-y-8 z-10 custom-scrollbar">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-6 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                 <div className={`w-8 h-8 rounded-full flex shrink-0 items-center justify-center mt-1 ${msg.role === 'assistant' ? 'bg-accent/20 text-accent border border-accent/30' : 'bg-card border border-white/5'}`}>
                    {msg.role === 'assistant' ? <Sparkles size={14} /> : <div className="w-full h-full rounded-full overflow-hidden"><img src="https://api.dicebear.com/7.x/notionists/svg?seed=Alex&backgroundColor=transparent" alt="User" /></div>}
                 </div>
                 <div className={`max-w-[80%] rounded-2xl p-5 text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-accent/10 border border-accent/20 text-foreground/90 rounded-tr-none'
                      : 'bg-card/40 border border-white/5 text-foreground/80 rounded-tl-none font-medium shadow-sm'
                 }`}>
                    {msg.content}
                 </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-6">
                 <div className="w-8 h-8 rounded-full flex shrink-0 items-center justify-center mt-1 bg-accent/20 text-accent border border-accent/30">
                    <Sparkles size={14} />
                 </div>
                 <div className="max-w-[80%] rounded-2xl p-5 text-sm leading-relaxed bg-card/40 border border-white/5 text-foreground/80 rounded-tl-none font-medium shadow-sm">
                    <div className="flex items-center gap-2">
                       <Loader2 size={16} className="animate-spin text-accent" />
                       <span>Đang xử lý câu hỏi...</span>
                    </div>
                 </div>
              </div>
            )}
            <div ref={messagesEndRef} />
         </div>

         {/* Suggested Questions */}
         <div className="px-6 lg:px-10 pb-4 flex gap-3 overflow-x-auto hide-scrollbar z-10">
            {suggestions.map((suggestion, idx) => (
               <button 
                  key={idx}
                  onClick={() => setInput(suggestion.text)}
                  className="flex items-center gap-2 whitespace-nowrap px-4 py-2 rounded-xl text-xs font-medium text-foreground/80 bg-card/50 border border-border hover:border-accent/30 hover:text-accent transition-colors"
               >
                  <suggestion.icon size={14} />
                  {suggestion.text}
               </button>
            ))}
         </div>

         {/* Input Box */}
         <div className="p-6 lg:p-10 pt-4 z-10 border-t border-border bg-card/30 backdrop-blur-md">
            <form onSubmit={handleSend} className="relative group">
               <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={isLoading}
                  placeholder="Hỏi AI về cuộc họp, quyết định hoặc yêu cầu tóm tắt..."
                  className="w-full bg-background border border-border group-hover:border-accent/40 focus:border-accent rounded-full py-4 pl-6 pr-16 text-sm focus:outline-none transition-all shadow-inner disabled:opacity-50 disabled:cursor-not-allowed"
               />
               <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full flex items-center justify-center transition-all bg-accent text-accent-foreground hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 disabled:bg-card disabled:text-foreground/30 shadow-[0_0_15px_rgba(212,175,55,0.2)] disabled:shadow-none"
               >
                  {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} className="-translate-x-px translate-y-px" />}
               </button>
            </form>
            <div className="text-center mt-3">
               <span className="text-[10px] uppercase font-semibold tracking-widest text-foreground/30 flex items-center justify-center gap-1">
                  <Sparkles size={10} className="text-accent" /> SynapNote Intelligence
               </span>
            </div>
         </div>
         
      </div>

    </div>
  );
}

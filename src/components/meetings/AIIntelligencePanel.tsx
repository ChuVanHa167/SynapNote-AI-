import { useState, useRef, useEffect } from 'react';
import { Sparkles, MessageSquareText, LayoutList, Lightbulb, CheckCircle2, Circle, Send, Loader2, RefreshCw } from 'lucide-react';
import { ActionItem } from '@/types/meeting';

interface Message {
  role: 'assistant' | 'user';
  content: string;
  isError?: boolean;
}

interface AIIntelligencePanelProps {
  summary: string;
  decisions: string[];
  actionItems: ActionItem[];
  onToggleTask: (id: string) => void;
  meetingId?: string;
}

const API_BASE_URL = 'http://localhost:8001';

export function AIIntelligencePanel({ summary, decisions, actionItems, onToggleTask, meetingId }: AIIntelligencePanelProps) {
  const [activeTab, setActiveTab] = useState<'summary' | 'chat'>('summary');
  const [chatMessages, setChatMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hãy hỏi bất kỳ điều gì về cuộc họp này.' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const handleRetry = () => {
    if (lastFailedMessage) {
      setChatInput(lastFailedMessage);
      setLastFailedMessage(null);
      setTimeout(() => handleChatSend(), 100);
    }
  };

  // Auto-scroll to bottom when chat messages change
  useEffect(() => {
    if (activeTab === 'chat') {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, activeTab]);

  const handleChatSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!chatInput.trim() || isChatLoading) return;

    const userMessage = chatInput.trim();
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          meeting_id: meetingId || null,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setChatMessages(prev => [...prev, { role: 'assistant', content: data.content }]);
        setLastFailedMessage(null);
      } else {
        const errorData = await response.json().catch(() => ({}));
        const errorMsg = errorData.detail || 'Không thể kết nối với server AI';
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: `Có lỗi xảy ra: ${errorMsg}`,
          isError: true
        }]);
        setLastFailedMessage(userMessage);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Không thể kết nối với server. Vui lòng kiểm tra kết nối mạng.',
        isError: true
      }]);
      setLastFailedMessage(userMessage);
    } finally {
      setIsChatLoading(false);
    }
  };

  return (
    <div className="glass-panel rounded-[2rem] flex-1 flex flex-col overflow-hidden border border-border">
      {/* Tabs */}
      <div className="flex items-center p-2 border-b border-border bg-card/20">
         <button 
            onClick={() => setActiveTab('summary')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'summary' ? 'bg-card/80 text-foreground shadow-sm border border-border' : 'text-foreground/80 hover:text-foreground/90'}`}
         >
            <Sparkles size={16} className={activeTab === 'summary' ? 'text-accent' : ''} />
            Phân tích AI
         </button>
         <button 
            onClick={() => setActiveTab('chat')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'chat' ? 'bg-card/80 text-foreground shadow-sm border border-border' : 'text-foreground/80 hover:text-foreground/90'}`}
         >
            <MessageSquareText size={16} className={activeTab === 'chat' ? 'text-accent' : ''} />
            Hỏi AI
         </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 lg:p-8 custom-scrollbar">
         {activeTab === 'summary' ? (
            <div className="space-y-10">
               {/* Executive Summary */}
               <section>
                  <h4 className="text-xs font-semibold tracking-widest uppercase text-foreground/80 mb-4 flex items-center gap-2">
                     <LayoutList size={14} className="text-accent" /> Tóm tắt điều hành
                  </h4>
                  <p className="text-sm text-foreground/90 leading-relaxed font-medium">
                     {summary}
                  </p>
               </section>

               {/* Key Decisions */}
               <section>
                  <h4 className="text-xs font-semibold tracking-widest uppercase text-foreground/80 mb-4 flex items-center gap-2">
                     <Lightbulb size={14} className="text-amber-500" /> Quyết định chính
                  </h4>
                  <ul className="space-y-3">
                     {decisions.map((dec, i) => (
                        <li key={i} className="flex gap-3 text-sm text-foreground/90 font-medium items-start bg-card/30 p-3 rounded-xl border border-white/5">
                           <span className="mt-1.5 w-1 h-1 rounded-full bg-amber-500 shrink-0"></span>
                           <span>{dec}</span>
                        </li>
                     ))}
                  </ul>
               </section>

               {/* Action Items */}
               <section>
                  <h4 className="text-xs font-semibold tracking-widest uppercase text-foreground/80 mb-4 flex items-center gap-2">
                     <CheckCircle2 size={14} className="text-emerald-500" /> Công việc cần làm
                  </h4>
                  <div className="space-y-2">
                     {actionItems.map(task => (
                        <div key={task.id} className="group flex items-center gap-4 p-3.5 rounded-xl hover:bg-card/40 border border-transparent hover:border-white/5 transition-all">
                           <button onClick={() => onToggleTask(task.id)} className="text-foreground/20 hover:text-emerald-500 transition-colors">
                              {task.status === 'completed' ? <CheckCircle2 size={18} className="text-emerald-500" /> : <Circle size={18} />}
                           </button>
                           <div className="flex-1 flex items-center justify-between">
                              <p className={`text-sm ${task.status === 'completed' ? 'line-through text-foreground/30' : 'text-foreground/80 font-medium'}`}>
                                 {task.task}
                              </p>
                              <div className="flex items-center gap-3">
                                 <span className="text-[10px] uppercase tracking-wider bg-accent/10 text-accent px-2 py-1 rounded-md">{task.assignee}</span>
                              </div>
                           </div>
                        </div>
                     ))}
                  </div>
               </section>
            </div>
         ) : (
            <div className="h-full flex flex-col gap-4">
               {/* Chat Messages */}
               <div className="flex-1 overflow-y-auto space-y-4 custom-scrollbar">
                  {chatMessages.map((msg, idx) => (
                     <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-7 h-7 rounded-full flex shrink-0 items-center justify-center ${
                           msg.role === 'assistant' ? 'bg-accent/20 text-accent' : 'bg-card text-foreground/60'
                        }`}>
                           {msg.role === 'assistant' ? <Sparkles size={14} /> : <MessageSquareText size={14} />}
                        </div>
                        <div className="max-w-[85%] flex flex-col gap-1">
                           <div className={`rounded-xl px-3 py-2 text-xs leading-relaxed ${
                              msg.role === 'user'
                                 ? 'bg-accent/10 text-foreground/90'
                                 : msg.isError
                                    ? 'bg-red-500/10 text-red-400 border border-red-500/30'
                                    : 'bg-card/50 text-foreground/80'
                           }`}>
                              {msg.content}
                           </div>
                           {msg.isError && lastFailedMessage && (
                              <button
                                 onClick={handleRetry}
                                 className="text-xs text-accent hover:underline flex items-center gap-1 ml-1"
                              >
                                 <RefreshCw size={10} /> Thử lại
                              </button>
                           )}
                        </div>
                     </div>
                  ))}
                  {isChatLoading && (
                     <div className="flex gap-3">
                        <div className="w-7 h-7 rounded-full flex shrink-0 items-center justify-center bg-accent/20 text-accent">
                           <Sparkles size={14} />
                        </div>
                        <div className="max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed bg-card/50 text-foreground/80 flex items-center gap-2">
                           <Loader2 size={12} className="animate-spin" />
                           <span>Đang xử lý...</span>
                        </div>
                     </div>
                  )}
                  <div ref={chatEndRef} />
               </div>

               {/* Chat Input */}
               <form onSubmit={handleChatSend} className="relative">
                  <input
                     type="text"
                     value={chatInput}
                     onChange={(e) => setChatInput(e.target.value)}
                     disabled={isChatLoading}
                     placeholder="Nhắn tin với AI..."
                     className="w-full bg-card border border-border focus:border-accent/50 rounded-2xl py-3 pl-4 pr-12 text-sm focus:outline-none transition-all shadow-inner disabled:opacity-50"
                  />
                  <button
                     type="submit"
                     disabled={!chatInput.trim() || isChatLoading}
                     className="absolute right-2 top-1/2 -translate-y-1/2 w-7 h-7 bg-accent text-accent-foreground rounded-lg flex items-center justify-center transition-colors hover:opacity-90 disabled:opacity-50 disabled:hover:opacity-50"
                  >
                     <Send size={14} />
                  </button>
               </form>
            </div>
         )}
      </div>
    </div>
  );
}

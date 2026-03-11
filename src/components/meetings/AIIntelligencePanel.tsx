import { useState } from 'react';
import { Sparkles, MessageSquareText, LayoutList, Lightbulb, CheckCircle2, Circle, ChevronRight } from 'lucide-react';
import { ActionItem } from '@/types/meeting';

interface AIIntelligencePanelProps {
  summary: string;
  decisions: string[];
  actionItems: ActionItem[];
  onToggleTask: (id: number) => void;
}

export function AIIntelligencePanel({ summary, decisions, actionItems, onToggleTask }: AIIntelligencePanelProps) {
  const [activeTab, setActiveTab] = useState<'summary' | 'chat'>('summary');

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
            <div className="h-full flex flex-col">
               <div className="flex-1 flex flex-col items-center justify-center text-center opacity-50">
                  <Sparkles size={32} className="text-accent mb-4" strokeWidth={1} />
                  <p className="text-sm font-medium">Hãy hỏi bất kỳ điều gì về cuộc họp này.</p>
                  <p className="text-xs mt-2">&quot;Quyết định về ngân sách là gì?&quot;</p>
               </div>
               <div className="mt-auto relative">
                  <input type="text" placeholder="Nhắn tin với AI..." className="w-full bg-card border border-border focus:border-accent/50 rounded-2xl py-4 pl-4 pr-12 text-sm focus:outline-none transition-all shadow-inner" />
                  <button className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-foreground/5 hover:bg-accent/20 hover:text-accent rounded-xl flex items-center justify-center transition-colors">
                     <ChevronRight size={16} />
                  </button>
               </div>
            </div>
         )}
      </div>
    </div>
  );
}

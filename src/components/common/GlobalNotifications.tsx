"use client";

import React from 'react';
import { useNotification, NotificationType } from '@/context/NotificationContext';
import { CheckCircle2, AlertCircle, X, Info, Loader2 } from 'lucide-react';

const getIcon = (type: NotificationType) => {
  switch (type) {
    case 'success':
      return <CheckCircle2 className="text-emerald-500" size={18} />;
    case 'error':
      return <AlertCircle className="text-red-500" size={18} />;
    case 'warning':
      return <AlertCircle className="text-amber-500" size={18} />;
    case 'info':
    default:
      return <Info className="text-blue-400" size={18} />;
  }
};

const getStyle = (type: NotificationType) => {
  switch (type) {
    case 'success':
      return 'border-emerald-500/30 bg-emerald-500/5';
    case 'error':
      return 'border-red-500/30 bg-red-500/5';
    case 'warning':
      return 'border-amber-500/30 bg-amber-500/5';
    case 'info':
    default:
      return 'border-blue-500/30 bg-blue-500/5';
  }
};

export function GlobalNotifications() {
  const { notifications, hideNotification } = useNotification();

  if (notifications.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-3 pointer-events-none">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`
            pointer-events-auto
            glass-panel px-5 py-4 rounded-2xl flex items-center gap-4 backdrop-blur-md shadow-2xl
            animate-in fade-in slide-in-from-bottom-4 duration-500
            border ${getStyle(notification.type)}
          `}
        >
          <div className={`h-9 w-9 rounded-full flex items-center justify-center bg-white/5`}>
            {getIcon(notification.type)}
          </div>
          
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground/90 leading-tight">
              {notification.message}
            </p>
          </div>

          <button
            onClick={() => hideNotification(notification.id)}
            className="p-1.5 rounded-lg hover:bg-white/5 text-foreground/40 transition-colors"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}

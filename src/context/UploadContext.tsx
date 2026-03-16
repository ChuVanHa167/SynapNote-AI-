"use client";

import React, { createContext, useContext, useState, useRef, useCallback } from 'react';

interface UploadStatus {
  isUploading: boolean;
  isProcessing: boolean;
  progress: number;
  meetingId: string | null;
  error: string | null;
  fileName: string | null;
  step: number; // 0: upload, 1: checking, 2: audio, 3: ai, 4: done
}

interface UploadContextType {
  status: UploadStatus;
  uploadFile: (file: File, title: string, duration: string) => Promise<void>;
  cancelUpload: () => void;
  resetUpload: () => void;
}

const UploadContext = createContext<UploadContextType | undefined>(undefined);

export function UploadProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<UploadStatus>({
    isUploading: false,
    isProcessing: false,
    progress: 0,
    meetingId: null,
    error: null,
    fileName: null,
    step: 0,
  });

  const xhrRef = useRef<XMLHttpRequest | null>(null);
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  const cancelUpload = useCallback(() => {
    if (xhrRef.current) {
      xhrRef.current.abort();
      xhrRef.current = null;
    }
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    setStatus({
      isUploading: false,
      isProcessing: false,
      progress: 0,
      meetingId: null,
      error: null,
      fileName: null,
      step: 0,
    });
  }, []);

  const resetUpload = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    setStatus({
      isUploading: false,
      isProcessing: false,
      progress: 0,
      meetingId: null,
      error: null,
      fileName: null,
      step: 0,
    });
  }, []);

  const startPolling = useCallback((meetingId: string) => {
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    
    pollTimerRef.current = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/meetings/${meetingId}`);
        if (res.ok) {
          const data = await res.json();
          if (data.status === "HOÀN THÀNH") {
            setStatus(prev => ({ ...prev, step: 4, isProcessing: false }));
            if (pollTimerRef.current) {
              clearInterval(pollTimerRef.current);
              pollTimerRef.current = null;
            }
          } else if (data.status === "LỖI") {
            setStatus(prev => ({ ...prev, error: "AI Processing failed", isProcessing: false }));
            if (pollTimerRef.current) {
              clearInterval(pollTimerRef.current);
              pollTimerRef.current = null;
            }
          } else {
            // Simulated step increment (could be refined with backend status)
            setStatus(prev => {
              if (prev.step < 3) return { ...prev, step: prev.step + 1 };
              return prev;
            });
          }
        }
      } catch (e) {
        console.error("Polling error:", e);
      }
    }, 3000);
  }, []);

  const uploadFile = useCallback(async (file: File, title: string, duration: string) => {
    if (status.isUploading) return;

    setStatus({
      isUploading: true,
      isProcessing: false,
      progress: 0,
      meetingId: null,
      error: null,
      fileName: file.name,
      step: 0,
    });

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("duration", duration);
      if (title.trim() !== '') {
        formData.append("title", title);
      }

      const xhr = new XMLHttpRequest();
      xhrRef.current = xhr;
      
      xhr.open("POST", "http://localhost:8000/meetings/upload", true);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          setStatus(prev => ({ ...prev, progress: percent }));
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const data = JSON.parse(xhr.responseText);
          setStatus(prev => ({ 
            ...prev, 
            progress: 100, 
            meetingId: data.id,
            isUploading: false,
            isProcessing: true,
            step: 1
          }));
          
          startPolling(data.id);
        } else {
          if (xhr.status !== 0) { // Not aborted
            setStatus(prev => ({ 
              ...prev, 
              isUploading: false, 
              error: `Upload failed with status ${xhr.status}` 
            }));
          }
        }
        xhrRef.current = null;
      };

      xhr.onerror = () => {
        if (xhrRef.current) {
          setStatus(prev => ({ 
            ...prev, 
            isUploading: false, 
            error: "Network error occurred" 
          }));
        }
        xhrRef.current = null;
      };

      xhr.send(formData);
    } catch (e) {
      setStatus(prev => ({ 
        ...prev, 
        isUploading: false, 
        error: e instanceof Error ? e.message : "Unknown error" 
      }));
    }
  }, [status.isUploading, startPolling]);

  return (
    <UploadContext.Provider value={{ status, uploadFile, cancelUpload, resetUpload }}>
      {children}
    </UploadContext.Provider>
  );
}

export function useUpload() {
  const context = useContext(UploadContext);
  if (context === undefined) {
    throw new Error('useUpload must be used within an UploadProvider');
  }
  return context;
}

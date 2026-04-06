"use client";

import { useState, useEffect } from 'react';
import { CheckCircle2, Loader2, X, ExternalLink, Link2, Unlink } from 'lucide-react';

interface Integration {
  provider: string;
  provider_name: string;
  description: string;
  icon_color: string;
  is_connected: boolean;
  status: string;
}

export function IntegrationsTab({ userId }: { userId?: string }) {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) return;
    fetchIntegrations();
  }, [userId]);

  const fetchIntegrations = async () => {
    try {
      const response = await fetch(`http://localhost:8001/integrations/available?user_id=${userId}`);
      if (!response.ok) throw new Error('Failed to fetch integrations');
      const data = await response.json();
      setIntegrations(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (provider: string) => {
    setConnecting(provider);
    try {
      // Get OAuth URL
      const response = await fetch(`http://localhost:8001/integrations/auth-url/${provider}?user_id=${userId}`);
      if (response.ok) {
        const { auth_url } = await response.json();
        // Open OAuth window
        window.location.href = auth_url;
      }
    } catch (err) {
      console.error(err);
    } finally {
      setConnecting(null);
    }
  };

  const handleDisconnect = async (provider: string) => {
    if (!confirm(`Ngắt kết nối với ${provider}?`)) return;
    
    try {
      const response = await fetch(`http://localhost:8001/integrations/disconnect/${provider}?user_id=${userId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        fetchIntegrations();
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-accent animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-in fade-in duration-500">
      <div className="border-b border-border pb-6">
        <h2 className="text-xl font-medium text-foreground/90 mb-1">Tích hợp ứng dụng</h2>
        <p className="text-sm text-foreground/80">Kết nối các công cụ làm việc của bạn để đồng bộ hoá cuộc họp và nhiệm vụ.</p>
      </div>

      <div className="space-y-4">
        {integrations.map((integration) => (
          <IntegrationCard 
            key={integration.provider}
            integration={integration}
            onConnect={() => handleConnect(integration.provider)}
            onDisconnect={() => handleDisconnect(integration.provider)}
            loading={connecting === integration.provider}
          />
        ))}

        {/* API Key Section */}
        <div className="flex items-center justify-between p-5 rounded-2xl border border-border bg-background/40">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-card border border-border flex items-center justify-center">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" className="text-foreground/80">
                <path d="M10 20a2 2 0 0 0 .553.895A2 2 0 0 0 12 22a2 2 0 0 0 1.447-.553A2 2 0 0 0 14 20M10 20a2 2 0 0 1-.895-.553A2 2 0 0 1 8 18a2 2 0 0 1 .553-1.447A2 2 0 0 1 10 16M10 20V10M14 20V10M10 10a2 2 0 0 1 .553-1.447A2 2 0 0 1 12 8a2 2 0 0 1 1.447.553A2 2 0 0 1 14 10M10 10a2 2 0 0 0-.895-.553A2 2 0 0 0 8 8a2 2 0 0 0-1.447.553A2 2 0 0 0 6 10M14 10a2 2 0 0 0 .553-1.447A2 2 0 0 0 16 8a2 2 0 0 0 1.447.553A2 2 0 0 0 18 10M6 10v8a2 2 0 0 0 .553 1.447A2 2 0 0 0 8 20a2 2 0 0 0 1.447-.553A2 2 0 0 0 10 18M18 10v8a2 2 0 0 1-.553 1.447A2 2 0 0 1 16 20a2 2 0 0 1-1.447-.553A2 2 0 0 1 14 18"/>
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-medium text-foreground/90">API Key</h3>
              <p className="text-xs text-foreground/80">Tích hợp tùy chỉnh qua Zapier/Make.</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-foreground/60 bg-background px-3 py-1.5 rounded-lg border border-border">
              sk_live_...x891
            </span>
            <button className="p-2 hover:bg-card rounded-lg transition-colors">
              <ExternalLink size={14} className="text-foreground/60" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function IntegrationCard({ 
  integration, 
  onConnect, 
  onDisconnect, 
  loading 
}: { 
  integration: Integration;
  onConnect: () => void;
  onDisconnect: () => void;
  loading: boolean;
}) {
  const isConnected = integration.is_connected;
  
  const getIcon = () => {
    switch (integration.provider) {
      case 'zoom':
        return (
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22.54 6.42a2.78 2.78 0 0 0-4.08 2.18v4.36a2.78 2.78 0 0 0 4.08 2.18V6.42Z"/>
            <path d="M4.08 17.58a2.78 2.78 0 0 0-2.18-4.08h4.36a2.78 2.78 0 0 0 2.18 4.08v-4.36A2.78 2.78 0 0 0 4.08 17.58Z"/>
            <path d="M8.44 6.42a2.78 2.78 0 0 0 4.08-2.18v4.36A2.78 2.78 0 0 0 8.44 6.42Z"/>
            <path d="M19.92 17.58a2.78 2.78 0 0 0 2.18-4.08h-4.36a2.78 2.78 0 0 0-2.18 4.08v-4.36A2.78 2.78 0 0 0 19.92 17.58Z"/>
          </svg>
        );
      case 'google':
        return (
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
        );
      case 'slack':
        return (
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
            <polyline points="14 2 14 8 20 8"/>
            <path d="m8 13 2 2 4-4"/>
          </svg>
        );
      case 'teams':
        return (
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M20.625 8.55c-.747.643-1.747.643-2.494 0-.746-.643-.746-1.683 0-2.326.747-.643 1.747-.643 2.494 0 .373.32.56.74.56 1.163 0 .423-.187.843-.56 1.163z"/>
            <path d="M20.067 11.4c0-.424-.187-.843-.56-1.163-.747-.643-1.747-.643-2.494 0-.373.32-.56.74-.56 1.163 0 .424.187.843.56 1.163.373.32.794.48 1.247.48.454 0 .874-.16 1.247-.48.373-.32.56-.74.56-1.163z"/>
            <path d="M15.75 8.55c-.747.643-1.747.643-2.494 0-.373-.32-.56-.74-.56-1.163 0-.423.187-.843.56-1.163.747-.643 1.747-.643 2.494 0 .373.32.56.74.56 1.163 0 .423-.187.843-.56 1.163z"/>
            <path d="M15.75 13.05c-.747.643-1.747.643-2.494 0-.373-.32-.56-.74-.56-1.163 0-.423.187-.843.56-1.163.747-.643 1.747-.643 2.494 0 .373.32.56.74.56 1.163 0 .423-.187.843-.56 1.163z"/>
            <path d="M3.75 8.25h5.25v-1.5H3.75v1.5z"/>
            <path d="M3.75 11.25h5.25v-1.5H3.75v1.5z"/>
            <path d="M3.75 14.25h5.25v-1.5H3.75v1.5z"/>
          </svg>
        );
      default:
        return <Link2 className="w-5 h-5" />;
    }
  };

  return (
    <div className={`flex items-center justify-between p-5 rounded-2xl border transition-colors ${
      isConnected 
        ? 'border-accent/20 bg-accent/5' 
        : 'border-border bg-background/40 hover:bg-card/40'
    }`}>
      <div className="flex items-center gap-4">
        <div 
          className="w-10 h-10 rounded-xl bg-card border border-border flex items-center justify-center p-2"
          style={{ color: integration.icon_color }}
        >
          {getIcon()}
        </div>
        <div>
          <h3 className="text-sm font-medium text-foreground/90 flex items-center gap-2">
            {integration.provider_name}
            {isConnected && (
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-500 text-[10px] font-semibold">
                Đã kết nối
              </span>
            )}
          </h3>
          <p className="text-xs text-foreground/80 mt-0.5">{integration.description}</p>
        </div>
      </div>
      
      <button
        onClick={isConnected ? onDisconnect : onConnect}
        disabled={loading}
        className={`px-4 py-2 rounded-xl text-xs font-medium border transition-all ${
          isConnected
            ? 'border-red-500/30 text-red-400 hover:bg-red-500/10'
            : 'border-border bg-card hover:bg-card/80 text-foreground'
        }`}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : isConnected ? (
          <span className="flex items-center gap-1">
            <Unlink size={12} />
            Ngắt kết nối
          </span>
        ) : (
          <span className="flex items-center gap-1">
            <Link2 size={12} />
            Kết nối
          </span>
        )}
      </button>
    </div>
  );
}

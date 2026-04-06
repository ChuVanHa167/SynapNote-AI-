"use client";

import { useState, useEffect } from 'react';
import { CheckCircle2, Loader2, CreditCard, Calendar, Users, Zap, Download, ArrowRight } from 'lucide-react';

interface BillingData {
  current_subscription: {
    id: string;
    plan_name: string;
    price_vnd: number;
    status: string;
    current_period_end: string;
    cancel_at_period_end: boolean;
  };
  usage_stats: {
    meetings_count: number;
    meetings_limit: number;
    audio_hours_used: number;
    audio_hours_limit: number;
    ai_processing_count: number;
    ai_processing_limit: number | null;
  };
  payment_method: {
    id: string;
    type: string;
    provider: string;
    last4: string;
    expiry_month: number;
    expiry_year: number;
  } | null;
  billing_history: Array<{
    id: string;
    amount_vnd: number;
    description: string;
    status: string;
    created_at: string;
  }>;
  available_plans: Array<{
    id: string;
    name: string;
    price_vnd: number;
    meetings_limit: number;
    audio_hours_limit: number;
    features: string[];
  }>;
}

export function BillingTab({ userId }: { userId?: string }) {
  const [data, setData] = useState<BillingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    if (!userId) return;
    
    fetchBillingData();
  }, [userId]);

  const fetchBillingData = async () => {
    try {
      const response = await fetch(`http://localhost:8001/billing/dashboard?user_id=${userId}`);
      if (!response.ok) throw new Error('Failed to fetch billing data');
      const billingData = await response.json();
      setData(billingData);
    } catch (err) {
      setError('Không thể tải dữ liệu thanh toán');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Bạn có chắc muốn hủy gói đăng ký?')) return;
    
    setCancelling(true);
    try {
      const response = await fetch('http://localhost:8001/billing/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, cancel_at_period_end: true })
      });
      
      if (response.ok) {
        alert('Gói đăng ký sẽ được hủy vào cuối chu kỳ hiện tại');
        fetchBillingData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setCancelling(false);
    }
  };

  const handleSubscribe = async (planId: string) => {
    try {
      const response = await fetch(`http://localhost:8001/billing/subscribe/${planId}?user_id=${userId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        alert('Đăng ký gói mới thành công!');
        fetchBillingData();
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

  if (error || !data) {
    return (
      <div className="text-center py-20 text-foreground/60">
        <p>{error || 'Không có dữ liệu'}</p>
        <button 
          onClick={fetchBillingData}
          className="mt-4 px-4 py-2 rounded-xl border border-border hover:bg-card transition-colors"
        >
          Thử lại
        </button>
      </div>
    );
  }

  const { current_subscription, usage_stats, payment_method, billing_history, available_plans } = data;
  const renewalDate = new Date(current_subscription.current_period_end).toLocaleDateString('vi-VN');

  return (
    <div className="space-y-10 animate-in fade-in duration-500">
      {/* Header */}
      <div className="border-b border-border pb-6">
        <h2 className="text-xl font-medium text-foreground/90 mb-1">Gói & Thanh toán</h2>
        <p className="text-sm text-foreground/80">Quản lý gói đăng ký và phương thức thanh toán của bạn.</p>
      </div>

      {/* Current Plan Card */}
      <div className="p-6 rounded-2xl border border-accent/20 bg-accent/5 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-accent/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
        <div className="relative z-10 flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-accent">Gói hiện tại</span>
            <h3 className="text-2xl font-semibold text-foreground/90 mt-1">{current_subscription.plan_name}</h3>
            <p className="text-sm text-foreground/80 mt-1">
              {current_subscription.price_vnd > 0 
                ? `${current_subscription.price_vnd.toLocaleString('vi-VN')}đ/tháng • Gia hạn: ${renewalDate}`
                : 'Miễn phí'
              }
            </p>
          </div>
          <div className="text-right">
            <button 
              onClick={handleCancel}
              disabled={cancelling || current_subscription.price_vnd === 0}
              className="px-4 py-2 rounded-xl text-sm font-medium border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-50"
            >
              {cancelling ? 'Đang xử lý...' : 'Hủy gói'}
            </button>
          </div>
        </div>
      </div>

      {/* Usage Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <UsageCard 
          icon={<Users className="w-5 h-5 text-accent" />}
          title="Cuộc họp"
          used={usage_stats.meetings_count}
          limit={usage_stats.meetings_limit}
        />
        <UsageCard 
          icon={<Calendar className="w-5 h-5 text-accent" />}
          title="Thời lượng"
          used={usage_stats.audio_hours_used}
          limit={usage_stats.audio_hours_limit}
          unit="h"
        />
        <UsageCard 
          icon={<Zap className="w-5 h-5 text-accent" />}
          title="AI Processing"
          used={usage_stats.ai_processing_count}
          limit={usage_stats.ai_processing_limit || 999999}
          unit=""
          unlimited={!usage_stats.ai_processing_limit}
        />
      </div>

      {/* Available Plans */}
      <div>
        <h3 className="text-lg font-medium text-foreground/90 mb-4">Các gói dịch vụ</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {available_plans.map((plan) => (
            <PlanCard 
              key={plan.id}
              plan={plan}
              isCurrent={current_subscription.plan_name === plan.name}
              onSubscribe={() => handleSubscribe(plan.id)}
            />
          ))}
        </div>
      </div>

      {/* Payment Method */}
      {payment_method && (
        <div>
          <h3 className="text-lg font-medium text-foreground/90 mb-4">Phương thức thanh toán</h3>
          <div className="p-5 rounded-2xl border border-border bg-background/40">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-blue-800 rounded-md flex items-center justify-center text-white text-xs font-bold">
                  {payment_method.provider?.toUpperCase() || 'CARD'}
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground/90">
                    •••• •••• •••• {payment_method.last4}
                  </p>
                  <p className="text-xs text-foreground/60">
                    Hết hạn {payment_method.expiry_month}/{payment_method.expiry_year}
                  </p>
                </div>
              </div>
              <button className="px-4 py-2 rounded-xl text-xs font-medium border border-border hover:bg-card transition-colors">
                Thay đổi
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Billing History */}
      <div>
        <h3 className="text-lg font-medium text-foreground/90 mb-4">Lịch sử thanh toán</h3>
        <div className="rounded-2xl border border-border bg-background/40 overflow-hidden">
          <div className="divide-y divide-border">
            {billing_history.length === 0 ? (
              <div className="p-8 text-center text-foreground/60">
                Chưa có lịch sử thanh toán
              </div>
            ) : (
              billing_history.map((item) => (
                <div key={item.id} className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-foreground/90">{item.description}</p>
                    <p className="text-xs text-foreground/60">
                      {new Date(item.created_at).toLocaleDateString('vi-VN')}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm font-medium text-foreground/90">
                      {item.amount_vnd.toLocaleString('vi-VN')}đ
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      item.status === 'success' 
                        ? 'bg-emerald-500/10 text-emerald-500'
                        : item.status === 'failed'
                        ? 'bg-red-500/10 text-red-500'
                        : 'bg-yellow-500/10 text-yellow-500'
                    }`}>
                      {item.status === 'success' ? 'Thành công' : item.status === 'failed' ? 'Thất bại' : 'Đang xử lý'}
                    </span>
                    <button className="p-2 hover:bg-card rounded-lg transition-colors">
                      <Download className="w-4 h-4 text-foreground/60" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function UsageCard({ icon, title, used, limit, unit = '', unlimited = false }: {
  icon: React.ReactNode;
  title: string;
  used: number;
  limit: number;
  unit?: string;
  unlimited?: boolean;
}) {
  const percentage = unlimited ? 0 : Math.min((used / limit) * 100, 100);
  
  return (
    <div className="p-5 rounded-2xl border border-border bg-background/40">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center">
          {icon}
        </div>
        <span className="text-sm font-medium text-foreground/90">{title}</span>
      </div>
      <div className="text-2xl font-semibold text-foreground/90">
        {used}{unit}
        <span className="text-sm font-normal text-foreground/60">
          {unlimited ? '/∞' : `/${limit}${unit}`}
        </span>
      </div>
      {!unlimited && (
        <div className="w-full h-1.5 bg-border rounded-full mt-2 overflow-hidden">
          <div 
            className="h-full bg-accent rounded-full transition-all" 
            style={{width: `${percentage}%`}}
          ></div>
        </div>
      )}
    </div>
  );
}

function PlanCard({ plan, isCurrent, onSubscribe }: {
  plan: BillingData['available_plans'][0];
  isCurrent: boolean;
  onSubscribe: () => void;
}) {
  const isPopular = plan.name === 'Pro';
  const isEnterprise = plan.price_vnd < 0;
  
  return (
    <div className={`p-5 rounded-2xl relative ${
      isCurrent 
        ? 'border-2 border-accent bg-accent/5' 
        : 'border border-border bg-background/40'
    }`}>
      {isPopular && !isCurrent && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="px-3 py-1 rounded-full bg-accent text-accent-foreground text-xs font-semibold">
            Phổ biến
          </span>
        </div>
      )}
      
      <div className="space-y-4">
        <div>
          <h4 className="text-lg font-semibold text-foreground/90">{plan.name}</h4>
          <p className="text-2xl font-bold text-foreground/90 mt-1">
            {isEnterprise ? 'Liên hệ' : plan.price_vnd === 0 
              ? 'Miễn phí' 
              : `${plan.price_vnd.toLocaleString('vi-VN')}đ`
            }
            {!isEnterprise && plan.price_vnd > 0 && (
              <span className="text-sm font-normal text-foreground/60">/tháng</span>
            )}
          </p>
          <p className="text-xs text-foreground/60 mt-1">
            {plan.name === 'Starter' ? 'Dành cho cá nhân' : 
             plan.name === 'Pro' ? 'Dành cho chuyên nghiệp' : 
             'Dành cho doanh nghiệp'}
          </p>
        </div>
        
        <ul className="space-y-2 text-sm">
          {plan.features.map((feature, idx) => (
            <li key={idx} className="flex items-center gap-2 text-foreground/80">
              <CheckCircle2 size={14} className={isCurrent ? 'text-accent' : 'text-emerald-500'} />
              {feature}
            </li>
          ))}
        </ul>
        
        <button 
          onClick={onSubscribe}
          disabled={isCurrent}
          className={`w-full py-2.5 rounded-xl text-sm font-medium transition-all ${
            isCurrent 
              ? 'bg-accent text-accent-foreground cursor-default'
              : isEnterprise
              ? 'border border-accent text-accent hover:bg-accent/10'
              : 'border border-border text-foreground/80 hover:bg-card'
          }`}
        >
          {isCurrent ? 'Gói hiện tại' : isEnterprise ? 'Liên hệ sales' : 'Nâng cấp'}
        </button>
      </div>
    </div>
  );
}

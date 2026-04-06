from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# 1. User Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str

class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    title: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: Optional[str] = None  # "dark" or "light"
    email_summaries: Optional[bool] = None
    action_item_alerts: Optional[bool] = None
    product_updates: Optional[bool] = None

class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class User(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    title: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: str = "dark"  # "dark" or "light"
    hashed_password: str
    email_summaries: bool = True
    action_item_alerts: bool = True
    product_updates: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# 2. Meeting Models
class ActionItem(BaseModel):
    id: str
    task: str
    assignee: str
    deadline: str
    status: str

class MeetingBase(BaseModel):
    title: str
    participants: int

class Meeting(MeetingBase):
    id: str
    date: str
    duration: str
    status: str
    summary: Optional[str] = None
    decisions: Optional[List[str]] = []
    action_items: Optional[List[ActionItem]] = []
    transcript: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    link_url: Optional[str] = None
    created_at: Optional[datetime] = None

# 3. Chat Models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    meeting_id: Optional[str] = None

# 4. Integrations
class IntegrationStatus(BaseModel):
    id: str
    platform: str
    status: str
    connected_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    config: Optional[dict] = None

class ConnectIntegrationRequest(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    webhook_url: Optional[str] = None
    config: Optional[dict] = None

class IntegrationHook(BaseModel):
    platform: str
    status: str
    config_url: str

class APIKey(BaseModel):
    id: str
    key: str
    name: str

class APIKeyCreate(BaseModel):
    name: str

# ===== SUBSCRIPTION & BILLING SCHEMAS =====
class SubscriptionPlan(BaseModel):
    id: str
    name: str
    price_vnd: int
    billing_cycle: str = "monthly"
    meetings_limit: int
    audio_hours_limit: int
    features: List[str] = []
    is_active: bool = True

class CurrentSubscription(BaseModel):
    id: str
    plan_name: str
    price_vnd: int
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False

class UsageStats(BaseModel):
    meetings_count: int
    meetings_limit: int
    audio_hours_used: float
    audio_hours_limit: int
    ai_processing_count: int
    ai_processing_limit: Optional[int] = None  # None = unlimited

class PaymentMethod(BaseModel):
    id: str
    type: str
    provider: Optional[str] = None
    last4: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    is_default: bool = False

class BillingHistoryItem(BaseModel):
    id: str
    amount_vnd: int
    description: str
    status: str
    created_at: datetime
    invoice_url: Optional[str] = None

class BillingDashboard(BaseModel):
    current_subscription: CurrentSubscription
    usage_stats: UsageStats
    payment_method: Optional[PaymentMethod] = None
    billing_history: List[BillingHistoryItem] = []
    available_plans: List[SubscriptionPlan] = []

class CancelSubscriptionRequest(BaseModel):
    cancel_at_period_end: bool = True  # If false, cancel immediately

# ===== INTEGRATION SCHEMAS =====
class IntegrationInfo(BaseModel):
    id: str
    provider: str
    provider_name: str
    status: str  # connected, disconnected, error
    connected_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    settings: Optional[dict] = None
    webhook_url: Optional[str] = None

class ConnectIntegrationRequest(BaseModel):
    code: str  # OAuth authorization code
    redirect_uri: str

class DisconnectIntegrationRequest(BaseModel):
    provider: str

class IntegrationAuthUrl(BaseModel):
    provider: str
    auth_url: str

class AvailableIntegration(BaseModel):
    provider: str
    provider_name: str
    description: str
    icon_url: Optional[str] = None
    is_connected: bool = False
    config_url: Optional[str] = None

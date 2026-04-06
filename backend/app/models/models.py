from sqlalchemy import Column, String, Integer, Text, Enum, ForeignKey, TIMESTAMP, func, Float
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    title = Column(String(100))
    avatar_url = Column(String(500))
    hashed_password = Column(String(255), nullable=False)
    
    # Theme preference: "dark" or "light"
    theme = Column(String(10), default="dark")
    
    # Notification Preferences
    email_summaries = Column(Integer, default=1)  # 1 for True, 0 for False (standard for most DBs)
    action_item_alerts = Column(Integer, default=1)
    product_updates = Column(Integer, default=0)
    
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    participants = Column(Integer, default=1)
    date = Column(String(50), nullable=False)
    duration = Column(String(50), default="0m 0s")
    status = Column(Enum('PENDING', 'ĐANG XỬ LÝ', 'HOÀN THÀNH', 'LỖI'), default='PENDING')
    summary = Column(Text)
    transcript = Column(Text)
    audio_url = Column(String(500))
    video_url = Column(String(500))
    link_url = Column(String(500))  # External link for meeting (Zoom, Google Meet, etc.)
    user_id = Column(String(36), ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # Relationships
    decisions = relationship("MeetingDecision", back_populates="meeting", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")

class MeetingDecision(Base):
    __tablename__ = "meeting_decisions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=False)
    content = Column(Text, nullable=False)
    
    meeting = relationship("Meeting", back_populates="decisions")

class ActionItem(Base):
    __tablename__ = "action_items"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=False)
    task = Column(String(255), nullable=False)
    assignee = Column(String(100))
    deadline = Column(String(50))
    status = Column(Enum('pending', 'in_progress', 'completed'), default='pending')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    meeting = relationship("Meeting", back_populates="action_items")

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

# ===== SUBSCRIPTION & BILLING =====
class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), nullable=False)  # Starter, Pro, Enterprise
    price_vnd = Column(Integer, nullable=False)  # Price in VND
    billing_cycle = Column(String(20), default="monthly")  # monthly, yearly
    meetings_limit = Column(Integer, nullable=False)  # Number of meetings per month
    audio_hours_limit = Column(Integer, nullable=False)  # Audio hours per month
    features = Column(Text)  # JSON string of features
    is_active = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    plan_id = Column(String(36), ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(Enum('active', 'cancelled', 'expired', 'pending'), default='active')
    current_period_start = Column(TIMESTAMP)
    current_period_end = Column(TIMESTAMP)
    cancel_at_period_end = Column(Integer, default=0)  # 1 = cancel at end of period
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

class BillingHistory(Base):
    __tablename__ = "billing_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    amount_vnd = Column(Integer, nullable=False)
    description = Column(String(255))  # e.g., "Pro Workspace - Thang 4/2026"
    status = Column(Enum('success', 'failed', 'pending', 'refunded'), default='pending')
    payment_method_id = Column(String(36), ForeignKey("payment_methods.id"))
    invoice_url = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # card, bank_transfer, momo, zalopay
    provider = Column(String(50))  # visa, mastercard, momo, etc.
    last4 = Column(String(4))  # Last 4 digits of card
    expiry_month = Column(Integer)
    expiry_year = Column(Integer)
    is_default = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

class UsageStats(Base):
    __tablename__ = "usage_stats"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    meetings_count = Column(Integer, default=0)
    audio_hours_used = Column(Float, default=0.0)  # Hours of audio processed
    ai_processing_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

# ===== INTEGRATIONS =====
class UserIntegration(Base):
    __tablename__ = "user_integrations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # google, zoom, slack, teams
    provider_name = Column(String(100))  # Google Meet, Zoom, Slack, Microsoft Teams
    status = Column(Enum('connected', 'disconnected', 'error'), default='disconnected')
    access_token = Column(Text)  # Encrypted access token
    refresh_token = Column(Text)  # Encrypted refresh token
    token_expires_at = Column(TIMESTAMP)
    settings = Column(Text)  # JSON string of integration-specific settings
    webhook_url = Column(String(500))
    last_sync_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

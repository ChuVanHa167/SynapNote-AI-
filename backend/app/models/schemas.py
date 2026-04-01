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
    created_at: Optional[datetime] = None

# 3. Chat Models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    meeting_id: Optional[str] = None

# 4. Integrations
class IntegrationHook(BaseModel):
    platform: str
    status: str
    config_url: str

class APIKey(BaseModel):
    id: str
    key: str
    name: str

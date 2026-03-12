from sqlalchemy import Column, String, Integer, Text, Enum, ForeignKey, TIMESTAMP, func
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
    hashed_password = Column(String(255), nullable=False)
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

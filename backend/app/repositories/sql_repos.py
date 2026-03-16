from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.repositories.interfaces import IMeetingRepository, IUserRepository, IApiKeyRepository
from app.models import models, schemas

class SqlMeetingRepository(IMeetingRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[schemas.Meeting]:
        db_meetings = self.db.query(models.Meeting).all()
        result = []
        for m in db_meetings:
            # Convert ORM to Schema
            result.append(self._to_schema(m))
        return result

    def get_by_id(self, meeting_id: str) -> Optional[schemas.Meeting]:
        db_meeting = self.db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
        if db_meeting:
            return self._to_schema(db_meeting)
        return None

    def create(self, meeting: schemas.Meeting) -> schemas.Meeting:
        db_meeting = models.Meeting(
            id=meeting.id,
            title=meeting.title,
            participants=meeting.participants,
            date=meeting.date,
            duration=meeting.duration,
            status=meeting.status,
            summary=meeting.summary,
            transcript=meeting.transcript,
            audio_url=meeting.audio_url,
            video_url=meeting.video_url
        )
        self.db.add(db_meeting)
        self.db.commit()
        self.db.refresh(db_meeting)
        return self._to_schema(db_meeting)

    def update(self, meeting_id: str, data: dict) -> schemas.Meeting:
        db_meeting = self.db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
        if db_meeting:
            print(f"[Repository] Updating meeting {meeting_id}. Keys: {list(data.keys())}")
            for key, value in data.items():
                if hasattr(db_meeting, key):
                    print(f"[Repository] Setting {key} = {value}")
                    setattr(db_meeting, key, value)
                else:
                    print(f"[Repository] WARNING: Attribute {key} not found on Meeting model")
            self.db.commit()
            print(f"[Repository] Commit finished for {meeting_id}")
            self.db.refresh(db_meeting)
            return self._to_schema(db_meeting)
        return None

    def delete(self, meeting_id: str) -> bool:
        db_meeting = self.db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
        if db_meeting:
            self.db.delete(db_meeting)
            self.db.commit()
            return True
        return False

    def _to_schema(self, db_meeting: models.Meeting) -> schemas.Meeting:
        # Map ORM to Pydantic
        action_items = [
            schemas.ActionItem(
                id=ai.id,
                task=ai.task,
                assignee=ai.assignee or "",
                deadline=ai.deadline or "",
                status=ai.status
            ) for ai in db_meeting.action_items
        ]
        
        decisions = [d.content for d in db_meeting.decisions]
        
        return schemas.Meeting(
            id=db_meeting.id,
            title=db_meeting.title,
            participants=db_meeting.participants,
            date=db_meeting.date,
            duration=db_meeting.duration,
            status=db_meeting.status,
            summary=db_meeting.summary,
            transcript=db_meeting.transcript,
            audio_url=db_meeting.audio_url,
            video_url=db_meeting.video_url,
            created_at=db_meeting.created_at,
            decisions=decisions,
            action_items=action_items
        )

class SqlUserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[schemas.User]:
        db_user = self.db.query(models.User).filter(models.User.email == email).first()
        if db_user:
            return schemas.User(
                id=db_user.id,
                email=db_user.email,
                display_name=db_user.display_name,
                title=db_user.title,
                avatar_url=db_user.avatar_url,
                hashed_password=db_user.hashed_password,
                email_summaries=bool(db_user.email_summaries),
                action_item_alerts=bool(db_user.action_item_alerts),
                product_updates=bool(db_user.product_updates)
            )
        return None

    def create(self, user: schemas.User) -> schemas.User:
        db_user = models.User(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            title=user.title,
            avatar_url=user.avatar_url,
            hashed_password=user.hashed_password,
            email_summaries=int(user.email_summaries),
            action_item_alerts=int(user.action_item_alerts),
            product_updates=int(user.product_updates)
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return schemas.User(
            id=db_user.id,
            email=db_user.email,
            display_name=db_user.display_name,
            title=db_user.title,
            avatar_url=db_user.avatar_url,
            hashed_password=db_user.hashed_password,
            email_summaries=bool(db_user.email_summaries),
            action_item_alerts=bool(db_user.action_item_alerts),
            product_updates=bool(db_user.product_updates)
        )

    def update(self, user_id: str, data: dict) -> schemas.User:
        db_user = self.db.query(models.User).filter(models.User.id == user_id).first()
        if db_user:
            for key, value in data.items():
                if hasattr(db_user, key):
                    if isinstance(value, bool):
                        setattr(db_user, key, int(value))
                    else:
                        setattr(db_user, key, value)
            self.db.commit()
            self.db.refresh(db_user)
            return schemas.User(
                id=db_user.id,
                email=db_user.email,
                display_name=db_user.display_name,
                title=db_user.title,
                avatar_url=db_user.avatar_url,
                hashed_password=db_user.hashed_password,
                email_summaries=bool(db_user.email_summaries),
                action_item_alerts=bool(db_user.action_item_alerts),
                product_updates=bool(db_user.product_updates)
            )
        return None

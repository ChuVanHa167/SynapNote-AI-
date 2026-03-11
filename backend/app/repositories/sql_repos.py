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
            transcript=meeting.transcript
        )
        self.db.add(db_meeting)
        self.db.commit()
        self.db.refresh(db_meeting)
        return self._to_schema(db_meeting)

    def update(self, meeting_id: str, data: dict) -> schemas.Meeting:
        db_meeting = self.db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
        if db_meeting:
            for key, value in data.items():
                if hasattr(db_meeting, key):
                    setattr(db_meeting, key, value)
            self.db.commit()
            self.db.refresh(db_meeting)
            return self._to_schema(db_meeting)
        return None

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
                hashed_password=db_user.hashed_password
            )
        return None

    def create(self, user: schemas.User) -> schemas.User:
        db_user = models.User(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            title=user.title,
            hashed_password=user.hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return schemas.User(
            id=db_user.id,
            email=db_user.email,
            display_name=db_user.display_name,
            title=db_user.title,
            hashed_password=db_user.hashed_password
        )

    def update(self, user_id: str, data: dict) -> schemas.User:
        db_user = self.db.query(models.User).filter(models.User.id == user_id).first()
        if db_user:
            for key, value in data.items():
                if hasattr(db_user, key):
                    setattr(db_user, key, value)
            self.db.commit()
            self.db.refresh(db_user)
            return schemas.User(
                id=db_user.id,
                email=db_user.email,
                display_name=db_user.display_name,
                title=db_user.title,
                hashed_password=db_user.hashed_password
            )
        return None

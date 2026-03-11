from typing import List, Optional, Dict
from app.models.schemas import User, Meeting, APIKey
from app.repositories.interfaces import IUserRepository, IMeetingRepository, IApiKeyRepository

class MockUserRepository(IUserRepository):
    def __init__(self):
        self.users: Dict[str, User] = {}
        # Pre-seed with mock admin
        mock_user = User(
            id="user_1",
            email="admin@synapnote.com",
            display_name="Admin",
            title="Administrator",
            hashed_password="hashed_password_mock"
        )
        self.users[mock_user.email] = mock_user

    def get_by_email(self, email: str) -> Optional[User]:
        return self.users.get(email)

    def create(self, user: User) -> User:
        self.users[user.email] = user
        return user

    def update(self, email: str, data: dict) -> User:
        user = self.users.get(email)
        if user:
            for key, value in data.items():
                setattr(user, key, value)
        return user

class MockMeetingRepository(IMeetingRepository):
    def __init__(self):
        self.meetings: Dict[str, Meeting] = {}
        # Pre-seed some mock data
        mock_meeting = Meeting(
            id="synap-workshop",
            title="Đồng bộ chiến lược Marketing Q4",
            participants=4,
            date="26 Thg 10, 2026",
            duration="45m 20s",
            status="HOÀN THÀNH",
            summary="Cuộc họp tập trung vào việc chốt ngân sách...",
            transcript="Mock Transcript Data here..."
        )
        self.meetings[mock_meeting.id] = mock_meeting

    def get_all(self) -> List[Meeting]:
        return list(self.meetings.values())

    def get_by_id(self, meeting_id: str) -> Optional[Meeting]:
        return self.meetings.get(meeting_id)

    def create(self, meeting: Meeting) -> Meeting:
        self.meetings[meeting.id] = meeting
        return meeting

    def update(self, meeting_id: str, data: dict) -> Meeting:
        meeting = self.meetings.get(meeting_id)
        if meeting:
            for key, value in data.items():
                setattr(meeting, key, value)
        return meeting

class MockApiKeyRepository(IApiKeyRepository):
    def __init__(self):
        self.keys = [
            APIKey(id="key_1", key="sk_live_test_api_key_123", name="Zapier Integration")
        ]

    def get_keys(self) -> List[APIKey]:
        return self.keys

    def create_key(self, api_key: APIKey) -> APIKey:
        self.keys.append(api_key)
        return api_key

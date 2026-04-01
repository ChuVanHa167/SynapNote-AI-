from typing import List, Optional
from abc import ABC, abstractmethod
from app.models.schemas import User, Meeting, APIKey

class IUserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]: pass
    
    @abstractmethod
    def create(self, user: User) -> User: pass
    
    @abstractmethod
    def update(self, user_id: str, data: dict) -> User: pass

class IMeetingRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Meeting]: pass
    
    @abstractmethod
    def get_by_id(self, meeting_id: str) -> Optional[Meeting]: pass
    
    @abstractmethod
    def create(self, meeting: Meeting) -> Meeting: pass
    
    @abstractmethod
    def update(self, meeting_id: str, data: dict) -> Meeting: pass

    @abstractmethod
    def delete(self, meeting_id: str) -> bool: pass

class IApiKeyRepository(ABC):
    @abstractmethod
    def get_keys(self) -> List[APIKey]: pass

    @abstractmethod
    def create_key(self, api_key: APIKey) -> APIKey: pass

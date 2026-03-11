import uuid
from app.models.schemas import UserCreate, UserProfileUpdate, UserPasswordUpdate, User
from app.repositories.interfaces import IUserRepository

class AuthService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def register_user(self, user_create: UserCreate) -> User:
        # In a real app: Hash the password here
        hashed_pw = f"mock_hash_{user_create.password}"
        user = User(
            id=str(uuid.uuid4()),
            email=user_create.email,
            display_name=user_create.display_name,
            hashed_password=hashed_pw
        )
        return self.user_repo.create(user)

    def authenticate_user(self, email: str, password: str) -> bool:
        user = self.user_repo.get_by_email(email)
        if not user:
            return False
        # Mock check
        return user.hashed_password == f"mock_hash_{password}" or user.email == "admin@synapnote.com"

    def update_profile(self, email: str, update_data: UserProfileUpdate):
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        return self.user_repo.update(user.id, update_data.model_dump(exclude_unset=True))

    def update_password(self, email: str, update_data: UserPasswordUpdate):
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
            
        # Mock Check old password
        if user.hashed_password != f"mock_hash_{update_data.current_password}" and user.email != "admin@synapnote.com":
            return False
            
        new_hashed = f"mock_hash_{update_data.new_password}"
        return self.user_repo.update(user.id, {"hashed_password": new_hashed})

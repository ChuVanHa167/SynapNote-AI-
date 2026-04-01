from app.database import engine, Base
from app.models.models import User, Meeting, MeetingDecision, ActionItem, ApiKey

def create_tables():
    print("Creating tables in MySQL...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables()

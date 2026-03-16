import os
import sys

# Add backend to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.repositories.sql_repos import SqlMeetingRepository
from app.services.meeting_service import MeetingService

db = SessionLocal()
repo = SqlMeetingRepository(db)
service = MeetingService(repo)

meeting_id = "5e9a3273-eebd-4551-951e-777c5337b95d"
file_path = "uploads/videos/raw_5e9a3273-eebd-4551-951e-777c5337b95d_fall_detection_1.mp4"

print(f"--- DEBUG START ---")
print(f"File exists: {os.path.exists(file_path)}")

try:
    service.process_ai_summary(meeting_id, file_path)
    print(f"--- DEBUG FINISHED ---")
    
    # Check result
    db.expire_all()
    meeting = repo.get_by_id(meeting_id)
    print(f"Final Audio URL in DB: {meeting.audio_url}")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

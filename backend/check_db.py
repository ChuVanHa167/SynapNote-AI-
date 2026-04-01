from app.database import SessionLocal
from app.models.models import Meeting

db = SessionLocal()
meetings = db.query(Meeting).all()
for m in meetings:
    print(f"ID: {m.id}")
    print(f"Title: {m.title}")
    print(f"Status: {m.status}")
    print(f"Audio URL: {m.audio_url}")
    print(f"Video URL: {m.video_url}")
    print("-" * 20)
db.close()

import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, BackgroundTasks, Depends, Form
from sqlalchemy.orm import Session
from app.models.schemas import Meeting
from app.services.meeting_service import MeetingService
from app.repositories.sql_repos import SqlMeetingRepository
from app.database import get_db

router = APIRouter(prefix="/meetings", tags=["meetings"])

def get_meeting_service(db: Session = Depends(get_db)):
    repo = SqlMeetingRepository(db)
    return MeetingService(repo)

@router.get("/", response_model=List[Meeting])
async def list_meetings(service: MeetingService = Depends(get_meeting_service)):
    return service.get_all_meetings()

@router.get("/{meeting_id}", response_model=Meeting)
async def get_meeting(meeting_id: str, service: MeetingService = Depends(get_meeting_service)):
    return service.get_meeting(meeting_id)

def run_background_processing(meeting_id: str, file_path: str):
    # This runs in a background thread and needs its own DB session
    from app.database import SessionLocal
    from app.repositories.sql_repos import SqlMeetingRepository
    
    db = SessionLocal()
    try:
        repo = SqlMeetingRepository(db)
        service = MeetingService(repo)
        service.process_ai_summary(meeting_id, file_path)
    finally:
        db.close()

@router.post("/upload", response_model=Meeting)
async def upload_audio(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    title: Optional[str] = Form(None), 
    duration: Optional[str] = Form(None),
    service: MeetingService = Depends(get_meeting_service)
):
    # 1. Start meeting in PENDING status
    new_meeting = service.upload_audio_and_process(file.filename, title, duration)
    
    # 2. Determine paths early (Persistent storage)
    is_video = file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
    persistent_dir = "uploads/videos" if is_video else "uploads"
    os.makedirs(persistent_dir, exist_ok=True)
    
    persistent_filename = f"raw_{new_meeting.id}_{file.filename}"
    persistent_path = os.path.join(persistent_dir, persistent_filename)
    public_url = f"/{persistent_dir}/{persistent_filename}"
    
    # 3. Save physical file directly to persistent storage
    print(f"[Upload] Đang lưu file: {file.filename}")
    try:
        await file.seek(0)
        content = await file.read()
        content_length = len(content)
        
        with open(persistent_path, "wb") as buffer:
            buffer.write(content)
        
        # Check saved file size
        actual_size = os.path.getsize(persistent_path)
        print(f"[Upload] Đã lưu xong. Buffer: {content_length} bytes, Disk: {actual_size} bytes")
        
        if actual_size == 0 or actual_size != content_length:
             print(f"[Upload] CẢNH BÁO: Kích thước file không khớp hoặc bằng 0!")
             
    except Exception as e:
        print(f"[Upload] LỖI khi lưu file: {str(e)}")
    
    # 4. Update DB with URL immediately so it's playable
    if is_video:
        service.meeting_repo.update(new_meeting.id, {"video_url": public_url})
    else:
        service.meeting_repo.update(new_meeting.id, {"audio_url": public_url})

    # 5. Start background AI processing (using the persistent path)
    background_tasks.add_task(run_background_processing, new_meeting.id, persistent_path)
    
    return service.get_meeting(new_meeting.id)

@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: str, service: MeetingService = Depends(get_meeting_service)):
    if not service.delete_meeting(meeting_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"message": "Meeting deleted successfully"}

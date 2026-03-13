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
    
    # 2. Save physical file to temp folder
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"raw_{new_meeting.id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 3. Add AI Audio + LLM transcribing to a queue/background task
    background_tasks.add_task(run_background_processing, new_meeting.id, file_path)
    
    return new_meeting

@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: str, service: MeetingService = Depends(get_meeting_service)):
    if not service.delete_meeting(meeting_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"message": "Meeting deleted successfully"}

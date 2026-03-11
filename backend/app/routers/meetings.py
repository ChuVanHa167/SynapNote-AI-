import os
import shutil
from typing import List
from fastapi import APIRouter, File, UploadFile, BackgroundTasks, Depends
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

@router.post("/upload", response_model=Meeting)
async def upload_audio(
    background_tasks: BackgroundTasks, 
    title: str = None, 
    file: UploadFile = File(...),
    service: MeetingService = Depends(get_meeting_service)
):
    # 1. Start meeting in PENDING status
    new_meeting = service.upload_audio_and_process(file.filename, title)
    
    # 2. Save physical file to temp folder
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"raw_{new_meeting.id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 3. Add AI Audio + LLM transcribing to a queue/background task
    background_tasks.add_task(service.process_ai_summary, new_meeting.id, file_path)
    
    return new_meeting

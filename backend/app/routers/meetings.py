import os
import shutil
import subprocess
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, BackgroundTasks, Depends, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.schemas import Meeting
from app.services.meeting_service import MeetingService
from app.services.download_service import download_with_progress, get_filename_from_url, is_video_url, is_audio_url
from app.services.job_tracker import job_tracker, JobProgress
from app.repositories.sql_repos import SqlMeetingRepository
from app.services.backblaze_storage import get_backblaze_storage
from app.services.audio_service import AudioProcessingService
from app.database import get_db
import json
import asyncio

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

def run_background_processing(meeting_id: str, file_path: str, stt_profile: str = "auto", duration: Optional[str] = None):
    # This runs in a background thread and needs its own DB session
    from app.database import SessionLocal
    from app.repositories.sql_repos import SqlMeetingRepository
    
    db = SessionLocal()
    try:
        repo = SqlMeetingRepository(db)
        service = MeetingService(repo)
        service.process_ai_summary(meeting_id, file_path, stt_profile=stt_profile, duration=duration)
    finally:
        db.close()

def process_file_upload_with_progress(
    job_id: str,
    meeting_id: str,
    file_path: str,
    is_video: bool,
    temp_path: Optional[str],
    stt_profile: str,
    duration: Optional[str]
):
    """Background task to process uploaded file with progress tracking"""
    from app.database import SessionLocal
    from app.services.audio_service import AudioProcessingService
    
    db = SessionLocal()
    try:
        repo = SqlMeetingRepository(db)
        service = MeetingService(repo)
        audio_service = AudioProcessingService()
        
        job_tracker.update_progress(job_id, 10, "Đang phân tích file...", "processing")
        
        # Get file size for progress calculation
        file_size = os.path.getsize(file_path)
        job_tracker.update_bytes(job_id, total=file_size, downloaded=file_size)
        
        # Try to detect duration from audio file if not provided or is 0m 0s
        final_duration = duration
        if not final_duration or final_duration == "0m 0s":
            if os.path.exists(file_path):
                final_duration = audio_service.get_duration(file_path)
                print(f"[File Upload] Auto-detected duration from audio file: {final_duration}")
        
        # Step 1: Upload to Backblaze if configured
        job_tracker.update_progress(job_id, 30, "Đang upload lên cloud storage...", "uploading")
        
        b2_url = None
        video_b2_url = None
        
        if get_backblaze_storage().is_configured():
            # Upload audio
            audio_remote = f"audio/{meeting_id}.mp3"
            b2_url = get_backblaze_storage().upload_file(file_path, audio_remote)
            if b2_url:
                print(f"[File Upload] Uploaded audio to Backblaze: {b2_url}")
                job_tracker.update_progress(job_id, 50, "Upload audio hoàn tất", "uploading")
            else:
                print(f"[File Upload] Failed to upload audio to Backblaze")
            
            # Upload video if applicable
            if is_video and temp_path and os.path.exists(temp_path):
                video_ext = os.path.splitext(temp_path)[1]
                video_remote = f"video/{meeting_id}{video_ext}"
                video_b2_url = get_backblaze_storage().upload_file(temp_path, video_remote)
                if video_b2_url:
                    print(f"[File Upload] Uploaded video to Backblaze: {video_b2_url}")
                os.remove(temp_path)
                print(f"[File Upload] Cleaned up temp video file")
        else:
            job_tracker.update_progress(job_id, 30, "Lưu trữ local (Backblaze chưa cấu hình)", "uploading")
        
        # Step 2: Update database
        job_tracker.update_progress(job_id, 60, "Đang cập nhật dữ liệu...", "processing")
        
        final_audio_url = b2_url if b2_url else f"/uploads/{meeting_id}.mp3"
        update_data = {"audio_url": final_audio_url}
        if video_b2_url:
            update_data["video_url"] = video_b2_url
        if final_duration and final_duration != "0m 0s":
            update_data["duration"] = final_duration
            
        service.meeting_repo.update(meeting_id, update_data)
        
        # Step 3: Start AI processing
        job_tracker.update_progress(job_id, 70, "Đang bắt đầu xử lý AI...", "processing")
        
        # Run AI processing with progress updates
        try:
            selected_profile = service._resolve_stt_profile(stt_profile, final_duration)
            print(f"[File Upload] STT profile: {selected_profile}")
            
            job_tracker.update_progress(job_id, 75, "Đang trích xuất giọng nói (STT)...", "processing")
            
            use_groq_gemini = os.getenv("USE_GROQ_GEMINI", "true").lower() in {"1", "true", "yes"}
            
            if use_groq_gemini:
                try:
                    ai_output = service.ai_bridge_service.process_audio_groq_gemini(file_path)
                    transcript_text = ai_output.get("transcript") or ""
                except Exception as groq_exc:
                    print(f"[File Upload] Groq failed, fallback: {str(groq_exc)}")
                    ai_output = service.ai_bridge_service.process_audio_file(file_path, profile=selected_profile)
                    transcript_text = ai_output.get("transcript") or ""
            else:
                ai_output = service.ai_bridge_service.process_audio_file(file_path, profile=selected_profile)
                transcript_text = ai_output.get("transcript") or ""
            
            job_tracker.update_progress(job_id, 90, "Đang tóm tắt nội dung...", "processing")
            
            # Update meeting with results
            updates = {
                "status": "HOÀN THÀNH",
                "transcript": transcript_text,
                "summary": ai_output.get("summary") or "Bản dịch đã được trích xuất thành công.",
                "decisions": ai_output.get("decisions") or [],
                "action_items": ai_output.get("action_items") or [],
            }
            service.meeting_repo.update(meeting_id, updates)
            
            job_tracker.update_progress(job_id, 100, "Hoàn thành!", "completed")
            job_tracker.complete_job(job_id, final_audio_url)
            print(f"[File Upload] Processing completed for meeting {meeting_id}")
            
        except Exception as ai_error:
            print(f"[File Upload] AI processing error: {str(ai_error)}")
            service.meeting_repo.update(meeting_id, {
                "status": "LỖI",
                "summary": f"Lỗi xử lý AI: {str(ai_error)}"
            })
            job_tracker.set_error(job_id, str(ai_error))
            
    except Exception as e:
        print(f"[File Upload] Error: {e}")
        job_tracker.set_error(job_id, str(e))
        # Update meeting status to error
        try:
            service.meeting_repo.update(meeting_id, {
                "status": "LỖI",
                "summary": f"Lỗi upload: {str(e)}"
            })
        except:
            pass
    finally:
        db.close()


@router.post("/upload")
async def upload_audio(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    duration: Optional[str] = Form(None),
    stt_profile: Optional[str] = Form("auto"),
    link_url: Optional[str] = Form(None),
    service: MeetingService = Depends(get_meeting_service)
):
    """
    Upload file trực tiếp với progress tracking
    Trả về job_id để theo dõi tiến độ qua SSE endpoint
    """
    print(f"[Upload] Received file: {file.filename}, size: {file.size}")

    # Create job for progress tracking
    job = job_tracker.create_job()
    job_id = job.job_id
    print(f"[Upload] Created job ID: {job_id}")

    # Initialize progress
    job_tracker.update_progress(job_id, 5, "Đang nhận file...", "processing")

    # 1. Start meeting in PENDING status
    new_meeting = service.upload_audio_and_process(file.filename, title, duration)
    print(f"[Upload] Created meeting ID: {new_meeting.id}")
    MeetingService.clear_cancel(new_meeting.id)

    # 2. Create uploads directory
    os.makedirs("uploads", exist_ok=True)

    # 3. Check if file is video
    is_video = file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm'))

    # 4. Generate output filename (audio only)
    audio_filename = f"{new_meeting.id}.mp3"
    audio_path = os.path.join("uploads", audio_filename)
    temp_path = None

    try:
        job_tracker.update_progress(job_id, 10, "Đang lưu file...", "processing")
        
        if is_video:
            # Save to temp file first, then extract audio
            temp_path = os.path.join("uploads", f"temp_{new_meeting.id}")
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Auto-detect duration from video file
            audio_service = AudioProcessingService()
            detected_duration = duration
            if not detected_duration:
                detected_duration = audio_service.get_duration(temp_path)
                print(f"[Upload] Auto-detected duration from video: {detected_duration}")

            job_tracker.update_progress(job_id, 20, "Đang chuyển đổi video sang audio...", "processing")
            
            # Convert video to audio using ffmpeg
            cmd = [
                audio_service.ffmpeg_path,
                "-i", temp_path,
                "-vn",  # No video
                "-acodec", "libmp3lame",
                "-q:a", "4",  # Quality 4 (~165kbps VBR)
                "-y",  # Overwrite
                audio_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"[Upload] Converted and saved: {audio_path}")
            
            # Try to get duration from converted audio if not detected earlier or was 0m 0s
            if not detected_duration or detected_duration == "0m 0s":
                if os.path.exists(audio_path):
                    detected_duration = audio_service.get_duration(audio_path)
                    print(f"[Upload] Auto-detected duration from converted audio: {detected_duration}")
                    # Update meeting with corrected duration
                    if detected_duration and detected_duration != "0m 0s":
                        service.meeting_repo.update(new_meeting.id, {"duration": detected_duration})
                        print(f"[Upload] Updated meeting {new_meeting.id} with duration: {detected_duration}")
        else:
            # Audio file - save directly
            with open(audio_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            print(f"[Upload] Saved audio file: {audio_path}")

            # Auto-detect duration from audio file
            audio_service = AudioProcessingService()
            detected_duration = duration
            if not detected_duration:
                detected_duration = audio_service.get_duration(audio_path)
                print(f"[Upload] Auto-detected duration from audio: {detected_duration}")
                # Update meeting with detected duration
                if detected_duration and detected_duration != "0m 0s":
                    service.meeting_repo.update(new_meeting.id, {"duration": detected_duration})
                    print(f"[Upload] Updated meeting {new_meeting.id} with duration: {detected_duration}")

        actual_size = os.path.getsize(audio_path)
        print(f"[Upload] File size: {actual_size} bytes")
        job_tracker.update_bytes(job_id, total=actual_size, downloaded=actual_size)

    except subprocess.CalledProcessError as e:
        print(f"[Upload] FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        job_tracker.set_error(job_id, f"Lỗi chuyển đổi: {str(e)}")
        service.meeting_repo.update(new_meeting.id, {"status": "LỖI", "summary": f"Conversion error: {str(e)}"})
        return {
            "job_id": job_id,
            "meeting_id": new_meeting.id,
            "status": "error",
            "message": f"Lỗi xử lý file: {str(e)}"
        }
    except Exception as e:
        print(f"[Upload] Error saving file: {str(e)}")
        job_tracker.set_error(job_id, f"Lỗi lưu file: {str(e)}")
        service.meeting_repo.update(new_meeting.id, {"status": "LỖI", "summary": f"Upload error: {str(e)}"})
        return {
            "job_id": job_id,
            "meeting_id": new_meeting.id,
            "status": "error",
            "message": f"Lỗi lưu file: {str(e)}"
        }

    # Update link_url if provided
    if link_url:
        service.meeting_repo.update(new_meeting.id, {"link_url": link_url})

    # Start background processing with progress tracking
    background_tasks.add_task(
        process_file_upload_with_progress,
        job_id,
        new_meeting.id,
        audio_path,
        is_video,
        temp_path,
        stt_profile or "auto",
        detected_duration,
    )

    print(f"[Upload] Started background processing for meeting: {new_meeting.id}, job: {job_id}")
    return {
        "job_id": job_id,
        "meeting_id": new_meeting.id,
        "status": "started",
        "message": "Bắt đầu xử lý file upload"
    }

def extract_b2_filename(url: str) -> str:
    """Extract the filename from a Backblaze B2 URL"""
    if not url or 'backblazeb2.com' not in url:
        return None
    # URL format: https://fXXX.backblazeb2.com/file/bucket-name/file-path
    parts = url.split('/file/')
    if len(parts) >= 2:
        # parts[1] contains bucket-name/file-path
        bucket_and_file = parts[1].split('/', 1)
        if len(bucket_and_file) >= 2:
            return bucket_and_file[1]  # Return file-path
    return None

@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: str, service: MeetingService = Depends(get_meeting_service)):
    # Get meeting first to find file URLs
    meeting = service.get_meeting(meeting_id)
    if not meeting:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Delete files from Backblaze if configured
    if get_backblaze_storage().is_configured():
        if meeting.audio_url and 'backblazeb2.com' in meeting.audio_url:
            audio_file = extract_b2_filename(meeting.audio_url)
            if audio_file:
                get_backblaze_storage().delete_file(audio_file)
                print(f"[Delete] Deleted audio from Backblaze: {audio_file}")
        
        if meeting.video_url and 'backblazeb2.com' in meeting.video_url:
            video_file = extract_b2_filename(meeting.video_url)
            if video_file:
                get_backblaze_storage().delete_file(video_file)
                print(f"[Delete] Deleted video from Backblaze: {video_file}")
    
    # Also delete local files
    if meeting.audio_url:
        local_audio = os.path.join("uploads", os.path.basename(meeting.audio_url))
        if os.path.exists(local_audio):
            os.remove(local_audio)
            print(f"[Delete] Deleted local audio: {local_audio}")
    
    # Delete from database
    if not service.delete_meeting(meeting_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return {"message": "Meeting deleted successfully"}

@router.post("/{meeting_id}/reprocess", response_model=Meeting)
async def reprocess_meeting(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    stt_profile: Optional[str] = "auto",
    service: MeetingService = Depends(get_meeting_service)
):
    # 1. Check if meeting exists
    meeting = service.get_meeting(meeting_id)
    if not meeting:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # 2. Update status to PENDING/PROCESSING
    MeetingService.clear_cancel(meeting_id)
    service.meeting_repo.update(meeting_id, {"status": "ĐANG XỬ LÝ"})
    
    # 3. Identify path for processing
    # We prefer extracted audio if it exists, otherwise video
    # Note: Logic in process_ai_summary handles this, so we just need a valid path
    import os
    is_video = meeting.video_url is not None
    persistent_dir = "uploads/videos" if is_video else "uploads/audio"
    filename = os.path.basename(meeting.video_url or meeting.audio_url)
    persistent_path = os.path.join(persistent_dir, filename)
    
    # 4. Trigger background task
    background_tasks.add_task(
        run_background_processing,
        meeting_id,
        persistent_path,
        stt_profile or "auto",
        meeting.duration,
    )
    
    return service.get_meeting(meeting_id)


@router.post("/{meeting_id}/stop", response_model=Meeting)
async def stop_processing(
    meeting_id: str,
    service: MeetingService = Depends(get_meeting_service),
):
    meeting = service.get_meeting(meeting_id)
    if not meeting:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Meeting not found")

    MeetingService.request_cancel(meeting_id)
    service.meeting_repo.update(
        meeting_id,
        {
            "status": "LỖI",
            "summary": "Da dung ban dich theo yeu cau nguoi dung.",
        },
    )
    return service.get_meeting(meeting_id)


# ==================== UPLOAD FROM URL WITH PROGRESS ====================

def process_url_upload_with_progress(
    job_id: str,
    file_url: str,
    title: Optional[str],
    duration: Optional[str],
    stt_profile: str,
    link_url: Optional[str]
):
    """Background task to download from URL and upload to Backblaze with progress tracking"""
    
    # Initialize audio service for ffmpeg path
    from app.services.audio_service import AudioProcessingService
    audio_service = AudioProcessingService()
    
    db = next(get_db())
    try:
        repo = SqlMeetingRepository(db)
        service = MeetingService(repo)
        
        # Create uploads directory
        os.makedirs("uploads", exist_ok=True)
        
        # Check file type
        filename = get_filename_from_url(file_url)
        is_video = is_video_url(file_url) or filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm'))
        is_audio = is_audio_url(file_url) or filename.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'))
        
        # Download file with progress
        job_tracker.update_progress(job_id, 10, "Bắt đầu tải xuống...", "downloading")
        
        temp_download_path = os.path.join("uploads", f"download_{job_id}")
        
        def download_callback(downloaded, total, message):
            if total > 0:
                progress = 10 + (downloaded / total) * 40
                job_tracker.update_progress(job_id, progress, message, "downloading")
                job_tracker.update_bytes(job_id, downloaded=downloaded, total=total)
        
        download_with_progress(file_url, temp_download_path, download_callback)
        job_tracker.update_progress(job_id, 50, "Tải xuống hoàn tất", "downloading")
        
        # Get duration from downloaded file BEFORE creating meeting
        detected_duration = duration
        if not detected_duration and os.path.exists(temp_download_path):
            detected_duration = audio_service.get_duration(temp_download_path)
            print(f"[URL Upload] Auto-detected duration from downloaded file: {detected_duration}")
            job_tracker.update_progress(job_id, 52, f"Thời lượng: {detected_duration}", "processing")
        
        # Create meeting with detected duration (will be updated later if needed)
        new_meeting = service.upload_audio_and_process(filename, title, detected_duration)
        MeetingService.clear_cancel(new_meeting.id)
        
        audio_filename = f"{new_meeting.id}.mp3"
        audio_path = os.path.join("uploads", audio_filename)
        temp_path = None
        final_duration = detected_duration  # Keep track of final duration
        
        # Convert if video
        if is_video:
            job_tracker.update_progress(job_id, 55, "Đang chuyển đổi video sang audio...", "processing")
            temp_path = temp_download_path
            
            cmd = [
                audio_service.ffmpeg_path,
                "-i", temp_path,
                "-vn",
                "-acodec", "libmp3lame",
                "-q:a", "4",
                "-y",
                audio_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            job_tracker.update_progress(job_id, 70, "Chuyển đổi hoàn tất", "processing")
            
            # Try to get duration from converted audio if not detected earlier or was 0m 0s
            if not final_duration or final_duration == "0m 0s":
                if os.path.exists(audio_path):
                    final_duration = audio_service.get_duration(audio_path)
                    print(f"[URL Upload] Auto-detected duration from converted audio: {final_duration}")
                    # Update meeting with corrected duration
                    if final_duration and final_duration != "0m 0s":
                        service.meeting_repo.update(new_meeting.id, {"duration": final_duration})
                        print(f"[URL Upload] Updated meeting {new_meeting.id} with duration: {final_duration}")
        else:
            # Audio file - just move
            shutil.move(temp_download_path, audio_path)
            job_tracker.update_progress(job_id, 55, "File âm thanh đã sẵn sàng", "processing")
            
            # For audio files, also verify duration if not detected
            if not final_duration or final_duration == "0m 0s":
                if os.path.exists(audio_path):
                    final_duration = audio_service.get_duration(audio_path)
                    print(f"[URL Upload] Auto-detected duration from audio file: {final_duration}")
                    if final_duration and final_duration != "0m 0s":
                        service.meeting_repo.update(new_meeting.id, {"duration": final_duration})
                        print(f"[URL Upload] Updated meeting {new_meeting.id} with duration: {final_duration}")
        
        # Upload to Backblaze with progress
        b2_url = None
        video_b2_url = None
        
        if get_backblaze_storage().is_configured():
            job_tracker.update_progress(job_id, 70, "Đang upload lên Backblaze B2...", "uploading")
            
            # Get file size for progress
            audio_size = os.path.getsize(audio_path)
            
            # Upload audio
            audio_remote = f"audio/{new_meeting.id}.mp3"
            b2_url = get_backblaze_storage().upload_file(audio_path, audio_remote)
            
            if b2_url:
                job_tracker.update_progress(job_id, 85, "Upload audio hoàn tất", "uploading")
                
                # Upload video if applicable
                if is_video and temp_path and os.path.exists(temp_path):
                    video_ext = os.path.splitext(filename)[1]
                    video_remote = f"video/{new_meeting.id}{video_ext}"
                    video_b2_url = get_backblaze_storage().upload_file(temp_path, video_remote)
                    if video_b2_url:
                        job_tracker.update_progress(job_id, 95, "Upload video hoàn tất", "uploading")
                    os.remove(temp_path)
            else:
                job_tracker.update_progress(job_id, 85, "Upload Backblaze thất bại, dùng local storage", "uploading")
        else:
            job_tracker.update_progress(job_id, 85, "Backblaze chưa cấu hình, dùng local storage", "uploading")
        
        # Update database
        final_audio_url = b2_url if b2_url else f"/uploads/{audio_filename}"
        update_data = {"audio_url": final_audio_url}
        if video_b2_url:
            update_data["video_url"] = video_b2_url
        if link_url:
            update_data["link_url"] = link_url
        
        updated_meeting = service.meeting_repo.update(new_meeting.id, update_data)
        
        # Start AI processing
        job_tracker.update_progress(job_id, 100, "Bắt đầu xử lý AI...", "completed")
        job_tracker.complete_job(job_id, final_audio_url)
        
        # Run AI processing in background
        run_background_processing(new_meeting.id, audio_path, stt_profile, final_duration)
        
    except Exception as e:
        print(f"[URL Upload] Error: {e}")
        job_tracker.set_error(job_id, str(e))
        raise


@router.post("/upload-from-url")
async def upload_from_url(
    background_tasks: BackgroundTasks,
    file_url: str = Form(..., description="URL của file cần tải"),
    title: Optional[str] = Form(None),
    duration: Optional[str] = Form(None),
    stt_profile: Optional[str] = Form("auto"),
    link_url: Optional[str] = Form(None),
    service: MeetingService = Depends(get_meeting_service)
):
    """
    Upload file từ URL với progress tracking
    Trả về job_id để theo dõi tiến độ qua SSE endpoint
    """
    # Create job
    job = job_tracker.create_job()
    job_id = job.job_id
    
    # Start background processing
    background_tasks.add_task(
        process_url_upload_with_progress,
        job_id,
        file_url,
        title,
        duration,
        stt_profile or "auto",
        link_url
    )
    
    return {
        "job_id": job_id,
        "message": "Bắt đầu tải file từ URL",
        "status": "started"
    }


@router.get("/upload-progress/{job_id}")
async def upload_progress(job_id: str):
    """
    SSE endpoint để nhận cập nhật tiến độ upload theo thời gian thực
    """
    async def event_generator():
        last_progress = -1
        last_status = ""
        
        while True:
            job = job_tracker.get_job(job_id)
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            
            # Only send if changed
            if job.progress != last_progress or job.status != last_status:
                last_progress = job.progress
                last_status = job.status
                
                data = {
                    "job_id": job.job_id,
                    "progress": round(job.progress, 1),
                    "status": job.status,
                    "message": job.message,
                    "total_bytes": job.total_bytes,
                    "downloaded_bytes": job.downloaded_bytes,
                    "uploaded_bytes": job.uploaded_bytes,
                    "file_url": job.file_url,
                    "error": job.error
                }
                yield f"data: {json.dumps(data)}\n\n"
            
            # End if completed or error
            if job.status in ("completed", "error"):
                break
            
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Get current job status (polling alternative to SSE)"""
    job = job_tracker.get_job(job_id)
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "progress": round(job.progress, 1),
        "status": job.status,
        "message": job.message,
        "total_bytes": job.total_bytes,
        "downloaded_bytes": job.downloaded_bytes,
        "uploaded_bytes": job.uploaded_bytes,
        "file_url": job.file_url,
        "error": job.error
    }


# ==================== AUDIO/VIDEO STREAMING ====================

def extract_b2_filename(url: str) -> Optional[str]:
    """Extract the filename from a Backblaze B2 URL
    
    Example: https://f003.backblazeb2.com/file/Synapnote-ai/audio/xxx.mp3
    Returns: audio/xxx.mp3
    """
    if not url or 'backblazeb2.com' not in url:
        return None
    try:
        # Format: https://fXXX.backblazeb2.com/file/bucket-name/file-path
        parts = url.split('/file/')
        if len(parts) >= 2:
            bucket_and_file = parts[1].split('/', 1)
            if len(bucket_and_file) >= 2:
                return bucket_and_file[1]  # Return file-path
    except Exception:
        pass
    return None

@router.get("/{meeting_id}/stream")
async def stream_media(
    meeting_id: str,
    service: MeetingService = Depends(get_meeting_service)
):
    """
    Stream audio/video file for a meeting.
    Downloads from Backblaze using SDK (with auth) if needed, or serves local files.
    This ensures proper CORS headers for media playback.
    """
    from fastapi.responses import FileResponse, StreamingResponse
    from fastapi import HTTPException
    import io
    
    meeting = service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Prefer audio_url, fallback to video_url
    media_url = meeting.audio_url or meeting.video_url
    if not media_url:
        raise HTTPException(status_code=404, detail="No media file found for this meeting")
    
    # If it's a local file (starts with /uploads)
    if media_url.startswith('/uploads'):
        file_path = os.path.join("uploads", os.path.basename(media_url))
        if os.path.exists(file_path):
            return FileResponse(
                file_path,
                media_type="audio/mpeg" if media_url.endswith('.mp3') else "video/mp4",
                filename=os.path.basename(media_url)
            )
        raise HTTPException(status_code=404, detail="Local file not found")
    
    # If it's a Backblaze URL, download using SDK (with auth)
    if 'backblazeb2.com' in media_url:
        try:
            # Extract filename from URL
            b2_filename = extract_b2_filename(media_url)
            if not b2_filename:
                raise HTTPException(status_code=500, detail="Invalid Backblaze URL format")
            
            print(f"[Stream] Downloading from Backblaze: {b2_filename}")
            
            # Download file using B2 SDK (with authentication)
            b2_storage = get_backblaze_storage()
            if not b2_storage.is_configured():
                raise HTTPException(status_code=500, detail="Backblaze not configured")
            
            file_bytes = b2_storage.download_file_bytes(b2_filename)
            if not file_bytes:
                raise HTTPException(status_code=404, detail="File not found in Backblaze")
            
            print(f"[Stream] Downloaded {len(file_bytes)} bytes from Backblaze")
            
            # Determine content type
            if b2_filename.endswith('.mp4'):
                content_type = 'video/mp4'
            elif b2_filename.endswith('.mp3'):
                content_type = 'audio/mpeg'
            elif b2_filename.endswith('.mov'):
                content_type = 'video/quicktime'
            elif b2_filename.endswith('.wav'):
                content_type = 'audio/wav'
            else:
                content_type = 'application/octet-stream'
            
            # Stream the file from memory
            return StreamingResponse(
                io.BytesIO(file_bytes),
                media_type=content_type,
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(len(file_bytes)),
                }
            )
        except HTTPException:
            raise
        except Exception as e:
            print(f"[Stream] Error downloading from Backblaze: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to stream media: {str(e)}")
    
    # For other external URLs, redirect
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=media_url)

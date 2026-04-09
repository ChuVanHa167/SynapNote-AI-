import os
import re
import shutil
import subprocess
import io
import unicodedata
from typing import Iterator, List, Optional, Tuple
from fastapi import APIRouter, File, UploadFile, BackgroundTasks, Depends, Form, Query, Response, Request, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.models.schemas import Meeting
from app.services.meeting_service import MeetingService
from app.services.download_service import download_with_progress, get_filename_from_url, is_video_url, is_audio_url
from app.services.job_tracker import job_tracker, JobProgress
from app.repositories.sql_repos import SqlMeetingRepository
from app.services.minio_storage import get_minio_storage
from app.services.audio_service import AudioProcessingService
from app.database import get_db
import json
import asyncio

router = APIRouter(prefix="/meetings", tags=["meetings"])

def get_meeting_service(db: Session = Depends(get_db)):
    repo = SqlMeetingRepository(db)
    return MeetingService(repo)


def _normalize_upload_filename(filename: Optional[str]) -> str:
    raw_name = os.path.basename(filename or "upload.bin")
    stem, ext = os.path.splitext(raw_name)

    normalized_stem = unicodedata.normalize("NFD", stem)
    normalized_stem = "".join(ch for ch in normalized_stem if unicodedata.category(ch) != "Mn")
    normalized_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", normalized_stem).strip("._")

    normalized_ext = unicodedata.normalize("NFD", ext)
    normalized_ext = "".join(ch for ch in normalized_ext if unicodedata.category(ch) != "Mn")
    normalized_ext = re.sub(r"[^A-Za-z0-9.]", "", normalized_ext)

    safe_stem = normalized_stem or "upload"
    return f"{safe_stem}{normalized_ext}"

@router.get("/", response_model=List[Meeting])
async def list_meetings(response: Response, service: MeetingService = Depends(get_meeting_service)):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return service.get_all_meetings()

@router.get("/{meeting_id}", response_model=Meeting)
async def get_meeting(meeting_id: str, response: Response, service: MeetingService = Depends(get_meeting_service)):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
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
        
        # Step 1: Upload to object storage if configured
        job_tracker.update_progress(job_id, 30, "Đang upload lên cloud storage...", "uploading")
        
        cloud_audio_url = None
        cloud_video_url = None
        
        minio_storage = get_minio_storage()
        if minio_storage.is_configured():
            # Upload audio
            audio_remote = f"audio/{meeting_id}.mp3"
            cloud_audio_url = minio_storage.upload_file(file_path, audio_remote)
            if cloud_audio_url:
                print(f"[File Upload] Uploaded audio to MinIO: {cloud_audio_url}")
                job_tracker.update_progress(job_id, 50, "Upload audio hoàn tất", "uploading")
            else:
                print(f"[File Upload] Failed to upload audio to MinIO")
            
            # Upload video if applicable
            if is_video and temp_path and os.path.exists(temp_path):
                video_ext = os.path.splitext(temp_path)[1]
                video_remote = f"video/{meeting_id}{video_ext}"
                cloud_video_url = minio_storage.upload_file(temp_path, video_remote)
                if cloud_video_url:
                    print(f"[File Upload] Uploaded video to MinIO: {cloud_video_url}")
                os.remove(temp_path)
                print(f"[File Upload] Cleaned up temp video file")
        else:
            job_tracker.update_progress(job_id, 30, "Lưu trữ local (MinIO chưa cấu hình)", "uploading")
        
        # Step 2: Update database
        job_tracker.update_progress(job_id, 60, "Đang cập nhật dữ liệu...", "processing")
        
        final_audio_url = cloud_audio_url if cloud_audio_url else f"/uploads/{meeting_id}.mp3"
        update_data = {"audio_url": final_audio_url}
        if cloud_video_url:
            update_data["video_url"] = cloud_video_url
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
    raw_filename = file.filename or "upload.bin"
    safe_filename = _normalize_upload_filename(raw_filename)
    print(f"[Upload] Received file: {raw_filename}, size: {file.size}")
    if safe_filename != raw_filename:
        print(f"[Upload] Normalized filename: {safe_filename}")

    # Create job for progress tracking
    job = job_tracker.create_job()
    job_id = job.job_id
    print(f"[Upload] Created job ID: {job_id}")

    # Initialize progress
    job_tracker.update_progress(job_id, 5, "Đang nhận file...", "processing")

    # 1. Start meeting in PENDING status
    new_meeting = service.upload_audio_and_process(safe_filename, title, duration)
    print(f"[Upload] Created meeting ID: {new_meeting.id}")
    MeetingService.clear_cancel(new_meeting.id)

    # 2. Create uploads directory
    os.makedirs("uploads", exist_ok=True)

    # 3. Check if file is video
    is_video = safe_filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm'))

    # 4. Generate output filename (audio only)
    audio_filename = f"{new_meeting.id}.mp3"
    audio_path = os.path.join("uploads", audio_filename)
    temp_path = None

    try:
        job_tracker.update_progress(job_id, 10, "Đang lưu file...", "processing")
        
        if is_video:
            # Save to temp file first, then extract audio
            temp_ext = os.path.splitext(safe_filename)[1] or ".tmp"
            temp_path = os.path.join("uploads", f"temp_{new_meeting.id}{temp_ext}")
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

@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: str, service: MeetingService = Depends(get_meeting_service)):
    # Get meeting first to find file URLs
    meeting = service.get_meeting(meeting_id)
    if not meeting:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Delete files from MinIO if configured
    minio_storage = get_minio_storage()
    if minio_storage.is_configured():
        if meeting.audio_url:
            audio_file = minio_storage.extract_object_name_from_url(meeting.audio_url)
            if audio_file:
                minio_storage.delete_file(audio_file)
                print(f"[Delete] Deleted audio from MinIO: {audio_file}")

        if meeting.video_url:
            video_file = minio_storage.extract_object_name_from_url(meeting.video_url)
            if video_file:
                minio_storage.delete_file(video_file)
                print(f"[Delete] Deleted video from MinIO: {video_file}")
    
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
    # We prefer local extracted audio/video if present.
    # If local media is missing but URL points to MinIO, download a temporary copy for reprocessing.
    import os
    is_video = meeting.video_url is not None
    media_url = meeting.video_url if is_video else meeting.audio_url
    filename = os.path.basename(media_url or "")

    candidates = [
        os.path.join("uploads", "videos", filename),
        os.path.join("uploads", "audio", filename),
        os.path.join("uploads", filename),
    ]
    persistent_path = next((path for path in candidates if os.path.exists(path)), None)

    if not persistent_path and media_url:
        object_name = extract_storage_object_name(media_url)
        if object_name and get_minio_storage().is_configured():
            file_bytes = get_minio_storage().download_file_bytes(object_name)
            if file_bytes:
                os.makedirs(os.path.join("uploads", "reprocess"), exist_ok=True)
                persistent_path = os.path.join("uploads", "reprocess", filename)
                with open(persistent_path, "wb") as f:
                    f.write(file_bytes)

    if not persistent_path:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Không tìm thấy file media để reprocess")
    
    # 4. Trigger background task
    background_tasks.add_task(
        run_background_processing,
        meeting_id,
        persistent_path,
        stt_profile or "auto",
        meeting.duration,
    )
    
    return service.get_meeting(meeting_id)


@router.post("/{meeting_id}/refresh-summary", response_model=Meeting)
async def refresh_summary_sections(
    meeting_id: str,
    service: MeetingService = Depends(get_meeting_service),
):
    meeting = service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    transcript_text = (meeting.transcript or "").strip()
    if not transcript_text:
        raise HTTPException(status_code=400, detail="Chưa có bản dịch để tạo lại tóm tắt")

    try:
        updated = service.regenerate_summary_sections(meeting_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Không thể tải lại tóm tắt: {str(exc)}") from exc

    if not updated:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return updated


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
    """Background task to download from URL and upload to object storage with progress tracking"""
    
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
        
        # Upload to MinIO with progress
        cloud_audio_url = None
        cloud_video_url = None
        minio_storage = get_minio_storage()

        if minio_storage.is_configured():
            job_tracker.update_progress(job_id, 70, "Đang upload lên MinIO...", "uploading")
            
            # Get file size for progress
            audio_size = os.path.getsize(audio_path)
            
            # Upload audio
            audio_remote = f"audio/{new_meeting.id}.mp3"
            cloud_audio_url = minio_storage.upload_file(audio_path, audio_remote)
            
            if cloud_audio_url:
                job_tracker.update_progress(job_id, 85, "Upload audio hoàn tất", "uploading")
                
                # Upload video if applicable
                if is_video and temp_path and os.path.exists(temp_path):
                    video_ext = os.path.splitext(filename)[1]
                    video_remote = f"video/{new_meeting.id}{video_ext}"
                    cloud_video_url = minio_storage.upload_file(temp_path, video_remote)
                    if cloud_video_url:
                        job_tracker.update_progress(job_id, 95, "Upload video hoàn tất", "uploading")
                    os.remove(temp_path)
            else:
                job_tracker.update_progress(job_id, 85, "Upload MinIO thất bại, dùng local storage", "uploading")
        else:
            job_tracker.update_progress(job_id, 85, "MinIO chưa cấu hình, dùng local storage", "uploading")
        
        # Update database
        final_audio_url = cloud_audio_url if cloud_audio_url else f"/uploads/{audio_filename}"
        update_data = {"audio_url": final_audio_url}
        if cloud_video_url:
            update_data["video_url"] = cloud_video_url
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

STREAM_CHUNK_SIZE = 1024 * 1024


def _media_type_from_name(name: str) -> str:
    lower = (name or "").lower()
    if lower.endswith('.mp4'):
        return 'video/mp4'
    if lower.endswith('.mp3'):
        return 'audio/mpeg'
    if lower.endswith('.mov'):
        return 'video/quicktime'
    if lower.endswith('.wav'):
        return 'audio/wav'
    return 'application/octet-stream'


def _range_not_satisfiable(total_size: int) -> HTTPException:
    return HTTPException(
        status_code=416,
        detail="Requested Range Not Satisfiable",
        headers={"Content-Range": f"bytes */{total_size}"},
    )


def _parse_byte_range(range_header: Optional[str], total_size: int) -> Optional[Tuple[int, int]]:
    if not range_header:
        return None

    if total_size <= 0:
        raise _range_not_satisfiable(0)

    normalized = range_header.strip().lower()
    if not normalized.startswith("bytes="):
        raise _range_not_satisfiable(total_size)

    requested_range = normalized[6:].split(",", 1)[0].strip()
    if "-" not in requested_range:
        raise _range_not_satisfiable(total_size)

    start_str, end_str = requested_range.split("-", 1)

    try:
        if start_str == "":
            suffix_length = int(end_str)
            if suffix_length <= 0:
                raise ValueError("Invalid suffix range")
            start = max(total_size - suffix_length, 0)
            end = total_size - 1
        else:
            start = int(start_str)
            if start < 0 or start >= total_size:
                raise ValueError("Range start out of bounds")
            if end_str == "":
                end = total_size - 1
            else:
                end = int(end_str)
            if end < start:
                raise ValueError("Range end before start")
            end = min(end, total_size - 1)
    except ValueError as exc:
        raise _range_not_satisfiable(total_size) from exc

    return start, end


def _iter_file_range(file_path: str, start: int, end: int) -> Iterator[bytes]:
    with open(file_path, "rb") as media_file:
        media_file.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            read_size = min(STREAM_CHUNK_SIZE, remaining)
            chunk = media_file.read(read_size)
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


def _stream_local_file(file_path: str, media_type: str, range_header: Optional[str]):
    total_size = os.path.getsize(file_path)
    byte_range = _parse_byte_range(range_header, total_size)

    if byte_range is None:
        return FileResponse(
            file_path,
            media_type=media_type,
            filename=os.path.basename(file_path),
            headers={"Accept-Ranges": "bytes"},
        )

    start, end = byte_range
    return StreamingResponse(
        _iter_file_range(file_path, start, end),
        status_code=206,
        media_type=media_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start}-{end}/{total_size}",
            "Content-Length": str(end - start + 1),
        },
    )


def _stream_memory_bytes(file_bytes: bytes, media_type: str, range_header: Optional[str]):
    total_size = len(file_bytes)
    byte_range = _parse_byte_range(range_header, total_size)

    if byte_range is None:
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=media_type,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(total_size),
            },
        )

    start, end = byte_range
    partial = file_bytes[start : end + 1]
    return StreamingResponse(
        io.BytesIO(partial),
        status_code=206,
        media_type=media_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start}-{end}/{total_size}",
            "Content-Length": str(len(partial)),
        },
    )

def extract_storage_object_name(url: str) -> Optional[str]:
    """Extract object key from a MinIO URL."""
    return get_minio_storage().extract_object_name_from_url(url)

@router.get("/{meeting_id}/stream")
async def stream_media(
    meeting_id: str,
    request: Request,
    response: Response,
    service: MeetingService = Depends(get_meeting_service)
):
    """
    Stream audio/video file for a meeting.
    Downloads from MinIO using SDK if needed, or serves local files.
    This ensures proper CORS headers for media playback.
    """
    # Set cache control for media streaming
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    range_header = request.headers.get("range")
    
    meeting = service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Prefer audio_url, fallback to video_url
    media_url = meeting.audio_url or meeting.video_url
    if not media_url:
        raise HTTPException(status_code=404, detail="No media file found for this meeting")
    
    # If it's a local file (starts with /uploads)
    if media_url.startswith('/uploads'):
        relative_path = media_url.replace('/uploads/', '', 1)
        file_name = os.path.basename(relative_path)
        candidates = [
            os.path.join("uploads", relative_path),
            os.path.join("uploads", file_name),
            os.path.join("uploads", "audio", file_name),
            os.path.join("uploads", "videos", file_name),
        ]

        file_path = next((path for path in candidates if os.path.exists(path)), None)
        if file_path:
            media_type = _media_type_from_name(file_path)
            return _stream_local_file(file_path, media_type, range_header)
        raise HTTPException(status_code=404, detail="Local file not found")
    
    # If it's a MinIO URL, download using SDK
    object_name = extract_storage_object_name(media_url)
    if object_name:
        try:
            print(f"[Stream] Downloading from MinIO: {object_name}")
            
            # Download file using MinIO SDK
            minio_storage = get_minio_storage()
            if not minio_storage.is_configured():
                raise HTTPException(status_code=500, detail="MinIO not configured")
            
            file_bytes = minio_storage.download_file_bytes(object_name)
            if not file_bytes:
                raise HTTPException(status_code=404, detail="File not found in MinIO")
            
            print(f"[Stream] Downloaded {len(file_bytes)} bytes from MinIO")

            media_type = _media_type_from_name(object_name)
            return _stream_memory_bytes(file_bytes, media_type, range_header)
        except HTTPException:
            raise
        except Exception as e:
            print(f"[Stream] Error downloading from MinIO: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to stream media: {str(e)}")
    
    # For other external URLs, redirect
    return RedirectResponse(url=media_url)

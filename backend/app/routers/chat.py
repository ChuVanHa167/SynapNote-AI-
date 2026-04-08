from pathlib import Path

import os
import time
import requests
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.models.schemas import ChatRequest, ChatMessage, Meeting
from app.database import get_db
from app.repositories.sql_repos import SqlMeetingRepository

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

router = APIRouter(prefix="/chat", tags=["ai-chat"])

GEMINI_MODEL = "gemini-flash-lite-latest"  # Update to the desired Gemini model name

def _get_gemini_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini_api_key")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    return api_key

def _get_gemini_model_candidates() -> List[str]:
    primary = (os.getenv("GEMINI_MODEL") or GEMINI_MODEL).strip()
    fallback_raw = os.getenv(
        "GEMINI_FALLBACK_MODELS",
        "gemini-flash-lite-latest,gemini-flash-lite-latest",
    )

    models: List[str] = []
    for model in [primary] + [m.strip() for m in fallback_raw.split(",")]:
        if model and model not in models:
            models.append(model)
    return models

def _is_retryable_gemini_status(status_code: int) -> bool:
    return status_code in {429, 500, 502, 503, 504}

def _build_context_from_meetings(meetings: List[Meeting]) -> str:
    """Build context string from multiple meetings for Gemini."""
    if not meetings:
        return "Khong co du lieu cuoc hop nao."

    context_parts = []
    for i, meeting in enumerate(meetings, 1):
        parts = []
        parts.append(f"=== CUOC HOP {i}: {meeting.title} ===")
        parts.append(f"Ngay: {meeting.date}")
        parts.append(f"Trang thai: {meeting.status}")

        if meeting.summary:
            parts.append(f"Tom tat: {meeting.summary}")

        if meeting.transcript:
            # Truncate long transcripts for context window
            transcript = meeting.transcript[:2000] + "..." if len(meeting.transcript) > 2000 else meeting.transcript
            parts.append(f"Noi dung chinh: {transcript}")

        if meeting.decisions:
            decisions = "\n".join([f"- {d}" for d in meeting.decisions])
            parts.append(f"Quyet dinh:\n{decisions}")

        if meeting.action_items:
            actions = "\n".join([f"- {a.task} (nguoi_phu_trach: {a.assignee}, trang_thai: {a.status})" for a in meeting.action_items])
            parts.append(f"Hanh dong:\n{actions}")

        context_parts.append("\n".join(parts))

    return "\n\n".join(context_parts)

def _call_gemini_api(message: str, context: str, system_instruction: Optional[str] = None) -> str:
    """Call Gemini API for chat response."""
    api_key = _get_gemini_api_key()
    max_retries_per_model = max(1, int(os.getenv("GEMINI_RETRY_PER_MODEL", "2")))
    base_delay_seconds = max(0.2, float(os.getenv("GEMINI_RETRY_BASE_DELAY", "1.0")))

    system_prompt = system_instruction or (
        "Ban la tro ly SynapNote toi uu cho Gemini Flash Lite. "
        "Nhiem vu: tra loi cau hoi dua tren du lieu cuoc hop duoc cung cap. "
        "Rang buoc bat buoc: luon tra loi bang tieng Viet, ngan gon, ro rang, dung trong tam. "
        "Khong suy doan. Khong bia du lieu. "
        "Neu nguon du lieu khong co thong tin de tra loi, phai noi ro phan thieu thay vi tu doan."
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"{system_prompt}\n\n"
                            "DU LIEU CUOC HOP (nguon su that):\n"
                            f"{context}\n\n"
                            "CAU HOI NGUOI DUNG:\n"
                            f"{message}\n\n"
                            "Huong dan output: chi tra loi bang tieng Viet; "
                            "co the dung gach dau dong neu can; khong can nhac lai prompt."
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "text/plain",
            "temperature": 0.25,
            "topK": 20,
            "topP": 0.9,
            "maxOutputTokens": 900,
        }
    }

    last_retryable_error = ""
    had_retryable_failure = False

    for model in _get_gemini_model_candidates():
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        for attempt in range(1, max_retries_per_model + 1):
            try:
                resp = requests.post(url, json=payload, timeout=60)
            except requests.exceptions.Timeout:
                had_retryable_failure = True
                last_retryable_error = f"timeout on {model}"
                if attempt < max_retries_per_model:
                    time.sleep(base_delay_seconds * attempt)
                continue
            except requests.exceptions.RequestException as exc:
                had_retryable_failure = True
                last_retryable_error = f"request_error on {model}: {exc}"
                if attempt < max_retries_per_model:
                    time.sleep(base_delay_seconds * attempt)
                continue

            if resp.status_code != 200:
                response_snippet = resp.text[:200]
                if _is_retryable_gemini_status(resp.status_code):
                    had_retryable_failure = True
                    last_retryable_error = f"{resp.status_code} on {model}: {response_snippet}"
                    if attempt < max_retries_per_model:
                        time.sleep(base_delay_seconds * attempt)
                        continue
                    break
                raise HTTPException(status_code=500, detail=f"Gemini API error: {resp.status_code} - {response_snippet}")

            try:
                data = resp.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    last_retryable_error = f"no candidates on {model}"
                    had_retryable_failure = True
                    if attempt < max_retries_per_model:
                        time.sleep(base_delay_seconds * attempt)
                        continue
                    break

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    last_retryable_error = f"empty parts on {model}"
                    had_retryable_failure = True
                    if attempt < max_retries_per_model:
                        time.sleep(base_delay_seconds * attempt)
                        continue
                    break

                text = (parts[0].get("text") or "").strip()
                if text:
                    return text

                last_retryable_error = f"empty text on {model}"
                had_retryable_failure = True
                if attempt < max_retries_per_model:
                    time.sleep(base_delay_seconds * attempt)
                    continue
                break
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                had_retryable_failure = True
                last_retryable_error = f"parse_error on {model}: {exc}"
                if attempt < max_retries_per_model:
                    time.sleep(base_delay_seconds * attempt)
                    continue
                break

    if had_retryable_failure:
        print(f"[chat] Gemini temporary overload after retries: {last_retryable_error}")
        return (
            "He thong AI dang tam thoi qua tai nen chua tra loi duoc ngay luc nay. "
            "Ban vui long thu lai sau 10-30 giay, hoac gui cau hoi ngan gon hon."
        )

    raise HTTPException(status_code=500, detail="Gemini API returned no valid response")

@router.post("/query", response_model=ChatMessage)
async def ask_assistant(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Ask the AI assistant a question about meetings.
    If meeting_id is provided, only that meeting's context is used.
    Otherwise, all meetings are used as context.
    """
    repo = SqlMeetingRepository(db)

    # Get context meetings
    if request.meeting_id:
        meeting = repo.get_by_id(request.meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        meetings_context = [meeting]
    else:
        # Get all meetings for context
        all_meetings = repo.get_all()
        if not all_meetings:
            return ChatMessage(
                role="assistant",
                content="Chua co du lieu cuoc hop nao trong he thong. Ban hay tai len file ghi am de bat dau."
            )
        meetings_context = all_meetings[:5]  # Limit to 5 most recent meetings

    # Build context string
    context = _build_context_from_meetings(meetings_context)

    # Check if we have enough data for AI processing
    has_transcript = any(m.transcript for m in meetings_context)
    has_summary = any(m.summary for m in meetings_context)

    if not has_transcript and not has_summary:
        return ChatMessage(
            role="assistant",
            content="Du lieu AI cua cac cuoc hop chua san sang. Ban hay doi qua trinh xu ly hoan tat hoac thu lai sau."
        )

    # Call Gemini API for intelligent response
    answer = _call_gemini_api(request.message, context)

    return ChatMessage(role="assistant", content=answer)

@router.get("/meetings", response_model=List[Meeting])
async def get_meetings_for_context(db: Session = Depends(get_db)):
    """Get all meetings for the data source dropdown."""
    repo = SqlMeetingRepository(db)
    return repo.get_all()

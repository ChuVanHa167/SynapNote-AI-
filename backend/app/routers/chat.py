import os
import json
import requests
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.schemas import ChatRequest, ChatMessage, Meeting
from app.database import get_db
from app.repositories.sql_repos import SqlMeetingRepository
from app.services.ai_bridge_service import AIBridgeService

router = APIRouter(prefix="/chat", tags=["ai-chat"])

GEMINI_MODEL = "gemini-flash-lite-latest"  # Update to the desired Gemini model name

def _get_gemini_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini_api_key")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    return api_key

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
            actions = "\n".join([f"- {a.task} (assignee: {a.assignee}, status: {a.status})" for a in meeting.action_items])
            parts.append(f"Hanh dong:\n{actions}")

        context_parts.append("\n".join(parts))

    return "\n\n".join(context_parts)

def _call_gemini_api(message: str, context: str, system_instruction: Optional[str] = None) -> str:
    """Call Gemini API for chat response."""
    api_key = _get_gemini_api_key()

    system_prompt = system_instruction or (
        "Ban la tro ly AI thong minh cho SynapNote. "
        "Ban tra loi cau hoi cua nguoi dung dua tren nguoi du lieu cuoc hop duoc cung cap. "
        "Tra loi bang tieng Viet tu nhien, de hieu. "
        "Neu khong co du lieu trong nguoi duoc cung cap, hay noi cho nguoi dung biet."
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"{system_prompt}\n\nNGUOI DU LIEU CUOC HOP:\n{context}\n\nCAU HOI NGUOI DUNG: {message}\n\nTRA LOI:"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1024,
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"

    try:
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Gemini API error: {resp.status_code}")

        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Gemini API request failed: {str(e)}")
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse Gemini response: {str(e)}")

@router.post("/query", response_model=ChatMessage)
async def ask_assistant(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Ask the AI assistant a question about meetings.
    If meeting_id is provided, only that meeting's context is used.
    Otherwise, all meetings are used as context.
    """
    repo = SqlMeetingRepository(db)
    ai_service = AIBridgeService()

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

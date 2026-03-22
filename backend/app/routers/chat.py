from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.schemas import ChatRequest, ChatMessage
from app.database import get_db
from app.repositories.sql_repos import SqlMeetingRepository
from app.services.ai_bridge_service import AIBridgeService

router = APIRouter(prefix="/chat", tags=["ai-chat"])

@router.post("/query", response_model=ChatMessage)
async def ask_assistant(request: ChatRequest, db: Session = Depends(get_db)):
    repo = SqlMeetingRepository(db)
    ai_service = AIBridgeService()

    meeting = repo.get_by_id(request.meeting_id) if request.meeting_id else None
    answer = ai_service.answer_question(request.message, meeting)

    return {"role": "assistant", "content": answer}

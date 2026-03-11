from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatMessage

router = APIRouter(prefix="/chat", tags=["ai-chat"])

@router.post("/query", response_model=ChatMessage)
async def ask_assistant(request: ChatRequest):
    # This simulates RAG approach
    # In reality: It fetches the transcript embeddings from Vector DB (Pinecone) based on request.room_id
    # Then sends the specific chunks to LLM (OpenAI)
    
    context_msg = "Tôi đang tìm kiếm trên toàn bộ dữ liệu."
    if request.meeting_id:
        context_msg = f"Dựa vào bản ghi âm của cuộc họp: {request.meeting_id}."

    mock_reply = f"{context_msg} Bạn vừa hỏi: '{request.message}'. Ngân sách đã được phê duyệt tăng 20%."
    return {"role": "assistant", "content": mock_reply}

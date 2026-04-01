from typing import List
from fastapi import APIRouter
from app.models.schemas import APIKey, IntegrationHook
from app.repositories.mock_repos import MockApiKeyRepository

router = APIRouter(prefix="/integrations", tags=["integrations"])
api_repo = MockApiKeyRepository()

@router.get("/keys", response_model=List[APIKey])
async def list_api_keys():
    return api_repo.get_keys()

@router.post("/webhooks/zoom")
async def zoom_webhook_handler(payload: IntegrationHook):
    # Receives webhook from Zoom when meeting ends to trigger audio download
    return {"status": "success", "message": "Triggered transcription processing"}

@router.post("/webhooks/slack/alert")
async def notify_slack(message: str):
    # Webhook handler config
    return {"status": "sent", "channel": "#general"}

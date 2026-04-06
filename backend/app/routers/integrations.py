from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import models, schemas
import uuid
import json
import secrets

router = APIRouter(prefix="/integrations", tags=["integrations"])

def generate_uuid():
    return str(uuid.uuid4())

def generate_api_key():
    """Tạo API key ngẫu nhiên an toàn"""
    return f"sk_live_{secrets.token_urlsafe(32)}"

# ============ AVAILABLE INTEGRATIONS ============

@router.get("/available", response_model=List[schemas.AvailableIntegration])
async def get_available_integrations(user_id: str, db: Session = Depends(get_db)):
    """Lấy danh sách tất cả tích hợp có sẵn với trạng thái kết nối"""
    # Lấy danh sách integrations đã kết nối của user
    connected = db.query(models.UserIntegration).filter(
        models.UserIntegration.user_id == user_id,
        models.UserIntegration.status == "connected"
    ).all()
    
    connected_providers = {i.provider: i for i in connected}
    
    # Danh sách tất cả providers
    available = [
        {
            "provider": "zoom",
            "provider_name": "Zoom Video Communications",
            "description": "Tự động lấy bản ghi âm từ Zoom Cloud",
            "icon_color": "#2D8CFF",
            "is_connected": "zoom" in connected_providers,
            "status": "connected" if "zoom" in connected_providers else "disconnected"
        },
        {
            "provider": "google",
            "provider_name": "Google Meet & Calendar",
            "description": "Tích hợp Google Meet và Calendar",
            "icon_color": "#4285F4",
            "is_connected": "google" in connected_providers,
            "status": "connected" if "google" in connected_providers else "disconnected"
        },
        {
            "provider": "slack",
            "provider_name": "Slack",
            "description": "Gửi thông báo tóm tắt cuộc họp thẳng vào Slack",
            "icon_color": "#4A154B",
            "is_connected": "slack" in connected_providers,
            "status": "connected" if "slack" in connected_providers else "disconnected"
        },
        {
            "provider": "teams",
            "provider_name": "Microsoft Teams",
            "description": "Tích hợp Microsoft Teams",
            "icon_color": "#6264A7",
            "is_connected": "teams" in connected_providers,
            "status": "connected" if "teams" in connected_providers else "disconnected"
        },
        {
            "provider": "webex",
            "provider_name": "Webex",
            "description": "Tích hợp Cisco Webex",
            "icon_color": "#00BCF2",
            "is_connected": "webex" in connected_providers,
            "status": "connected" if "webex" in connected_providers else "disconnected"
        }
    ]
    
    return available


# ============ USER INTEGRATIONS ============

@router.get("/status", response_model=List[schemas.IntegrationInfo])
async def get_user_integrations(user_id: str, db: Session = Depends(get_db)):
    """Lấy trạng thái tất cả các tích hợp của user"""
    integrations = db.query(models.UserIntegration).filter(
        models.UserIntegration.user_id == user_id
    ).all()
    
    # Danh sách các platform hỗ trợ
    supported_platforms = ["zoom", "slack", "google", "teams", "webex"]
    
    result = []
    connected_platforms = {i.provider: i for i in integrations}
    
    for platform in supported_platforms:
        if platform in connected_platforms:
            integration = connected_platforms[platform]
            settings = json.loads(integration.settings) if integration.settings else {}
            result.append(schemas.IntegrationInfo(
                id=integration.id,
                provider=platform,
                provider_name=integration.provider_name or platform,
                status=integration.status,
                connected_at=integration.created_at,
                last_sync_at=integration.last_sync_at,
                settings=settings,
                webhook_url=integration.webhook_url
            ))
        else:
            # Platform chưa kết nối
            provider_names = {
                "zoom": "Zoom Video Communications",
                "slack": "Slack",
                "google": "Google Meet & Calendar",
                "teams": "Microsoft Teams",
                "webex": "Webex"
            }
            result.append(schemas.IntegrationInfo(
                id="",
                provider=platform,
                provider_name=provider_names.get(platform, platform),
                status="disconnected",
                connected_at=None,
                last_sync_at=None,
                settings=None,
                webhook_url=None
            ))
    
    return result

@router.get("/status/{provider}", response_model=schemas.IntegrationInfo)
async def get_integration_status(provider: str, user_id: str, db: Session = Depends(get_db)):
    """Lấy trạng thái chi tiết một tích hợp"""
    integration = db.query(models.UserIntegration).filter(
        models.UserIntegration.user_id == user_id,
        models.UserIntegration.provider == provider
    ).first()
    
    if not integration:
        return schemas.IntegrationInfo(
            id="",
            provider=provider,
            provider_name=provider,
            status="disconnected",
            connected_at=None,
            last_sync_at=None,
            settings=None,
            webhook_url=None
        )
    
    settings = json.loads(integration.settings) if integration.settings else {}
    
    return schemas.IntegrationInfo(
        id=integration.id,
        provider=integration.provider,
        provider_name=integration.provider_name or provider,
        status=integration.status,
        connected_at=integration.created_at,
        last_sync_at=integration.last_sync_at,
        settings=settings,
        webhook_url=integration.webhook_url
    )

@router.post("/connect/{provider}")
async def connect_integration(
    provider: str,
    user_id: str,
    request: schemas.ConnectIntegrationRequest,
    db: Session = Depends(get_db)
):
    """Kết nối một tích hợp mới"""
    # Kiểm tra provider hợp lệ
    valid_providers = ["zoom", "slack", "google", "teams", "webex"]
    if provider not in valid_providers:
        raise HTTPException(status_code=400, detail=f"Invalid provider. Supported: {valid_providers}")
    
    # Kiểm tra đã kết nối chưa
    existing = db.query(models.UserIntegration).filter(
        models.UserIntegration.user_id == user_id,
        models.UserIntegration.provider == provider
    ).first()
    
    if existing and existing.status == "connected":
        raise HTTPException(status_code=400, detail=f"{provider} is already connected")
    
    # Validate token/config dựa vào provider
    is_valid = await validate_provider_credentials(provider, request)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid credentials for {provider}")
    
    settings = json.dumps(request.config) if request.config else None
    
    # Provider name mapping
    provider_names = {
        "zoom": "Zoom Video Communications",
        "slack": "Slack",
        "google": "Google Meet & Calendar",
        "teams": "Microsoft Teams",
        "webex": "Webex"
    }
    
    if existing:
        # Cập nhật integration hiện có
        existing.status = "connected"
        existing.access_token = request.access_token
        existing.refresh_token = request.refresh_token
        existing.webhook_url = request.webhook_url
        existing.settings = settings
        existing.updated_at = datetime.now()
        existing.last_sync_at = datetime.now()
    else:
        # Tạo integration mới
        integration = models.UserIntegration(
            id=generate_uuid(),
            user_id=user_id,
            provider=provider,
            provider_name=provider_names.get(provider, provider),
            status="connected",
            access_token=request.access_token,
            refresh_token=request.refresh_token,
            webhook_url=request.webhook_url,
            settings=settings,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_sync_at=datetime.now()
        )
        db.add(integration)
    
    db.commit()
    
    return {
        "message": f"{provider} connected successfully",
        "provider": provider,
        "status": "connected"
    }

@router.post("/disconnect/{provider}")
async def disconnect_integration(provider: str, user_id: str, db: Session = Depends(get_db)):
    """Ngắt kết nối một tích hợp"""
    integration = db.query(models.UserIntegration).filter(
        models.UserIntegration.user_id == user_id,
        models.UserIntegration.provider == provider
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail=f"{provider} integration not found")
    
    # Xóa access token và cập nhật status
    integration.status = "disconnected"
    integration.access_token = None
    integration.refresh_token = None
    integration.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "message": f"{provider} disconnected successfully",
        "provider": provider,
        "status": "disconnected"
    }

@router.post("/sync/{provider}")
async def sync_integration(provider: str, user_id: str, db: Session = Depends(get_db)):
    """Đồng bộ dữ liệu từ tích hợp"""
    integration = db.query(models.UserIntegration).filter(
        models.UserIntegration.user_id == user_id,
        models.UserIntegration.provider == provider,
        models.UserIntegration.status == "connected"
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail=f"{provider} is not connected")
    
    # Thực hiện đồng bộ (trong thực tế sẽ gọi API của provider)
    integration.last_sync_at = datetime.now()
    integration.updated_at = datetime.now()
    db.commit()
    
    # Giả lập kết quả đồng bộ
    synced_data = {
        "zoom": {"meetings": 5, "recordings": 3},
        "slack": {"messages": 150, "channels": 3},
        "google": {"meetings": 8, "recordings": 2},
        "teams": {"meetings": 3, "recordings": 1},
    }
    
    return {
        "message": f"{provider} synced successfully",
        "synced_at": integration.last_sync_at.isoformat(),
        "data": synced_data.get(provider, {})
    }

# ============ API KEYS ============

@router.get("/api-keys", response_model=List[schemas.APIKey])
async def list_api_keys(user_id: str, db: Session = Depends(get_db)):
    """Lấy danh sách API keys của user"""
    keys = db.query(models.ApiKey).filter(
        models.ApiKey.user_id == user_id
    ).all()
    
    return [
        schemas.APIKey(
            id=k.id,
            key=f"{k.api_key[:15]}...{k.api_key[-4:]}",  # Mask key for security
            name=k.name
        ) for k in keys
    ]

@router.post("/api-keys", response_model=schemas.APIKey)
async def create_api_key(user_id: str, request: schemas.APIKeyCreate, db: Session = Depends(get_db)):
    """Tạo API key mới"""
    new_key = generate_api_key()
    
    api_key = models.ApiKey(
        id=generate_uuid(),
        user_id=user_id,
        api_key=new_key,
        name=request.name
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    # Trả về key đầy đủ chỉ một lần
    return schemas.APIKey(
        id=api_key.id,
        key=api_key.api_key,
        name=api_key.name
    )

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: str, user_id: str, db: Session = Depends(get_db)):
    """Thu hồi API key"""
    api_key = db.query(models.ApiKey).filter(
        models.ApiKey.id == key_id,
        models.ApiKey.user_id == user_id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(api_key)
    db.commit()
    
    return {"message": "API key revoked successfully"}

# ============ WEBHOOKS ============

@router.post("/webhooks/{platform}")
async def handle_platform_webhook(platform: str, payload: dict, db: Session = Depends(get_db)):
    """Nhận webhook từ các platform (Zoom, Slack, etc.)"""
    # Xác thực webhook (trong thực tế sẽ verify signature)
    
    if platform == "zoom":
        # Xử lý Zoom webhook
        event_type = payload.get("event")
        if event_type == "recording.completed":
            # Tự động tải và xử lý recording
            return {
                "status": "success",
                "message": "Zoom recording will be processed",
                "recording_id": payload.get("payload", {}).get("object", {}).get("uuid")
            }
    
    elif platform == "slack":
        # Xử lý Slack webhook
        return {
            "status": "success",
            "message": "Slack notification processed"
        }
    
    return {"status": "received", "platform": platform}

# ============ HELPER FUNCTIONS ============

async def validate_provider_credentials(provider: str, request: schemas.ConnectIntegrationRequest) -> bool:
    """Validate credentials cho từng provider"""
    
    if provider == "zoom":
        # Trong thực tế sẽ gọi Zoom API để validate token
        return bool(request.access_token and len(request.access_token) > 10)
    
    elif provider == "slack":
        # Validate Slack token
        return bool(request.access_token and request.access_token.startswith("xoxb-"))
    
    elif provider == "google":
        # Validate Google OAuth token
        return bool(request.access_token)
    
    elif provider == "teams":
        # Validate Microsoft Teams token
        return bool(request.access_token)
    
    elif provider == "webex":
        # Validate Webex token
        return bool(request.access_token)
    
    return False

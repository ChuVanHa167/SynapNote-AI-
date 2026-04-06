from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import schemas
from app.models.models import UserSubscription, SubscriptionPlan, BillingHistory, PaymentMethod, UsageStats, UserIntegration
from app.repositories.sql_repos import SqlUserRepository
from app.services.auth_service import get_current_user_email

router = APIRouter(prefix="/billing", tags=["billing"])

# ===== SEED DATA =====
def seed_subscription_plans(db: Session):
    """Seed default subscription plans if none exist"""
    existing = db.query(SubscriptionPlan).first()
    if existing:
        return
    
    plans = [
        SubscriptionPlan(
            name="Starter",
            price_vnd=0,
            meetings_limit=10,
            audio_hours_limit=5,
            features='["10 cuộc họp/tháng", "5 giờ audio", "Tóm tắt cơ bản"]',
            is_active=1
        ),
        SubscriptionPlan(
            name="Pro",
            price_vnd=500000,
            meetings_limit=100,
            audio_hours_limit=50,
            features='["100 cuộc họp/tháng", "50 giờ audio", "Phân tích AI nâng cao", "Xuất PDF/Word"]',
            is_active=1
        ),
        SubscriptionPlan(
            name="Enterprise",
            price_vnd=-1,  # Contact sales
            meetings_limit=999999,
            audio_hours_limit=999999,
            features='["Không giới hạn cuộc họp", "Không giới hạn audio", "API access", "Hỗ trợ 24/7"]',
            is_active=1
        )
    ]
    for plan in plans:
        db.add(plan)
    db.commit()

# ===== BILLING DASHBOARD =====
@router.get("/dashboard", response_model=schemas.BillingDashboard)
async def get_billing_dashboard(
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """Get complete billing dashboard data for a user"""
    seed_subscription_plans(db)
    
    # Get user
    user_repo = SqlUserRepository(db)
    user = user_repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get current subscription
    subscription = db.query(UserSubscription).filter(
        UserSubscription.user_id == user.id
    ).order_by(UserSubscription.created_at.desc()).first()
    
    # Get or create default subscription (Pro trial)
    if not subscription:
        pro_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == "Pro").first()
        if pro_plan:
            subscription = UserSubscription(
                user_id=user.id,
                plan_id=pro_plan.id,
                status="active",
                current_period_start=datetime.now(),
                current_period_end=datetime.now() + timedelta(days=30),
                cancel_at_period_end=0
            )
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
    
    # Get plan details
    current_plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == subscription.plan_id
    ).first() if subscription else None
    
    # Get current month usage
    current_month = datetime.now()
    usage = db.query(UsageStats).filter(
        UsageStats.user_id == user.id,
        UsageStats.month == current_month.month,
        UsageStats.year == current_month.year
    ).first()
    
    if not usage:
        usage = UsageStats(
            user_id=user.id,
            month=current_month.month,
            year=current_month.year,
            meetings_count=47,  # Demo data
            audio_hours_used=24.5,
            ai_processing_count=12
        )
        db.add(usage)
        db.commit()
    
    # Get payment method
    payment_method = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == user.id,
        PaymentMethod.is_default == 1
    ).first()
    
    # Get billing history
    history = db.query(BillingHistory).filter(
        BillingHistory.user_id == user.id
    ).order_by(BillingHistory.created_at.desc()).limit(10).all()
    
    # Get available plans
    all_plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == 1).all()
    
    return schemas.BillingDashboard(
        current_subscription=schemas.CurrentSubscription(
            id=subscription.id if subscription else "",
            plan_name=current_plan.name if current_plan else "Pro",
            price_vnd=current_plan.price_vnd if current_plan else 500000,
            status=subscription.status if subscription else "active",
            current_period_start=subscription.current_period_start if subscription else datetime.now(),
            current_period_end=subscription.current_period_end if subscription else datetime.now() + timedelta(days=30),
            cancel_at_period_end=bool(subscription.cancel_at_period_end) if subscription else False
        ),
        usage_stats=schemas.UsageStats(
            meetings_count=usage.meetings_count if usage else 0,
            meetings_limit=current_plan.meetings_limit if current_plan else 100,
            audio_hours_used=usage.audio_hours_used if usage else 0,
            audio_hours_limit=current_plan.audio_hours_limit if current_plan else 50,
            ai_processing_count=usage.ai_processing_count if usage else 0,
            ai_processing_limit=None  # Unlimited for Pro
        ),
        payment_method=schemas.PaymentMethod(
            id=payment_method.id,
            type=payment_method.type,
            provider=payment_method.provider,
            last4=payment_method.last4,
            expiry_month=payment_method.expiry_month,
            expiry_year=payment_method.expiry_year,
            is_default=bool(payment_method.is_default)
        ) if payment_method else None,
        billing_history=[
            schemas.BillingHistoryItem(
                id=h.id,
                amount_vnd=h.amount_vnd,
                description=h.description,
                status=h.status,
                created_at=h.created_at,
                invoice_url=h.invoice_url
            ) for h in history
        ],
        available_plans=[
            schemas.SubscriptionPlan(
                id=p.id,
                name=p.name,
                price_vnd=p.price_vnd,
                billing_cycle=p.billing_cycle,
                meetings_limit=p.meetings_limit,
                audio_hours_limit=p.audio_hours_limit,
                features=eval(p.features) if p.features else [],
                is_active=bool(p.is_active)
            ) for p in all_plans
        ]
    )

# ===== SUBSCRIPTION MANAGEMENT =====
@router.post("/subscribe/{plan_id}")
async def subscribe_to_plan(
    plan_id: str,
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """Subscribe user to a plan"""
    user_repo = SqlUserRepository(db)
    user = user_repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Cancel existing subscription if any
    existing = db.query(UserSubscription).filter(
        UserSubscription.user_id == user.id,
        UserSubscription.status == "active"
    ).first()
    
    if existing:
        existing.status = "cancelled"
        db.commit()
    
    # Create new subscription
    new_sub = UserSubscription(
        user_id=user.id,
        plan_id=plan.id,
        status="active",
        current_period_start=datetime.now(),
        current_period_end=datetime.now() + timedelta(days=30),
        cancel_at_period_end=0
    )
    db.add(new_sub)
    db.commit()
    
    # Create billing record
    if plan.price_vnd > 0:
        billing = BillingHistory(
            user_id=user.id,
            amount_vnd=plan.price_vnd,
            description=f"{plan.name} - Tháng {datetime.now().month}/{datetime.now().year}",
            status="success"
        )
        db.add(billing)
        db.commit()
    
    return {"message": f"Subscribed to {plan.name} successfully"}

@router.post("/cancel")
async def cancel_subscription(
    request: schemas.CancelSubscriptionRequest,
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """Cancel current subscription"""
    user_repo = SqlUserRepository(db)
    user = user_repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    subscription = db.query(UserSubscription).filter(
        UserSubscription.user_id == user.id,
        UserSubscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    if request.cancel_at_period_end:
        subscription.cancel_at_period_end = 1
    else:
        subscription.status = "cancelled"
    
    db.commit()
    
    return {"message": "Subscription cancelled successfully"}

# ===== PAYMENT METHODS =====
@router.get("/payment-methods", response_model=List[schemas.PaymentMethod])
async def get_payment_methods(
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """Get user's payment methods"""
    user_repo = SqlUserRepository(db)
    user = user_repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    methods = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == user.id,
        PaymentMethod.is_active == 1
    ).all()
    
    return [
        schemas.PaymentMethod(
            id=m.id,
            type=m.type,
            provider=m.provider,
            last4=m.last4,
            expiry_month=m.expiry_month,
            expiry_year=m.expiry_year,
            is_default=bool(m.is_default)
        ) for m in methods
    ]

@router.post("/payment-methods")
async def add_payment_method(
    method: schemas.PaymentMethod,
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """Add new payment method"""
    user_repo = SqlUserRepository(db)
    user = user_repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Unset default for existing methods
    if method.is_default:
        db.query(PaymentMethod).filter(
            PaymentMethod.user_id == user.id
        ).update({"is_default": 0})
    
    new_method = PaymentMethod(
        user_id=user.id,
        type=method.type,
        provider=method.provider,
        last4=method.last4,
        expiry_month=method.expiry_month,
        expiry_year=method.expiry_year,
        is_default=1 if method.is_default else 0
    )
    db.add(new_method)
    db.commit()
    
    return {"message": "Payment method added successfully"}

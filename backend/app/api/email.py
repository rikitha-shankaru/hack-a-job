from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import EmailSendRequest, EmailSendResponse
from app.services.email_service import EmailService
from app.models import User, TailoredAsset

router = APIRouter()

@router.post("/send", response_model=EmailSendResponse)
async def send_email(
    request: EmailSendRequest,
    db: Session = Depends(get_db)
):
    """Send tailored assets via email"""
    try:
        # Validate user and assets exist
        user = db.query(User).filter(User.id == request.userId).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        assets = db.query(TailoredAsset).filter(TailoredAsset.id == request.assetsId).first()
        if not assets:
            raise HTTPException(status_code=404, detail="Assets not found")
        
        if assets.user_id != user.id:
            raise HTTPException(status_code=403, detail="Assets do not belong to user")
        
        # Send email
        service = EmailService()
        await service.send_assets_email(user, assets)
        
        # Update status
        assets.status = "emailed"
        db.commit()
        
        return EmailSendResponse(status="sent")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


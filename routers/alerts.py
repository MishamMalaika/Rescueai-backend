from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, get_admin_user
import models, schemas
from datetime import datetime

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# ─── Create Alert ─────────────────────────────────────────────
@router.post("/", response_model=schemas.AlertResponse)
def create_alert(alert: schemas.AlertCreate, db: Session = Depends(get_db)):
    new_alert = models.Alert(
        alert_type = alert.alert_type,
        confidence = alert.confidence,
        area       = alert.area,
        camera_id  = alert.camera_id,
        user_id    = alert.user_id,
        video_path = alert.video_path
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return new_alert

# ─── Get All Alerts — Admin ───────────────────────────────────
@router.get("/", response_model=list[schemas.AlertResponse])
def get_all_alerts(db: Session = Depends(get_db), current_user: models.User = Depends(get_admin_user)):
    return db.query(models.Alert).order_by(models.Alert.created_at.desc()).all()

# ─── Get My Area Alerts — NGO ─────────────────────────────────
@router.get("/my", response_model=list[schemas.AlertResponse])
def get_my_alerts(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Alert).filter(
        models.Alert.area == current_user.area
    ).order_by(models.Alert.created_at.desc()).all()

# ─── Get Single Alert ─────────────────────────────────────────
@router.get("/{alert_id}", response_model=schemas.AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

# ─── Delete Alert — Admin ─────────────────────────────────────
@router.delete("/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_admin_user)):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()
    return {"message": "Alert deleted successfully"}
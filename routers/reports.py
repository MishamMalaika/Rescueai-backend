from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, get_admin_user
import models, schemas
from datetime import datetime

router = APIRouter(prefix="/reports", tags=["Reports"])

# ─── Get All Reports — Admin ──────────────────────────────────
@router.get("/", response_model=list[schemas.ReportResponse])
def get_all_reports(db: Session = Depends(get_db), current_user: models.User = Depends(get_admin_user)):
    return db.query(models.Report).order_by(models.Report.date.desc()).all()

# ─── Get My Area Reports — NGO ────────────────────────────────
@router.get("/my", response_model=list[schemas.ReportResponse])
def get_my_reports(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Report).filter(
        models.Report.area == current_user.area
    ).order_by(models.Report.date.desc()).all()

# ─── Get Rescues — All ────────────────────────────────────────
@router.get("/rescues", response_model=list[schemas.RescueResponse])
def get_rescues(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role == "admin":
        return db.query(models.Rescue).order_by(models.Rescue.created_at.desc()).all()
    return db.query(models.Rescue).filter(
        models.Rescue.user_id == current_user.id
    ).order_by(models.Rescue.created_at.desc()).all()

# ─── Create Rescue ────────────────────────────────────────────
@router.post("/rescues", response_model=schemas.RescueResponse)
def create_rescue(rescue: schemas.RescueCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # RES-ID generate karo
    count = db.query(models.Rescue).count()
    rescue_id = f"RES-{count + 1}"

    new_rescue = models.Rescue(
        rescue_id  = rescue_id,
        location   = rescue.location,
        status     = "pending",
        alert_id   = rescue.alert_id,
        user_id    = current_user.id
    )
    db.add(new_rescue)
    db.commit()
    db.refresh(new_rescue)
    return new_rescue

# ─── Update Rescue Status ─────────────────────────────────────
@router.patch("/rescues/{rescue_id}")
def update_rescue_status(rescue_id: int, status: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    rescue = db.query(models.Rescue).filter(models.Rescue.id == rescue_id).first()
    if not rescue:
        raise HTTPException(status_code=404, detail="Rescue not found")
    rescue.status = status
    db.commit()
    return {"message": f"Rescue status updated to {status}"}
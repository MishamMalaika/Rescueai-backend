from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, get_admin_user
import models, schemas

router = APIRouter(prefix="/cameras", tags=["Cameras"])

# ─── Add Camera — Admin Only ──────────────────────────────────
@router.post("/", response_model=schemas.CameraResponse)
def add_camera(camera: schemas.CameraCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_admin_user)):
    new_camera = models.Camera(
        name       = camera.name,
        location   = camera.location,
        stream_url = camera.stream_url,
        area       = camera.area
    )
    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)
    return new_camera

@router.get("/", response_model=list[schemas.CameraResponse])
def get_all_cameras(db: Session = Depends(get_db), current_user: models.User = Depends(get_admin_user)):
    return db.query(models.Camera).all()

@router.get("/my", response_model=list[schemas.CameraResponse])
def get_my_cameras(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Camera).filter(
        models.Camera.area == current_user.area
    ).all()

@router.delete("/{camera_id}")
def delete_camera(camera_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_admin_user)):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    db.delete(camera)
    db.commit()
    return {"message": "Camera deleted successfully"}

@router.patch("/{camera_id}/toggle")
def toggle_camera(camera_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_admin_user)):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    camera.is_active = not camera.is_active
    db.commit()
    return {"message": f"Camera {'activated' if camera.is_active else 'deactivated'}"}
from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import engine, get_db
from auth import verify_password, create_access_token
from routers import users, alerts, cameras, reports
from services.injury_service import detect_injury, detect_injury_image
from services.limping_service import detect_limping
import models, schemas
import shutil
import uuid
import os
import cv2

# ─── Database Tables Create ───────────────────────────────────
models.Base.metadata.create_all(bind=engine)

# ─── App ──────────────────────────────────────────────────────
app = FastAPI(title="RescueAI API", version="1.0.0")

# ─── CORS — Pehle ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Uploads Folder ───────────────────────────────────────────
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ─── Routers ──────────────────────────────────────────────────
app.include_router(users.router)
app.include_router(alerts.router)
app.include_router(cameras.router)
app.include_router(reports.router)

# ─── Frame Save Function ──────────────────────────────────────
def save_detection_frame(video_path: str, output_path: str):
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2)
    ret, frame = cap.read()
    cap.release()
    if ret:
        cv2.imwrite(output_path, frame)
        return output_path
    return None

# ─── Login ────────────────────────────────────────────────────
@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

# ─── Video Upload + Detection ─────────────────────────────────
@app.post("/detect")
async def detect(
    file: UploadFile = File(...),
    camera_id: int = 1,
    area: str = "Unknown",
    db: Session = Depends(get_db)
):
    file_ext  = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = f"uploads/{file_name}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    injury_result  = detect_injury(file_path)
    limping_result = detect_limping(file_path)

    injured = injury_result["injured"]
    limping = limping_result["limping"]

    if injured and limping:
        alert_type = "both"
    elif injured:
        alert_type = "injury"
    elif limping:
        alert_type = "limping"
    else:
        alert_type = None

    # ─── Frame Screenshot Save ────────────────────────────────
    thumb_name = f"{uuid.uuid4()}_thumb.jpg"
    thumb_path = f"uploads/{thumb_name}"
    save_detection_frame(file_path, thumb_path)

    if alert_type:
        camera = db.query(models.Camera).filter(
            models.Camera.id == camera_id
        ).first()

        new_alert = models.Alert(
            alert_type = alert_type,
            confidence = injury_result["confidence"],
            area       = area,
            camera_id  = camera.id if camera else None,
            video_path = file_path,
            image_path = thumb_path,  # ← detection frame
        )
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)

    return {
        "injury":      injury_result,
        "limping":     limping_result,
        "alert_type":  alert_type,
        "alert_saved": alert_type is not None,
        "video_path":  file_path,
        "image_path":  thumb_path,
    }

# ─── Image Upload + Injury Detection ──────────────────────────
@app.post("/detect-image")
async def detect_image(
    file: UploadFile = File(...),
    camera_id: int = 1,
    area: str = "Unknown",
    db: Session = Depends(get_db)
):
    file_ext  = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = f"uploads/{file_name}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    injury_result = detect_injury_image(file_path)
    alert_type = "injury" if injury_result["injured"] else None

    if alert_type:
        camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
        new_alert = models.Alert(
            alert_type = alert_type,
            confidence = injury_result["confidence"],
            area       = area,
            camera_id  = camera.id if camera else None,
            video_path = file_path,
            image_path = file_path,  # ← image hi thumbnail hai
        )
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)

    return {
        "injury":      injury_result,
        "alert_type":  alert_type,
        "alert_saved": alert_type is not None,
        "image_path":  file_path,
    }

# ─── Health Check ─────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "RescueAI Backend Running ✅"}
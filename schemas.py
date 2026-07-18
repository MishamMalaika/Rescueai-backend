from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ─── User Schemas ─────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "ngo"
    area: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    area: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

# ─── Camera Schemas ───────────────────────────────────────────
class CameraCreate(BaseModel):
    name: str
    location: str
    stream_url: str
    area: str

class CameraResponse(BaseModel):
    id: int
    name: str
    location: str
    stream_url: str
    area: str
    is_active: bool

    class Config:
        from_attributes = True

# ─── Alert Schemas ────────────────────────────────────────────
class AlertCreate(BaseModel):
    alert_type: str
    confidence: Optional[float]
    area: str
    camera_id: int
    user_id: Optional[int]
    video_path: Optional[str]
    image_path: Optional[str] = None  # ← add kiya

class AlertResponse(BaseModel):
    id: int
    alert_type: str
    confidence: Optional[float]
    area: str
    camera_id: Optional[int]
    video_path: Optional[str]
    image_path: Optional[str] = None  # ← add kiya
    created_at: datetime

    class Config:
        from_attributes = True

# ─── Report Schemas ───────────────────────────────────────────
class ReportResponse(BaseModel):
    id: int
    area: str
    total_alerts: int
    injury_count: int
    limping_count: int
    date: datetime

    class Config:
        from_attributes = True

# ─── Token Schema ─────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str

# ─── Rescue Schemas ───────────────────────────────────────────
class RescueCreate(BaseModel):
    location: str
    alert_id: Optional[int] = None

class RescueResponse(BaseModel):
    id: int
    rescue_id: str
    location: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
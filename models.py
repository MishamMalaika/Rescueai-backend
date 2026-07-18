from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    email       = Column(String, unique=True, index=True, nullable=False)
    password    = Column(String, nullable=False)
    role        = Column(String, default="ngo")
    area        = Column(String, nullable=True)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    alerts      = relationship("Alert", back_populates="user")

class Camera(Base):
    __tablename__ = "cameras"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    location    = Column(String, nullable=False)
    stream_url  = Column(String, nullable=False)
    area        = Column(String, nullable=False)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    alerts      = relationship("Alert", back_populates="camera")

class Alert(Base):
    __tablename__ = "alerts"

    id            = Column(Integer, primary_key=True, index=True)
    alert_type    = Column(String, nullable=False)
    confidence    = Column(Float, nullable=True)
    area          = Column(String, nullable=False)
    camera_id     = Column(Integer, ForeignKey("cameras.id"), nullable=True)
    user_id       = Column(Integer, ForeignKey("users.id"))
    video_path    = Column(String, nullable=True)
    image_path    = Column(String, nullable=True)  # ← detection frame screenshot
    created_at    = Column(DateTime, default=datetime.utcnow)

    camera        = relationship("Camera", back_populates="alerts")
    user          = relationship("User", back_populates="alerts")

class Report(Base):
    __tablename__ = "reports"

    id              = Column(Integer, primary_key=True, index=True)
    area            = Column(String, nullable=False)
    total_alerts    = Column(Integer, default=0)
    injury_count    = Column(Integer, default=0)
    limping_count   = Column(Integer, default=0)
    date            = Column(DateTime, default=datetime.utcnow)

class Rescue(Base):
    __tablename__ = "rescues"

    id          = Column(Integer, primary_key=True, index=True)
    rescue_id   = Column(String, nullable=False)
    location    = Column(String, nullable=False)
    status      = Column(String, default="pending")
    alert_id    = Column(Integer, ForeignKey("alerts.id"))
    user_id     = Column(Integer, ForeignKey("users.id"))
    created_at  = Column(DateTime, default=datetime.utcnow)
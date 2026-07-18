from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from auth import hash_password, get_current_user, get_admin_user
import models, schemas

router = APIRouter(prefix="/users", tags=["Users"])

# ─── Register ─────────────────────────────────────────────────
@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = models.User(
        name     = user.name,
        email    = user.email,
        password = hash_password(user.password[:72]),
        role     = user.role,
        area     = user.area
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# ─── Get All Users — Admin Only ───────────────────────────────
@router.get("/", response_model=list[schemas.UserResponse])
def get_users(db: Session = Depends(get_db), current_user: models.User = Depends(get_admin_user)):
    return db.query(models.User).all()

# ─── Get My Profile ───────────────────────────────────────────
@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# ─── Update User — Admin Only ─────────────────────────────────
@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, updated: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_admin_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.name  = updated.name
    user.email = updated.email
    user.role  = updated.role
    user.area  = updated.area
    if updated.password:
        user.password = hash_password(updated.password[:72])
    db.commit()
    db.refresh(user)
    return user

# ─── Delete User — Admin Only ─────────────────────────────────
@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_admin_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Admin doosre admin ko delete nahi kar sakta — sirf khud ko kar sakta hai
    if user.role == "admin" and user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete another admin")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
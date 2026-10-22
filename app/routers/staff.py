from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Staff, StaffRole, User
from app.schemas import StaffCreate, StaffUpdate, StaffResponse, StaffRoleResponse
from app.auth import get_current_admin, get_password_hash

router = APIRouter(prefix="/staff", tags=["Staff Management"])

@router.get("/roles", response_model=List[StaffRoleResponse])
def get_staff_roles(db: Session = Depends(get_db)):
    return db.query(StaffRole).all()

@router.get("", response_model=List[StaffResponse])
@router.get("/", response_model=List[StaffResponse])
def get_staff_members(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(Staff).order_by(Staff.created_at.desc()).all()

from app.google_drive import normalize_image_url

@router.post("", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    staff_in: StaffCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    existing = db.query(Staff).filter(Staff.email == staff_in.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Staff email already exists")

    role = db.query(StaffRole).filter(StaffRole.id == staff_in.role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role ID")

    staff = Staff(
        name=staff_in.name,
        email=staff_in.email,
        phone=staff_in.phone,
        hashed_password=get_password_hash(staff_in.password),
        role_id=staff_in.role_id,
        joining_date=staff_in.joining_date,
        image_url=normalize_image_url(staff_in.image_url or ""),
        published=staff_in.published
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff

@router.put("/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: str,
    staff_in: StaffUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")

    if staff_in.name is not None:
        staff.name = staff_in.name
    if staff_in.email is not None:
        staff.email = staff_in.email
    if staff_in.phone is not None:
        staff.phone = staff_in.phone
    if staff_in.role_id is not None:
        role = db.query(StaffRole).filter(StaffRole.id == staff_in.role_id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role ID")
        staff.role_id = staff_in.role_id
    if staff_in.joining_date is not None:
        staff.joining_date = staff_in.joining_date
    if staff_in.image_url is not None:
        staff.image_url = normalize_image_url(staff_in.image_url)
    if staff_in.published is not None:
        staff.published = staff_in.published

    db.commit()
    db.refresh(staff)
    return staff

@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff(
    staff_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")

    db.delete(staff)
    db.commit()
    return None

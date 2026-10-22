from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Coupon, User
from app.schemas import CouponCreate, CouponUpdate, CouponResponse
from app.auth import get_current_admin

router = APIRouter(prefix="/coupons", tags=["Coupons"])

@router.get("", response_model=List[CouponResponse])
@router.get("/", response_model=List[CouponResponse])
def get_coupons(published_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(Coupon)
    if published_only:
        query = query.filter(Coupon.published == True)
    return query.order_by(Coupon.created_at.desc()).all()

@router.get("/validate/{code}", response_model=CouponResponse)
def validate_coupon(code: str, db: Session = Depends(get_db)):
    coupon = db.query(Coupon).filter(Coupon.code.ilike(code)).first()
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid coupon code")
    if not coupon.published:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon is inactive")
    return coupon

from app.google_drive import normalize_image_url

@router.post("", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon(
    coupon_in: CouponCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    existing = db.query(Coupon).filter(Coupon.code.ilike(coupon_in.code)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon code already exists")

    coupon = Coupon(
        code=coupon_in.code.upper(),
        campaign_name=coupon_in.campaign_name,
        discount_type=coupon_in.discount_type,
        discount_value=coupon_in.discount_value,
        start_date=coupon_in.start_date,
        end_date=coupon_in.end_date,
        image_url=normalize_image_url(coupon_in.image_url or ""),
        published=coupon_in.published
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon

@router.put("/{coupon_id}", response_model=CouponResponse)
def update_coupon(
    coupon_id: str,
    coupon_in: CouponUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")

    if coupon_in.code is not None:
        coupon.code = coupon_in.code.upper()
    if coupon_in.campaign_name is not None:
        coupon.campaign_name = coupon_in.campaign_name
    if coupon_in.discount_type is not None:
        coupon.discount_type = coupon_in.discount_type
    if coupon_in.discount_value is not None:
        coupon.discount_value = coupon_in.discount_value
    if coupon_in.start_date is not None:
        coupon.start_date = coupon_in.start_date
    if coupon_in.end_date is not None:
        coupon.end_date = coupon_in.end_date
    if coupon_in.image_url is not None:
        coupon.image_url = normalize_image_url(coupon_in.image_url)
    if coupon_in.published is not None:
        coupon.published = coupon_in.published

    db.commit()
    db.refresh(coupon)
    return coupon

@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coupon(
    coupon_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")

    db.delete(coupon)
    db.commit()
    return None

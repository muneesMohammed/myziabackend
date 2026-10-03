from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, func
from app.database import get_db
from app.models import User, Order
from app.schemas import UserResponse, UserRegister
from app.auth import get_password_hash, get_current_admin

router = APIRouter(prefix="/customers", tags=["Customers"])

def format_customer_response(user: User) -> dict:
    orders = user.orders if user.orders is not None else []
    total_orders = len(orders)
    total_spent = sum(o.total_amount for o in orders if o.total_amount)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone or "",
        "address": user.address or "",
        "role": user.role,
        "is_active": user.is_active,
        "total_orders": total_orders,
        "total_spent": round(total_spent, 2),
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

@router.get("", response_model=List[dict])
@router.get("/", response_model=List[dict])
def get_customers(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(User).options(joinedload(User.orders)).filter(User.role == "customer")
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.name.ilike(pattern),
                User.email.ilike(pattern),
                User.phone.ilike(pattern)
            )
        )
    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    return [format_customer_response(u) for u in users]

@router.get("/{customer_id}", response_model=dict)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == customer_id, User.role == "customer").first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    resp = format_customer_response(user)
    orders = db.query(Order).filter(Order.customer_id == user.id).order_by(desc(Order.created_at)).all()
    resp["orders"] = [
        {
            "id": o.id,
            "invoice_no": o.invoice_no,
            "status": o.status,
            "total_amount": o.total_amount,
            "order_time": o.order_time
        }
        for o in orders
    ]
    return resp

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_customer(user_in: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")

    user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        phone=user_in.phone,
        address=user_in.address,
        role="customer",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return format_customer_response(user)

@router.put("/{customer_id}", response_model=dict)
def update_customer(customer_id: str, name: Optional[str] = None, phone: Optional[str] = None, address: Optional[str] = None, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == customer_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    if name:
        user.name = name
    if phone is not None:
        user.phone = phone
    if address is not None:
        user.address = address

    db.commit()
    db.refresh(user)
    return format_customer_response(user)

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: str, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == customer_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    db.delete(user)
    db.commit()
    return None

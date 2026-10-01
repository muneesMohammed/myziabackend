from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Staff
from app.schemas import UserRegister, UserLogin, UserResponse, Token
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserRegister, db: Session = Depends(get_db)):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
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

    access_token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
    return Token(access_token=access_token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=Token)
def login_user(user_in: UserLogin, db: Session = Depends(get_db)):
    # Check User
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        # Check Staff table if not in User table
        staff = db.query(Staff).filter(Staff.email == user_in.email).first()
        if staff and verify_password(user_in.password, staff.hashed_password):
            access_token = create_access_token(data={"sub": staff.id, "email": staff.email, "role": "admin"})
            user_resp = UserResponse(
                id=staff.id,
                name=staff.name,
                email=staff.email,
                phone=staff.phone,
                role="admin",
                is_active=staff.published,
                created_at=staff.created_at
            )
            return Token(access_token=access_token, user=user_resp)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is disabled")

    access_token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
    return Token(access_token=access_token, user=UserResponse.model_validate(user))


@router.post("/admin-login", response_model=Token)
def admin_login(user_in: UserLogin, db: Session = Depends(get_db)):
    # Check Staff table
    staff = db.query(Staff).filter(Staff.email == user_in.email).first()
    if staff and verify_password(user_in.password, staff.hashed_password):
        access_token = create_access_token(data={"sub": staff.id, "email": staff.email, "role": "admin"})
        user_resp = UserResponse(
            id=staff.id,
            name=staff.name,
            email=staff.email,
            phone=staff.phone,
            role="admin",
            is_active=staff.published,
            created_at=staff.created_at
        )
        return Token(access_token=access_token, user=user_resp)

    # Check User table with admin role
    user = db.query(User).filter(User.email == user_in.email, User.role.in_(["admin", "super_admin"])).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
    return Token(access_token=access_token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Review, Product, User
from app.schemas import ReviewCreate, ReviewResponse
from app.auth import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.get("", response_model=List[ReviewResponse])
@router.get("/", response_model=List[ReviewResponse])
def get_reviews(product_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Review)
    if product_id:
        query = query.filter(Review.product_id == product_id)
    return query.order_by(Review.created_at.desc()).all()

@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == review_in.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    date_str = datetime.utcnow().strftime("%Y-%m-%d")

    review = Review(
        product_id=review_in.product_id,
        user_name=current_user.name or review_in.user_name,
        content=review_in.content,
        rating=review_in.rating,
        date=date_str
    )
    db.add(review)

    # Update product average rating
    all_reviews = db.query(Review).filter(Review.product_id == review_in.product_id).all()
    ratings = [r.rating for r in all_reviews] + [review_in.rating]
    product.rating = round(sum(ratings) / len(ratings), 1)

    db.commit()
    db.refresh(review)
    return review

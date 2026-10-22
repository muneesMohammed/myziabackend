import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Category, User
from app.schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from app.auth import get_current_admin

router = APIRouter(prefix="/categories", tags=["Categories"])

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_-]+', '-', text).strip('-')

@router.get("", response_model=List[CategoryResponse])
@router.get("/", response_model=List[CategoryResponse])
def get_categories(published_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(Category)
    if published_only:
        query = query.filter(Category.published == True)
    return query.order_by(Category.name.asc()).all()

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(
        (Category.id == category_id) | (Category.slug == category_id)
    ).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

from app.google_drive import normalize_image_url

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    slug = category_in.slug or slugify(category_in.name)
    existing = db.query(Category).filter(Category.slug == slug).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category with this slug already exists")

    category = Category(
        name=category_in.name,
        slug=slug,
        description=category_in.description,
        image_url=normalize_image_url(category_in.image_url or ""),
        published=category_in.published
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    if category_in.name is not None:
        category.name = category_in.name
    if category_in.slug is not None:
        category.slug = category_in.slug
    elif category_in.name is not None:
        category.slug = slugify(category_in.name)
    if category_in.description is not None:
        category.description = category_in.description
    if category_in.image_url is not None:
        category.image_url = normalize_image_url(category_in.image_url)
    if category_in.published is not None:
        category.published = category_in.published

    db.commit()
    db.refresh(category)
    return category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    db.delete(category)
    db.commit()
    return None

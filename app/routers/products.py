import json
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from app.database import get_db
from app.models import Product, Category, InventoryLog, User, Review, OrderItem, CartItem
from app.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.auth import get_current_admin

router = APIRouter(prefix="/products", tags=["Products"])

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_-]+', '-', text).strip('-')

def format_product_response(product: Product) -> dict:
    gallery_list = []
    if product.gallery:
        try:
            gallery_list = json.loads(product.gallery)
        except Exception:
            gallery_list = [product.image_url] if product.image_url else []

    category_name = product.category.name if product.category else "Uncategorized"

    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "title": product.name,  # for frontendclone compatibility
        "slug": product.slug,
        "description": product.description,
        "category_id": product.category_id,
        "category_name": category_name,
        "category": category_name,  # for frontendclone compatibility
        "cost_price": product.cost_price,
        "selling_price": product.selling_price,
        "price": product.selling_price,  # for frontendclone compatibility
        "srcUrl": product.image_url,  # for frontendclone compatibility
        "stock": product.stock,
        "min_stock_threshold": product.min_stock_threshold,
        "image_url": product.image_url,
        "gallery": gallery_list,
        "discount_amount": product.discount_amount,
        "discount_percentage": product.discount_percentage,
        "discount": {  # for frontendclone compatibility
            "amount": product.discount_amount,
            "percentage": product.discount_percentage
        },
        "rating": product.rating,
        "published": product.published,
        "created_at": product.created_at
    }

@router.get("", response_model=List[dict])
@router.get("/", response_model=List[dict])
def get_products(
    category_id: Optional[str] = None,
    category_slug: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = "newest",  # price_asc, price_desc, rating, newest
    published_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Product)

    if published_only:
        query = query.filter(Product.published == True)

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if category_slug:
        cat = db.query(Category).filter(Category.slug == category_slug).first()
        if cat:
            query = query.filter(Product.category_id == cat.id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.sku.ilike(search_pattern),
                Product.description.ilike(search_pattern)
            )
        )

    if min_price is not None:
        query = query.filter(Product.selling_price >= min_price)

    if max_price is not None:
        query = query.filter(Product.selling_price <= max_price)

    if sort_by == "price_asc":
        query = query.order_by(asc(Product.selling_price))
    elif sort_by == "price_desc":
        query = query.order_by(desc(Product.selling_price))
    elif sort_by == "rating":
        query = query.order_by(desc(Product.rating))
    else:
        query = query.order_by(desc(Product.created_at))

    products = query.offset(skip).limit(limit).all()
    return [format_product_response(p) for p in products]

@router.get("/{id_or_slug}", response_model=dict)
def get_product(id_or_slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(
        or_(Product.id == id_or_slug, Product.slug == id_or_slug, Product.sku == id_or_slug)
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return format_product_response(product)

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    slug = product_in.slug or slugify(product_in.name)
    existing_slug = db.query(Product).filter(Product.slug == slug).first()
    if existing_slug:
        slug = f"{slug}-{product_in.sku.lower()}"

    existing_sku = db.query(Product).filter(Product.sku == product_in.sku).first()
    if existing_sku:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product with this SKU already exists")

    gallery_json = json.dumps(product_in.gallery or [])

    product = Product(
        sku=product_in.sku,
        name=product_in.name,
        slug=slug,
        description=product_in.description,
        category_id=product_in.category_id,
        cost_price=product_in.cost_price,
        selling_price=product_in.selling_price,
        stock=product_in.stock,
        min_stock_threshold=product_in.min_stock_threshold,
        image_url=product_in.image_url or "",
        gallery=gallery_json,
        discount_amount=product_in.discount_amount,
        discount_percentage=product_in.discount_percentage,
        rating=product_in.rating,
        published=product_in.published
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Log initial inventory
    if product.stock > 0:
        inv_log = InventoryLog(
            product_id=product.id,
            change=product.stock,
            reason="Initial product creation stock"
        )
        db.add(inv_log)
        db.commit()

    return format_product_response(product)

@router.put("/{product_id}", response_model=dict)
def update_product(
    product_id: str,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    old_stock = product.stock

    if product_in.name is not None:
        product.name = product_in.name
    if product_in.slug is not None:
        product.slug = product_in.slug
    elif product_in.name is not None:
        product.slug = slugify(product_in.name)
    if product_in.sku is not None:
        product.sku = product_in.sku
    if product_in.description is not None:
        product.description = product_in.description
    if product_in.category_id is not None:
        product.category_id = product_in.category_id
    if product_in.cost_price is not None:
        product.cost_price = product_in.cost_price
    if product_in.selling_price is not None:
        product.selling_price = product_in.selling_price
    if product_in.stock is not None:
        product.stock = product_in.stock
    if product_in.min_stock_threshold is not None:
        product.min_stock_threshold = product_in.min_stock_threshold
    if product_in.image_url is not None:
        product.image_url = product_in.image_url
    if product_in.gallery is not None:
        product.gallery = json.dumps(product_in.gallery)
    if product_in.discount_amount is not None:
        product.discount_amount = product_in.discount_amount
    if product_in.discount_percentage is not None:
        product.discount_percentage = product_in.discount_percentage
    if product_in.rating is not None:
        product.rating = product_in.rating
    if product_in.published is not None:
        product.published = product_in.published

    db.commit()
    db.refresh(product)

    # Log inventory change if stock was updated
    if product_in.stock is not None and product_in.stock != old_stock:
        stock_diff = product_in.stock - old_stock
        inv_log = InventoryLog(
            product_id=product.id,
            change=stock_diff,
            reason="Manual stock adjustment by admin"
        )
        db.add(inv_log)
        db.commit()

    return format_product_response(product)

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Remove dependent rows before deleting the product because the DB enforces non-null
    # foreign keys on reviews, order_items, inventory logs, and cart entries.
    db.query(Review).filter(Review.product_id == product_id).delete(synchronize_session=False)
    db.query(InventoryLog).filter(InventoryLog.product_id == product_id).delete(synchronize_session=False)
    db.query(OrderItem).filter(OrderItem.product_id == product_id).delete(synchronize_session=False)
    db.query(CartItem).filter(CartItem.product_id == product_id).delete(synchronize_session=False)

    db.delete(product)
    db.commit()
    return None

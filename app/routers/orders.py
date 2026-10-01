import uuid
import random
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.database import get_db
from app.models import Order, OrderItem, Product, Coupon, InventoryLog, Notification, User
from app.schemas import OrderCreate, OrderStatusUpdate, OrderResponse, OrderItemResponse
from app.auth import get_current_user, get_current_admin, get_current_user_optional

router = APIRouter(prefix="/orders", tags=["Orders"])

def generate_invoice_no() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    rand_digits = random.randint(1000, 9999)
    return f"INV-{timestamp}-{rand_digits}"

def format_order_response(order: Order) -> dict:
    items_resp = []
    for item in order.items:
        items_resp.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product.name if item.product else "Unknown Product",
            "product_sku": item.product.sku if item.product else "",
            "image_url": item.product.image_url if item.product else "",
            "quantity": item.quantity,
            "unit_price": item.unit_price
        })

    return {
        "id": order.id,
        "invoice_no": order.invoice_no,
        "customer_id": order.customer_id,
        "customer_name": order.customer.name if order.customer else "Guest Customer",
        "customer_email": order.customer.email if order.customer else "",
        "customer_phone": order.customer.phone if order.customer else "",
        "customer_address": order.customer.address if order.customer else "",
        "coupon_id": order.coupon_id,
        "status": order.status,
        "payment_method": order.payment_method,
        "shipping_cost": order.shipping_cost,
        "total_amount": order.total_amount,
        "order_time": order.order_time,
        "created_at": order.created_at,
        "items": items_resp
    }

@router.get("", response_model=List[dict])
@router.get("/", response_model=List[dict])
def get_orders(
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Order)

    # If customer (non-admin), filter to own orders
    if current_user.role not in ["admin", "super_admin", "staff", "cashier"]:
        query = query.filter(Order.customer_id == current_user.id)

    if status_filter:
        query = query.filter(Order.status == status_filter)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Order.invoice_no.ilike(search_pattern),
                Order.customer_id.ilike(search_pattern)
            )
        )

    orders = query.order_by(desc(Order.created_at)).all()
    return [format_order_response(o) for o in orders]

@router.get("/{order_id}", response_model=dict)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(
        or_(Order.id == order_id, Order.invoice_no == order_id)
    ).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Authorization check
    if current_user.role not in ["admin", "super_admin", "staff", "cashier"] and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return format_order_response(order)

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    if not order_in.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order must contain at least one item")

    # Determine customer account
    customer_user = current_user

    if not customer_user and order_in.customer_email:
        # Check if user with email already exists
        customer_user = db.query(User).filter(User.email.ilike(order_in.customer_email)).first()
        if not customer_user:
            # Auto-create customer account for checkout
            customer_user = User(
                name=order_in.customer_name or "Guest Customer",
                email=order_in.customer_email,
                hashed_password="",
                phone=order_in.customer_phone,
                address=order_in.customer_address,
                role="customer",
                is_active=True
            )
            db.add(customer_user)
            db.flush()
        else:
            if order_in.customer_phone and not customer_user.phone:
                customer_user.phone = order_in.customer_phone
            if order_in.customer_address and not customer_user.address:
                customer_user.address = order_in.customer_address

    if not customer_user:
        # Fallback to default Guest customer record
        customer_user = db.query(User).filter(User.email == "guest@myziya.com").first()
        if not customer_user:
            customer_user = User(
                name="Guest Customer",
                email="guest@myziya.com",
                hashed_password="",
                role="customer",
                is_active=True
            )
            db.add(customer_user)
            db.flush()

    customer_id = customer_user.id

    coupon_id = None
    discount_amount = 0.0

    if order_in.coupon_code:
        coupon = db.query(Coupon).filter(Coupon.code.ilike(order_in.coupon_code), Coupon.published == True).first()
        if coupon:
            coupon_id = coupon.id
            if coupon.discount_type == "percentage":
                # Applied after total calculated
                pass
            else:
                discount_amount = coupon.discount_value

    items_to_create = []
    subtotal = 0.0

    for item_in in order_in.items:
        product = db.query(Product).filter(Product.id == item_in.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product ID {item_in.product_id} not found"
            )

        if product.stock < item_in.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name}'. Available: {product.stock}"
            )

        unit_price = item_in.unit_price if item_in.unit_price is not None else product.selling_price
        subtotal += unit_price * item_in.quantity

        items_to_create.append((product, item_in.quantity, unit_price))

    # Calculate discount if percentage coupon
    if order_in.coupon_code:
        coupon = db.query(Coupon).filter(Coupon.code.ilike(order_in.coupon_code), Coupon.published == True).first()
        if coupon and coupon.discount_type == "percentage":
            discount_amount = (subtotal * coupon.discount_value) / 100.0

    total_amount = max(0.0, subtotal - discount_amount + order_in.shipping_cost)
    invoice_no = generate_invoice_no()

    order = Order(
        invoice_no=invoice_no,
        customer_id=customer_id,
        coupon_id=coupon_id,
        status="pending",
        payment_method=order_in.payment_method,
        shipping_cost=order_in.shipping_cost,
        total_amount=round(total_amount, 2),
        order_time=datetime.utcnow()
    )
    db.add(order)
    db.flush()

    for product, qty, unit_price in items_to_create:
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=qty,
            unit_price=unit_price
        )
        db.add(order_item)

        # Decrement product stock
        product.stock -= qty

        # Add inventory log
        inv_log = InventoryLog(
            product_id=product.id,
            change=-qty,
            reason=f"Sale order {invoice_no}"
        )
        db.add(inv_log)

        # Trigger low stock notification if needed
        if product.stock <= product.min_stock_threshold:
            notification = Notification(
                title=f"Low Stock Alert: '{product.name}' has only {product.stock} items left!",
                type="low_stock",
                is_read=False,
                published=True,
                image_url=product.image_url
            )
            db.add(notification)

    # Trigger new order notification
    customer_name = current_user.name if current_user else (customer_user.name if customer_user else "Guest")
    order_notification = Notification(
        title=f"New Order #{invoice_no} placed by {customer_name} for ${round(total_amount, 2)}",
        type="new_order",
        is_read=False,
        published=True
    )
    db.add(order_notification)

    db.commit()
    db.refresh(order)

    return format_order_response(order)

@router.patch("/{order_id}/status", response_model=dict)
def update_order_status(
    order_id: str,
    status_in: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    valid_statuses = ["pending", "processing", "delivered", "cancelled"]
    if status_in.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    order.status = status_in.status
    db.commit()
    db.refresh(order)
    return format_order_response(order)

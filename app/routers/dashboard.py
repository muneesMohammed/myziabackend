from datetime import date, datetime, time, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import case, desc, func
from app.database import get_db
from app.models import Order, OrderItem, Product, User
from app.schemas import DashboardSummary
from app.auth import get_current_admin
from app.routers.orders import format_order_response

router = APIRouter(prefix="/dashboard", tags=["Admin Dashboard"])

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    month_start = today.replace(day=1)
    last_month_end = month_start
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)

    def revenue_between(start: date, end: date) -> float:
        result = db.query(func.sum(Order.total_amount)).filter(
            Order.status != "cancelled",
            Order.order_time >= datetime.combine(start, time.min),
            Order.order_time < datetime.combine(end, time.min),
        ).scalar()
        return round(float(result or 0), 2)

    revenue_result = db.query(func.sum(Order.total_amount)).filter(
        Order.status != "cancelled"
    ).scalar()
    total_revenue = round(float(revenue_result or 0), 2)

    total_orders = db.query(Order).count()
    total_products = db.query(Product).count()
    total_customers = db.query(User).filter(User.role == "customer").count()

    # Low Stock Products count (stock <= min_stock_threshold)
    low_stock_count = db.query(Product).filter(Product.stock <= Product.min_stock_threshold).count()

    # Order count by status
    pending_count = db.query(Order).filter(Order.status == "pending").count()
    processing_count = db.query(Order).filter(Order.status == "processing").count()
    delivered_count = db.query(Order).filter(Order.status == "delivered").count()
    cancelled_count = db.query(Order).filter(Order.status == "cancelled").count()

    weekly_start = today - timedelta(days=6)
    weekly_rows = db.query(
        func.date(Order.order_time).label("order_date"),
        func.sum(case((Order.status != "cancelled", Order.total_amount), else_=0)).label("revenue"),
        func.count(Order.id).label("orders"),
    ).filter(
        Order.order_time >= datetime.combine(weekly_start, time.min),
        Order.order_time < datetime.combine(tomorrow, time.min),
    ).group_by(func.date(Order.order_time)).all()

    weekly_by_date = {
        (weekly_start + timedelta(days=offset)).isoformat(): {"revenue": 0.0, "orders": 0}
        for offset in range(7)
    }
    for row in weekly_rows:
        day_key = str(row.order_date)
        if day_key in weekly_by_date:
            weekly_by_date[day_key] = {
                "revenue": round(float(row.revenue or 0), 2),
                "orders": int(row.orders or 0),
            }

    best_sellers = db.query(
        Product.id.label("product_id"),
        Product.name.label("product_name"),
        func.sum(OrderItem.quantity).label("quantity_sold"),
    ).join(OrderItem, OrderItem.product_id == Product.id).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        Order.status != "cancelled"
    ).group_by(Product.id, Product.name).order_by(
        desc("quantity_sold")
    ).limit(5).all()

    return DashboardSummary(
        total_revenue=round(total_revenue, 2),
        total_orders=total_orders,
        total_products=total_products,
        total_customers=total_customers,
        low_stock_products_count=low_stock_count,
        pending_orders_count=pending_count,
        processing_orders_count=processing_count,
        delivered_orders_count=delivered_count,
        cancelled_orders_count=cancelled_count,
        today_revenue=revenue_between(today, tomorrow),
        yesterday_revenue=revenue_between(today - timedelta(days=1), today),
        this_month_revenue=revenue_between(month_start, tomorrow),
        last_month_revenue=revenue_between(last_month_start, last_month_end),
        weekly_sales=[
            {"date": day, **values}
            for day, values in weekly_by_date.items()
        ],
        best_sellers=[
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "quantity_sold": int(row.quantity_sold or 0),
            }
            for row in best_sellers
        ],
    )

@router.get("/recent-orders", response_model=List[dict])
def get_recent_orders(
    limit: int = 10,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    orders = db.query(Order).order_by(desc(Order.created_at)).limit(limit).all()
    return [format_order_response(o) for o in orders]

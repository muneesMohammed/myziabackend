from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# --- Auth & User Schemas ---
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    address: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


# --- Staff Schemas ---
class StaffRoleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    is_default: bool

    class Config:
        from_attributes = True

class StaffCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    role_id: int
    joining_date: Optional[str] = None
    image_url: Optional[str] = None
    published: bool = True

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    joining_date: Optional[str] = None
    image_url: Optional[str] = None
    published: Optional[bool] = None

class StaffResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role_id: int
    joining_date: Optional[str] = None
    image_url: Optional[str] = None
    published: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Category Schemas ---
class CategoryCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = ""
    published: bool = True

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    published: Optional[bool] = None

class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    image_url: str
    published: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Product Schemas ---
class ProductCreate(BaseModel):
    sku: str
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    category_id: str
    cost_price: float = 0.0
    selling_price: float
    stock: int = 0
    min_stock_threshold: int = 5
    image_url: Optional[str] = ""
    gallery: Optional[List[str]] = []
    discount_amount: float = 0.0
    discount_percentage: float = 0.0
    rating: float = 5.0
    published: bool = True

class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    stock: Optional[int] = None
    min_stock_threshold: Optional[int] = None
    image_url: Optional[str] = None
    gallery: Optional[List[str]] = None
    discount_amount: Optional[float] = None
    discount_percentage: Optional[float] = None
    rating: Optional[float] = None
    published: Optional[bool] = None

class ProductResponse(BaseModel):
    id: str
    sku: str
    name: str
    slug: str
    description: Optional[str] = None
    category_id: str
    category_name: Optional[str] = None
    cost_price: float
    selling_price: float
    stock: int
    min_stock_threshold: int
    image_url: str
    gallery: List[str] = []
    discount_amount: float
    discount_percentage: float
    rating: float
    published: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Coupon Schemas ---
class CouponCreate(BaseModel):
    code: str
    campaign_name: str
    discount_type: str = "percentage"  # percentage, fixed
    discount_value: float
    start_date: str
    end_date: str
    image_url: Optional[str] = ""
    published: bool = True

class CouponUpdate(BaseModel):
    code: Optional[str] = None
    campaign_name: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    image_url: Optional[str] = None
    published: Optional[bool] = None

class CouponResponse(BaseModel):
    id: str
    code: str
    campaign_name: str
    discount_type: str
    discount_value: float
    start_date: str
    end_date: str
    image_url: str
    published: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Order Schemas ---
class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    unit_price: Optional[float] = None

class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    image_url: Optional[str] = None
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    coupon_code: Optional[str] = None
    payment_method: str = "cash"  # cash, card, credit
    shipping_cost: float = 0.0
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    items: List[OrderItemCreate]

class OrderStatusUpdate(BaseModel):
    status: str  # pending, processing, delivered, cancelled

class OrderResponse(BaseModel):
    id: str
    invoice_no: str
    customer_id: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    coupon_id: Optional[str] = None
    status: str
    payment_method: str
    shipping_cost: float
    total_amount: float
    order_time: datetime
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True


# --- Review Schemas ---
class ReviewCreate(BaseModel):
    product_id: str
    user_name: str
    content: str
    rating: float = Field(ge=1.0, le=5.0)

class ReviewResponse(BaseModel):
    id: str
    product_id: str
    user_name: str
    content: str
    rating: float
    date: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Notification Schemas ---
class NotificationResponse(BaseModel):
    id: str
    staff_id: Optional[str] = None
    title: str
    type: str
    is_read: bool
    published: bool
    image_url: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Dashboard Summary Schema ---
class DashboardDay(BaseModel):
    date: str
    revenue: float
    orders: int

class DashboardBestSeller(BaseModel):
    product_id: str
    product_name: str
    quantity_sold: int

class DashboardSummary(BaseModel):
    total_revenue: float
    total_orders: int
    total_products: int
    total_customers: int
    low_stock_products_count: int
    pending_orders_count: int
    processing_orders_count: int
    delivered_orders_count: int
    cancelled_orders_count: int
    today_revenue: float
    yesterday_revenue: float
    this_month_revenue: float
    last_month_revenue: float
    weekly_sales: List[DashboardDay]
    best_sellers: List[DashboardBestSeller]

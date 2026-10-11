import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    role = Column(String(50), default="customer", nullable=False)  # customer, admin, cashier
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")


class StaffRole(Base):
    __tablename__ = "staff_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)  # super_admin, admin, cashier
    display_name = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)

    staff_members = relationship("Staff", back_populates="role")


class Staff(Base):
    __tablename__ = "staff"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("staff_roles.id"), nullable=False)
    joining_date = Column(String(50), nullable=True)
    image_url = Column(String(500), nullable=True)
    published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = relationship("StaffRole", back_populates="staff_members")
    notifications = relationship("Notification", back_populates="staff")
    inventory_logs = relationship("InventoryLog", back_populates="staff")


class Category(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=False, default="")
    published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True)
    cost_price = Column(Float, default=0.0, nullable=False)
    selling_price = Column(Float, nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    min_stock_threshold = Column(Integer, default=5, nullable=False)
    image_url = Column(String(500), nullable=False, default="")
    gallery = Column(Text, nullable=True, default="[]")  # JSON encoded list of URLs
    discount_amount = Column(Float, default=0.0)
    discount_percentage = Column(Float, default=0.0)
    rating = Column(Float, default=5.0)
    published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    inventory_logs = relationship("InventoryLog", back_populates="product", cascade="all, delete-orphan")


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(100), unique=True, index=True, nullable=False)
    campaign_name = Column(String(255), nullable=False)
    discount_type = Column(String(50), default="percentage", nullable=False)  # percentage, fixed
    discount_value = Column(Float, nullable=False)
    start_date = Column(String(50), nullable=False)
    end_date = Column(String(50), nullable=False)
    image_url = Column(String(500), nullable=False, default="")
    published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("Order", back_populates="coupon")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_no = Column(String(100), unique=True, index=True, nullable=False)
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    coupon_id = Column(String(36), ForeignKey("coupons.id"), nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, processing, delivered, cancelled
    payment_method = Column(String(50), default="cash", nullable=False)  # cash, card, credit
    shipping_cost = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, nullable=False)
    order_time = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("User", back_populates="orders")
    coupon = relationship("Coupon", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    user_name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    rating = Column(Float, nullable=False, default=5.0)
    date = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="reviews")


class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    staff_id = Column(String(36), ForeignKey("staff.id"), nullable=True)
    change = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="inventory_logs")
    staff = relationship("Staff", back_populates="inventory_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    staff_id = Column(String(36), ForeignKey("staff.id"), nullable=True)
    title = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # new_order, low_stock
    is_read = Column(Boolean, default=False)
    published = Column(Boolean, default=True)
    image_url = Column(String(500), nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    staff = relationship("Staff", back_populates="notifications")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product")

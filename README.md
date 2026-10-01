# MyZiya Perfume - Professional FastAPI & SQL Backend

A production-ready, modular **FastAPI** backend with **SQLAlchemy ORM**, **JWT Authentication**, and comprehensive database models designed for both the **Customer Frontend Clone** and the **Admin Dashboard**.

---

## 🌟 Key Features

1. **Authentication & Authorization**:
   - JWT Access Token generation and decoding.
   - Secure password hashing using `bcrypt`.
   - Customer registration & login (`/api/v1/auth/register`, `/api/v1/auth/login`).
   - Admin & Staff login (`/api/v1/auth/admin-login`).
   - Role-based Access Control (Admin/Staff vs. Customer).

2. **Complete SQL Database Schema (SQLAlchemy ORM)**:
   - `users`: Customers and Admins.
   - `staff_roles` & `staff`: Admin staff permissions & staff management.
   - `categories`: Fragrance family categories with slugs & images.
   - `products`: Complete fragrance catalog (SKU, prices, stock, min stock threshold, ratings, discounts, image gallery).
   - `coupons`: Promotional discount coupons (percentage & fixed).
   - `orders` & `order_items`: Customer orders with automatic invoice generation (`INV-YYYYMMDD-XXXX`).
   - `reviews`: Product reviews & auto-calculated average ratings.
   - `inventory_logs`: Automated audit trail for stock additions & sales deductions.
   - `notifications`: Admin alerts for new orders and low-stock warnings.
   - `cart_items`: Shopping cart persistence per user.

3. **Frontend Clone & Admin Dashboard Compatibility**:
   - `GET /api/v1/products` returns compatibility fields (`title`, `category`, `srcUrl`, `price`, `discount`) for standard Next.js / React shop templates.
   - `GET /api/v1/dashboard/summary` provides real-time sales metrics, revenue, order breakdown, and stock alerts for the Admin UI.

4. **Interactive Swagger & OpenAPI Documentation**:
   - Interactive UI available at `http://127.0.0.1:8000/docs` or `http://127.0.0.1:8000/redoc`.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+

### 2. Installation & Virtual Environment Setup
```bash
# Navigate to the backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Seeding
To populate the database with initial luxury perfumes, categories, coupons, demo admin, customer account, and sample orders:
```bash
python -m app.seed
```

**Default Credentials Seeded**:
- **Admin Account**:
  - Email: `admin@ziyaperfume.com`
  - Password: `Admin@123456`
- **Customer Account**:
  - Email: `customer@ziyaperfume.com`
  - Password: `Customer@123456`

---

## 🏃 Running the Server

Start the development server with live reload:
```bash
python run.py
```
or directly with Uvicorn:
```bash
uvicorn app.main:app --reload --port 8000
```
Access the server at:
- **API Base**: `http://127.0.0.1:8000/api/v1`
- **Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---

## 🧪 Running Automated Tests

Run the backend integration test suite:
```bash
python test_backend.py
```

---

## 📁 Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & CORS configuration
│   ├── config.py            # Settings & JWT configuration
│   ├── database.py          # SQLAlchemy engine & session maker
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic v2 schemas
│   ├── auth.py              # JWT token handling & auth dependencies
│   ├── seed.py              # Data seeder script
│   └── routers/
│       ├── auth.py          # Auth endpoints (/auth)
│       ├── products.py      # Product CRUD & filtering (/products)
│       ├── categories.py    # Category CRUD (/categories)
│       ├── coupons.py       # Coupon management (/coupons)
│       ├── orders.py        # Order creation & checkout (/orders)
│       ├── reviews.py       # Product reviews (/reviews)
│       ├── staff.py         # Staff management (/staff)
│       ├── dashboard.py     # Admin analytics (/dashboard)
│       └── notifications.py # Admin notifications (/notifications)
├── test_backend.py          # Test suite
├── requirements.txt         # Dependencies
├── run.py                   # Uvicorn runner
└── myziya_perfume.db        # SQLite database (auto-created)
```

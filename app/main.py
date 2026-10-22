from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import settings
from app.database import engine, Base
from app.routers import (
    auth,
    products,
    categories,
    coupons,
    orders,
    reviews,
    staff,
    dashboard,
    notifications,
    customers,
    payments,
    upload
)
from app.seed import seed_database
from fastapi.staticfiles import StaticFiles
import os

# Auto-create tables on app startup
Base.metadata.create_all(bind=engine)

# Ensure uploads directory exists
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(uploads_dir, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount local uploads directory for static image serving fallback
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Mount public images directory for catalog perfume images fallback
images_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "myziyawebapplication", "public", "images"))
if os.path.exists(images_dir):
    app.mount("/images", StaticFiles(directory=images_dir), name="images")


@app.on_event("startup")
def run_startup():
    try:
        with engine.connect() as conn:
            if "mysql" in settings.get_database_url:
                conn.execute(text("ALTER TABLE products MODIFY category_id VARCHAR(36) NULL"))
                conn.commit()
    except Exception as e:
        print(f"[Migration] Table check notice: {e}")
    try:
        seed_database()
    except Exception as e:
        print(f"[Seed] Auto-seed notice: {e}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
api_routers = [
    auth.router,
    customers.router,
    products.router,
    categories.router,
    coupons.router,
    orders.router,
    reviews.router,
    staff.router,
    dashboard.router,
    notifications.router,
    payments.router,
    upload.router
]

# Mount on /api/v1
for r in api_routers:
    app.include_router(r, prefix=settings.API_V1_STR)

# Also mount at root as fallback so /auth/admin-login, /products, etc. never 404
for r in api_routers:
    app.include_router(r)

@app.get("/")
def root():
    return {
        "message": "Welcome to MyZiya Perfume FastAPI & SQL Backend!",
        "version": settings.PROJECT_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    return {"status": "healthy", "version": settings.PROJECT_VERSION}

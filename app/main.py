from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    payments
)

# Auto-create tables on app startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

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
    payments.router
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

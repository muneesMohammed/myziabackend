import hashlib
import hmac
from typing import Optional

import razorpay
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/payments", tags=["Payments"])


class PaymentCreateRequest(BaseModel):
    amount: int
    currency: str = "INR"
    receipt: Optional[str] = None


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("/create-order")
def create_razorpay_order(payload: PaymentCreateRequest):
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return {
            "id": f"mock_order_{payload.receipt or 'demo'}",
            "amount": max(payload.amount, 1),
            "currency": payload.currency,
            "key": "rzp_test_mock",
            "mock": True,
        }

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    order = client.order.create(
        {
            "amount": max(payload.amount, 1) * 100,
            "currency": payload.currency,
            "receipt": payload.receipt or f"receipt_{hash(payload)}",
            "payment_capture": 1,
        }
    )

    return {
        "id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "key": settings.RAZORPAY_KEY_ID,
        "receipt": order.get("receipt"),
        "mock": False,
    }


@router.post("/verify-payment")
def verify_razorpay_payment(payload: PaymentVerifyRequest):
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return {
            "verified": True,
            "payment_id": payload.razorpay_payment_id,
            "order_id": payload.razorpay_order_id,
            "message": "Mock verification successful",
        }

    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if generated_signature != payload.razorpay_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Razorpay signature")

    return {
        "verified": True,
        "payment_id": payload.razorpay_payment_id,
        "order_id": payload.razorpay_order_id,
    }

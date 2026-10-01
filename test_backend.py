import sys
import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Product, Review, InventoryLog

client = TestClient(app)

class TestFastAPIBackend(unittest.TestCase):

    def test_01_health_check(self):
        response = client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_02_customer_login(self):
        payload = {"email": "customer@ziyaperfume.com", "password": "Customer@123456"}
        response = client.post("/api/v1/auth/login", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], "customer@ziyaperfume.com")
        self.assertEqual(data["user"]["role"], "customer")
        # Save token for next tests
        TestFastAPIBackend.customer_token = data["access_token"]

    def test_03_admin_login(self):
        payload = {"email": "admin@ziyaperfume.com", "password": "Admin@123456"}
        response = client.post("/api/v1/auth/admin-login", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], "admin@ziyaperfume.com")
        self.assertEqual(data["user"]["role"], "admin")
        TestFastAPIBackend.admin_token = data["access_token"]

    def test_04_get_categories(self):
        response = client.get("/api/v1/categories")
        self.assertEqual(response.status_code, 200)
        categories = response.json()
        self.assertGreater(len(categories), 0)
        self.assertTrue(any(c["slug"] == "oud-oriental" for c in categories))

    def test_05_get_products(self):
        response = client.get("/api/v1/products")
        self.assertEqual(response.status_code, 200)
        products = response.json()
        self.assertGreater(len(products), 0)

        # Check frontend clone compatibility keys
        first_product = products[0]
        self.assertIn("title", first_product)
        self.assertIn("category", first_product)
        self.assertIn("srcUrl", first_product)
        self.assertIn("price", first_product)
        self.assertIn("discount", first_product)

    def test_06_validate_coupon(self):
        response = client.get("/api/v1/coupons/validate/ZIYA20")
        self.assertEqual(response.status_code, 200)
        coupon = response.json()
        self.assertEqual(coupon["code"], "ZIYA20")
        self.assertEqual(coupon["discount_value"], 20.0)

    def test_07_create_order(self):
        # Fetch a product to order
        prod_resp = client.get("/api/v1/products")
        products = prod_resp.json()
        product = products[0]

        headers = {"Authorization": f"Bearer {TestFastAPIBackend.customer_token}"}
        order_payload = {
            "coupon_code": "ZIYA20",
            "payment_method": "card",
            "shipping_cost": 10.0,
            "items": [
                {"product_id": product["id"], "quantity": 1}
            ]
        }
        response = client.post("/api/v1/orders", json=order_payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        order_data = response.json()
        self.assertIn("invoice_no", order_data)
        self.assertEqual(order_data["status"], "pending")
        self.assertGreater(order_data["total_amount"], 0)

    def test_08_admin_dashboard_summary(self):
        headers = {"Authorization": f"Bearer {TestFastAPIBackend.admin_token}"}
        response = client.get("/api/v1/dashboard/summary", headers=headers)
        self.assertEqual(response.status_code, 200)
        summary = response.json()
        self.assertIn("total_revenue", summary)
        self.assertIn("total_orders", summary)
        self.assertIn("low_stock_products_count", summary)
        self.assertIn("today_revenue", summary)
        self.assertIn("weekly_sales", summary)
        self.assertIn("best_sellers", summary)
        self.assertEqual(len(summary["weekly_sales"]), 7)
        self.assertGreater(summary["total_products"], 0)

    def test_09_admin_notifications(self):
        headers = {"Authorization": f"Bearer {TestFastAPIBackend.admin_token}"}
        response = client.get("/api/v1/notifications", headers=headers)
        self.assertEqual(response.status_code, 200)
        notifications = response.json()
        self.assertGreater(len(notifications), 0)

    def test_10_delete_product_with_related_records(self):
        headers = {"Authorization": f"Bearer {TestFastAPIBackend.admin_token}"}
        categories = client.get("/api/v1/categories")
        category_id = categories.json()[0]["id"]

        unique_suffix = "DELTEST" + str(__import__('uuid').uuid4())[:8].upper()
        payload = {
            "sku": f"{unique_suffix}",
            "name": f"Delete Test Product {unique_suffix}",
            "slug": f"delete-test-product-{unique_suffix.lower()}",
            "category_id": category_id,
            "cost_price": 12,
            "selling_price": 30,
            "stock": 8,
            "min_stock_threshold": 2,
            "image_url": "",
            "gallery": [],
            "discount_amount": 0,
            "discount_percentage": 0,
            "rating": 5.0,
            "published": True,
        }
        created = client.post("/api/v1/products", json=payload, headers=headers)
        self.assertEqual(created.status_code, 201)
        product_id = created.json()["id"]

        db = SessionLocal()
        try:
            db.add(Review(
                product_id=product_id,
                user_name="Tester",
                content="To be deleted",
                rating=5.0,
                date="2026-09-20"
            ))
            db.add(InventoryLog(
                product_id=product_id,
                staff_id=None,
                change=-2,
                reason="Delete test"
            ))
            db.commit()
        finally:
            db.close()

        response = client.delete(f"/api/v1/products/{product_id}", headers=headers)
        self.assertEqual(response.status_code, 204)


if __name__ == "__main__":
    unittest.main()

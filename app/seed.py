import json
from datetime import datetime
from app.database import SessionLocal, engine, Base
from app.models import (
    User, StaffRole, Staff, Category, Product, Coupon, Order, OrderItem, Review, InventoryLog, Notification
)
from app.auth import get_password_hash

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Staff Roles
        if db.query(StaffRole).count() == 0:
            roles = [
                StaffRole(id=1, name="super_admin", display_name="Super Admin", is_default=False),
                StaffRole(id=2, name="admin", display_name="Admin", is_default=True),
                StaffRole(id=3, name="cashier", display_name="Cashier", is_default=False)
            ]
            db.add_all(roles)
            db.commit()
            print("[OK] Staff roles seeded")

        # 2. Seed Admin & Customer Users
        if db.query(User).count() == 0:
            admin_user = User(
                name="Ziya Super Admin",
                email="admin@ziyaperfume.com",
                hashed_password=get_password_hash("Admin@123456"),
                phone="+1234567890",
                address="123 Luxury Avenue, Paris, France",
                role="admin",
                is_active=True
            )
            second_admin_user = User(
                name="admin",
                email="admin@myziyaperfume.com",
                hashed_password=get_password_hash("admin123"),
                phone="+1234567890",
                address="123 Luxury Avenue, Paris, France",
                role="admin",
                is_active=True
            )
            customer_user = User(
                name="Sophia Laurent",
                email="customer@ziyaperfume.com",
                hashed_password=get_password_hash("Customer@123456"),
                phone="+1987654321",
                address="742 Evergreen Terrace, New York, USA",
                role="customer",
                is_active=True
            )
            db.add_all([admin_user, second_admin_user, customer_user])
            db.commit()
            print("[OK] Users seeded (Admin & Customer)")

        # 3. Seed Staff Members
        if db.query(Staff).count() == 0:
            staff_member = Staff(
                name="Alexander Vance",
                email="staff@ziyaperfume.com",
                hashed_password=get_password_hash("Staff@123456"),
                phone="+1122334455",
                role_id=2,
                joining_date="2024-01-15",
                image_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&q=80",
                published=True
            )
            db.add(staff_member)
            db.commit()
            print("[OK] Staff member seeded")

        # 4. Seed Categories
        categories_data = [
            {"name": "Perfumed Cream", "slug": "perfumed-cream", "description": "Silk-smooth perfumed creams enriched with long-lasting scent essence.", "image_url": "/images/pic1.png"},
            {"name": "Oudh Oil", "slug": "oudh-oil", "description": "Pure concentrated attar and agarwood oil distillations.", "image_url": "/images/pic2.png"},
            {"name": "Pocket Spray", "slug": "pocket-spray", "description": "Travel-friendly premium pocket perfume sprays.", "image_url": "/images/pic3.png"},
            {"name": "Bakhoor", "slug": "bakhoor", "description": "Aromatic incense chips and smoke diffusion bakhoor sticks.", "image_url": "/images/pic4.png"},
            {"name": "Fresheners", "slug": "fresheners", "description": "Luxurious ambient air and room freshener oils.", "image_url": "/images/pic5.png"},
            {"name": "Oud & Oriental", "slug": "oud-oriental", "description": "Rich wood scents infused with smoky spices and agarwood.", "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=600&q=80"},
            {"name": "Floral & Musk", "slug": "floral-musk", "description": "Damask roses, jasmine blossoms, and velvety white musk.", "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=600&q=80"},
            {"name": "Fresh & Citrus", "slug": "fresh-citrus", "description": "Italian bergamot, coastal breeze, and sunny Mediterranean citrus.", "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=600&q=80"},
            {"name": "Woody & Amber", "slug": "woody-amber", "description": "Golden amber, cedarwood notes, and sensual vanilla warmth.", "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=600&q=80"},
            {"name": "Luxury Attar", "slug": "luxury-attar", "description": "Alcohol-free concentrated perfume oils.", "image_url": "https://images.unsplash.com/photo-1616949755610-8c9bbc08f138?w=600&q=80"}
        ]

        cat_map = {}
        for cat_item in categories_data:
            existing_cat = db.query(Category).filter(Category.slug == cat_item["slug"]).first()
            if not existing_cat:
                cat = Category(
                    name=cat_item["name"],
                    slug=cat_item["slug"],
                    description=cat_item["description"],
                    image_url=cat_item["image_url"],
                    published=True
                )
                db.add(cat)
                db.commit()
                db.refresh(cat)
                cat_map[cat.slug] = cat.id
            else:
                cat_map[existing_cat.slug] = existing_cat.id

        print("[OK] Categories seeded")

        # 5. Seed Products
        raw_products = [
            {"id": "1", "title": "Solid Perfume Cream", "category": "perfumed-cream", "srcUrl": "/images/pic1.png", "gallery": ["/images/pic1.png", "/images/pic10.png", "/images/pic11.png"], "price": 120, "discount": {"amount": 0, "percentage": 0}, "rating": 4.5, "sku": "ZY-CRM-001", "is_new": True, "is_top": False},
            {"id": "2", "title": "12ml Ishq Pure Attar Oil", "category": "oudh-oil", "srcUrl": "/images/pic2.png", "gallery": ["/images/pic2.png"], "price": 260, "discount": {"amount": 0, "percentage": 20}, "rating": 3.5, "sku": "ZY-OIL-002", "is_new": True, "is_top": False},
            {"id": "3", "title": "myzia-Mariyam-spray", "category": "pocket-spray", "srcUrl": "/images/pic3.png", "gallery": ["/images/pic3.png"], "price": 180, "discount": {"amount": 0, "percentage": 0}, "rating": 4.5, "sku": "ZY-SPT-003", "is_new": True, "is_top": False},
            {"id": "4", "title": "Oudh Sticks Smoke Diffusion", "category": "bakhoor", "srcUrl": "/images/pic4.png", "gallery": ["/images/pic4.png", "/images/pic10.png", "/images/pic11.png"], "price": 160, "discount": {"amount": 0, "percentage": 30}, "rating": 4.5, "sku": "ZY-BKH-004", "is_new": True, "is_top": False},
            {"id": "5", "title": "12ml Aura77 Pure Attar Oil", "category": "fresheners", "srcUrl": "/images/pic5.png", "gallery": ["/images/pic5.png", "/images/pic10.png", "/images/pic11.png"], "price": 232, "discount": {"amount": 0, "percentage": 20}, "rating": 5.0, "sku": "ZY-FRS-005", "is_new": False, "is_top": True},
            {"id": "6", "title": "Jasmin Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic6.png", "gallery": ["/images/pic6.png", "/images/pic10.png", "/images/pic11.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 4.0, "sku": "ZY-CRM-006", "is_new": False, "is_top": True},
            {"id": "7", "title": "Aseel Bakhoor stick", "category": "bakhoor", "srcUrl": "/images/pic7.png", "gallery": ["/images/pic7.png"], "price": 80, "discount": {"amount": 0, "percentage": 0}, "rating": 3.0, "sku": "ZY-BKH-007", "is_new": False, "is_top": True},
            {"id": "8", "title": "Sabaya Pocket Spray", "category": "pocket-spray", "srcUrl": "/images/pic8.png", "gallery": ["/images/pic8.png"], "price": 210, "discount": {"amount": 0, "percentage": 0}, "rating": 4.5, "sku": "ZY-SPT-008", "is_new": False, "is_top": True},
            {"id": "12", "title": "Gentelman pocket Spray", "category": "pocket-spray", "srcUrl": "/images/pic12.png", "gallery": ["/images/pic12.png", "/images/pic10.png", "/images/pic11.png"], "price": 242, "discount": {"amount": 0, "percentage": 20}, "rating": 4.0, "sku": "ZY-SPT-012", "is_new": False, "is_top": False},
            {"id": "13", "title": "David of Cool Water Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic13.png", "gallery": ["/images/pic13.png", "/images/pic10.png", "/images/pic11.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-013", "is_new": False, "is_top": False},
            {"id": "14", "title": "Marj Pocket Spray", "category": "pocket-spray", "srcUrl": "/images/pic14.png", "gallery": ["/images/pic14.png"], "price": 180, "discount": {"amount": 0, "percentage": 0}, "rating": 4.5, "sku": "ZY-SPT-014", "is_new": False, "is_top": False},
            {"id": "15", "title": "Lavendor Bakhoor Stick", "category": "bakhoor", "srcUrl": "/images/pic15.png", "gallery": ["/images/pic15.png"], "price": 150, "discount": {"amount": 0, "percentage": 30}, "rating": 5.0, "sku": "ZY-BKH-015", "is_new": False, "is_top": False},
            {"id": "16", "title": "Dhoop Bakhoor Stick", "category": "bakhoor", "srcUrl": "/images/pic16.png", "gallery": ["/images/pic16.png"], "price": 150, "discount": {"amount": 0, "percentage": 30}, "rating": 5.0, "sku": "ZY-BKH-016", "is_new": False, "is_top": False},
            {"id": "17", "title": "Lamsat Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic17.png", "gallery": ["/images/pic17.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-017", "is_new": False, "is_top": False},
            {"id": "18", "title": "External Love Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic18.png", "gallery": ["/images/pic18.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-018", "is_new": False, "is_top": False},
            {"id": "19", "title": "Aseel Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic19.png", "gallery": ["/images/pic19.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-019", "is_new": False, "is_top": False},
            {"id": "20", "title": "Chelsea Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic20.png", "gallery": ["/images/pic20.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-020", "is_new": False, "is_top": False},
            {"id": "21", "title": "Abiyadh Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic21.png", "gallery": ["/images/pic21.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-021", "is_new": False, "is_top": False},
            {"id": "22", "title": "Blue Lady Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic22.png", "gallery": ["/images/pic22.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-022", "is_new": False, "is_top": False},
            {"id": "23", "title": "dvos Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic23.png", "gallery": ["/images/pic24.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-023", "is_new": False, "is_top": False},
            {"id": "24", "title": "Lovely Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic24.png", "gallery": ["/images/pic24.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-024", "is_new": False, "is_top": False},
            {"id": "25", "title": "Chocolate Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic25.png", "gallery": ["/images/pic25.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-025", "is_new": False, "is_top": False},
            {"id": "26", "title": "HHH Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic26.png", "gallery": ["/images/pic26.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-026", "is_new": False, "is_top": False},
            {"id": "27", "title": "Fog Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic27.png", "gallery": ["/images/pic27.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-027", "is_new": False, "is_top": False},
            {"id": "28", "title": "CR7 Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic28.png", "gallery": ["/images/pic28.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-028", "is_new": False, "is_top": False},
            {"id": "29", "title": "Maryam Gold Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic29.png", "gallery": ["/images/pic29.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-029", "is_new": False, "is_top": False},
            {"id": "30", "title": "Shams Al Oudh Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic30.png", "gallery": ["/images/pic30.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-030", "is_new": False, "is_top": False},
            {"id": "31", "title": "Zahira Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic31.png", "gallery": ["/images/pic31.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-031", "is_new": False, "is_top": False},
            {"id": "32", "title": "Lerils Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic32.png", "gallery": ["/images/pic32.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-032", "is_new": False, "is_top": False},
            {"id": "33", "title": "CutiKura Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic33.png", "gallery": ["/images/pic33.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-033", "is_new": False, "is_top": False},
            {"id": "34", "title": "Sandal Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic34.png", "gallery": ["/images/pic34.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-034", "is_new": False, "is_top": False},
            {"id": "35", "title": "Open Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic35.png", "gallery": ["/images/pic35.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-035", "is_new": False, "is_top": False},
            {"id": "36", "title": "Broot Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic36.png", "gallery": ["/images/pic36.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-036", "is_new": False, "is_top": False},
            {"id": "37", "title": "Javadhu Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic37.png", "gallery": ["/images/pic37.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-037", "is_new": False, "is_top": False},
            {"id": "38", "title": "Jordan Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic38.png", "gallery": ["/images/pic38.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-038", "is_new": False, "is_top": False},
            {"id": "39", "title": "Leo Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic39.png", "gallery": ["/images/pic39.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-039", "is_new": False, "is_top": False},
            {"id": "40", "title": "Yardly Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic40.png", "gallery": ["/images/pic40.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-040", "is_new": False, "is_top": False},
            {"id": "41", "title": "Galaxy Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic41.png", "gallery": ["/images/pic41.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-041", "is_new": False, "is_top": False},
            {"id": "42", "title": "BlackXS Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic42.png", "gallery": ["/images/pic42.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-042", "is_new": False, "is_top": False},
            {"id": "43", "title": "White Oudh Perfumed Cream", "category": "perfumed-cream", "srcUrl": "/images/pic43.png", "gallery": ["/images/pic43.png"], "price": 145, "discount": {"amount": 0, "percentage": 0}, "rating": 3.5, "sku": "ZY-CRM-043", "is_new": False, "is_top": False},
            # Additional luxury products from previous seed
            {"id": "44", "title": "Ziya Royal Oud Elixir", "category": "oud-oriental", "srcUrl": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&q=80", "gallery": ["https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&q=80"], "price": 185, "discount": {"amount": 25, "percentage": 13.5}, "rating": 4.9, "sku": "ZY-OUD-001", "is_new": True, "is_top": True},
            {"id": "45", "title": "Ziya Midnight Amber Noir", "category": "woody-amber", "srcUrl": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&q=80", "gallery": ["https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&q=80"], "price": 140, "discount": {"amount": 0, "percentage": 0}, "rating": 4.8, "sku": "ZY-WOD-002", "is_new": False, "is_top": True},
            {"id": "46", "title": "Ziya Velvet Rose & Musk", "category": "floral-musk", "srcUrl": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&q=80", "gallery": ["https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&q=80"], "price": 125, "discount": {"amount": 15, "percentage": 12.0}, "rating": 4.7, "sku": "ZY-FLR-003", "is_new": True, "is_top": False},
            {"id": "47", "title": "Ziya Citrus Breeze Extraits", "category": "fresh-citrus", "srcUrl": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&q=80", "gallery": ["https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&q=80"], "price": 110, "discount": {"amount": 0, "percentage": 0}, "rating": 4.6, "sku": "ZY-CRS-004", "is_new": False, "is_top": False},
            {"id": "48", "title": "Ziya Imperial Sapphire Attar", "category": "luxury-attar", "srcUrl": "https://images.unsplash.com/photo-1616949755610-8c9bbc08f138?w=800&q=80", "gallery": ["https://images.unsplash.com/photo-1616949755610-8c9bbc08f138?w=800&q=80"], "price": 220, "discount": {"amount": 30, "percentage": 13.6}, "rating": 5.0, "sku": "ZY-ATR-005", "is_new": False, "is_top": True}
        ]

        def slugify(text: str) -> str:
            import re
            return re.sub(r'[\s_-]+', '-', re.sub(r'[^\w\s-]', '', text.lower())).strip('-')

        for item in raw_products:
            slug = slugify(item["title"])
            existing_p = db.query(Product).filter(
                (Product.id == item["id"]) | (Product.sku == item["sku"]) | (Product.slug == slug)
            ).first()
            if not existing_p:
                cat_id = cat_map.get(item["category"], list(cat_map.values())[0])
                prod = Product(
                    id=item["id"],
                    sku=item["sku"],
                    name=item["title"],
                    slug=slug,
                    description=f"Exquisite fragrance blend of {item['title']}. Crafted with premium ingredients for long-lasting sillage.",
                    category_id=cat_id,
                    cost_price=round(item["price"] * 0.4, 2),
                    selling_price=float(item["price"]),
                    stock=50,
                    min_stock_threshold=5,
                    image_url=item["srcUrl"],
                    gallery=json.dumps(item["gallery"]),
                    discount_amount=float(item["discount"]["amount"]),
                    discount_percentage=float(item["discount"]["percentage"]),
                    rating=float(item["rating"]),
                    published=True
                )
                db.add(prod)
                db.commit()
        print(f"[OK] Products seeded")

        # 6. Seed Coupons
        if db.query(Coupon).count() == 0:
            coupons = [
                Coupon(
                    code="ZIYA20",
                    campaign_name="Summer Luxury Festival",
                    discount_type="percentage",
                    discount_value=20.0,
                    start_date="2026-01-01",
                    end_date="2026-12-31",
                    image_url="https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&q=80",
                    published=True
                ),
                Coupon(
                    code="WELCOME10",
                    campaign_name="New Customer Welcome",
                    discount_type="fixed",
                    discount_value=15.0,
                    start_date="2026-01-01",
                    end_date="2026-12-31",
                    image_url="https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=600&q=80",
                    published=True
                )
            ]
            db.add_all(coupons)
            db.commit()
            print("[OK] Coupons seeded")

        # 7. Seed Reviews
        if db.query(Review).count() == 0:
            reviews_list = [
                {"user_name": "Alex K.", "content": "Finding clothes that align with my personal style used to be a challenge until I discovered MyZiya. The perfume range is truly remarkable!", "rating": 5.0, "date": "August 14, 2023"},
                {"user_name": "Sarah M.", "content": "I'm blown away by the quality and style of the perfumed creams. Every piece I've bought has exceeded my expectations.", "rating": 5.0, "date": "August 15, 2023"},
                {"user_name": "Ethan R.", "content": "This attar oil is a must-have for anyone who appreciates luxury fragrances. The scent profile is exquisite and long lasting.", "rating": 5.0, "date": "August 16, 2023"},
                {"user_name": "Olivia P.", "content": "As a fragrance enthusiast, I value purity and authenticity. This perfume cream not only smells divine but feels wonderful on skin.", "rating": 5.0, "date": "August 17, 2023"},
                {"user_name": "Liam K.", "content": "This Bakhoor is a fusion of rich traditional spices and soothing wood. The smoke diffusion fills the room with calm elegance.", "rating": 5.0, "date": "August 18, 2023"},
                {"user_name": "Samantha D.", "content": "I absolutely love this pocket spray! Convenient to carry and the fragrance notes are super pleasant.", "rating": 5.0, "date": "August 19, 2023"}
            ]
            first_product = db.query(Product).first()
            prod_id = first_product.id if first_product else "1"

            for r_item in reviews_list:
                rev = Review(
                    product_id=prod_id,
                    user_name=r_item["user_name"],
                    content=r_item["content"],
                    rating=r_item["rating"],
                    date=r_item["date"]
                )
                db.add(rev)
            db.commit()
            print("[OK] Reviews seeded")

        # 8. Seed Sample Orders
        if db.query(Order).count() == 0:
            customer = db.query(User).filter(User.email == "customer@ziyaperfume.com").first()
            p1 = db.query(Product).filter(Product.id == "1").first() or db.query(Product).first()

            if customer and p1:
                sample_order = Order(
                    invoice_no="INV-2026-8891",
                    customer_id=customer.id,
                    status="delivered",
                    payment_method="card",
                    shipping_cost=15.0,
                    total_amount=p1.selling_price + 15.0,
                    order_time=datetime.utcnow()
                )
                db.add(sample_order)
                db.flush()

                item1 = OrderItem(order_id=sample_order.id, product_id=p1.id, quantity=1, unit_price=p1.selling_price)
                db.add(item1)

                low_stock_notif = Notification(
                    title="Low Stock Alert: 'Ziya Citrus Breeze Extraits' has only 4 items left!",
                    type="low_stock",
                    is_read=False,
                    published=True,
                    image_url="https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=600&q=80"
                )
                db.add(low_stock_notif)

                db.commit()
                print("[OK] Sample orders & notifications seeded")

        print("Database seeding completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

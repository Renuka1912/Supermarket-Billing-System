"""Seed script to populate initial data."""
import sqlite3
import os
from werkzeug.security import generate_password_hash
import config
from database import init_db

def seed():
    # Initialize schema
    init_db()

    db = sqlite3.connect(config.DATABASE)
    db.row_factory = sqlite3.Row

    # Seed admin user
    admin_hash = generate_password_hash('admin123')
    try:
        db.execute(
            "INSERT INTO users (username, password_hash, full_name, role, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
            ('admin', admin_hash, 'Administrator', 'admin', '9999999999', 'admin@supermarket.com')
        )
    except sqlite3.IntegrityError:
        pass

    # Seed a sample cashier
    cashier_hash = generate_password_hash('staff123')
    try:
        db.execute(
            "INSERT INTO users (username, password_hash, full_name, role, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
            ('cashier1', cashier_hash, 'Ravi Kumar', 'cashier', '9876543210', 'ravi@supermarket.com')
        )
    except sqlite3.IntegrityError:
        pass

    # Seed categories
    categories = [
        ('Grocery', 'Rice, flour, oil, spices and daily essentials'),
        ('Beverages', 'Soft drinks, juices, water, tea and coffee'),
        ('Snacks', 'Chips, biscuits, namkeen and packaged snacks'),
        ('Dairy', 'Milk, curd, butter, cheese and paneer'),
        ('Household Items', 'Cleaning supplies, detergents, and home essentials'),
        ('Personal Care', 'Soaps, shampoos, skincare and hygiene products'),
        ('Fruits & Vegetables', 'Fresh fruits and vegetables'),
        ('Bakery', 'Bread, cakes, pastries and baked goods'),
    ]
    for name, desc in categories:
        try:
            db.execute("INSERT INTO categories (name, description) VALUES (?, ?)", (name, desc))
        except sqlite3.IntegrityError:
            pass

    # Seed sample products
    products = [
        ('Basmati Rice 5kg', 'RICE5KG001', 1, 320, 399, 50, 10, '2027-06-30', 5),
        ('Tata Salt 1kg', 'SALT1KG001', 1, 18, 25, 100, 20, '2028-01-01', 0),
        ('Sunflower Oil 1L', 'OIL1L001', 1, 120, 155, 40, 10, '2027-03-15', 5),
        ('Coca Cola 750ml', 'COKE750001', 2, 30, 40, 80, 15, '2026-12-31', 12),
        ('Pepsi 2L', 'PEPSI2L001', 2, 65, 85, 30, 10, '2026-11-30', 12),
        ('Lays Classic 52g', 'LAYS52G001', 3, 15, 20, 100, 20, '2026-09-30', 12),
        ('Parle-G 250g', 'PARLEG250', 3, 20, 27, 120, 25, '2027-04-30', 0),
        ('Amul Milk 500ml', 'AMUL500ML', 4, 24, 29, 60, 20, '2026-04-10', 0),
        ('Amul Butter 100g', 'AMULBT100', 4, 42, 56, 30, 10, '2026-06-15', 12),
        ('Surf Excel 1kg', 'SURF1KG01', 5, 180, 225, 25, 5, '2028-01-01', 18),
        ('Dettol Soap 75g', 'DETTL75G1', 6, 30, 42, 60, 15, '2027-08-01', 12),
        ('Britannia Bread', 'BREAD001', 8, 35, 45, 20, 5, '2026-03-10', 0),
    ]
    for p in products:
        try:
            db.execute(
                """INSERT INTO products (name, barcode, category_id, purchase_price, selling_price,
                   stock_qty, min_stock, expiry_date, gst_percent) VALUES (?,?,?,?,?,?,?,?,?)""",
                p
            )
        except sqlite3.IntegrityError:
            pass

    # Seed suppliers
    suppliers = [
        ('Agarwal Distributors', '9876501234', '15 Market Road, Chennai', 'GST29AAA0001', 'agarwal@dist.com'),
        ('Fresh Farm Supplies', '9876505678', '42 Farm Lane, Bangalore', 'GST29BBB0002', 'freshfarm@supply.com'),
        ('Metro Beverages', '9876509012', '8 Industrial Area, Hyderabad', 'GST36CCC0003', 'metro@bev.com'),
    ]
    for s in suppliers:
        try:
            db.execute(
                "INSERT INTO suppliers (name, contact, address, gst_number, email) VALUES (?,?,?,?,?)", s
            )
        except sqlite3.IntegrityError:
            pass

    # Seed default settings
    settings = [
        ('shop_name', 'SuperMart'),
        ('gst_number', 'GST29XXXXX0001'),
        ('shop_address', '123 Main Street, Chennai - 600001'),
        ('shop_phone', '044-12345678'),
        ('currency_symbol', '₹'),
        ('receipt_footer', 'Thank you for shopping with us!'),
    ]
    for key, value in settings:
        try:
            db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        except sqlite3.IntegrityError:
            pass

    db.commit()
    db.close()
    print("✅ Database seeded successfully!")
    print("   Admin login: admin / admin123")
    print("   Staff login: cashier1 / staff123")

if __name__ == '__main__':
    seed()

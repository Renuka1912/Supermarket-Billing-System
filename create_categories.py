#!/usr/bin/env python3
import sqlite3

print("Creating categories table...")

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

try:
    # Create categories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    print("✓ Categories table created successfully")
    
    # Check if table has data
    cursor.execute("SELECT COUNT(*) FROM categories")
    count = cursor.fetchone()[0]
    print(f"✓ Categories in table: {count}")
    
    # Add sample categories if table is empty
    if count == 0:
        categories = [
            ('Dairy', 'Milk, Yogurt, Cheese, Butter'),
            ('Vegetables', 'Fresh vegetables and produce'),
            ('Fruits', 'Fresh fruits'),
            ('Snacks', 'Chips, Popcorn, Cookies, etc.'),
            ('Beverages', 'Soft drinks, Juices, Water'),
            ('Bakery', 'Bread, Cakes, Pastries'),
            ('Spices', 'Powders and spices'),
            ('Oil & Condiments', 'Cooking oils, vinegar, sauces')
        ]
        
        cursor.executemany(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            categories
        )
        conn.commit()
        print(f"✓ Added {len(categories)} sample categories")
        
        # Show what was added
        cursor.execute("SELECT id, name FROM categories")
        cats = cursor.fetchall()
        for cat_id, name in cats:
            print(f"  - {name}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    conn.rollback()
finally:
    conn.close()
    print("\nDone!")

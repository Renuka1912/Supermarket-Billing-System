import sqlite3

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check categories
cursor.execute('SELECT * FROM categories')
cats = cursor.fetchall()
print(f'Total categories: {len(cats)}')
if len(cats) > 0:
    for cat in cats:
        print(f'  - ID: {cat["id"]}, Name: {cat["name"]}, Desc: {cat.get("description", "N/A")}')
else:
    print('  No categories found!')

# Check products with categories
cursor.execute('''SELECT COUNT(*) as count FROM products WHERE category_id IS NOT NULL''')
result = cursor.fetchone()
print(f'\nProducts with category: {result["count"]}')

conn.close()

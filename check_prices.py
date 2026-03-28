import sqlite3

conn = sqlite3.connect('supermarket.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('SELECT id, name, selling_price, purchase_price FROM products ORDER BY id DESC LIMIT 10')
for row in cursor.fetchall():
    print(f'ID: {row[0]}, Name: {row[1]}, Selling: {row[2]}, Purchase: {row[3]}')
conn.close()

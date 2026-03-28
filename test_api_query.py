import sqlite3

# Test the exact query that the API uses
conn = sqlite3.connect('supermarket.db')
conn.row_factory = sqlite3.Row  # This makes it return dict-like objects

query = """SELECT s.*, u.full_name as cashier_name, c.name as customer_name
           FROM sales s LEFT JOIN users u ON s.user_id = u.id
           LEFT JOIN customers c ON s.customer_id = c.id 
           WHERE 1=1 ORDER BY s.sale_date DESC LIMIT 200"""

cursor = conn.cursor()
cursor.execute(query)
sales = cursor.fetchall()

print(f"API Query Results: {len(sales)} records")

if sales:
    print("\nFirst record (dict format):")
    first_sale = sales[0]
    print(f"  Keys: {list(first_sale.keys())}")
    print(f"  ID: {first_sale['id']}")
    print(f"  Invoice: {first_sale['invoice_number']}")
    print(f"  Date: {first_sale['sale_date']}")
    print(f"  Customer: {first_sale['customer_name']}")
    print(f"  Cashier: {first_sale['cashier_name']}")
    print(f"  Total: {first_sale['total']}")
    
    # Check if any records have missing data
    print(f"\nData completeness check:")
    missing_cashier = sum(1 for s in sales if not s['cashier_name'])
    missing_customer = sum(1 for s in sales if not s['customer_name'])
    print(f"  Records missing cashier: {missing_cashier}/{len(sales)}")
    print(f"  Records missing customer: {missing_customer}/{len(sales)}")

conn.close()

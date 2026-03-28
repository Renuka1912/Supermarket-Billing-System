import sqlite3

# Check database directly for sales records and cashier information
conn = sqlite3.connect('supermarket.db')
cursor = conn.cursor()

# Check if there are sales records
cursor.execute("SELECT COUNT(*) FROM sales")
sales_count = cursor.fetchone()[0]
print(f"Total sales records: {sales_count}")

if sales_count > 0:
    # Check sales with user information
    query = """
    SELECT s.id, s.invoice_number, s.sale_date, s.customer_id, s.user_id, 
           u.full_name as cashier_name, c.name as customer_name
    FROM sales s 
    LEFT JOIN users u ON s.user_id = u.id 
    LEFT JOIN customers c ON s.customer_id = c.id 
    ORDER BY s.sale_date DESC 
    LIMIT 5
    """
    
    cursor.execute(query)
    sales = cursor.fetchall()
    
    print("\nSample sales records with cashier/customer info:")
    for i, sale in enumerate(sales):
        print(f"\nRecord {i+1}:")
        print(f"  ID: {sale[0]}")
        print(f"  Invoice: {sale[1]}")
        print(f"  Date: {sale[2]}")
        print(f"  Customer ID: {sale[3]}")
        print(f"  User ID: {sale[4]}")
        print(f"  Cashier Name: {sale[5]}")
        print(f"  Customer Name: {sale[6]}")

# Check users table for cashiers
cursor.execute("SELECT id, username, full_name, role FROM users WHERE role = 'cashier'")
cashiers = cursor.fetchall()
print(f"\nCashier users ({len(cashiers)}):")
for cashier in cashiers:
    print(f"  ID: {cashier[0]}, Username: {cashier[1]}, Name: {cashier[2]}")

# Check customers table
cursor.execute("SELECT COUNT(*) FROM customers")
customer_count = cursor.fetchone()[0]
print(f"\nTotal customers: {customer_count}")

if customer_count > 0:
    cursor.execute("SELECT id, name FROM customers LIMIT 3")
    customers = cursor.fetchall()
    print("Sample customers:")
    for customer in customers:
        print(f"  ID: {customer[0]}, Name: {customer[1]}")

conn.close()

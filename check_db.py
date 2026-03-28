import sqlite3
import datetime

conn = sqlite3.connect('supermarket.db')
cursor = conn.cursor()

# Check if sales table exists and its structure
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="sales"')
table_exists = cursor.fetchone()
print('Sales table exists:', table_exists is not None)

if table_exists:
    cursor.execute('PRAGMA table_info(sales)')
    columns = cursor.fetchall()
    print('Sales table columns:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')
    
    # Check recent sales
    cursor.execute('SELECT COUNT(*) FROM sales')
    total_sales = cursor.fetchone()[0]
    print(f'Total sales in database: {total_sales}')
    
    # Check today's sales
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*) FROM sales WHERE DATE(sale_date) = ?', [today])
    today_sales_count = cursor.fetchone()[0]
    print(f'Today sales count: {today_sales_count}')
    
    # Get today's sales total
    cursor.execute('SELECT COALESCE(SUM(total), 0) FROM sales WHERE DATE(sale_date) = ?', [today])
    today_sales_total = cursor.fetchone()[0]
    print(f'Today sales total: {today_sales_total}')
    
    # Get recent sales sample
    cursor.execute('SELECT id, invoice_number, total, sale_date, user_id FROM sales ORDER BY sale_date DESC LIMIT 3')
    recent = cursor.fetchall()
    print('Recent sales:')
    for sale in recent:
        print(f'  ID: {sale[0]}, Invoice: {sale[1]}, Total: {sale[2]}, Date: {sale[3]}, User ID: {sale[4]}')

conn.close()

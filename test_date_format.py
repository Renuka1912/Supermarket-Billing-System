import sqlite3

# Check database directly for date format and test date filtering
conn = sqlite3.connect('supermarket.db')
cursor = conn.cursor()

# Check actual date format in database
cursor.execute("SELECT sale_date FROM sales ORDER BY sale_date DESC LIMIT 5")
dates = cursor.fetchall()
print("Sample dates in database:")
for date in dates:
    print(f"  {date[0]} (type: {type(date[0])})")

# Test date filtering directly
test_queries = [
    ("No filter", "SELECT COUNT(*) FROM sales"),
    ("Today only", "SELECT COUNT(*) FROM sales WHERE DATE(sale_date) = DATE('2024-03-04')"),
    ("Date range", "SELECT COUNT(*) FROM sales WHERE DATE(sale_date) >= DATE('2024-03-01') AND DATE(sale_date) <= DATE('2024-03-04')"),
    ("Date from only", "SELECT COUNT(*) FROM sales WHERE DATE(sale_date) >= DATE('2024-03-01')"),
    ("Date to only", "SELECT COUNT(*) FROM sales WHERE DATE(sale_date) <= DATE('2024-03-04')"),
]

print("\nDate filtering test results:")
for desc, query in test_queries:
    cursor.execute(query)
    count = cursor.fetchone()[0]
    print(f"{desc}: {count} records")

# Test with actual date format
cursor.execute("SELECT sale_date FROM sales LIMIT 1")
first_date = cursor.fetchone()
if first_date:
    sample_date = first_date[0]
    print(f"\nTesting with sample date: {sample_date}")
    
    # Try different date comparisons
    tests = [
        f"SELECT COUNT(*) FROM sales WHERE sale_date >= '{sample_date}'",
        f"SELECT COUNT(*) FROM sales WHERE DATE(sale_date) = DATE('{sample_date}')",
        f"SELECT COUNT(*) FROM sales WHERE DATE(sale_date) >= DATE('{sample_date}')",
    ]
    
    for test_query in tests:
        try:
            cursor.execute(test_query)
            count = cursor.fetchone()[0]
            print(f"Query: {test_query[:50]}... = {count}")
        except Exception as e:
            print(f"Error: {e}")

conn.close()


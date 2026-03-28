import requests
import json

# Test the sales API
try:
    response = requests.get('http://localhost:5000/api/sales')
    print("API Status:", response.status_code)
    
    if response.status_code == 200:
        sales_data = response.json()
        print(f"Found {len(sales_data)} sales records")
        
        if sales_data:
            # Print first few records to check data structure
            print("\nSample sales records:")
            for i, sale in enumerate(sales_data[:3]):
                print(f"\nRecord {i+1}:")
                print(f"  ID: {sale.get('id')}")
                print(f"  Invoice: {sale.get('invoice_number')}")
                print(f"  Date: {sale.get('sale_date')}")
                print(f"  Customer: {sale.get('customer_name')}")
                print(f"  Cashier: {sale.get('cashier_name')}")
                print(f"  User ID: {sale.get('user_id')}")
                print(f"  Total: {sale.get('total')}")
        else:
            print("No sales records found")
    else:
        print("Error:", response.text)
        
except Exception as e:
    print("Error:", e)

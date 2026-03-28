import requests
import json

# Test the sales API with date filtering
try:
    # Test without date filtering first
    response = requests.get('http://localhost:5000/api/sales')
    print("API Status (no filter):", response.status_code)
    
    if response.status_code == 200:
        sales_data = response.json()
        print(f"Total records without filter: {len(sales_data)}")
        
        if sales_data:
            # Print first record to check date format
            first_sale = sales_data[0]
            print(f"First sale date: {first_sale.get('sale_date')}")
            print(f"Date type: {type(first_sale.get('sale_date'))}")
    
    # Test with date filtering
    test_dates = [
        ('2024-03-04', '2024-03-04'),  # Same day
        ('2024-03-01', '2024-03-04'),  # Date range
    ]
    
    for date_from, date_to in test_dates:
        url = f'http://localhost:5000/api/sales?date_from={date_from}&date_to={date_to}'
        print(f"\nTesting URL: {url}")
        
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            filtered_data = response.json()
            print(f"Filtered records: {len(filtered_data)}")
            
            if filtered_data:
                print(f"First filtered date: {filtered_data[0].get('sale_date')}")
        else:
            print(f"Error: {response.text}")
            
except Exception as e:
    print(f"Error: {e}")

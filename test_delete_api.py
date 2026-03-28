import requests
import json

# Test the delete API endpoint
try:
    # Test getting users first
    response = requests.get('http://localhost:5000/api/users')
    print("Get users status:", response.status_code)
    if response.status_code == 200:
        users = response.json()
        print("Users:", users)
        if users:
            # Try to delete the first user (for testing)
            first_user = users[0]
            print(f"Attempting to delete user: {first_user['full_name']} (ID: {first_user['id']})")
            
            delete_response = requests.delete(f'http://localhost:5000/api/users/{first_user["id"]}')
            print("Delete response status:", delete_response.status_code)
            print("Delete response:", delete_response.text)
        else:
            print("No users found")
    else:
        print("Failed to get users:", response.text)
        
except Exception as e:
    print("Error:", e)

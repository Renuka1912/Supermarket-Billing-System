import sqlite3

conn = sqlite3.connect('supermarket.db')
cursor = conn.cursor()

# Find ravikumar in the database
cursor.execute("SELECT id, username, full_name, role, is_active FROM users WHERE full_name LIKE '%ravi%' OR username LIKE '%ravi%'")
users = cursor.fetchall()

print("Users matching 'ravi':")
for user in users:
    print(f"ID: {user[0]}, Username: {user[1]}, Name: {user[2]}, Role: {user[3]}, Active: {user[4]}")

if not users:
    print("No users found matching 'ravi'")
else:
    print(f"\nFound {len(users)} matching user(s)")

conn.close()

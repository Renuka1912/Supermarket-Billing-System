import sqlite3

conn = sqlite3.connect('supermarket.db')
cursor = conn.cursor()

# Delete ravikumar (ID: 2)
cursor.execute("DELETE FROM users WHERE id = 2")
deleted_rows = cursor.rowcount
conn.commit()

if deleted_rows > 0:
    print("✅ Successfully deleted 'ravikumar' from the database")
    print(f"Deleted {deleted_rows} user(s)")
else:
    print("❌ No user was deleted (user may not exist)")

conn.close()

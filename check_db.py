import pymysql

# Connect to MySQL server
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='gamehub_db'
)

try:
    with connection.cursor() as cursor:
        # Check user table structure
        cursor.execute("DESCRIBE user")
        columns = cursor.fetchall()
        print("User table columns:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")

        # Check if balance column exists
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        print(f"\nTotal users: {user_count}")

        if user_count > 0:
            cursor.execute("SELECT username, balance FROM user LIMIT 5")
            users = cursor.fetchall()
            print("\nSample users with balance:")
            for user in users:
                print(f"  {user[0]}: ${user[1]}")

finally:
    connection.close()

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
        # Add image column to game table
        try:
            cursor.execute("ALTER TABLE game ADD COLUMN image VARCHAR(255) DEFAULT 'https://via.placeholder.com/200x300?text=No+Image'")
            print("Added image column to game table.")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("image column already exists.")
            else:
                raise

    connection.commit()
finally:
    connection.close()

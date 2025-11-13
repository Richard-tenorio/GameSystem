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
        # Add balance column with default value
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN balance FLOAT NOT NULL DEFAULT 100.0")
            print("Added balance column to user table with default 100.0.")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("balance column already exists.")
            else:
                raise

    connection.commit()
finally:
    connection.close()

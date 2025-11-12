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
        # Add reset_token column
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN reset_token VARCHAR(100)")
            print("Added reset_token column to user table.")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("reset_token column already exists.")
            else:
                raise

        # Add reset_expires column
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN reset_expires DATETIME")
            print("Added reset_expires column to user table.")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("reset_expires column already exists.")
            else:
                raise

    connection.commit()
finally:
    connection.close()

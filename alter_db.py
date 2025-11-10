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
        cursor.execute("ALTER TABLE user MODIFY password_hash VARCHAR(256) NOT NULL")
        print("Altered password_hash column to VARCHAR(256).")
    connection.commit()
finally:
    connection.close()

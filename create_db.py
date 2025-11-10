import pymysql

# Connect to MySQL server (without specifying database)
connection = pymysql.connect(
    host='localhost',
    user='root',
    password=''
)

try:
    with connection.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS gamehub_db")
        print("Database 'gamehub_db' created successfully.")
    connection.commit()
finally:
    connection.close()

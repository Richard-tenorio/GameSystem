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
        cursor.execute("ALTER TABLE game_suggestion ADD COLUMN description TEXT")
        print("Added description column to game_suggestion table.")
    connection.commit()
finally:
    connection.close()

import pymysql
import os
from urllib.parse import urlparse

def add_user_fields():
    try:
        # Parse database URL from environment
        database_url = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost/gamehub_db'
        parsed = urlparse(database_url)

        # Extract connection details
        host = parsed.hostname or 'localhost'
        user = parsed.username or 'root'
        password = parsed.password or ''
        database = parsed.path.lstrip('/') or 'gamehub_db'

        # Connect to database
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with connection.cursor() as cursor:
            # Add email column (nullable first, then update)
            cursor.execute("""
                ALTER TABLE user
                ADD COLUMN email VARCHAR(120) AFTER username
            """)

            # Add full_name column
            cursor.execute("""
                ALTER TABLE user
                ADD COLUMN full_name VARCHAR(100) AFTER email
            """)

            # Add age column
            cursor.execute("""
                ALTER TABLE user
                ADD COLUMN age INT AFTER full_name
            """)

            # Update existing users with default values
            cursor.execute("""
                UPDATE user
                SET email = CONCAT(username, '@example.com'),
                    full_name = username,
                    age = 18
                WHERE email IS NULL OR full_name IS NULL OR age IS NULL
            """)

            # Now make columns NOT NULL and UNIQUE
            cursor.execute("""
                ALTER TABLE user
                MODIFY COLUMN email VARCHAR(120) NOT NULL UNIQUE,
                MODIFY COLUMN full_name VARCHAR(100) NOT NULL,
                MODIFY COLUMN age INT NOT NULL
            """)

        connection.commit()
        print("Successfully added email, full_name, and age columns to user table.")

    except Exception as e:
        print(f"Error adding columns: {e}")
        connection.rollback()

    finally:
        connection.close()

if __name__ == "__main__":
    add_user_fields()

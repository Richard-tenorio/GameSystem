from flask import Flask
from config import Config
from models import db, User, Game, Purchase, UserGame, Rating, GameSuggestion, TopupRequest
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print("Database Contents:")

    # Get all tables
    result = db.session.execute(text("SHOW TABLES"))
    tables = [row[0] for row in result]
    print(f"Total tables: {len(tables)}")
    print("Tables:", tables)
    print()

    # Contents of each table
    for table in tables:
        print(f"Table: {table}")
        try:
            result = db.session.execute(text(f"SELECT * FROM {table}"))
            rows = result.fetchall()
            if rows:
                columns = result.keys()
                print(f"Columns: {list(columns)}")
                for row in rows:
                    print(f"  {row}")
            else:
                print("  No data")
        except Exception as e:
            print(f"  Error: {e}")
        print()

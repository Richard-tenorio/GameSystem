from flask import Flask
from config import Config
from models import db
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])
    try:
        result = db.session.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
        print("Tables:", tables)
        for table in tables:
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            print(f"{table}: {count} rows")
    except Exception as e:
        print("Error:", e)

from flask import Flask
from config import Config
from models import db
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    result = db.session.execute(text("DESCRIBE topup_request"))
    columns = [row[0] for row in result]
    if 'status' not in columns:
        db.session.execute(text("ALTER TABLE topup_request ADD COLUMN status VARCHAR(20) DEFAULT 'pending'"))
        print("Added status column")
    db.session.commit()
    print("Migration complete")

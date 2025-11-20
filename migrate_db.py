from flask import Flask
from config import Config
from models import db
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Migrate GameSuggestion table
    result = db.session.execute(text("DESCRIBE game_suggestion"))
    columns = [row[0] for row in result]
    print("GameSuggestion columns:", columns)

    if 'description' not in columns:
        db.session.execute(text("ALTER TABLE game_suggestion ADD COLUMN description TEXT"))
        print("Added description column")

    if 'last_updated' not in columns:
        db.session.execute(text("ALTER TABLE game_suggestion ADD COLUMN last_updated DATETIME"))
        print("Added last_updated column")

    if 'updated_by' not in columns:
        db.session.execute(text("ALTER TABLE game_suggestion ADD COLUMN updated_by VARCHAR(80)"))
        print("Added updated_by column")

    # Migrate TopupRequest table
    result = db.session.execute(text("DESCRIBE topup_request"))
    columns = [row[0] for row in result]
    print("TopupRequest columns:", columns)

    if 'payment_method' not in columns:
        db.session.execute(text("ALTER TABLE topup_request ADD COLUMN payment_method VARCHAR(50)"))
        print("Added payment_method column")

    if 'reference_number' not in columns:
        db.session.execute(text("ALTER TABLE topup_request ADD COLUMN reference_number VARCHAR(50)"))
        print("Added reference_number column")

    if 'date_processed' not in columns:
        db.session.execute(text("ALTER TABLE topup_request ADD COLUMN date_processed DATETIME"))
        print("Added date_processed column")

    if 'processed_by' not in columns:
        db.session.execute(text("ALTER TABLE topup_request ADD COLUMN processed_by VARCHAR(80)"))
        print("Added processed_by column")

    db.session.commit()
    print("Migration complete")

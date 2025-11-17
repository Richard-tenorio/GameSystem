from models import db, GameSuggestion
from config import Config
from flask import Flask
import sqlalchemy as sa

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Check if columns exist
    inspector = sa.inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('game_suggestion')]

    print('Current GameSuggestion columns:', columns)

    # Add missing columns
    if 'installation_instructions' not in columns:
        print('Adding installation_instructions column...')
        with db.engine.connect() as conn:
            conn.execute(sa.text("ALTER TABLE game_suggestion ADD COLUMN installation_instructions TEXT"))
            conn.commit()
        print('installation_instructions column added.')

    if 'installation_file' not in columns:
        print('Adding installation_file column...')
        with db.engine.connect() as conn:
            conn.execute(sa.text("ALTER TABLE game_suggestion ADD COLUMN installation_file VARCHAR(255)"))
            conn.commit()
        print('installation_file column added.')

    print('Migration completed successfully!')

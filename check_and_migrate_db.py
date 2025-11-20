from flask import Flask
from config import Config
from models import db, User, Game, Purchase, UserGame, Rating, GameSuggestion, TopupRequest, Notification
from sqlalchemy import text, inspect

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def get_model_columns(model_class):
    """Get column names from SQLAlchemy model."""
    return [column.name for column in model_class.__table__.columns]

def get_db_columns(table_name):
    """Get column names from database table."""
    try:
        result = db.session.execute(text(f"DESCRIBE {table_name}"))
        return [row[0] for row in result]
    except Exception as e:
        print(f"Error describing table {table_name}: {e}")
        return []

def add_column(table_name, column_name, column_type):
    """Add a column to the table."""
    try:
        db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
        print(f"Added column {column_name} to {table_name}")
    except Exception as e:
        print(f"Error adding column {column_name} to {table_name}: {e}")

with app.app_context():
    models = [
        ('user', User),
        ('game', Game),
        ('purchase', Purchase),
        ('user_game', UserGame),
        ('rating', Rating),
        ('game_suggestion', GameSuggestion),
        ('topup_request', TopupRequest),
        ('notification', Notification)
    ]

    for table_name, model_class in models:
        print(f"\nChecking table: {table_name}")
        model_cols = get_model_columns(model_class)
        db_cols = get_db_columns(table_name)
        print(f"Model columns: {model_cols}")
        print(f"DB columns: {db_cols}")

        missing_cols = [col for col in model_cols if col not in db_cols]
        if missing_cols:
            print(f"Missing columns: {missing_cols}")
            # For each missing column, determine the type from the model
            for col_name in missing_cols:
                column = getattr(model_class.__table__.columns, col_name)
                col_type = str(column.type).upper()
                if column.nullable:
                    col_type += " NULL"
                else:
                    col_type += " NOT NULL"
                if column.default is not None:
                    col_type += f" DEFAULT {column.default.arg}"
                add_column(table_name, col_name, col_type)
        else:
            print("All columns present.")

    db.session.commit()
    print("\nMigration complete.")

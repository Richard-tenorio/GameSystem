from models import db, GameSuggestion
from config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print('Database columns for GameSuggestion:')
    cols = GameSuggestion.__table__.columns
    for col in cols:
        print(f'  {col.name}: {col.type}')

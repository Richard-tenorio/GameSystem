from models import db, Game
from config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    games = Game.query.all()
    print(f'Total games: {len(games)}')
    for g in games[:5]:  # Show first 5 games
        print(f'{g.title}: {g.image}')

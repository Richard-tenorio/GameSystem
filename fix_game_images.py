from flask import Flask
from config import Config
from models import db, Game

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    games = Game.query.all()
    for game in games:
        if not game.image or game.image == 'None':
            # Set a placeholder image URL
            placeholder_url = f"https://via.placeholder.com/200x300?text={game.title.replace(' ', '+')}"
            game.image = placeholder_url
            print(f"Updated {game.title} with placeholder: {placeholder_url}")
        else:
            print(f"{game.title} already has image: {game.image}")

    db.session.commit()
    print("All games updated with images")

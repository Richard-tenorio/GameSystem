import requests
from flask import Flask
from config import Config
from models import db, Game
import os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    games = Game.query.all()
    for game in games:
        if game.image and game.image.startswith('http'):
            try:
                response = requests.get(game.image)
                if response.status_code == 200:
                    # Generate a filename
                    ext = game.image.split('.')[-1].split('?')[0]  # get extension before ?
                    if '?' in ext:
                        ext = 'jpg'  # default
                    filename = f"game_{game.id}.{ext}"
                    filepath = os.path.join('static', 'uploads', filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    game.image = filename
                    db.session.commit()
                    print(f"Downloaded image for game {game.id} to {filename}")
                else:
                    print(f"Failed to download image for game {game.id}")
            except Exception as e:
                print(f"Error downloading image for game {game.id}: {e}")
        else:
            # Check if local file exists
            if game.image and not os.path.exists(os.path.join('static', 'uploads', game.image)):
                print(f"Local image file missing for game {game.id}: {game.image}")

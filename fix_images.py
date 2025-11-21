from flask import Flask
from config import Config
from models import db, Game
import os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Map game IDs to their image files based on the files in uploads
    image_files = {
        '9c46ffdc-c417-47ff-b8a7-d60bd974bb43.png': 1,
        'cab98ad1-216b-4f19-a27f-fd6af7d29f0b.jfif': 2,
        '0def9f3c-9a26-46da-a3fd-bc9c355dcab6.png': 3,
        '068738ed-5137-443a-81e1-33f76cb4e4d2.jpg': 12,
        '3a3667ed-22c3-465a-82c4-f1f6242e5acc.jpg': 10,
        '0b252c5f-8602-4635-8fe1-27ad03f0978e.png': 11
    }

    for filename, game_id in image_files.items():
        game = Game.query.get(game_id)
        if game:
            game.image = filename
            db.session.commit()
            print(f"Updated game {game_id} with image {filename}")

    print("Database updated with image filenames")

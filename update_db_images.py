from flask import Flask
from config import Config
from models import db, Game

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Update games with their image filenames
    updates = [
        (1, '9c46ffdc-c417-47ff-b8a7-d60bd974bb43.png'),
        (2, 'cab98ad1-216b-4f19-a27f-fd6af7d29f0b.jfif'),
        (3, '0def9f3c-9a26-46da-a3fd-bc9c355dcab6.png'),
        (10, '3a3667ed-22c3-465a-82c4-f1f6242e5acc.jpg'),
        (11, '0b252c5f-8602-4635-8fe1-27ad03f0978e.png'),
        (12, '068738ed-5137-443a-81e1-33f76cb4e4d2.jpg')
    ]

    for game_id, image_filename in updates:
        game = Game.query.get(game_id)
        if game:
            game.image = image_filename
            db.session.commit()
            print(f"Updated game {game_id} ({game.title}) with image {image_filename}")
        else:
            print(f"Game {game_id} not found")

    print("Database image update complete")

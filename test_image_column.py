from models import db, Game
from config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print('Testing image column...')
    try:
        # Check if image column exists
        game = Game.query.first()
        if game:
            print(f'Game found: {game.title}')
            print(f'Has image attribute: {hasattr(game, "image")}')
            print(f'Image value: {game.image}')
        else:
            print('No games in database')

        # Test creating a game with image
        new_game = Game(
            title='Test Game with Image',
            platform='PC',
            quantity=10,
            price=29.99,
            genre='Action',
            image='https://example.com/game-image.jpg'
        )
        db.session.add(new_game)
        db.session.commit()
        print('Successfully created game with image')

        # Clean up
        db.session.delete(new_game)
        db.session.commit()
        print('Test completed successfully')

    except Exception as e:
        print(f'Error: {e}')
        db.session.rollback()

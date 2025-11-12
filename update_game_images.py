from models import db, Game
from config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Sample game images - you can replace these with actual URLs
game_images = {
    'ss': 'https://images.unsplash.com/photo-1556438064-2d7646166914?w=400&h=600&fit=crop',
    'a': 'https://images.unsplash.com/photo-1511512578047-dfb367046420?w=400&h=600&fit=crop',
    'aa': 'https://images.unsplash.com/photo-1542751371-adc38448a05e?w=400&h=600&fit=crop',
    'dsf': 'https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?w=400&h=600&fit=crop',
    'asd': 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=400&h=600&fit=crop'
}

with app.app_context():
    games = Game.query.all()
    updated_count = 0

    for game in games:
        if game.title in game_images:
            game.image = game_images[game.title]
            updated_count += 1
            print(f'Updated {game.title} with image: {game.image}')

    if updated_count > 0:
        db.session.commit()
        print(f'Successfully updated {updated_count} games with custom images')
    else:
        print('No games were updated - titles did not match the sample images')

    # Show current state
    print('\nCurrent game images:')
    for game in games:
        print(f'{game.title}: {game.image}')

from models import db, User, Game
from config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print('=== BALANCE SYSTEM VERIFICATION ===')

    # Check if balance column exists in User model
    print(f'User model has balance attribute: {hasattr(User, "balance")}')

    # Check database connection and user count
    try:
        user_count = User.query.count()
        print(f'Total users in database: {user_count}')

        if user_count > 0:
            first_user = User.query.first()
            print(f'First user balance: ${first_user.balance}')
            print(f'First user: {first_user.username}')

        # Check if games exist for testing purchases
        game_count = Game.query.count()
        print(f'Total games in database: {game_count}')

        if game_count > 0:
            first_game = Game.query.first()
            print(f'First game: {first_game.title} - ${first_game.price}')

        print('\n✅ Balance system database setup verified!')
        print('✅ Ready for live testing at http://localhost:5000')

    except Exception as e:
        print(f'❌ Database error: {e}')

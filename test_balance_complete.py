from models import db, User, Game
from config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print('Testing database connection...')
    try:
        user = User.query.first()
        print('Database working correctly')
        print(f'User model has balance: {hasattr(User, "balance")}')
        print(f'First user balance: {user.balance if user else "No users"}')
        game = Game.query.first()
        print(f'First game price: {game.price if game else "No games"}')
        print('Balance system test completed successfully!')
    except Exception as e:
        print(f'Database error: {e}')

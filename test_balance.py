from models import db, User, Game, Purchase
from config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print('Testing balance system...')

    # Check if User model has balance attribute
    print(f'User model has balance: {hasattr(User, "balance")}')

    # Get first user and check balance
    user = User.query.first()
    if user:
        print(f'First user: {user.username}, Balance: ${user.balance:.2f}')
    else:
        print('No users found')

    # Check if there are any games
    game = Game.query.first()
    if game:
        print(f'First game: {game.title}, Price: ${game.price:.2f}')
    else:
        print('No games found')

    print('Balance system test completed.')

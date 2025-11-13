print('Testing database connection...')
from models import db, User
from config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print('Context entered')
    user = User.query.first()
    if user:
        print(f'User found: {user.username}')
        print(f'Balance: ${user.balance:.2f}')
        print(f'Has balance attribute: {hasattr(user, "balance")}')
    else:
        print('No users found')

    # Check if there are any games
    from models import Game
    game = Game.query.first()
    if game:
        print(f'Game found: {game.title}, Price: ${game.price:.2f}')
    else:
        print('No games found')

print('Test completed successfully')

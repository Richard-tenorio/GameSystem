from models import db, User
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
        print(f'User model has reset_token: {hasattr(User, "reset_token")}')
        print(f'User model has reset_expires: {hasattr(User, "reset_expires")}')
    except Exception as e:
        print(f'Database error: {e}')

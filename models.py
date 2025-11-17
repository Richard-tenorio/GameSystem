from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)  # Added index for frequent lookups
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='customer', index=True)  # Added index for role filtering
    balance = db.Column(db.Float, nullable=False, default=100.0)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_expires = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)  # Added index for title searches
    platform = db.Column(db.String(50), nullable=False, index=True)  # Added index for platform filtering
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    genre = db.Column(db.String(50), nullable=True, index=True)  # Added index for genre filtering
    image = db.Column(db.String(255), nullable=True, default=None)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False, index=True)  # Added index for username queries
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False, index=True)  # Added index for game_id queries
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)  # Added index for date sorting
    condition = db.Column(db.String(20), nullable=False, default='new')  # 'new' or 'used'
    price_paid = db.Column(db.Float, nullable=False)
    seller_username = db.Column(db.String(80), nullable=True)  # for used games
    game = db.relationship('Game', backref='purchases')

class UserGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False, index=True)  # Added index for username queries
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=True)  # Allow null for community games
    condition = db.Column(db.String(20), nullable=False, default='new')
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)  # Added index for date sorting
    listed_for_sale = db.Column(db.Boolean, nullable=False, default=False, index=True)  # Added index for marketplace queries
    sale_price = db.Column(db.Float, nullable=True)
    # For community games
    title = db.Column(db.String(100), nullable=True)
    platform = db.Column(db.String(50), nullable=True)
    genre = db.Column(db.String(50), nullable=True)
    game = db.relationship('Game', backref='user_games')

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False, index=True)  # Added index for username queries
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False, index=True)  # Added index for game_id queries
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)  # Added index for date sorting
    game = db.relationship('Game', backref='ratings')

class GameSuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)  # Added index for title searches
    platform = db.Column(db.String(50), nullable=False, index=True)  # Added index for platform filtering
    genre = db.Column(db.String(50), nullable=True, index=True)  # Added index for genre filtering
    description = db.Column(db.Text, nullable=True)
    installation_instructions = db.Column(db.Text, nullable=False)  # Required installation instructions
    installation_file = db.Column(db.String(255), nullable=True, default=None)  # Optional installation file
    suggested_by = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False, index=True)  # Added index for user queries
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)  # Added index for status filtering
    date_suggested = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)  # Added index for date sorting
    image = db.Column(db.String(255), nullable=True, default=None)  # Store image filename for suggestions

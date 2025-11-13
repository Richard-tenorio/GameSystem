from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='customer')
    balance = db.Column(db.Float, nullable=False, default=100.0)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_expires = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    genre = db.Column(db.String(50), nullable=True)
    image = db.Column(db.String(255), nullable=True, default='https://via.placeholder.com/200x300?text=No+Image')

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    condition = db.Column(db.String(20), nullable=False, default='new')  # 'new' or 'used'
    price_paid = db.Column(db.Float, nullable=False)
    seller_username = db.Column(db.String(80), nullable=True)  # for used games
    game = db.relationship('Game', backref='purchases')

class UserGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=True)  # Allow null for community games
    condition = db.Column(db.String(20), nullable=False, default='new')
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    listed_for_sale = db.Column(db.Boolean, nullable=False, default=False)
    sale_price = db.Column(db.Float, nullable=True)
    # For community games
    title = db.Column(db.String(100), nullable=True)
    platform = db.Column(db.String(50), nullable=True)
    genre = db.Column(db.String(50), nullable=True)
    game = db.relationship('Game', backref='user_games')

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    game = db.relationship('Game', backref='ratings')

class GameSuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    genre = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    suggested_by = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'approved', 'rejected'
    date_suggested = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

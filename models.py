from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='customer', index=True)
    balance = db.Column(db.Float, nullable=False, default=100.0)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_expires = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    platform = db.Column(db.String(50), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    genre = db.Column(db.String(50), nullable=True, index=True)
    image = db.Column(db.String(255), nullable=True, default=None)
    installation_file = db.Column(db.String(255), nullable=True, default=None)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False, index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False, index=True)
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    condition = db.Column(db.String(20), nullable=False, default='new')
    price_paid = db.Column(db.Float, nullable=False)
    sale_username = db.Column(db.String(80), nullable=True)
    game = db.relationship('Game', backref='purchases')

class UserGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False, index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=True)
    condition = db.Column(db.String(20), nullable=False, default='new')
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    listed_for_sale = db.Column(db.Boolean, nullable=False, default=False, index=True)
    sale_price = db.Column(db.Float, nullable=True)
    title = db.Column(db.String(100), nullable=True)
    platform = db.Column(db.String(50), nullable=True)
    genre = db.Column(db.String(50), nullable=True)
    game = db.relationship('Game', backref='user_games')

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False, index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    game = db.relationship('Game', backref='ratings')

class GameSuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    platform = db.Column(db.String(50), nullable=False, index=True)
    genre = db.Column(db.String(50), nullable=True, index=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    description = db.Column(db.Text, nullable=True)
    installation_instructions = db.Column(db.Text, nullable=False)
    installation_file = db.Column(db.String(255), nullable=True, default=None)
    suggested_by = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    date_suggested = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    image = db.Column(db.String(255), nullable=True, default=None)
    last_updated = db.Column(db.DateTime, nullable=True, default=None)
    updated_by = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=True, default=None)

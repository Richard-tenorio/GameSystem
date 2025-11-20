from flask import Flask
from config import Config
from models import db, User, Purchase, UserGame, Rating, GameSuggestion, TopupRequest, Notification

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Update User table
    User.query.filter_by(username='Admin3').update({'username': 'Richard'})
    User.query.filter_by(username='Richard').update({'email': 'tenoriormilos@gmail.com'})
    db.session.commit()
    print("Updated User table")

    # Update Purchase table
    Purchase.query.filter_by(username='Admin3').update({'username': 'Richard'})
    db.session.commit()
    print("Updated Purchase table")

    # Update UserGame table
    UserGame.query.filter_by(username='Admin3').update({'username': 'Richard'})
    db.session.commit()
    print("Updated UserGame table")

    # Update Rating table
    Rating.query.filter_by(username='Admin3').update({'username': 'Richard'})
    db.session.commit()
    print("Updated Rating table")

    # Update GameSuggestion table for suggested_by
    GameSuggestion.query.filter_by(suggested_by='Admin3').update({'suggested_by': 'Richard'})
    # Also for updated_by
    GameSuggestion.query.filter_by(updated_by='Admin3').update({'updated_by': 'Richard'})
    db.session.commit()
    print("Updated GameSuggestion table")

    # Update TopupRequest table for username
    TopupRequest.query.filter_by(username='Admin3').update({'username': 'Richard'})
    # Also for processed_by
    TopupRequest.query.filter_by(processed_by='Admin3').update({'processed_by': 'Richard'})
    db.session.commit()
    print("Updated TopupRequest table")

    # Update Notification table
    Notification.query.filter_by(username='Admin3').update({'username': 'Richard'})
    db.session.commit()
    print("Updated Notification table")

    print("All username updates completed.")

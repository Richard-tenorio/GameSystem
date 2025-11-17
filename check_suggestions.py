from flask import Flask
from config import Config
from models import db, GameSuggestion

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    suggestions = GameSuggestion.query.filter_by(status='approved').all()
    print('Approved suggestions:')
    for s in suggestions:
        print(f'ID: {s.id}, Title: {s.title}, Image: {s.image}')

    # Check suggestion ID 4 specifically
    suggestion_4 = GameSuggestion.query.filter_by(id=4).first()
    if suggestion_4:
        print(f'\nSuggestion ID 4 details:')
        print(f'Title: {suggestion_4.title}')
        print(f'Image: {suggestion_4.image}')
        print(f'Status: {suggestion_4.status}')

        # Update the image if it's None
        if suggestion_4.image is None:
            suggestion_4.image = 'suggestion_4_45f0bfff.png'
            db.session.commit()
            print('Updated image for suggestion 4 to: suggestion_4_45f0bfff.png')

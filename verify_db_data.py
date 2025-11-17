from models import db, GameSuggestion
from config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print('Checking GameSuggestion table data...')
    suggestions = GameSuggestion.query.all()

    if not suggestions:
        print('No GameSuggestion records found in database.')
    else:
        print(f'Found {len(suggestions)} GameSuggestion records:')
        for suggestion in suggestions:
            print(f'\nID: {suggestion.id}')
            print(f'Title: {suggestion.title}')
            print(f'Platform: {suggestion.platform}')
            print(f'Installation Instructions: {suggestion.installation_instructions or "None"}')
            print(f'Installation File: {suggestion.installation_file or "None"}')
            print(f'Status: {suggestion.status}')
            print('-' * 50)

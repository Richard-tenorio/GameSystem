from flask import Flask
from config import Config
from models import db, User

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Find the user with username 'Admin3'
    admin_user = User.query.filter_by(username='Admin3').first()

    if admin_user:
        print(f"Found user: {admin_user.username}")
        # Update the username to 'Richard'
        admin_user.username = 'Richard'
        db.session.commit()
        print("Successfully updated Admin3 to Richard")
    else:
        print("User 'Admin3' not found in database")

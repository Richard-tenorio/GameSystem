from flask import Flask
from config import Config
from models import db, User

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', full_name='Administrator', age=30, role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: username=admin, password=admin123")
    else:
        print("Admin user already exists")

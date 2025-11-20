from flask import Flask
from config import Config
from models import db, TopupRequest

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    topups = TopupRequest.query.all()
    print(f"Total topup requests: {len(topups)}")
    for topup in topups:
        print(f"ID: {topup.id}, Username: {topup.username}, Amount: {topup.amount}, Payment Method: {topup.payment_method}, Reference: {topup.reference_number}, Status: {topup.status}, Date: {topup.date_requested}")

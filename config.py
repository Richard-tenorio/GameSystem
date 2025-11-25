import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost/gamehub_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'another-fallback-secret-key'

    # Database connection pooling for better performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Test connections before using them
        'pool_recycle': 300,    # Recycle connections after 5 minutes
        'pool_size': 10,        # Maintain 10 connections in pool
        'max_overflow': 20,     # Allow up to 20 additional connections
    }

    # Email configuration for OTP - Dynamic sending to each user's email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = 'tenoriormilos@gmail.com'  # Your Gmail address
    MAIL_PASSWORD = 'xury qvnw zckb cvwr'  # Your Gmail app password

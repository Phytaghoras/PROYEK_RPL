# app/config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'bebasdehmauapa')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'  # URL untuk database SQLite
    SQLALCHEMY_TRACK_MODIFICATIONS = False

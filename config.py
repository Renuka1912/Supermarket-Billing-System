import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = 'supermarket-billing-secret-key-2024'
DATABASE = os.path.join(BASE_DIR, 'supermarket.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

DEBUG = True

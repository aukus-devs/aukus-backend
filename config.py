import os
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SESSION_SECRET = os.getenv("FLASK_SESSION_SECRET")
UPLOAD_FOLDER = '/static/uploads'

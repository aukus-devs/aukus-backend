import logging
import os

ENV = os.getenv("ENV", "local")
DB_URL = os.getenv("DB_URL", "")

IS_LOCAL = ENV == "local"

DATABASE_URL = "mysql+asyncmy://root:pass@127.0.0.1:3306/aukus4" if IS_LOCAL else DB_URL

TOKEN_SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")

EVENTLAB_API_URL = os.getenv("EVENTLAB_API_URL", "http://localhost:8300")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

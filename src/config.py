import logging
import os
import sys

ENV = os.getenv("ENV", "local")
DB_URL = os.getenv("DB_URL", "")

IS_LOCAL = ENV == "local"

DATABASE_URL = "mysql+asyncmy://root:pass@127.0.0.1:3306/aukus4" if IS_LOCAL else DB_URL

TOKEN_SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")

EVENTLAB_API_URL = "http://localhost:8300" if IS_LOCAL else "https://api.eventlab.dev"

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "eventlab")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "")
S3_FOLDER = os.getenv("S3_FOLDER", "aukus4-uploads")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "https://storage.yandexcloud.net")
S3_REGION_NAME = os.getenv("S3_REGION_NAME", "ru-central1")

EMOTES_CDN_PROXY = os.getenv("EMOTES_CDN_PROXY", "https://cdn.rhhhhhhh.live/")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

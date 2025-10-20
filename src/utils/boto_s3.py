import os
import logging
from boto.s3.key import Key
from boto.s3.connection import S3Connection
import urllib.parse
from dotenv import load_dotenv

from src.config import IS_LOCAL


load_dotenv()
os.environ["S3_USE_SIGV4"] = "True"


def init_s3_connection():
    if IS_LOCAL:
        return None, None

    try:
        conn = S3Connection(host="storage.yandexcloud.net")  # pyright: ignore[reportArgumentType]
        conn.auth_region_name = "ru-central1"
        bucket_name = os.getenv("S3_BUCKET_NAME")
        bucket = conn.get_bucket(bucket_name)
        return bucket, bucket_name
    except Exception as e:
        logging.error(f"init_s3_connection error: {e}")
        return None, None


bucket, bucket_name = init_s3_connection()


def upload_file_s3(file, file_id) -> tuple[str | None, Exception | None]:
    try:
        file_key_1 = Key(bucket)
        file_key_1.key = file_id
        file_key_1.set_contents_from_file(file)
        return (
            f"""https://storage.yandexcloud.net/{bucket_name}/{urllib.parse.quote(file_id, safe="~()*!.'")}""",
            None,
        )
    except Exception as e:
        logging.error(f"upload_file_s3 error: {e}")
        return None, e


def delete_file_s3(file_id):
    try:
        logging.info(f"Trying delete file {file_id}")
        file_key_1 = Key(bucket)
        file_key_1.key = file_id
        file_key_1.delete()
        return True
    except Exception as e:
        logging.error(f"delete_file_s3 error: {e}")
        return False

import logging
import boto3
import urllib.parse
import io
from dotenv import load_dotenv

from src.config import (
    IS_LOCAL,
    S3_BUCKET_NAME,
    S3_ACCESS_KEY_ID,
    S3_SECRET_ACCESS_KEY,
    S3_FOLDER,
    S3_ENDPOINT_URL,
    S3_REGION_NAME,
)


load_dotenv()


def init_s3_connection():
    logging.info("Initializing S3 connection...")

    if IS_LOCAL:
        logging.info("Running in local mode, S3 connection disabled")
        return None, None

    try:
        logging.info("Creating S3 client for Yandex Cloud...")
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            endpoint_url=S3_ENDPOINT_URL,
            region_name=S3_REGION_NAME,
        )
        bucket_name = S3_BUCKET_NAME

        if not bucket_name:
            logging.error("S3_BUCKET_NAME environment variable not set")
            return None, None

        logging.info(f"S3 client created successfully, bucket: {bucket_name}")
        return s3_client, bucket_name
    except Exception as e:
        logging.error(f"init_s3_connection error: {e}")
        return None, None


_s3_client = None
_bucket_name = None


def get_s3_client():
    global _s3_client, _bucket_name
    if _s3_client is None:
        logging.info("S3 client not initialized, creating new connection...")
        _s3_client, _bucket_name = init_s3_connection()
    else:
        logging.debug("Using existing S3 client")
    return _s3_client, _bucket_name


async def upload_file_s3(file, file_id) -> tuple[str | None, Exception | None]:
    try:
        s3_client, bucket_name = get_s3_client()
        if not s3_client or not bucket_name:
            return None, Exception("S3 client not initialized")

        s3_key = f"{S3_FOLDER}/{file_id}" if S3_FOLDER else file_id

        file_content = await file.read()

        file_obj = io.BytesIO(file_content)

        s3_client.upload_fileobj(file_obj, bucket_name, s3_key)
        return (
            f"""{S3_ENDPOINT_URL}/{bucket_name}/{urllib.parse.quote(s3_key, safe="~()*!.'")}""",
            None,
        )
    except Exception as e:
        logging.error(f"upload_file_s3 error: {e}")
        return None, e


def delete_file_s3(file_id):
    try:
        logging.info(f"Trying delete file {file_id}")
        s3_client, bucket_name = get_s3_client()
        if not s3_client or not bucket_name:
            logging.error("S3 client not initialized")
            return False

        s3_key = f"{S3_FOLDER}/{file_id}" if S3_FOLDER else file_id

        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        return True
    except Exception as e:
        logging.error(f"delete_file_s3 error: {e}")
        return False

import os
import logging
from boto.s3.key import Key
from boto.s3.connection import S3Connection
os.environ['S3_USE_SIGV4'] = 'True'
conn = S3Connection(
    host='storage.yandexcloud.net'
)
conn.auth_region_name = 'ru-central1'

bucket = conn.get_bucket('aukus-2025-prod')


def upload_file_s3(file, file_id) -> tuple[str | None, Exception | None]:
    try:
        file_key_1 = Key(conn.get_bucket('aukus-2025-prod2'))
        file_key_1.key = file_id
        file_key_1.set_contents_from_file(file)
        return f'https://storage.yandexcloud.net/aukus-2025-prod/{file_id}', None
    except Exception as e:
        logging.error(f"upload_file_s3 error: {e}")
        return None, e


def delete_file_s3(file_id):
    try:
        file_key_1 = Key(bucket)
        file_key_1.key = file_id
        file_key_1.delete()
        return True
    except Exception as e:
        logging.error(f"delete_file_s3 error: {e}")
        return False

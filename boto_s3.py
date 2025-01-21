import os
from boto.s3.key import Key
from boto.s3.connection import S3Connection
os.environ['S3_USE_SIGV4'] = 'True'
conn = S3Connection(
    host='storage.yandexcloud.net'
)
conn.auth_region_name = 'ru-central1'

bucket = conn.get_bucket('aukus-2025-prod')


def upload_file_s3(file, file_id):
    file_key_1 = Key(bucket)
    file_key_1.key = file_id
    file_key_1.set_contents_from_file(file)
    return f'https://storage.yandexcloud.net/aukus-2025-prod/{file_id}'


def delete_file_s3(file_id):
    file_key_1 = Key(bucket)
    file_key_1.key = file_id
    file_key_1.delete()

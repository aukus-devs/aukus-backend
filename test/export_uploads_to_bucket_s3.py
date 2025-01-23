from db_client.db_client import DatabaseClient
import os
from boto.s3.key import Key
from boto.s3.connection import S3Connection
import urllib.parse

conn = S3Connection(host="storage.yandexcloud.net")
conn.auth_region_name = "ru-central1"
bucket_name = "aukus-2024-prod"
bucket = conn.get_bucket(bucket_name)

db = DatabaseClient()

players = db.get_all_users(False)

for player in players:
    files = db.get_player_files_dict_by_player_id(player["id"])
    if files:
        for file in files:
            #            print(file)
            file_path = file["url"]
            file_id = urllib.parse.quote_plus(file["url"].replace("/uploads/", ""))
            file_key_1 = Key(bucket)
            file_key_1.key = file_id
            file_key_1.set_contents_from_filename(f'static{file["url"]}')
            db.update_player_files_url_by_file_id(
                file_id=file["id"],
                url=f"https://storage.yandexcloud.net/{bucket_name}/{file_id}",
            )

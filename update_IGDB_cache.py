from db_client.db_client import DatabaseClient
from db_client.games_db_client import GamesDatabaseClient
from requests_cache import CachedSession
import json
import os
from dotenv import load_dotenv
import logging
from datetime import timedelta
import time

load_dotenv()
IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
igdb_session = CachedSession("igdb_cache", expire_after=timedelta(days=25), allowable_methods=['GET', 'POST'])
db = DatabaseClient()
games_db = GamesDatabaseClient()

playermoves = db.get_all_moves(limit=1000)
for move in playermoves:
    try:
        print("Get info for: " + move["item_title"].lower())
        igdb_token = db.get_igdb_token()["igdb_token"]
        headers = {"Client-ID": IGDB_CLIENT_ID, "Authorization": "Bearer " + igdb_token}
        wrong_platforms = games_db.get_wrong_platforms()
        payload_fix = ""
        for platform in wrong_platforms:
            payload_fix += "|id=" + str(platform["platform_id"])
        payload = ('fields id,name,cover.image_id, first_release_date; limit 50; where name ~ *"' + move["item_title"].lower() + '"* & (platforms = [6]' + payload_fix +');').encode('utf-8')
        response = igdb_session.post("https://api.igdb.com/v4/games", headers=headers, data=payload, timeout=2)
        print("IGDB response: " + response.text)
        time.sleep(0.5)
    except Exception as e:
        logging.error("Error: " + str(e))

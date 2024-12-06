from functools import wraps
from flask import Blueprint, request, jsonify, session
from db_client.db_client import DatabaseClient
from db_client.games_db_client import GamesDatabaseClient
from datetime import date
import secrets
from requests_cache import CachedSession
from datetime import timedelta
import json
import os
from dotenv import load_dotenv
import logging
import urllib.parse

db = DatabaseClient()
games_db = GamesDatabaseClient()
load_dotenv()
IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
igdb_session = CachedSession("igdb_cache", expire_after=timedelta(days=25), allowable_methods=['GET', 'POST'])

def search_igdb(title: str):
    igdb_token = db.get_igdb_token()["igdb_token"]
    wrong_platforms = games_db.get_wrong_platforms()
    payload_fix = ""
    for platform in wrong_platforms:
        payload_fix += "|id=" + str(platform["platform_id"])
    headers = {"Client-ID": IGDB_CLIENT_ID, "Authorization": "Bearer " + igdb_token}
    payload = ('fields id,name,cover.image_id, first_release_date; limit 50; where name ~ *"' + title.lower() + '"* & (platforms = [6]' + payload_fix +');').encode('utf-8')
    games = []
    try:
        response = igdb_session.post("https://api.igdb.com/v4/games", headers=headers, data=payload, timeout=2)
        if response.ok and "name" in response.text and len(response.text) > 2:
            games_json = json.loads(response.content.decode('utf-8'))
            for game in games_json:
                games.append({
                    "id": game["id"],
                    "gameName": game["name"],
                    "first_release_date": game["first_release_date"] if "first_release_date" in game else 0,
                    "box_art_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/" + game["cover"]["image_id"] + ".jpg" if "cover" in game else ""
                })
    except Exception as e:
        logging.error("IGDB search failed: " + str(e))
    return games


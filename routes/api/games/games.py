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

games_bp = Blueprint("games", __name__)
db = DatabaseClient()
games_db = GamesDatabaseClient()
load_dotenv()
IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
igdb_session = CachedSession("igdb_cache", expire_after=timedelta(days=25), allowable_methods=['GET', 'POST'])

@games_bp.route("/api/games", methods=["GET"])
def search_games():
    raw_query_string = request.query_string.decode()
    args = urllib.parse.parse_qs(raw_query_string, separator=' ')
    if not "title" in args:
        return jsonify({"error": f"Missing required field: title"}), 400
    title = args["title"][0].lower()
    igdb_token = db.get_igdb_token()["igdb_token"]
    headers = {"Client-ID": IGDB_CLIENT_ID, "Authorization": "Bearer " + igdb_token}
    payload = ('fields id,name,cover.image_id; limit 50; where name ~ *"' + title + '"*;').encode('utf-8')
    games = []
    try:
        response = igdb_session.post("https://api.igdb.com/v4/games", headers=headers, data=payload, timeout=1)
        if response.ok and "name" in response.text and len(response.text) > 2:
            games_json = json.loads(response.content.decode('utf-8'))
            for game in games_json:
                games.append({
                    "id": game["id"],
                    "gameName": game["name"],
                    "box_art_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/" + game["cover"]["image_id"] + ".jpg" if "cover" in game else ""
                })
        else:
            games = games_db.search_games(title)
    except:
        games.extend(games_db.search_games(title))
    return jsonify({"games": games})

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

games_bp = Blueprint("games", __name__)
db = DatabaseClient()
games_db = GamesDatabaseClient()
load_dotenv()
IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
igdb_session = CachedSession("igdb_cache", expire_after=timedelta(days=25), allowable_methods=['GET', 'POST'])

@games_bp.route("/api/games", methods=["GET"])
def search_games():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": f"Missing required field: title"}), 400
    if len(title) == 0:
        return jsonify({"games": []})
    igdb_token = db.get_igdb_token()["igdb_token"]
    headers = {"Client-ID": IGDB_CLIENT_ID, "Authorization": "Bearer " + igdb_token}
    response = igdb_session.post("https://api.igdb.com/v4/games", headers=headers, data='search "' + title + '"; fields id, name, cover.image_id;', timeout=1)
    games = None
    if response.ok and "name" in response.text and len(response.text) > 2:
        games = []
        games_json = json.loads(response.content.decode('utf-8'))
        for game in games_json:
            games.append({
                "id": game["id"],
                "gameName": game["name"],
                "box_art_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/" + game["cover"]["image_id"] + ".jpg" if "cover" in game else ""
            })
    else:
        games = games_db.search_games(title)
    return jsonify({"games": games})

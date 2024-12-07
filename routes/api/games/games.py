from functools import wraps
from flask import Blueprint, request, jsonify, session
from db_client.db_client import DatabaseClient
from db_client.games_db_client import GamesDatabaseClient
from datetime import date
import secrets
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
    games = games_db.search_games_igdb(title)
    return jsonify({"games": games})

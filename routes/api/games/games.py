from functools import wraps
from flask import Blueprint, request, jsonify, session
from db_client.games_db_client import GamesDatabaseClient
from datetime import date
import secrets

games_bp = Blueprint("games", __name__)
db = GamesDatabaseClient()


@games_bp.route("/api/games", methods=["GET"])
def search_games():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": f"Missing required field: title"}), 400
    games = db.search_games(title)
    return jsonify({"games": games})

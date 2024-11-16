from functools import wraps
from flask import Blueprint, request, jsonify, session
from db_client.games_db_client import GamesDatabaseClient
from datetime import date
import secrets

games_bp = Blueprint("games", __name__)
db = GamesDatabaseClient()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session and "role" not in session:
            return jsonify({"error": f"Auth required"}), 401
        return f(*args, **kwargs)

    return decorated_function


@games_bp.route("/api/games", methods=["GET"])
@login_required
def search_games():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": f"Missing required field: title"}), 400
    games = db.search_games(title)
    return jsonify({"games": games})

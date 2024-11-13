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


def available_for_roles(roles=None):
    if roles is None:
        roles = ["player", "moder", "admin"]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "username" not in session and "role" not in session:
                return jsonify({"error": f"Auth required"}), 401
            if session["role"] not in roles:
                return jsonify({"error": f"Forbidden"}), 403
            return f(*args, **kwargs)

        return decorated_function

    return decorator


@games_bp.route("/api/games", methods=["GET"])
def get_players():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": f"Missing required field: title"}), 400
    games = db.search_games(title)
    return jsonify({"games": games})

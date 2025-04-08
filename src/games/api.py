from flask import Blueprint, request, jsonify
import urllib.parse
from src.games.queries import search_games_igdb

games_bp = Blueprint("games", __name__)


@games_bp.route("/api/games", methods=["GET"])
def search_games():
    raw_query_string = request.query_string.decode()
    args = urllib.parse.parse_qs(raw_query_string, separator=" ")
    if not "title" in args:
        return jsonify({"error": "Missing required field: title"}), 400
    title = args["title"][0].lower()
    games = search_games_igdb(title)
    return jsonify({"games": games})

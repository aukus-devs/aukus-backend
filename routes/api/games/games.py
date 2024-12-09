from functools import wraps
from flask import Blueprint, request, jsonify, session
from db_client.games_db_client import GamesDatabaseClient
from datetime import date
import secrets
from datetime import timedelta
import json
import os
from dotenv import load_dotenv
import logging
import urllib.parse
from howlongtobeatpy import HowLongToBeat

games_bp = Blueprint("games", __name__)
games_db = GamesDatabaseClient()
load_dotenv()


@games_bp.route("/test_api/games", methods=["GET"])
def search_games():
    raw_query_string = request.query_string.decode()
    args = urllib.parse.parse_qs(raw_query_string, separator=' ')
    if not "title" in args:
        return jsonify({"error": f"Missing required field: title"}), 400
    title = args["title"][0].lower()
    games = games_db.search_games_igdb(title)
    return jsonify({"games": games})


@games_bp.route("/test_api/hltb", methods=["GET"])
def search_htlb():
    raw_query_string = request.query_string.decode()
    args = urllib.parse.parse_qs(raw_query_string, separator=' ')
    if not "title" in args:
        return jsonify({"error": f"Missing required field: title"}), 400
    title = args["title"][0].lower()
    results = HowLongToBeat().search(title)
    hltb_games = []
    for game in results:
        hltb_games.append({
            "gameName": game.game_name,
            "mainStory": game.main_story,
            "mainExtra": game.main_extra,
            "completionist": game.completionist,
            "all_styles": game.all_styles,
            "release_world": game.release_world,
            "profile_platforms": game.profile_platforms,
            "game_image_url": game.game_image_url,
        })
    return jsonify({"hltb_games": hltb_games})

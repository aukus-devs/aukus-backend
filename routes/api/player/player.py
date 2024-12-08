from functools import wraps
from db_client.games_db_client import GamesDatabaseClient
from flask import Blueprint, request, jsonify, session
from db_client.db_client import DatabaseClient
from datetime import date
import secrets
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import json
import os
from dotenv import load_dotenv
import logging
import notifications

player_bp = Blueprint("player", __name__)
scheduler = BackgroundScheduler()
db = DatabaseClient()
games_db = GamesDatabaseClient()
load_dotenv()
scheduler.start()


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


@player_bp.route("/api/dons", methods=["GET"])
def get_dons():
    dons_data = db.get_dons()
    dons = []
    for donate in dons_data:
        dons.append({
            "name": donate["name"],
            "text": donate["text"],
            "type": "big" if int(donate["sum"]) >= 5000 else "small",
        })
    return jsonify({"dons": dons})


@player_bp.route("/api/players", methods=["GET"])
def get_players():
    move_id = request.args.get("move_id")
    players_data = db.get_all_players()
    if move_id:
        last_cells = db.get_players_positions_by_move_id(move_id)
    else:
        last_cells = db.get_players_last_cell_number()
    players = []
    players_games = [
        player["player_current_game"] for player in players_data
        if player["player_current_game"]
    ]
    games_images = games_db.search_games_multiple_igdb(players_games)
    games_images_by_name = {
        game["gameName"].lower(): game["box_art_url"]
        for game in games_images
    }

    for player in players_data:
        last_cell = next(
            (cell["cell_to"]
             for cell in last_cells if cell["player_id"] == player["id"]),
            0,
        )
        image = None
        if player["player_current_game"]:
            image = games_images_by_name.get(
                player["player_current_game"].lower())
        current_game_duration = None
        if player["player_current_game"] != None:
            current_game_duration = db.calculate_time_by_category_name(
                player["player_current_game"],
                player["id"])["total_difference_in_seconds"]
        if current_game_duration is None:
            current_game_duration = 0

        player_info = {
            "id": player["id"],
            "name": player["username"],
            "twitch_stream_link": player["twitch_stream_link"],
            "vk_stream_link": player["vk_stream_link"],
            "kick_stream_link": player["kick_stream_link"],
            "donation_link": player["donation_link"],
            "stream_last_category": player["player_stream_current_category"],
            "is_online": bool(player["player_is_online"]),
            "online_count": int(player["online_count"]),
            "current_game": player["player_current_game"],
            "current_game_duration": int(current_game_duration),
            "current_auction_total_sum": player["current_auction_total_sum"],
            "auction_timer_started_at": player["auction_timer_started_at"],
            "url_handle": player["player_url_handle"],
            "map_position": last_cell,
            "first_name": player["name"],
            "last_name": player["surname"],
            "current_game_updated_at": player["current_game_updated_at"],
            "telegram_link": player["telegram_link"],
            "current_game_image": image,
        }
        players.append(player_info)

    return jsonify({"players": players})


@player_bp.route("/api/player_move", methods=["POST"])
@login_required
def add_player_move():
    data = request.get_json()
    required_fields = [
        "player_id", "dice_roll", "type", "item_title", "item_review"
    ]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    if data.get("stair_from") and data.get("snake_from"):
        return jsonify(
            {"error": f"Stair and snake cannot be used at the same time"}), 400

    last_cells = db.get_players_last_cell_number()
    last_cell_number = next(
        (cell["cell_to"]
         for cell in last_cells if cell["player_id"] == data["player_id"]),
        0,
    )

    try:
        player_id = data["player_id"]
        dice_roll = data["dice_roll"]
        cell_from = last_cell_number
        cell_to = data["move_to"]
        stair_from = data.get("stair_from")
        stair_to = data.get("stair_to")
        snake_from = data.get("snake_from")
        snake_to = data.get("snake_to")
        move_type = data["type"]
        item_title = data["item_title"]
        item_review = data["item_review"]
        item_rating = data.get("item_rating")
        item_length = data.get("item_length")

        db.add_player_move(
            player_id=player_id,
            dice_roll=dice_roll,
            cell_from=cell_from,
            cell_to=cell_to,
            stair_from=stair_from,
            stair_to=stair_to,
            snake_from=snake_from,
            snake_to=snake_to,
            move_type=move_type,
            item_title=item_title,
            item_review=item_review,
            item_rating=item_rating,
            item_length=item_length,
        )
        db.update_last_auction_result_by_player_id(player_id, None, None)
        try:
            category_time_duration = db.calculate_time_by_category_name(
                item_title, player_id)["total_difference_in_seconds"]
            scheduler.add_job(notifications.on_player_move,
                              args=[
                                  db.get_user_by_id(player_id)["username"],
                                  dice_roll, cell_from, cell_to, move_type,
                                  item_title, item_review, item_rating,
                                  category_time_duration
                              ])
        except Exception as e:
            logging.error("Error send notification on player move: " + str(e))
        return jsonify(
            {"message":
             "Player move added and position updated successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@player_bp.route("/api/player_move_vod_link", methods=["POST"])
@login_required
def add_vod_link_to_player_move():
    data = request.get_json()
    required_fields = ["vod_link", "title", "move_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        vod_link = data["vod_link"]
        title = data["title"]
        move_id = data["move_id"]

        player_move = db.get_move_by_id(move_id)
        if player_move:
            db.update_player_move_vod_link(move_id=move_id,
                                           vod_link=vod_link,
                                           title=title)
            return jsonify(
                {"message": "Player move vod link updated successfully"}), 200
        else:
            return jsonify(
                {"error": f"Player move with id {move_id} not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@player_bp.route("/api/player_stats", methods=["GET"])
def player_stats():
    # Получаем информацию обо всех игроках
    players_stats = db.get_players_stats()
    # Формируем JSON-ответ
    players = []
    for stats in players_stats:
        player_info = {
            "id": stats["player_id"],
            "map_position": int(stats["map_position"]),
            "total_moves": int(stats["total_moves"]),
            "games_completed": int(stats["games_completed"]),
            "games_dropped": int(stats["games_dropped"]),
            "sheikh_moments": int(stats["sheikh_moments"]),
            "rerolls": int(stats["rerolls"]),
            "movies": int(stats["movies"]),
            "ladders": int(stats["ladders"]),
            "snakes": int(stats["snakes"]),
            "tiny_games": int(stats["tiny_games"]),
            "short_games": int(stats["short_games"]),
            "medium_games": int(stats["medium_games"]),
            "long_games": int(stats["long_games"]),
        }
        players.append(player_info)

    players_with_stats = {s["player_id"] for s in players_stats}
    all_players = db.get_all_players()
    for player in all_players:
        if player["id"] not in players_with_stats:
            players.append({
                "id": player["id"],
                "map_position": 0,
                "total_moves": 0,
                "games_completed": 0,
                "games_dropped": 0,
                "sheikh_moments": 0,
                "rerolls": 0,
                "movies": 0,
                "ladders": 0,
                "snakes": 0,
                "tiny_games": 0,
                "short_games": 0,
                "medium_games": 0,
                "long_games": 0,
            })

    return jsonify({"players": players})


@player_bp.route("/api/current_user", methods=["GET"])
@login_required
def current_user():
    user_info = db.get_user_by_name(session["username"])
    if user_info:
        return jsonify({
            "user_id": user_info["id"],
            "role": user_info["role"],
            "moder_for": user_info["moder_for"],
            "url_handle": user_info["player_url_handle"],
            "name": user_info["username"],
        })
    return jsonify({"error": "Not found"}), 404


@player_bp.route("/api/reset_stats", methods=["GET"])
@login_required
def reset_stats():
    db.remove_moves_by_player_name(session["username"])
    return jsonify({"message": "Position reset"})


@player_bp.route("/api/moves", methods=["GET"])
def get_moves():
    player_id = request.args.get("player_id")
    date_param = request.args.get("date")
    limit = min(int(request.args.get("limit", 10)), 200)
    last_move = None
    if player_id:
        moves = db.get_moves_by_player(player_id=player_id)
    elif date_param:
        try:
            date.fromisoformat(date_param)
        except ValueError:
            return jsonify(
                {"error": "Incorrect data format, should be YYYY-MM-DD"}), 422
        moves = db.get_moves_by_date(date=date_param)
        last_move = db.get_last_move_id_to_date(date=date_param)
    else:
        moves = db.get_all_moves(limit=limit)

    last_move_id = last_move["id"] if last_move else None
    moves_titles = [
        m["item_title"] for m in moves if m["item_title"] is not None
    ]
    games = games_db.search_games_multiple_igdb(moves_titles)
    games_images = {g["gameName"].lower(): g["box_art_url"] for g in games}

    return jsonify({
        "last_move_id":
        last_move_id,
        "moves": [{
            "id":
            m["id"],
            "created_at":
            m["created_at"],
            "dice_roll":
            m["dice_roll"],
            "cell_from":
            m["cell_from"],
            "cell_to":
            m["cell_to"],
            "stair_from":
            m["stair_from"],
            "stair_to":
            m["stair_to"],
            "snake_from":
            m["snake_from"],
            "snake_to":
            m["snake_to"],
            "type":
            m["type"],
            "item_title":
            m["item_title"],
            "item_review":
            m["item_review"],
            "item_rating":
            m["item_rating"],
            "item_length":
            m["item_length"],
            "vod_link":
            m["vod_link"],
            "player_id":
            m["player_id"],
            "player_move_id":
            m["player_move_id"],
            "item_image":
            games_images.get(m["item_title"].lower()),
            "stream_title_category_duration":
            db.calculate_time_by_category_name(
                m["item_title"],
                m["player_id"])["total_difference_in_seconds"],
        } for m in moves],
    })


@player_bp.route("/api/reset_pointauc_token", methods=["POST"])
@login_required
def reset_pointauc_token():
    new_token = secrets.token_urlsafe(8)
    user_info = db.get_user_by_name(session["username"])
    db.update_player_pointauc_token(user_info["id"], new_token)
    return jsonify({"token": new_token})


@player_bp.route("/api/point_auc/result", methods=["POST"])
def pointauc_result_callback():
    data = request.get_json() or {}
    logging.info(str(data))
    require_fields = ["token", "winner_title"]
    for field in require_fields:
        if field not in request.json:
            return jsonify({"error": f"{field} is required"}), 400

    user_info = db.get_user_by_token(data["token"])
    if not user_info:
        return jsonify({"error": "Invalid token"}), 400
    if "auc_value" in data and "lots_count" in data:
        try:
            if int(data["lots_count"]) > 2:
                db.update_last_auction_result_by_player_id(
                    user_info["id"], data["winner_title"], data["auc_value"])
                try:
                    scheduler.add_job(
                        notifications.on_pointauc_result,
                        args=[user_info["username"], data["winner_title"]])
                except Exception as e:
                    logging.error(
                        "Error send notification on pointauc result: " +
                        str(e))
        except Exception as e:
            db.update_last_auction_result_by_player_id(user_info["id"],
                                                       data["winner_title"])
            logger.error("Error update_last_auction_result_by_player_id " +
                         str(e))
    else:
        db.update_last_auction_result_by_player_id(user_info["id"],
                                                   data["winner_title"])
    return jsonify({"message": "updated successfully"})


@player_bp.route("/api/point_auc/timer_started", methods=["POST"])
def pointauc_timer_callback():
    data = request.get_json() or {}
    logging.info(str(data))
    require_fields = ["token"]
    for field in require_fields:
        if field not in request.json:
            return jsonify({"error": f"{field} is required"}), 400

    user_info = db.get_user_by_token(data["token"])
    if not user_info:
        return jsonify({"error": "Invalid token"}), 400

    current_auc_timer_started_at = user_info["auction_timer_started_at"]
    if current_auc_timer_started_at is None:
        db.update_last_auction_date_by_player_id(user_info["id"])

        try:
            scheduler.add_job(notifications.on_pointauc_timer_started,
                              args=[user_info["username"]])
        except Exception as e:
            logging.error(
                "Error send notification on pointauc started, current time is None: "
                + str(e))
    else:
        current_utc_time = datetime.utcnow()
        time_difference = current_utc_time - current_auc_timer_started_at
        if time_difference >= timedelta(
                minutes=80):  # drop game time + auction default time
            db.update_last_auction_date_by_player_id(user_info["id"])

            try:
                scheduler.add_job(notifications.on_pointauc_timer_started,
                                  args=[user_info["username"]])
            except Exception as e:
                logging.error("Error send notification on pointauc started: " +
                              str(e))

    return jsonify({"message": "updated successfully"})


@player_bp.route("/api/player_current_game", methods=["POST"])
@login_required
def update_player_current_game():
    data = request.get_json()
    required_fields = ["title", "player_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        title = data["title"]
        player_id = data["player_id"]

        db.update_player_current_game(player_id=player_id, title=title)
        return jsonify({"message": "Player game updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

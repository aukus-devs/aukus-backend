from functools import wraps
from flask import Blueprint, request, jsonify, session
from db_client.db_client import DatabaseClient
from datetime import date
import secrets

player_bp = Blueprint("player", __name__)
db = DatabaseClient()


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


@player_bp.route("/api/players", methods=["GET"])
def get_players():
    move_id = request.args.get("move_id")
    players_data = db.get_all_players()
    if move_id:
        last_cells = db.get_players_positions_by_move_id(move_id)
    else:
        last_cells = db.get_players_last_cell_number()
    players = []
    for player in players_data:
        last_cell = next(
            (
                cell["cell_to"]
                for cell in last_cells
                if cell["player_id"] == player["id"]
            ),
            0,
        )
        player_info = {
            "id": player["id"],
            "name": player["username"],
            "twitch_stream_link": player["twitch_stream_link"],
            "vk_stream_link": player["vk_stream_link"],
            "donation_link": player["donation_link"],
            "stream_last_category": player["player_stream_current_category"],
            "is_online": bool(player["player_is_online"]),
            "current_game": player["player_current_game"],
            "url_handle": player["player_url_handle"],
            "map_position": last_cell,
            "first_name": player["name"],
            "last_name": player["surname"],
            "current_game_updated_at": player["current_game_updated_at"],
            "telegram_link": player["telegram_link"],
        }
        players.append(player_info)

    return jsonify({"players": players})


@player_bp.route("/api/player_move", methods=["POST"])
@login_required
def add_player_move():
    data = request.get_json()
    required_fields = ["player_id", "dice_roll", "type", "item_title", "item_review"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    if data.get("stair_from") and data.get("snake_from"):
        return jsonify(
            {"error": f"Stair and snake cannot be used at the same time"}
        ), 400

    last_cells = db.get_players_last_cell_number()
    last_cell_number = next(
        (
            cell["cell_to"]
            for cell in last_cells
            if cell["player_id"] == data["player_id"]
        ),
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
        db.update_current_game_by_player_id(player_id, None)
        return jsonify(
            {"message": "Player move added and position updated successfully"}
        ), 201

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
            db.update_player_move_vod_link(
                move_id=move_id, vod_link=vod_link, title=title
            )
            return jsonify(
                {"message": "Player move vod link updated successfully"}
            ), 201
        else:
            return jsonify({"error": f"Player move with id {move_id} not found"}), 404

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
            "map_position": stats["map_position"],
            "total_moves": stats["total_moves"],
            "games_completed": stats["games_completed"],
            "games_dropped": stats["games_dropped"],
            "sheikh_moments": stats["sheikh_moments"],
            "rerolls": stats["rerolls"],
            "movies": stats["movies"],
            "ladders": stats["ladders"],
            "snakes": stats["snakes"],
        }
        players.append(player_info)

    players_with_stats = {s["player_id"] for s in players_stats}
    all_players = db.get_all_players()
    for player in all_players:
        if player["id"] not in players_with_stats:
            players.append(
                {
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
                }
            )

    return jsonify({"players": players})


@player_bp.route("/api/current_user", methods=["GET"])
@login_required
def current_user():
    user_info = db.get_user_by_name(session["username"])
    if user_info:
        return jsonify(
            {
                "user_id": user_info["id"],
                "role": user_info["role"],
                "moder_for": user_info["moder_for"],
                "url_handle": user_info["player_url_handle"],
                "name": user_info["username"],
            }
        )
    return jsonify({"error": "Not found"}), 404


@player_bp.route("/api/reset_stats", methods=["GET"])
@login_required
def reset_stats():
    db.remove_moves_by_player_name(session["username"])
    return jsonify({"message": "Position reset"})


@player_bp.route("/api/moves", methods=["GET"])
def get_moves():
    player_id = request.args.get("player_id")
    last_move = None
    if player_id:
        moves = db.get_moves_by_player(player_id=player_id)
    else:
        date_param = request.args.get("date") or str(date.today())
        try:
            date.fromisoformat(date_param)
        except ValueError:
            return jsonify(
                {"error": "Incorrect data format, should be YYYY-MM-DD"}
            ), 422
        moves = db.get_moves_by_date(date=date_param)
        last_move = db.get_last_move_id_to_date(date=date_param)
    last_move_id = last_move["id"] if last_move else None
    return jsonify(
        {
            "last_move_id": last_move_id,
            "moves": [
                {
                    "id": m["id"],
                    "created_at": m["created_at"],
                    "dice_roll": m["dice_roll"],
                    "cell_from": m["cell_from"],
                    "cell_to": m["cell_to"],
                    "stair_from": m["stair_from"],
                    "stair_to": m["stair_to"],
                    "snake_from": m["snake_from"],
                    "snake_to": m["snake_to"],
                    "type": m["type"],
                    "item_title": m["item_title"],
                    "item_review": m["item_review"],
                    "item_rating": m["item_rating"],
                    "item_length": m["item_length"],
                    "vod_link": m["vod_link"],
                    "player_id": m["player_id"],
                    "player_move_id": m["player_move_id"],
                }
                for m in moves
            ],
        }
    )


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
    require_fields = ["token", "winner_title"]
    for field in require_fields:
        if field not in request.json:
            return jsonify({"error": f"{field} is required"}), 400

    user_info = db.get_user_by_token(data["token"])
    if not user_info:
        return jsonify({"error": "Invalid token"}), 400

    db.update_current_game_by_player_id(user_info["id"], data["winner_title"])
    return jsonify({"message": "updated successfully"})

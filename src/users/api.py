from flask import Blueprint, jsonify, request, session, redirect, flash, render_template
from src.games.queries import search_games_multiple_igdb
from src.moves.queries import (
    get_players_last_moves,
    get_players_last_moves_before_move_id,
)
from src.users.queries import get_all_players, get_user_by_login
from src.core.extensions import bcrypt
from src.users.serializers import PlayerDetailed

users_bp = Blueprint("users", __name__)


@users_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        user = get_user_by_login(username)

        if user:
            is_valid = bcrypt.check_password_hash(user.password_hash, password)
            if is_valid:
                session["username"] = user.name
                session["role"] = user.role
                return redirect("/")
            else:
                flash("Неверное имя пользователя или пароль. Попробуйте снова.")
        else:
            flash("Пользователь не найден или отключён")

    return render_template("login.html")


@users_bp.route("/api/players", methods=["GET"])
def get_players():
    move_id = request.args.get("move_id", type=int)
    players_data = get_all_players()
    if move_id:
        last_moves = get_players_last_moves_before_move_id(move_id)
    else:
        last_moves = get_players_last_moves()
    players = []
    players_games = [
        player.player_current_game
        for player in players_data
        if player.player_current_game
    ]
    games_images = search_games_multiple_igdb(players_games)
    games_images_by_name = {
        game["gameName"].lower(): game["box_art_url"] for game in games_images
    }

    for player in players_data:
        last_position: int = next(
            (move.cell_to for move in last_moves if move.player_id == player.id),
            0,
        )
        image = None
        if player["player_current_game"]:
            image = games_images_by_name.get(player["player_current_game"].lower())
        current_game_duration = None
        if player["player_current_game"] != None:
            current_game_duration = db.calculate_time_by_category_name(
                player["player_current_game"], player["id"]
            )["total_difference_in_seconds"]
        if current_game_duration is None:
            current_game_duration = 0

        player_info = PlayerDetailed(
            id=player["id"],
            name=player["username"],
            first_name=player["name"],
            last_name=player["surname"],
            url_handle=player["player_url_handle"],
            map_position=last_position,
            twitch_stream_link=player["twitch_stream_link"],
            vk_stream_link=player["vk_stream_link"],
            kick_stream_link=player["kick_stream_link"],
            donation_link=player["donation_link"],
            telegram_link=player["telegram_link"],
            current_game=player["player_current_game"],
            current_game_duration=current_game_duration,
            current_game_updated_at=player["current_game_updated_at"],
            current_game_image=image,
            is_online=bool(player["player_is_online"]),
            online_count=int(player["online_count"]),
            current_auction_total_sum=player["current_auction_total_sum"],
            auction_timer_started_at=player["auction_timer_started_at"],
            stream_last_category=player["player_stream_current_category"],
        )
        players.append(player_info.dict())

    return jsonify({"players": players})

from functools import wraps
from flask import Blueprint, request, jsonify, session
from db_client.db_client import DatabaseClient

player_bp = Blueprint('player', __name__)
db = DatabaseClient()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session and 'role' not in session:
            return jsonify({'error': f'Auth required'}), 401
        return f(*args, **kwargs)

    return decorated_function


@player_bp.route('/api/players', methods=['GET'])
def get_players():
    players_data = db.get_all_players()
    players = []
    for player in players_data:
        map_position = db.get_last_cell_number(player_id=player[0])
        player_info = {
            'id': player[0],
            'name': player[1],
            'twitch_stream_link': player[3],
            'vk_stream_link': player[9],
            'donation_link': player[10],
            'is_online': True if player[4] else False,
            'current_game': player[5],
            'url_handle': player[6],
            'map_position': map_position[0] if map_position else 0
        }
        players.append(player_info)

    return jsonify({'players': players})


@player_bp.route('/api/player_move', methods=['POST'])
@login_required
def add_player_move():
    data = request.get_json()
    required_fields = ['player_id', 'dice_roll', 'type', 'item_title', 'item_review']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    if data.get('stair_from') and data.get('snake_from'):
        return jsonify({'error': f'Stair and snake cannot be used at the same time'}), 400

    last_cell_number_db = db.get_last_cell_number(player_id=data['player_id'])
    last_cell_number = last_cell_number_db[0] if last_cell_number_db else 0

    try:
        player_id = data['player_id']
        dice_roll = data['dice_roll']
        cell_from = last_cell_number if last_cell_number else 0
        cell_to = data['move_to']
        stair_from = data.get('stair_from')
        stair_to = data.get('stair_to')
        snake_from = data.get('snake_from')
        snake_to = data.get('snake_to')
        move_type = data['type']
        item_title = data['item_title']
        item_review = data['item_review']
        item_rating = data.get('item_rating')
        item_length = data.get('item_length')

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
            item_length=item_length
        )
        return jsonify({'message': 'Player move added and position updated successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@player_bp.route('/api/player_move_vod_link', methods=['POST'])
@login_required
def add_vod_link_to_player_move():
    data = request.get_json()
    required_fields = ['move_id', 'vod_link']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        vod_link = data.get('vod_link')
        move_id = data.get('move_id')

        player_move = db.get_move_by_id(move_id)
        if player_move:
            db.update_player_move_vod_link(
                move_id=move_id,
                vod_link=vod_link
            )
            return jsonify({'message': 'Player move vod link updated successfully'}), 201
        else:
            return jsonify({'error': f'Player move with id {move_id} not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@player_bp.route('/api/player_stats', methods=['GET'])
def player_stats():
    # Получаем информацию обо всех игроках

    players_data = db.get_all_players()
    # Формируем JSON-ответ
    players = []
    for player in players_data:
        map_position = db.get_last_cell_number(player_id=player[0])
        total_moves = db.get_moves_count_by_player_id(player_id=player[0])
        games_completed = db.get_games_completed_by_player_id(player_id=player[0])
        games_dropped = db.get_games_dropped_by_player_id(player_id=player[0])
        sheikh_moments = db.get_games_sheikh_by_player_id(player_id=player[0])
        rerolls = db.get_reroll_count_by_player_id(player_id=player[0])
        movies = db.get_movies_count_by_player_id(player_id=player[0])
        ladders = db.get_ladders_count_by_player_id(player_id=player[0])
        snakes = db.get_snakes_count_by_player_id(player_id=player[0])
        player_info = {
            'id': player[0],
            'map_position': map_position[0] if map_position else 0,
            'total_moves': total_moves[0] if total_moves else 0,
            'games_completed': games_completed[0] if games_completed else 0,
            'games_dropped': games_dropped[0] if games_dropped else 0,
            'sheikh_moments': sheikh_moments[0] if sheikh_moments else 0,
            'rerolls': rerolls[0] if rerolls else 0,
            'movies': movies[0] if movies else 0,
            'ladders': ladders[0] if ladders else 0,
            'snakes': snakes[0] if snakes else 0
        }
        players.append(player_info)

    return jsonify({'players': players})


@player_bp.route('/api/players/<int:player_id>', methods=['GET'])
def get_player_moves(player_id):
    moves = db.get_moves_by_player(player_id=player_id)
    return jsonify({'moves': [
        {
            'id': m[0],
            'created_at': m[1],
            'dice_roll': m[2],
            'cell_from': m[3],
            'cell_to': m[4],
            'stair_from': m[5],
            'stair_to': m[6],
            'snake_from': m[7],
            'snake_to': m[8],
            'type': m[9],
            'item_title': m[10],
            'item_review': m[11],
            'item_rating': m[12],
            'item_length': m[13],
            'vod_link': m[14]
        } for m in moves
    ]})


@player_bp.route('/api/get_current_user_id', methods=['GET'])
def get_current_user_id():
    if session.get("username") is None:
        return jsonify({"error": "Need auth"}), 401
    user_info = db.get_user_info_by_name(session["username"])
    if user_info:
        return jsonify({"user_id": user_info[0], "role": user_info[1]})
    else:
        return jsonify({"error": "Not found"}), 404


@player_bp.route('/api/reset_stats', methods=['GET'])
@login_required
def reset_stats():
    db.remove_moves_by_player_name(session['username'])
    return jsonify({'message': 'Position reset'})

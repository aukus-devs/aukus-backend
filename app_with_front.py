import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler

from config import DB, SESSION_SECRET, UPLOAD_FOLDER
from db_client.db_client import DatabaseClient

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = SESSION_SECRET
DATABASE = DB


def get_db():
    return DatabaseClient()


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.route('/manifest.json')
def send_manifest():
    return send_from_directory('static', 'manifest.json')


@app.route('/favicon.ico')
def send_favicon():
    return send_from_directory('static', 'favicon.ico')


@app.route('/asset-manifest.json')
def send_asset_manifest():
    return send_from_directory('static', 'asset-manifest.json')


@app.route('/static/<path:path>')
def send_static(path):
    import pdb
    pdb.set_trace()
    return send_from_directory('static', path)


@app.route('/assets/<path:path>')
def send_assets(path):
    return send_from_directory('assets', path)


@app.route('/')
def index():
    if 'username' in session and 'role' in session:
        return render_template('index.html')
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Получаем соединение с базой данных для текущего запроса
        db = get_db()

        # Проверяем пользователя в базе данных
        user = db.get_user_by_logpass(username=username, password=password)

        if user:
            # Если пользователь найден, сохраняем его в сессии
            session['username'] = user[1]
            session['role'] = user[2]
            return redirect(url_for('index'))
        else:
            return "Неверное имя пользователя или пароль. Попробуйте снова."

    return render_template('login.html')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session and 'role' not in session:
            return jsonify({'error': f'Auth required'}), 401
        return f(*args, **kwargs)

    return decorated_function


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))


@app.route('/api/players', methods=['GET'])
def get_players():
    db = get_db()
    players_data = db.get_all_players()
    players = []
    for player in players_data:
        map_position = db.get_last_cell_number(player_id=player[0])
        player_info = {
            'id': player[0],
            'name': player[1],
            'stream_link': player[3],
            'is_online': True if player[4] else False,
            'current_game': player[5],
            'url_handle': player[6],
            'map_position': map_position[0] if map_position else 0
        }
        players.append(player_info)

    return jsonify({'players': players})


@app.route('/api/player_move', methods=['POST'])
@login_required
def add_player_move():
    data = request.get_json()
    db_client = get_db()
    required_fields = ['player_id', 'dice_roll', 'type', 'item_title', 'item_review']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    if data.get('stair_from') and data.get('snake_from'):
        return jsonify({'error': f'Stair and snake cannot be used at the same time'}), 400

    last_cell_number_db = db_client.get_last_cell_number(player_id=data['player_id'])
    last_cell_number = last_cell_number_db[0] if last_cell_number_db else 0

    try:
        player_id = data['player_id']
        dice_roll = data['dice_roll']
        cell_from = last_cell_number if last_cell_number else 0
        cell_to = data['cell_to']
        stair_from = data.get('stair_from')
        stair_to = data.get('stair_to')
        snake_from = data.get('snake_from')
        snake_to = data.get('snake_to')
        move_type = data['type']
        item_title = data['item_title']
        item_review = data['item_review']
        item_rating = data.get('item_rating')
        item_length = data.get('item_length')

        db_client.add_player_move(
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


@app.route('/api/player_stats', methods=['GET'])
@login_required
def player_stats():
    # Получаем информацию обо всех игроках
    db = get_db()
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


@app.route('/api/players/<int:player_id>', methods=['GET'])
@login_required
def get_player_moves(player_id):
    db = get_db()
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
            'item_length': m[13]
        } for m in moves
    ]})


@app.route('/api/get_current_user_id', methods=['GET'])
@login_required
def get_current_user_id():
    db = get_db()
    user_id = db.get_user_id_by_name(session['username'])
    return jsonify({'user_id': user_id[0]})


@app.route('/api/reset_stats', methods=['GET'])
@login_required
def reset_stats():
    db = get_db()
    db.remove_moves_by_player_name(session['username'])
    return jsonify({'message': 'Position reset'})


@app.route('/api/canvas/<int:player_id>/upload', methods=['POST'])
@login_required
def upload_canvas_image(player_id):
    db = get_db()
    file = request.files['file']
    width = request.form['width']
    height = request.form['height']
    last_file_id = db.get_last_image_id(player_id=player_id)
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    name = str(player_id) + '-' + str(last_file_id[0] + 1) + '.' + file_extension if last_file_id else str(
        player_id) + '-' + str('1') + '.' + file_extension
    file.save(str(os.path.join(basedir, UPLOAD_FOLDER, name)))
    url = str(UPLOAD_FOLDER + '/' + name)
    db.add_image(player_id=player_id, url=url, width=width, height=height)
    return jsonify({
        'id': last_file_id[0] + 1 if last_file_id else 1,
        'rotation': 0.0,
        'x': 0.0,
        'y': 0.0,
        'url': url,
        'width': float(width),
        'height': float(height)
    })


@app.route('/api/canvas/<int:player_id>', methods=['GET'])
def get_canvas_files(player_id):
    # Получаем соединение с базой данных
    db = get_db()

    # Запрос файлов для конкретного игрока
    player_files = db.get_player_files_by_player_id(player_id)

    # Формируем JSON-ответ
    files = [
        {
            'id': file[0],
            'rotation': file[1],
            'x': file[2],
            'y': file[3],
            'url': file[4],
            'width': file[5],
            'height': file[6]
        } for file in player_files
    ]

    return jsonify({'objects': files}), 200


def reset_finished_players():
    db = get_db()
    db.reset_finished_players()


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(reset_finished_players, 'interval', minutes=1)
    scheduler.start()
    app.run(host='0.0.0.0', port=5000, debug=True)

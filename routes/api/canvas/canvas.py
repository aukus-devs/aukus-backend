from functools import wraps
from flask import request, session, jsonify, Blueprint

from config import UPLOAD_FOLDER, BASE_DIR
from db_client.db_client import DatabaseClient

canvas_bp = Blueprint('canvas', __name__)
db = DatabaseClient()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session and 'role' not in session:
            return jsonify({'error': f'Auth required'}), 401
        return f(*args, **kwargs)

    return decorated_function


@canvas_bp.route('/api/canvas/<int:player_id>/upload', methods=['POST'])
@login_required
def upload_canvas_image(player_id):
    file = request.files['file']
    width = request.form['width']
    height = request.form['height']
    last_file_id = db.get_last_image_id(player_id=player_id)
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    name = str(player_id) + '-' + str(last_file_id[0] + 1) + '.' + file_extension if last_file_id else str(
        player_id) + '-' + str('1') + '.' + file_extension
    file.save(BASE_DIR + UPLOAD_FOLDER + '/' + name)
    url = str('/uploads/' + name)
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


@canvas_bp.route('/api/canvas/<int:player_id>', methods=['GET'])
def get_canvas_files(player_id):
    player_files = db.get_player_files_by_player_id(player_id)
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

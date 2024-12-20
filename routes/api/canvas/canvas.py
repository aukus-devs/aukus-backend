from functools import wraps
from flask import request, session, jsonify, Blueprint

from config import UPLOAD_FOLDER, BASE_DIR
from db_client.db_client import DatabaseClient

canvas_bp = Blueprint("canvas", __name__)
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


@canvas_bp.route("/api/canvas/<int:player_id>/upload", methods=["POST"])
@login_required
def upload_canvas_image(player_id):
    file = request.files["file"]
    width = request.form["width"]
    height = request.form["height"]
    last_file_id = db.get_last_image_id(player_id=player_id)
    if not file.filename:
        return jsonify({"error": "No file found"})

    file_extension = file.filename.rsplit(".", 1)[1].lower()
    name = (
        str(player_id) + "-" + str(last_file_id[0] + 1) + "." + file_extension
        if last_file_id
        else str(player_id) + "-" + str("1") + "." + file_extension
    )
    file.save(BASE_DIR + UPLOAD_FOLDER + "/" + name)
    url = str("/uploads/" + name)
    z_index = db.add_image(player_id=player_id, url=url, width=width, height=height)
    return jsonify(
        {
            "id": last_file_id[0] + 1 if last_file_id else 1,
            "rotation": 0.0,
            "x": 0.0,
            "y": 0.0,
            "url": url,
            "width": float(width),
            "height": float(height),
            "z_index": z_index,
            "scaleX": 1,
            "scaleY": 1,
        }
    )


@canvas_bp.route("/api/canvas/<int:player_id>", methods=["GET"])
def get_canvas_files(player_id):
    player_files = db.get_player_files_by_player_id(player_id)
    files = [
        {
            "id": file[0],
            "rotation": file[1],
            "x": file[2],
            "y": file[3],
            "url": file[4],
            "width": file[5],
            "height": file[6],
            "zIndex": file[7],
            "scaleX": file[8],
            "scaleY": file[9],
        }
        for file in player_files
    ]

    return jsonify({"objects": files}), 200


@canvas_bp.route("/api/canvas/<int:player_id>/update", methods=["PUT"])
@login_required
def update_canvas(player_id):
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Invalid request format"}), 400

    required_fields = ["id", "rotation", "x", "y", "width", "height", "zIndex"]
    for i in data:
        for field in required_fields:
            if field not in i:
                return jsonify({"error": f"Missing required field: {field}"}), 400

    current_objects = db.get_player_files_by_player_id(player_id)
    current_ids = {obj[0] for obj in current_objects}
    incoming_ids = {obj["id"] for obj in data}
    ids_to_delete = current_ids - incoming_ids
    for i in incoming_ids:
        if i not in current_ids:
            return jsonify({"error": f"id {i} not found in current files"}), 400

    try:
        for i in data:
            if i["scaleX"]:
                if i["scaleX"] > 1 or i["scaleX"] < -1:
                    return jsonify({"error": "Invalid scale value"}), 400

            if i["scaleY"]:
                if i["scaleY"] > 1 or i["scaleY"] < -1:
                    return jsonify({"error": "Invalid scale value"}), 400

            db.update_player_files_by_file_id(
                file_id=i["id"],
                rotation=i["rotation"],
                x=i["x"],
                y=i["y"],
                width=i["width"],
                height=i["height"],
                z_index=i["zIndex"],
                scale_x=i["scaleX"],
                scale_y=i["scaleY"],
            )
        for i in ids_to_delete:
            db.delete_file(file_id=i)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(
        {
            "message": f'Updated {incoming_ids}. Deleted {ids_to_delete if ids_to_delete else "none"}'
        }
    ), 200

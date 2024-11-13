import logging
from datetime import datetime, timedelta
from flask import Flask
from flask_session.__init__ import Session
from routes.api.login.login import auth_bp
from routes.api.player.player import player_bp
from routes.api.canvas.canvas import canvas_bp
from routes.api.games.games import games_bp
import config


logging.basicConfig(level = logging.INFO)
app = Flask(__name__)


def create_app():
    app.secret_key = config.SESSION_SECRET
    app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
    app.config["SESSION_PERMANENT"] = True
    app.config["SESSION_TYPE"] = "filesystem"
    app.config['SESSION_FILE_THRESHOLD'] = 250
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
    app.config['DEBUG'] = True
    app.json.ensure_ascii = False
    app.json.mimetype = "application/json; charset=utf-8"

    Session(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(player_bp)
    app.register_blueprint(canvas_bp)
    app.register_blueprint(games_bp)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5533, debug=True, use_reloader=False)

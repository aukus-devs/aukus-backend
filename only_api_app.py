from flask import Flask
from routes.api.login.login import auth_bp
from routes.api.player.player import player_bp
from routes.api.canvas.canvas import canvas_bp
from apscheduler.schedulers.background import BackgroundScheduler
from db_client.db_client import DatabaseClient
import config

app = Flask(__name__)


def create_app():
    app.secret_key = config.SESSION_SECRET
    app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER

    app.register_blueprint(auth_bp)
    app.register_blueprint(player_bp)
    app.register_blueprint(canvas_bp)
    return app


def reset_finished_players():
    db = DatabaseClient()
    db.reset_finished_players()


if __name__ == '__main__':
    app = create_app()
    scheduler = BackgroundScheduler()
    scheduler.add_job(reset_finished_players, 'interval', minutes=1)
    scheduler.start()
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == 'only_api_app':
    scheduler = BackgroundScheduler()
    scheduler.add_job(reset_finished_players, 'interval', minutes=1)
    scheduler.start()

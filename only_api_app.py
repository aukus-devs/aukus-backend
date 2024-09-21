import requests
from lxml import html
from dotenv import load_dotenv
import os
import logging
from flask import Flask
from routes.api.login.login import auth_bp
from routes.api.player.player import player_bp
from routes.api.canvas.canvas import canvas_bp
from apscheduler.schedulers.background import BackgroundScheduler
from db_client.db_client import DatabaseClient
import config

load_dotenv()
twitch_headers = {
    "Client-ID": os.getenv("TWITCH_CLIENT_ID"),
    "Authorization": os.getenv("TWITCH_BEARER_TOKEN"),
}
app = Flask(__name__)
logger = app.logger

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
    
    
def refresh_stream_statuses():
    try:
        db = DatabaseClient()
        players = db.get_all_players()
        for player in players:
            if player[3]: #twitch link exists
                logger.info("Start twitch check for " + player[1])
                url = "https://api.twitch.tv/helix/streams?user_login=" + player[3].rsplit('/', 1)[1]
                response = requests.get(url, headers=twitch_headers, timeout=15)
                data = response.json()["data"]
                if len(data) != 0 and data[0]["type"] == "live":
                    stream = data[0]
                    db.update_stream_status(player_id=player[0], is_online=True, category=stream["game_name"])
                else:
                    db.update_stream_status(player_id=player[0], is_online=False)
            elif player[9]: #vkplay link exists
                logger.info("Start vkplay check for " + player[1])
                vkplay_page = requests.get(player[9])
                content = html.fromstring(vkplay_page.content)
                category_xpath = content.xpath('/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[1]/div/div[2]/div[1]/div[3]/a')
                if len(category_xpath) != 0:
                    db.update_stream_status(player_id=player[0], is_online=True, category=category_xpath[0].text)
                else:
                    db.update_stream_status(player_id=player[0], is_online=False)
    except Exception as e:
        logger.error("Stream check failed for " + player[1] + ",: " + str(e))
        db.update_stream_status(player_id=player[0], is_online=False)


if __name__ == '__main__':
    app = create_app()
    scheduler = BackgroundScheduler()
    scheduler.add_job(reset_finished_players, 'interval', minutes=1)
    scheduler.add_job(refresh_stream_statuses, 'interval', minutes=1)
    scheduler.start()
    app.run(host='0.0.0.0', port=5533, debug=True, use_reloader=False)


if __name__ == 'only_api_app':
    logger = logging.getLogger('gunicorn.error')
    scheduler = BackgroundScheduler()
    scheduler.add_job(reset_finished_players, 'interval', minutes=1)
    scheduler.add_job(refresh_stream_statuses, 'interval', minutes=1)
    scheduler.start()

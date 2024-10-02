import requests
from lxml import html
from dotenv import load_dotenv
import os
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BlockingScheduler
from db_client.db_client import DatabaseClient
import config

load_dotenv()
twitch_headers = {
    "Client-ID": os.getenv("TWITCH_CLIENT_ID"),
    "Authorization": os.getenv("TWITCH_BEARER_TOKEN"),
}

logging.basicConfig(level = logging.INFO)


def reset_finished_players():
    db = DatabaseClient()
    db.reset_finished_players()


def refresh_stream_statuses():
    try:
        db = DatabaseClient()
        players = db.get_all_players()
        for player in players:
            if player[3]: #twitch link exists
                #logging.info("Start twitch check for " + player[1] + ", URL: " + player[3])
                url = "https://api.twitch.tv/helix/streams?user_login=" + player[3].rsplit('/', 1)[1]
                response = requests.get(url, headers=twitch_headers, timeout=15)
                data = response.json()["data"]
                #logging.info(data)
                if len(data) != 0 and data[0]["type"] == "live":
                    stream = data[0]
                    db.update_stream_status(player_id=player[0], is_online=True, category=stream["game_name"])
                else:
                    db.update_stream_status(player_id=player[0], is_online=False)
            elif player[9]: #vkplay link exists
                #logging.info("Start vkplay check for " + player[1] + ", URL: " + player[9])
                vkplay_page = requests.get(player[9], timeout=30)
                content = html.fromstring(vkplay_page.content)
                category_xpath = content.xpath('/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[1]/div/div[2]/div[1]/div[3]/a')
                if len(category_xpath) != 0:
                    db.update_stream_status(player_id=player[0], is_online=True, category=category_xpath[0].text)
                else:
                    db.update_stream_status(player_id=player[0], is_online=False)
    except Exception as e:
        logging.error("Stream check failed for " + player[1] + ",: " + str(e))
        db.update_stream_status(player_id=player[0], is_online=False)


scheduler = BlockingScheduler()
scheduler.add_job(reset_finished_players, 'interval', minutes=1)
scheduler.add_job(refresh_stream_statuses, 'interval', minutes=1)
scheduler.start()

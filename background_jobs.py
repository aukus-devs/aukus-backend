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

logging.basicConfig(level=logging.INFO)


def reset_finished_players():
    db = DatabaseClient()
    db.reset_finished_players()


def refresh_stream_statuses():
    try:
        db = DatabaseClient()
        players = db.get_all_players()
        for player in players:
            # logging.info(str(player))
            if player["twitch_stream_link"]:  # twitch link exists
                # logging.info("Start twitch check for " + player["username"] + ", URL: " + player["twitch_stream_link"])
                url = (
                    "https://api.twitch.tv/helix/streams?user_login="
                    + player["twitch_stream_link"].rsplit("/", 1)[1]
                )
                response = requests.get(url, headers=twitch_headers, timeout=15)
                data = response.json()["data"]
                # logging.info(data)
                if len(data) != 0 and data[0]["type"] == "live":
                    stream = data[0]
                    if (
                        stream["game_name"] != player["player_stream_current_category"]
                        or player["player_is_online"] == False
                    ):  # comparing category with DB
                        db.update_stream_status(
                            player_id=player["id"],
                            is_online=True,
                            category=stream["game_name"],
                        )
                else:
                    if player["player_is_online"] == True:  # is online in DB?
                        db.update_stream_status(player_id=player["id"], is_online=False)
            elif player["vk_stream_link"]:  # vkplay link exists
                logging.info("Start vkplay check for " + player["username"] + ", URL: " + player["vk_stream_link"])
                vkplay_page = requests.get(player["vk_stream_link"], timeout=30)
                content = html.fromstring(vkplay_page.content)
                #logging.info("IDDQD" + str(content))
                category_xpath = content.xpath(
                    "/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[1]/div/div[2]/div[1]/div/a"
                    #"/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[1]/div/div[2]/div[1]/div[3]/a"
                )
                if len(category_xpath) != 0:
                    if (
                        category_xpath[0].text
                        != player["player_stream_current_category"]
                        or player["player_is_online"] == False
                    ):  # comparing category with DB
                        db.update_stream_status(
                            player_id=player["id"],
                            is_online=True,
                            category=category_xpath[0].text,
                        )
                else:
                    if player["player_is_online"] == True:  # is online in DB?
                        db.update_stream_status(player_id=player["id"], is_online=False)
    except Exception as e:
        logging.error("Stream check failed for " + player["username"] + ",: " + str(e))
        db.update_stream_status(player_id=player["id"], is_online=False)


scheduler = BlockingScheduler()
# scheduler.add_job(reset_finished_players, 'interval', minutes=1)
scheduler.add_job(refresh_stream_statuses, "interval", minutes=1)
scheduler.start()

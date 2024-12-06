import requests
from lxml import html
from dotenv import load_dotenv
import os
import sys
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BlockingScheduler
from db_client.db_client import DatabaseClient
import config
import json

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
                            online_count=int(stream["viewer_count"]),
                            category=stream["game_name"],
                        )
                    db.update_current_online_count_by_player_id(
                        player_id=player["id"],
                        online_count=int(stream["viewer_count"]),
                    )
                else:
                    if player["player_is_online"] == True:  # is online in DB?
                        db.update_stream_status(player_id=player["id"], is_online=False)
            elif player["vk_stream_link"]:  # vkplay link exists
                #logging.info("Start vkplay check for " + player["username"] + ", URL: " + player["vk_stream_link"])
                vkplay_page = None
                try:
                    vkplay_page = requests.get(player["vk_stream_link"], timeout=110)
                except Exception as e:
                    pass
                if vkplay_page is None:
                    vkplay_page = requests.get(player["vk_stream_link"], timeout=110)
                content = html.fromstring(vkplay_page.content)
                #logging.info("IDDQD" + str(content))
                category_xpath = content.xpath(
                    "/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[1]/div/div[2]/div[1]/div/a"
                )
                online_count_xpath = content.xpath(
                    "/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[1]/div/div[1]/div[2]/div[2]/div[2]/div[2]/div"
                )
                if len(category_xpath) != 0 and "StreamStatus_text" in vkplay_page.text:
                    online_count = int(online_count_xpath[0].text)
                    if (
                        category_xpath[0].text
                        != player["player_stream_current_category"]
                        or player["player_is_online"] == False
                    ):  # comparing category with DB
                        db.update_stream_status(
                            player_id=player["id"],
                            is_online=True,
                            online_count=online_count,
                            category=category_xpath[0].text,
                        )
                    db.update_current_online_count_by_player_id(
                        player_id=player["id"],
                        online_count=online_count,
                    )
                else:
                    if player["player_is_online"] == True:  # is online in DB?
                        db.update_stream_status(player_id=player["id"], is_online=False)
            elif player["kick_stream_link"]:
                #logging.info("Start kick check for " + player["username"] + ", URL: " + player["kick_stream_link"])
                try:
                    url = "http://localhost:20080/v1" # cloudflare bypass proxy
                    headers = {"Content-Type": "application/json"}
                    data = {
                        "cmd": "request.get",
                        "url": "https://kick.com/api/v1/channels/" + player["kick_stream_link"].split("/")[-1],
                        "maxTimeout": 60000
                    }
                    response = requests.post(url, headers = headers, json = data)
                    response_json_text = response.text
                    response_json_text = response_json_text.replace("<html><head></head><body>", "")
                    response_json_text = response_json_text.replace("</body></html>", "")
                    content = json.loads(json.loads(response_json_text)["solution"]["response"])
                    if content["livestream"] == None:
                        if player["player_is_online"] == True:
                            db.update_stream_status(player_id=player["id"], is_online=False)
                    else:
                        content = content["livestream"]
                        is_online = content["is_live"]
                        online_count = int(content["viewer_count"])
                        category = content["categories"][0]["name"]
                        if category != player["player_stream_current_category"] or player["player_is_online"] != is_online:
                            db.update_stream_status(
                                player_id=player["id"],
                                is_online=is_online,
                                online_count=online_count,
                                category=category,
                            )
                        db.update_current_online_count_by_player_id(
                            player_id=player["id"],
                            online_count=online_count,
                        )
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    logging.error("Stream check failed for " + player["username"] + ",: " + str(e) + ", line: " + str(exc_tb.tb_lineno))
                    if player["player_is_online"] == True:
                        db.update_stream_status(player_id=player["id"], is_online=False)
    except Exception as e:
        logging.error("Stream check failed for " + player["username"] + ",: " + str(e))


scheduler = BlockingScheduler()
# scheduler.add_job(reset_finished_players, 'interval', minutes=1)
scheduler.add_job(refresh_stream_statuses, "interval", minutes=2)
scheduler.start()

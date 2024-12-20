import requests
from lxml import html
from dotenv import load_dotenv
import os
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BlockingScheduler
from db_client.db_client import DatabaseClient
import config

logging.basicConfig(level=logging.INFO)


def refresh_stream_statuses():
    try:
        db = DatabaseClient()
        db.update_stream_status(
            player_id="1",
            is_online=True,
            category="test",
        )
    except Exception as e:
        logging.error("Stream check failed for " + ",: " + str(e))


#        db.update_stream_status(player_id=player["id"], is_online=False)

db = DatabaseClient()
players = db.get_all_players()
for player in players:
    print(player["username"])
    print(player["player_current_game"])
    print(
        db.calculate_time_by_category_name(player["player_current_game"], player["id"])[
            "total_difference_in_seconds"
        ]
    )
# print(db.calculate_time_by_category_name("tes2t", 1))
# print(
#    db.calculate_time_by_category_name("Finding Paradise",
#                                       15)["total_difference_in_seconds"])
# refresh_stream_statuses()

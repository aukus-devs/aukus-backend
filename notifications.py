from db_client.games_db_client import GamesDatabaseClient
import requests
import logging
import db_client
import os
import json
from dotenv import load_dotenv

load_dotenv()
MOVES_DISCORD_WEBHOOK = os.getenv("MOVES_DISCORD_WEBHOOK")
AUKUS_TG_BOT_TOKEN = os.getenv("AUKUS_TG_BOT_TOKEN")
AUKUS_SOCKS5_PROXY = os.getenv("AUKUS_SOCKS5_PROXY")

games_db = GamesDatabaseClient()


def on_player_move(player, dice_roll, cell_from, cell_to, move_type, item_title, item_review, item_rating):
    covers = games_db.search_games_multiple_igdb([item_title.lower()])
    image_url = covers[0]["box_art_url"] if len(covers) != 0 else ""
    if len(image_url) == 0:
        image_url = "https://aukus.fun/uploads/splash.jpg"
    username =  str(player["username"])
    turn_description = ""
    if move_type == "completed":
        turn_description = "Прошёл"
    if move_type == "drop":
        turn_description = "Дроп"
    if move_type == "movie":
        turn_description = "Фильм"
    if move_type == "reroll":
        turn_description = "Реролл"
    if move_type == "sheikh":
        turn_description = "Шейх-момент"
    try:
        #send to TG
        message = '👉 <b>' + str(player["username"]) + '</b>\n🎲 Ролл кубика: <b>' + str(dice_roll)  + '</b>, ход на карте: <b>'  + str(cell_from)  + '</b>-><b>'  + str(cell_to)  + '</b>\n❔ Тип хода: <b>'  + turn_description + '</b>\n🎮 Название: <b>'  + item_title  + '</b>\n⭐ ️Оценка: <b>' + str(item_rating) + '/10\n✍️ Отзыв: ' + item_review + '</b>'
        response = requests.get('https://api.telegram.org/' + AUKUS_TG_BOT_TOKEN + '/sendPhoto?chat_id=-1002372388698&caption=' + message + '&reply_markup={"inline_keyboard": [[{"text": "Посмотреть на сайте", "url": "https://aukus.fun"}]]}&parse_mode=html&photo='+ image_url, timeout=2)
        #logging.info("TG response: " + response.text)
    except Exception as e:
        logging.error("Error send on new move to TG: " + str(e))

    try:
        #send to Discord
        proxies = {
            'http' : AUKUS_SOCKS5_PROXY,
            'https' : AUKUS_SOCKS5_PROXY,
        }
        url = MOVES_DISCORD_WEBHOOK
        description = '🎲 Ролл кубика: **' + str(dice_roll)  + '**, ход на карте: **'  + str(cell_from)  + '**->**'  + str(cell_to)  + '**\n❔ Тип хода: **'  + turn_description + '**\n 🎮Название: **'  + item_title  + '**\n⭐ ️Оценка: **' + str(item_rating) + '/10\n✍ ️Отзыв: ' + item_review + '**'
        payload = json.dumps({
            "content": "Новый ход!",
            "embeds": [
            {
                "title": '👉 **' + str(player["username"]) + "**",
                "url": "https://aukus.fun",
                "description": description,
                "image": {
                    "url": image_url
                }
            }
         ]
        })
        headers = {
           'Content-Type': 'application/json',
        }
        response = requests.post(url, data=payload, timeout=2, proxies=proxies, headers=headers)
        #logging.info("Discord response: " + response.text)
    except Exception as e:
        logging.error("Error send on new move to Discord: " + str(e))


def on_pointauc_result(username, title):
    try:
        #send to TG
        message = '👉 <b>' + username + '</b>\n🎲 Выпало на ауке: <b>' + str(title)  + '</b>'
        response = requests.get('https://api.telegram.org/' + AUKUS_TG_BOT_TOKEN + '/sendPhoto?chat_id=-1002372388698&caption=' + message + '&reply_markup={"inline_keyboard": [[{"text": "Посмотреть на сайте", "url": "https://aukus.fun"}]]}&parse_mode=html&photo=https://aukus.fun/uploads/splash.jpg', timeout=2)
        #logging.info("TG response: " + response.text)
    except Exception as e:
        logging.error("Error send pointauc result to TG: " + str(e))

    try:
        #send to Discord
        proxies = {
            'http' : AUKUS_SOCKS5_PROXY,
            'https' : AUKUS_SOCKS5_PROXY,
        }
        url = MOVES_DISCORD_WEBHOOK
        description = '🎲 Выпало на ауке: **' + str(title)  + '**'
        payload = json.dumps({
            "content": "Выпал новый лот выпал на ауке!",
            "embeds": [
            {
                "title": '👉 **' + username + "**",
                "url": "https://aukus.fun",
                "description": description,
                "image": {
                    "url": "https://aukus.fun/uploads/splash.jpg"
                }
            }
         ]
        })
        headers = {
           'Content-Type': 'application/json',
        }
        response = requests.post(url, data=payload, timeout=2, proxies=proxies, headers=headers)
        #logging.info("Discord response: " + response.text)
    except Exception as e:
        logging.error("Error send pointauc result to Discord: " + str(e))

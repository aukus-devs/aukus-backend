import datetime
import MySQLdb
from MySQLdb.cursors import DictCursor
import logging
import os
import sys
from dotenv import load_dotenv
from contextlib import closing


load_dotenv()
MYSQL_LOGIN = os.getenv("MYSQL_LOGIN")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQLCONF = {
    "host": "127.0.0.1",
    "user": MYSQL_LOGIN,
    "password": MYSQL_PASSWORD,
    "db": "twitch_games_db",
    "port": 3306,
    "charset": "utf8mb4",
    "autocommit": True,
}


class GamesDatabaseClient:
    def __init__(self):
        self.connection = MySQLdb.connect(**MYSQLCONF)

    def safe_close(self):
        try:
            self.connection.close()
        except:
            pass

    def conn(self):
        if self.connection.open:
            try:
                self.connection.ping(True)
                return self.connection
            except:
                self.safe_close()
                self.connection = MySQLdb.connect(**MYSQLCONF)
                return self.connection
        else:
            self.safe_close()
            self.connection = MySQLdb.connect(**MYSQLCONF)
            return self.connection

    def search_games(self, title: str):
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT * FROM game WHERE LOWER(gameName) LIKE %s",
                ("%" + title.lower() + "%",),
            )
            return cursor.fetchall()

    def search_games_multiple(self, titles: list[str]):
        if not titles:
            return []
        placeholders = ", ".join(["%s"] * len(titles))
        titles_lower = [title.lower() for title in titles]
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                f"SELECT * FROM game WHERE LOWER(gameName) IN ({placeholders})",
                titles_lower,
            )
            return cursor.fetchall()

    def get_wrong_platforms(self):
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT * FROM wrong_platforms",
                (),
            )
            return cursor.fetchall()

    def insert_to_IGDB(self, game_id, name, cover_url, release_year, platforms):
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                """
                INSERT INTO igdb_games (game_id, name, cover_url, release_year, platforms)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (game_id, name, cover_url, release_year, platforms),
            )

    def search_games_igdb(self, title: str):
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                """SELECT * FROM igdb_games WHERE JSON_CONTAINS(platforms, '[6]') AND LOWER(gameName) LIKE %s
                   ORDER BY
                       LENGTH(gameName) ASC
                   LIMIT 50
                """,
                ("%" + title.lower() + "%",),
            )
            return cursor.fetchall()

    def search_games_multiple_igdb(self, titles: list[str]):
        if not titles:
            return []
        placeholders = ", ".join(["%s"] * len(titles))
        titles_lower = [title.lower() for title in titles]
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                f"SELECT * FROM igdb_games WHERE JSON_CONTAINS(platforms, '[6]') AND LOWER(gameName) IN ({placeholders})",
                titles_lower,
            )
            return cursor.fetchall()


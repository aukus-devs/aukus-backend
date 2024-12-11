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
                self.connection.ping()
                return self.connection
            except:
                self.safe_close()
                self.connection = MySQLdb.connect(**MYSQLCONF)
                return self.connection
        else:
            self.safe_close()
            self.connection = MySQLdb.connect(**MYSQLCONF)
            return self.connection

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
                """
                    SELECT g.gameName, g.box_art_url, g.release_year, g.game_id
                    FROM igdb_games g
                    JOIN game_platforms gp ON g.id = gp.game_id
                    WHERE gp.platform_id = 6
                    AND LOWER(g.gameName) LIKE %s
                    ORDER BY
                        CASE
                            WHEN LOWER(g.gameName) LIKE %s THEN 0
                            ELSE 1
                        END,
                        LENGTH(g.gameName) ASC
                    LIMIT 20;
                """,
                (
                    "%" + title.strip().lower() + "%",
                    title.lower() + "%",
                ),
            )
            return cursor.fetchall()

    def search_games_multiple_igdb(self, titles: list[str]):
        if not titles:
            return []
        results = []
        with closing(self.conn().cursor(DictCursor)) as cursor:
            for title in titles:
                cursor.execute(
                    """
                        SELECT g.gameName, g.box_art_url, g.release_year, g.game_id
                        FROM igdb_games g
                        JOIN game_platforms gp ON g.id = gp.game_id
                        WHERE gp.platform_id = 6 AND g.gameName = %s
                        ORDER BY LENGTH(g.gameName) ASC
                        LIMIT 1;
                    """,
                    (title.strip().lower(),),
                )
                results.extend(cursor.fetchall())
        return results

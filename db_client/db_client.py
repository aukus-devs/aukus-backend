import datetime
import MySQLdb
from MySQLdb.cursors import DictCursor
import logging
import os
from dotenv import load_dotenv
from contextlib import closing
import re

load_dotenv()
MYSQL_LOGIN = os.getenv("MYSQL_LOGIN")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_AUKUS_DB_NAME = os.getenv("MYSQL_AUKUS_DB_NAME")
AUKUS_SAVE_STREAM_CATEGORIES = os.getenv("AUKUS_SAVE_STREAM_CATEGORIES")
MYSQLCONF = {
    "host": MYSQL_HOST,
    "user": MYSQL_LOGIN,
    "password": MYSQL_PASSWORD,
    "db": MYSQL_AUKUS_DB_NAME,
    "port": 3306,
    "charset": "utf8mb4",
    "autocommit": True,
}


class DatabaseClient:
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
            except Exception as e:
                logging.error("MySQL main DB ping error: " + str(e))
                self.safe_close()
                self.connection = MySQLdb.connect(**MYSQLCONF)
                return self.connection
        else:
            self.safe_close()
            self.connection = MySQLdb.connect(**MYSQLCONF)
            return self.connection

    # --- Методы для работы с таблицей player_moves ---

    def search_moves(self, title):
        """Поиск ходов по item_title"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT * FROM player_moves WHERE item_title LIKE %s",
                ("%" + title + "%",),
            )
            return cursor.fetchall()

    def search_history_moves(self, title):
        """Поиск ходов по item_title"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT * FROM aukus_history WHERE item_title LIKE %s",
                ("%" + title + "%",),
            )
            return cursor.fetchall()

    def calculate_time_by_category_name(self, category_name, player_id):
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                """
                WITH time_differences AS (
                    SELECT
                        category_name,
                        player_id,
                        category_date,
                        LEAD(category_name) OVER (PARTITION BY player_id ORDER BY id) AS next_category_name,
                        LEAD(category_date) OVER (PARTITION BY player_id ORDER BY id) AS next_category_date
                    FROM
                        categories_history
                )
                SELECT
                    category_name,
                    SUM(
                        CASE
                            WHEN next_category_name IS NULL THEN
                                TIMESTAMPDIFF(SECOND, category_date, NOW())
                            WHEN next_category_name != category_name THEN
                                TIMESTAMPDIFF(SECOND, category_date, next_category_date)
                            ELSE
                                0
                        END
                    ) AS total_difference_in_seconds
                FROM
                    time_differences
                WHERE
                    category_name = %s AND
                    player_id = %s
                GROUP BY
                    category_name;
                """,
                (
                    re.sub(r"\(.*?\)", "", category_name.strip()),
                    player_id,
                ),
            )
            result = cursor.fetchone()
            if result is None:
                return {"total_difference_in_seconds": 0}
            else:
                return result

    def update_player_move_vod_link(self, move_id, vod_link, title):
        """Обновить поле vod_link и item_title в таблице player_moves"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                """
                UPDATE player_moves
                SET vod_link = %s, item_title = %s
                WHERE id = %s
            """,
                (vod_link, title, move_id),
            )

    def get_move_by_id(self, move_id):
        """Получить ход игрока по ID"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute("SELECT * FROM player_moves WHERE id = %s", (move_id,))
            return cursor.fetchone()

    def get_moves_count_by_player_id(self, player_id):
        """Получить количество ходов игрока"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT COUNT(*) as count FROM player_moves WHERE player_id = %s",
                (player_id,),
            )
            return cursor.fetchone()

    def get_games_completed_by_player_id(self, player_id):
        """Получить количество завершенных игр"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                'SELECT COUNT(*) as count FROM player_moves WHERE player_id = %s AND type = "completed"',
                (player_id,),
            )
            return cursor.fetchone()

    def get_games_dropped_by_player_id(self, player_id):
        """Получить количество пропущенных игр"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                'SELECT COUNT(*) as count FROM player_moves WHERE player_id = %s AND type = "drop"',
                (player_id,),
            )
            return cursor.fetchone()

    def get_games_sheikh_by_player_id(self, player_id):
        """Получить количество игр с шейхой"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                'SELECT COUNT(*) as count FROM player_moves WHERE player_id = %s AND type = "sheikh"',
                (player_id,),
            )
            return cursor.fetchone()

    def get_reroll_count_by_player_id(self, player_id):
        """Получить количество рероллов"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                'SELECT COUNT(*) as count FROM player_moves WHERE player_id = %s AND type = "reroll"',
                (player_id,),
            )
            return cursor.fetchone()

    def get_movies_count_by_player_id(self, player_id):
        """Получить количество фильмов"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                'SELECT COUNT(*) as count FROM player_moves WHERE player_id = %s AND type = "movie"',
                (player_id,),
            )
            return cursor.fetchone()

    def get_ladders_count_by_player_id(self, player_id):
        """Получить количество ладдеров"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT COUNT(*) as count FROM player_moves WHERE player_id = %s AND stair_from IS NOT NULL",
                (player_id,),
            )
            return cursor.fetchone()

    def get_snakes_count_by_player_id(self, player_id):
        """Получить количество змей"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT COUNT(*) as count FROM player_moves WHERE player_id = %s AND snake_from IS NOT NULL",
                (player_id,),
            )
            return cursor.fetchone()

    def reset_finished_players(self):
        last_cells = self.get_players_last_cell_number()
        for i in last_cells:
            if i["cell_to"] >= 101:
                self.remove_moves_by_player_id(i["player_id"])
        return True

    def add_image(
        self, player_id, url, s3_file_id, width, height, x=0, y=0, rotation=0
    ):
        """Добавить изображение"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "SELECT MAX(zIndex) FROM player_files WHERE player_id = %s",
                (player_id,),
            )
            z_index = cursor.fetchone()
            z_index = (z_index[0] + 1) if z_index[0] is not None else 0
            cursor.execute(
                "INSERT INTO player_files (player_id, rotation, x, y, url, s3_file_id, width, height, zIndex)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (player_id, rotation, x, y, url, s3_file_id, width, height, z_index),
            )
            return z_index

    def get_last_image_id(self):
        """Получить ID последнего изображения"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                """SELECT COALESCE(
                       (SELECT MAX(id) FROM player_files),
                       0
                   ) AS max_id;"""
            )
            return cursor.fetchone()

    def get_player_files_by_player_id(self, player_id):
        sql = """
            SELECT id, rotation, x, y, url, width, height, zIndex, scaleX, scaleY
            FROM player_files
            WHERE player_id = %s
        """
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(sql, (player_id,))
            return cursor.fetchall()

    def get_player_files_dict_by_player_id(self, player_id):
        sql = """
            SELECT *
            FROM player_files
            WHERE player_id = %s
        """
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(sql, (player_id,))
            return cursor.fetchall()

    def update_player_files_url_by_file_id(self, file_id, url):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "UPDATE player_files SET url = %s WHERE id = %s",
                (url, file_id),
            )

    def delete_file(self, file_id):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute("DELETE FROM player_files WHERE id = %s", (file_id,))

    def get_file(self, file_id):
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute("SELECT * FROM player_files WHERE id = %s", (file_id,))
            return cursor.fetchone()

    def delete_files_by_player_id(self, player_id):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "DELETE FROM player_files WHERE player_id = %s", (player_id,)
            )

    def update_player_files_by_file_id(
        self, file_id, width, height, x, y, rotation, z_index, scale_x=1, scale_y=1
    ):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "UPDATE player_files SET width = %s, height = %s, x = %s, y = %s, rotation = %s, zIndex = %s, scaleX = %s, scaleY = %s WHERE id = %s",
                (width, height, x, y, rotation, z_index, scale_x, scale_y, file_id),
            )

    def insert_player_files_by_player_id(
        self, player_id, width, height, x, y, rotation, url
    ):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "INSERT INTO player_files (player_id, width, height, x, y, rotation, url) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (player_id, width, height, x, y, rotation, url),
            )

    def update_stream_status(
        self, player_id, is_online, online_count: int = 0, category=None
    ):
        """Обновить поля player_is_online и player_stream_current_category в таблице users"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                """
                UPDATE users
                SET player_is_online = %s, online_count = %s
                WHERE id = %s
            """,
                (is_online, online_count, player_id),
            )
            if category is not None:
                cursor.execute(
                    """
                    UPDATE users
                    SET player_stream_current_category = %s, online_count = %s
                    WHERE id = %s
                """,
                    (category, online_count, player_id),
                )
                if AUKUS_SAVE_STREAM_CATEGORIES:
                    cursor.execute(
                        "INSERT INTO categories_history (category_name, online_count, player_id) VALUES (%s, %s, %s)",
                        (
                            category,
                            online_count,
                            player_id,
                        ),
                    )
            else:
                if AUKUS_SAVE_STREAM_CATEGORIES:
                    cursor.execute(
                        "INSERT INTO categories_history (category_name, online_count, player_id) VALUES (%s, %s, %s)",
                        (
                            "Offline",
                            online_count,
                            player_id,
                        ),
                    )

    # def get_players_stats(self):
    #     """Получить статистику всех игроков"""
    #     with closing(self.conn().cursor(DictCursor)) as cursor:
    #         cursor.execute(
    #             """
    #             SELECT
    #             moves.player_id,
    #             COUNT(*) as total_moves,
    #             SUM(CASE WHEN moves.type = 'completed' THEN 1 ELSE 0 END) as games_completed,
    #             SUM(CASE WHEN moves.type = 'drop' THEN 1 ELSE 0 END) as games_dropped,
    #             SUM(CASE WHEN moves.type = 'sheikh' THEN 1 ELSE 0 END) as sheikh_moments,
    #             SUM(CASE WHEN moves.type = 'reroll' THEN 1 ELSE 0 END) as rerolls,
    #             SUM(CASE WHEN moves.type = 'movie' THEN 1 ELSE 0 END) as movies,
    #             SUM(CASE WHEN moves.stair_from IS NOT NULL THEN 1 ELSE 0 END) as ladders,
    #             SUM(CASE WHEN moves.snake_from IS NOT NULL THEN 1 ELSE 0 END) as snakes,
    #             SUM(CASE WHEN moves.type = 'completed' && moves.item_length = 'tiny' THEN 1 ELSE 0 END) as tiny_games,
    #             SUM(CASE WHEN moves.type = 'completed' && moves.item_length = 'short' THEN 1 ELSE 0 END) as short_games,
    #             SUM(CASE WHEN moves.type = 'completed' && moves.item_length = 'medium' THEN 1 ELSE 0 END) as medium_games,
    #             SUM(CASE WHEN moves.type = 'completed' && moves.item_length = 'long' THEN 1 ELSE 0 END) as long_games,
    #             AVG(CASE WHEN moves.type <> 'reroll' THEN ABS(moves.dice_roll) ELSE null END) as average_move,
    #             AVG(
    #               CASE
    #                 WHEN moves.cell_to > 101
    #                 THEN NULL
    #                 WHEN moves.item_length in ('tiny', 'short')
    #                 THEN ABS(moves.dice_roll)
    #                 WHEN moves.item_length = 'medium' and moves.cell_from < 81
    #                 THEN ABS(moves.dice_roll / 2)
    #                 WHEN moves.item_length = 'long' and moves.cell_from < 81
    #                 THEN ABS(moves.dice_roll / 3)
    #                 WHEN moves.cell_from < 81 and (type = 'drop' or type = 'sheikh')
    #                 THEN ABS(moves.dice_roll)
    #                 WHEN moves.cell_from >= 81 and moves.item_length in ('medium', 'long')
    #                 THEN ABS(moves.dice_roll)
    #                 WHEN moves.cell_from >= 81 and (type = 'drop' or type = 'sheikh')
    #                 THEN ABS(moves.dice_roll / 2)
    #                 ELSE
    #                 NULL
    #               END
    #             ) as average_dice_roll,
    #             SUM(CASE WHEN moves.stair_from IS NOT NULL && moves.stair_to IS NOT NULL THEN moves.stair_to - moves.stair_from ELSE 0 END) as ladders_moves_sum,
    #             SUM(CASE WHEN moves.snake_from IS NOT NULL && moves.snake_to IS NOT NULL THEN moves.snake_to - moves.snake_from ELSE 0 END) as snakes_moves_sum,
    #             COALESCE((
    #               SELECT subquery.cell_to
    #               FROM player_moves subquery
    #               WHERE subquery.player_id = moves.player_id
    #               ORDER BY subquery.id DESC
    #               LIMIT 1
    #             ), 0) as map_position
    #             FROM player_moves moves
    #             GROUP BY moves.player_id
    #             """
    #         )
    #         stats = cursor.fetchall()
    #         return stats

    def get_dons(self):
        """Получить всех донатеров"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute("SELECT * FROM dons ORDER BY sum desc, id desc")
            return cursor.fetchall()

    def get_igdb_token(self):
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute("SELECT * FROM igdb_token")
            return cursor.fetchone()

    def insert_random_result(
        self,
        player_id,
        player_move_id,
        is_from_random_org,
        json_short_data,
        json_full_data=None,
    ):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "INSERT INTO random_results (player_id, player_move_id, json_short_data, json_full_data, is_from_random_org) VALUES (%s, %s, %s, %s, %s)",
                (
                    player_id,
                    player_move_id,
                    json_short_data,
                    json_full_data,
                    is_from_random_org,
                ),
            )

    def get_random_result(self, player_id, player_move_id):
        sql = """
            SELECT json_short_data, is_from_random_org
            FROM random_results
            WHERE player_id = %s and player_move_id = %s
        """
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                sql,
                (
                    player_id,
                    player_move_id,
                ),
            )
            return cursor.fetchone()

    def insert_rules(self, rules_json):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "INSERT INTO rules (rules_data) VALUES (%s)",
                (rules_json,),
            )

    def get_rules(self, all=False):
        sql = """
            SELECT *
            FROM rules
            ORDER BY version DESC
        """
        if not all:
            sql += " LIMIT 1"
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def close(self):
        """Закрыть соединение с базой данных"""
        self.conn().close()

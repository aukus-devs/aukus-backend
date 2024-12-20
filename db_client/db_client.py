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
MYSQLCONF = {
    "host": "127.0.0.1",
    "user": MYSQL_LOGIN,
    "password": MYSQL_PASSWORD,
    "db": "aukus_db",
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

    # --- Методы для работы с таблицей users ---

    def add_user(
        self,
        name,
        role,
        stream_link,
        is_online,
        current_game,
        url_handle,
        moder_for,
        password,
        vk_stream_link,
        donation_link,
        player_stream_current_category,
        first_name,
        last_name,
    ):
        """Добавить нового пользователя"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, role, twitch_stream_link, player_is_online, player_current_game,
                                   player_url_handle, moder_for, password, vk_stream_link, donation_link, player_stream_current_category, name, surname)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    name,
                    role,
                    stream_link,
                    is_online,
                    current_game,
                    url_handle,
                    moder_for,
                    password,
                    vk_stream_link,
                    donation_link,
                    player_stream_current_category,
                    first_name,
                    last_name,
                ),
            )

    def get_user_by_id(self, user_id):
        """Получить пользователя по ID"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE id = %s and is_active = 1", (user_id,)
            )
            return cursor.fetchone()

    def get_user_by_logpass(self, username, password):
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE UPPER(username) = UPPER(%s) AND password = %s AND is_active = 1",
                (username, password),
            )
            return cursor.fetchone()

    def get_all_users(self):
        """Получить всех пользователей"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute("SELECT * FROM users WHERE is_active = 1")
            return cursor.fetchall()

    def update_user(
        self,
        user_id,
        name=None,
        role=None,
        stream_link=None,
        is_online=None,
        current_game=None,
        url_handle=None,
        moder_for=None,
        password=None,
        vk_stream_link=None,
        donation_link=None,
        player_stream_current_category=None,
        first_name=None,
        last_name=None,
    ):
        """Обновить информацию о пользователе"""
        updates = []
        params = []

        if name:
            updates.append("username = %s")
            params.append(name)
        if role:
            updates.append("role = %s")
            params.append(role)
        if stream_link:
            updates.append("twitch_stream_link = %s")
            params.append(stream_link)
        if is_online is not None:
            updates.append("player_is_online = %s")
            params.append(is_online)
        if current_game:
            updates.append("player_current_game = %s")
            params.append(current_game)
        if url_handle:
            updates.append("player_url_handle = %s")
            params.append(url_handle)
        if moder_for is not None:
            updates.append("moder_for = %s")
            params.append(moder_for)
        if password:
            updates.append("password = %s")
            params.append(password)
        if vk_stream_link:
            updates.append("vk_stream_link = %s")
            params.append(vk_stream_link)
        if donation_link:
            updates.append("donation_link = %s")
            params.append(donation_link)
        if player_stream_current_category:
            updates.append("player_stream_current_category = %s")
            params.append(player_stream_current_category)
        if first_name:
            updates.append("name = %s")
            params.append(first_name)
        if last_name:
            updates.append("surname = %s")
            params.append(last_name)

        params.append(user_id)
        query = f'UPDATE users SET {", ".join(updates)} WHERE id = %s'
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(query, params)

    def delete_user(self, user_id):
        """Удалить пользователя по ID"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

    # --- Методы для работы с таблицей playermoves ---

    def get_moves_by_player(self, player_id):
        """Получить все ходы определенного игрока"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT * FROM playermoves WHERE player_id = %s order by id desc",
                (player_id,),
            )
            return cursor.fetchall()

    def get_moves_by_date(self, date: str):
        """Получить все ходы за день"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT * FROM playermoves WHERE DATE(created_at) = %s order by id desc",
                (date,),
            )
            return cursor.fetchall()

    def get_last_move_id_to_date(self, date: str):
        """Получить последний ход перед днем"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT MAX(id) as id FROM playermoves WHERE DATE(created_at) < %s",
                (date,),
            )
            return cursor.fetchone()

    def get_all_moves(self, limit: int = 50):
        """Получить все ходы"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT * FROM playermoves order by id desc limit %s", (limit,)
            )
            return cursor.fetchall()

    def search_moves(self, title):
        """Поиск ходов по item_title"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT * FROM playermoves WHERE item_title LIKE %s",
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

    def update_player_move(
        self,
        move_id,
        dice_roll=None,
        cell_from=None,
        cell_to=None,
        stair_from=None,
        stair_to=None,
        snake_from=None,
        snake_to=None,
        move_type=None,
        item_title=None,
        item_review=None,
        item_rating=None,
        item_length=None,
        vod_link=None,
    ):
        """Обновить информацию о ходе игрока"""
        updates = []
        params = []

        if dice_roll is not None:
            updates.append("dice_roll = %s")
            params.append(dice_roll)
        if cell_from is not None:
            updates.append("cell_from = %s")
            params.append(cell_from)
        if cell_to is not None:
            updates.append("cell_to = %s")
            params.append(cell_to)
        if stair_from is not None:
            updates.append("stair_from = %s")
            params.append(stair_from)
        if stair_to is not None:
            updates.append("stair_to = %s")
            params.append(stair_to)
        if snake_from is not None:
            updates.append("snake_from = %s")
            params.append(snake_from)
        if snake_to is not None:
            updates.append("snake_to = %s")
            params.append(snake_to)
        if move_type is not None:
            updates.append("type = %s")
            params.append(move_type)
        if item_title is not None:
            updates.append("item_title = %s")
            params.append(item_title)
        if item_review is not None:
            updates.append("item_review = %s")
            params.append(item_review)
        if item_rating is not None:
            updates.append("item_rating = %s")
            params.append(item_rating)
        if item_length is not None:
            updates.append("item_length = %s")
            params.append(item_length)
        if vod_link is not None:
            updates.append("vod_link = %s")
            params.append(vod_link)

        params.append(move_id)
        query = f'UPDATE playermoves SET {", ".join(updates)} WHERE id = %s'
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(query, params)

    def delete_player_move(self, move_id):
        """Удалить ход игрока по ID"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute("DELETE FROM playermoves WHERE id = %s", (move_id,))

    # --- Методы для получения игроков с позицией на карте ---

    def get_all_players(self) -> list[dict]:
        """Получить всех игроков с их текущей позицией на карте"""
        query = """
        SELECT *
        FROM users u
        WHERE u.role = 'player' and is_active = 1
        """
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def add_player_move(
        self,
        player_id,
        dice_roll,
        cell_from,
        cell_to,
        stair_from=None,
        stair_to=None,
        snake_from=None,
        snake_to=None,
        move_type=None,
        item_title=None,
        item_review=None,
        item_rating=None,
        item_length=None,
        vod_link=None,
    ):
        """Добавить ход игрока и обновить его позицию на карте"""
        # Добавляем новый ход в playermoves
        with closing(self.conn().cursor()) as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO playermoves (player_id, dice_roll, cell_from, cell_to, stair_from, stair_to,
                                             snake_from, snake_to, type, item_title, item_review, item_rating, item_length, vod_link)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        player_id,
                        dice_roll,
                        cell_from,
                        cell_to,
                        stair_from,
                        stair_to,
                        snake_from,
                        snake_to,
                        move_type,
                        item_title,
                        item_review,
                        item_rating,
                        item_length,
                        vod_link,
                    ),
                )
            except Exception as e:
                logging.error("add_player_move: " + str(e))
                self.conn().rollback()  # откат изменений в случае ошибки
                raise e

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
        """Обновить поле vod_link и item_title в таблице playermoves"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                """
                UPDATE playermoves
                SET vod_link = %s, item_title = %s
                WHERE id = %s
            """,
                (vod_link, title, move_id),
            )

    def update_player_current_game(self, player_id: int, title: str):
        """Обновить поле player_current_game в таблице users"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                """
                UPDATE users
                SET player_current_game = %s
                WHERE id = %s
                """,
                (title, player_id),
            )

    def update_player_position(self, player_id, new_position):
        """Обновить поле map_position в таблице users"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                """
                UPDATE users
                SET map_position = %s
                WHERE id = %s
            """,
                (new_position, player_id),
            )

    def update_player_stream_category(self, player_id, player_stream_current_category):
        """Обновить поле player_stream_current_category в таблице users"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                """
                UPDATE users
                SET player_stream_current_category = %s
                WHERE id = %s
            """,
                (player_stream_current_category, player_id),
            )

    def get_move_by_id(self, move_id):
        """Получить ход игрока по ID"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute("SELECT * FROM playermoves WHERE id = %s", (move_id,))
            return cursor.fetchone()

    def get_players_last_cell_number(self):
        """Получить последние ячейки игроков"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                """
                SELECT moves.player_id as player_id, moves.id as id, moves.cell_to as cell_to
                FROM playermoves moves
                JOIN (
                    SELECT player_id, MAX(id) as max_id
                    FROM playermoves
                    GROUP BY player_id
                ) sub
                on moves.id = sub.max_id
                """
            )
            return cursor.fetchall()

    def get_players_positions_by_move_id(self, move_id: int):
        """Получить позиции игроков на определенный ход"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                """
                SELECT moves.player_id as player_id, moves.id as id, moves.cell_to as cell_to
                FROM playermoves moves
                JOIN (
                    SELECT player_id, MAX(id) as max_id
                    FROM playermoves
                    WHERE id < %s
                    GROUP BY player_id
                ) sub
                on moves.id = sub.max_id
            """,
                (move_id,),
            )
            return cursor.fetchall()

    def get_moves_count_by_player_id(self, player_id):
        """Получить количество ходов игрока"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT COUNT(*) as count FROM playermoves WHERE player_id = %s",
                (player_id,),
            )
            return cursor.fetchone()

    def get_games_completed_by_player_id(self, player_id):
        """Получить количество завершенных игр"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                'SELECT COUNT(*) as count FROM playermoves WHERE player_id = %s AND type = "completed"',
                (player_id,),
            )
            return cursor.fetchone()

    def get_games_dropped_by_player_id(self, player_id):
        """Получить количество пропущенных игр"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                'SELECT COUNT(*) as count FROM playermoves WHERE player_id = %s AND type = "drop"',
                (player_id,),
            )
            return cursor.fetchone()

    def get_games_sheikh_by_player_id(self, player_id):
        """Получить количество игр с шейхой"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                'SELECT COUNT(*) as count FROM playermoves WHERE player_id = %s AND type = "sheikh"',
                (player_id,),
            )
            return cursor.fetchone()

    def get_reroll_count_by_player_id(self, player_id):
        """Получить количество рероллов"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                'SELECT COUNT(*) as count FROM playermoves WHERE player_id = %s AND type = "reroll"',
                (player_id,),
            )
            return cursor.fetchone()

    def get_movies_count_by_player_id(self, player_id):
        """Получить количество фильмов"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                'SELECT COUNT(*) as count FROM playermoves WHERE player_id = %s AND type = "movie"',
                (player_id,),
            )
            return cursor.fetchone()

    def get_ladders_count_by_player_id(self, player_id):
        """Получить количество ладдеров"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT COUNT(*) as count FROM playermoves WHERE player_id = %s AND stair_from IS NOT NULL",
                (player_id,),
            )
            return cursor.fetchone()

    def get_snakes_count_by_player_id(self, player_id):
        """Получить количество змей"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT COUNT(*) as count FROM playermoves WHERE player_id = %s AND snake_from IS NOT NULL",
                (player_id,),
            )
            return cursor.fetchone()

    def get_user_by_name(self, username):
        """Получить инфу пользователя по имени"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE UPPER(username) = UPPER(%s) and is_active = 1",
                (username,),
            )
            return cursor.fetchone()

    def get_user_by_token(self, token: str):
        """Получить инфу пользователя по токену"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute("SELECT * FROM users WHERE pointauc_token = %s", (token,))
            return cursor.fetchone()

    def remove_moves_by_player_name(self, username):
        """Удалить все ходы игрока"""
        player_id = self.get_user_by_name(username)["id"]
        with closing(self.conn().cursor()) as cursor:
            cursor.execute("DELETE FROM playermoves WHERE player_id = %s", (player_id,))

    def remove_moves_by_player_id(self, player_id):
        """Удалить все ходы игрока"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute("DELETE FROM playermoves WHERE player_id = %s", (player_id,))

    def reset_finished_players(self):
        last_cells = self.get_players_last_cell_number()
        for i in last_cells:
            if i["cell_to"] >= 101:
                self.remove_moves_by_player_id(i["player_id"])
        return True

    def add_image(self, player_id, url, width, height, x=0, y=0, rotation=0):
        """Добавить изображение"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "SELECT MAX(zIndex) FROM PlayerFiles WHERE player_id = %s", (player_id,)
            )
            z_index = cursor.fetchone()
            z_index = (z_index[0] + 1) if z_index[0] is not None else 0
            cursor.execute(
                "INSERT INTO PlayerFiles (player_id, rotation, x, y, url, width, height, zIndex)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (player_id, rotation, x, y, url, width, height, z_index),
            )
            return z_index

    def get_last_image_id(self, player_id):
        """Получить ID последнего изображения игрока"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "SELECT id FROM PlayerFiles WHERE player_id = %s ORDER BY id DESC LIMIT 1",
                (player_id,),
            )
            return cursor.fetchone()

    def update_last_auction_result_by_player_id(
        self, player_id: int, game: str | None, auc_value: int | None = 0
    ):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "UPDATE users SET player_current_game = %s, current_game_updated_at = %s, current_auction_total_sum = %s, auction_timer_started_at = NULL WHERE id = %s",
                (game, datetime.datetime.utcnow(), auc_value, player_id),
            )

    def update_current_online_count_by_player_id(self, player_id, online_count):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "UPDATE users SET online_count = %s WHERE id = %s",
                (online_count, player_id),
            )

    def update_last_auction_date_by_player_id(self, player_id):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "UPDATE users SET auction_timer_started_at = %s WHERE id = %s",
                (datetime.datetime.utcnow(), player_id),
            )

    def get_player_files_by_player_id(self, player_id):
        sql = """
            SELECT id, rotation, x, y, url, width, height, zIndex, scaleX, scaleY
            FROM PlayerFiles
            WHERE player_id = %s
        """
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(sql, (player_id,))
            return cursor.fetchall()

    def delete_file(self, file_id):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute("DELETE FROM PlayerFiles WHERE id = %s", (file_id,))

    def delete_files_by_player_id(self, player_id):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute("DELETE FROM PlayerFiles WHERE player_id = %s", (player_id,))

    def update_player_files_by_file_id(
        self, file_id, width, height, x, y, rotation, z_index, scale_x=1, scale_y=1
    ):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "UPDATE PlayerFiles SET width = %s, height = %s, x = %s, y = %s, rotation = %s, zIndex = %s, scaleX = %s, scaleY = %s WHERE id = %s",
                (width, height, x, y, rotation, z_index, scale_x, scale_y, file_id),
            )

    def insert_player_files_by_player_id(
        self, player_id, width, height, x, y, rotation, url
    ):
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                "INSERT INTO PlayerFiles (player_id, width, height, x, y, rotation, url) VALUES (%s, %s, %s, %s, %s, %s, %s)",
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
                #cursor.execute(
                #    "INSERT INTO categories_history (category_name, online_count, player_id) VALUES (%s, %s, %s)",
                #    (
                #        category,
                #        online_count,
                #        player_id,
                #    ),
                #)
            #else:
                #cursor.execute(
                #    "INSERT INTO categories_history (category_name, online_count, player_id) VALUES (%s, %s, %s)",
                #    (
                #        "Offline",
                #        online_count,
                #        player_id,
                #    ),
                #)

    def update_player_pointauc_token(self, player_id: int, token: str):
        """Обновить поле pointauc_token в таблице users"""
        with closing(self.conn().cursor()) as cursor:
            cursor.execute(
                """
                UPDATE users
                SET pointauc_token = %s
                WHERE id = %s
            """,
                (token, player_id),
            )

    def get_players_stats(self):
        """Получить статистику всех игроков"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute(
                """
                SELECT
                moves.player_id,
                COUNT(*) as total_moves,
                SUM(CASE WHEN moves.type = 'completed' THEN 1 ELSE 0 END) as games_completed,
                SUM(CASE WHEN moves.type = 'drop' THEN 1 ELSE 0 END) as games_dropped,
                SUM(CASE WHEN moves.type = 'sheikh' THEN 1 ELSE 0 END) as sheikh_moments,
                SUM(CASE WHEN moves.type = 'reroll' THEN 1 ELSE 0 END) as rerolls,
                SUM(CASE WHEN moves.type = 'movie' THEN 1 ELSE 0 END) as movies,
                SUM(CASE WHEN moves.stair_from IS NOT NULL THEN 1 ELSE 0 END) as ladders,
                SUM(CASE WHEN moves.snake_from IS NOT NULL THEN 1 ELSE 0 END) as snakes,
                SUM(CASE WHEN moves.type = 'completed' && moves.item_length = 'tiny' THEN 1 ELSE 0 END) as tiny_games,
                SUM(CASE WHEN moves.type = 'completed' && moves.item_length = 'short' THEN 1 ELSE 0 END) as short_games,
                SUM(CASE WHEN moves.type = 'completed' && moves.item_length = 'medium' THEN 1 ELSE 0 END) as medium_games,
                SUM(CASE WHEN moves.type = 'completed' && moves.item_length = 'long' THEN 1 ELSE 0 END) as long_games,
                AVG(CASE WHEN moves.type <> 'reroll' THEN ABS(moves.dice_roll) ELSE null END) as average_move,
                AVG(
                  CASE
                    WHEN moves.cell_to > 101
                    THEN NULL
                    WHEN moves.item_length in ('tiny', 'short')
                    THEN ABS(moves.dice_roll)
                    WHEN moves.item_length = 'medium' and moves.cell_from < 81
                    THEN ABS(moves.dice_roll / 2)
                    WHEN moves.item_length = 'long' and moves.cell_from < 81
                    THEN ABS(moves.dice_roll / 3)
                    WHEN moves.cell_from < 81 and (type = 'drop' or type = 'sheikh')
                    THEN ABS(moves.dice_roll)
                    WHEN moves.cell_from >= 81 and moves.item_length in ('medium', 'long')
                    THEN ABS(moves.dice_roll)
                    WHEN moves.cell_from >= 81 and (type = 'drop' or type = 'sheikh')
                    THEN ABS(moves.dice_roll / 2)
                    ELSE
                    NULL
                  END
                ) as average_dice_roll,
                SUM(CASE WHEN moves.stair_from IS NOT NULL && moves.stair_to IS NOT NULL THEN moves.stair_to - moves.stair_from ELSE 0 END) as ladders_moves_sum,
                SUM(CASE WHEN moves.snake_from IS NOT NULL && moves.snake_to IS NOT NULL THEN moves.snake_to - moves.snake_from ELSE 0 END) as snakes_moves_sum,
                COALESCE((
                  SELECT subquery.cell_to
                  FROM playermoves subquery
                  WHERE subquery.player_id = moves.player_id
                  ORDER BY subquery.id DESC
                  LIMIT 1
                ), 0) as map_position
                FROM playermoves moves
                GROUP BY moves.player_id
                """
            )
            stats = cursor.fetchall()
            return stats

    def get_dons(self):
        """Получить всех донатеров"""
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute("SELECT * FROM dons ORDER BY sum desc, id desc")
            return cursor.fetchall()

    def get_igdb_token(self):
        with closing(self.conn().cursor(DictCursor)) as cursor:
            cursor.execute("SELECT * FROM igdb_token")
            return cursor.fetchone()

    def close(self):
        """Закрыть соединение с базой данных"""
        self.conn().close()

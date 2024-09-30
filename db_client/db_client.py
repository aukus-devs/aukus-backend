import sqlite3


class DatabaseClient:
    def __init__(self, db_name='aukus.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()

    # --- Методы для работы с таблицей users ---

    def add_user(self, name, role, stream_link, is_online, current_game, url_handle, moder_for, password,
                 vk_stream_link, donation_link, player_stream_current_category):
        """Добавить нового пользователя"""
        self.cursor.execute('''
            INSERT INTO users (name, role, twitch_stream_link, player_is_online, player_current_game,
                               player_url_handle, moder_for, password, vk_stream_link, donation_link, player_stream_current_category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, role, stream_link, is_online, current_game, url_handle, moder_for, password, vk_stream_link,
              donation_link, player_stream_current_category))
        self.conn.commit()

    def get_user_by_id(self, user_id):
        """Получить пользователя по ID"""
        self.cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return self.cursor.fetchone()

    def get_user_by_logpass(self, username, password):
        return self.cursor.execute('SELECT * FROM users WHERE UPPER(username) = UPPER(?) AND password = ?',
                                   (username, password)).fetchone()

    def get_all_users(self):
        """Получить всех пользователей"""
        self.cursor.execute('SELECT * FROM users')
        return self.cursor.fetchall()

    def update_user(self, user_id, name=None, role=None, stream_link=None, is_online=None, current_game=None,
                    url_handle=None, moder_for=None, password=None, vk_stream_link=None, donation_link=None, player_stream_current_category=None):
        """Обновить информацию о пользователе"""
        updates = []
        params = []

        if name:
            updates.append('name = ?')
            params.append(name)
        if role:
            updates.append('role = ?')
            params.append(role)
        if stream_link:
            updates.append('twitch_stream_link = ?')
            params.append(stream_link)
        if is_online is not None:
            updates.append('player_is_online = ?')
            params.append(is_online)
        if current_game:
            updates.append('player_current_game = ?')
            params.append(current_game)
        if url_handle:
            updates.append('player_url_handle = ?')
            params.append(url_handle)
        if moder_for is not None:
            updates.append('moder_for = ?')
            params.append(moder_for)
        if password:
            updates.append('password = ?')
            params.append(password)
        if vk_stream_link:
            updates.append('vk_stream_link = ?')
            params.append(vk_stream_link)
        if donation_link:
            updates.append('donation_link = ?')
            params.append(donation_link)
        if player_stream_current_category:
            updates.append('player_stream_current_category = ?')
            params.append(player_stream_current_category)

        params.append(user_id)
        query = f'UPDATE users SET {", ".join(updates)} WHERE id = ?'
        self.cursor.execute(query, params)
        self.conn.commit()

    def delete_user(self, user_id):
        """Удалить пользователя по ID"""
        self.cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        self.conn.commit()

    # --- Методы для работы с таблицей playermoves ---

    def get_moves_by_player(self, player_id):
        """Получить все ходы определенного игрока"""
        self.cursor.execute(
            "SELECT id, created_at, dice_roll, cell_from, cell_to, stair_from, stair_to, snake_from, snake_to, type, item_title, item_review, item_rating, item_length, vod_link, player_id FROM playermoves WHERE player_id = ? order by id desc",
            (player_id,),
        )
        return self.cursor.fetchall()

    def get_moves_by_date(self, date: str):
        """Получить все ходы за день"""
        self.cursor.execute(
            "SELECT id, created_at, dice_roll, cell_from, cell_to, stair_from, stair_to, snake_from, snake_to, type, item_title, item_review, item_rating, item_length, vod_link, player_id FROM playermoves WHERE DATE(created_at) = ? order by id desc",
            (date,),
        )
        return self.cursor.fetchall()

    def get_all_moves(self):
        """Получить все ходы"""
        self.cursor.execute('SELECT * FROM playermoves')
        return self.cursor.fetchall()

    def update_player_move(self, move_id, dice_roll=None, cell_from=None, cell_to=None, stair_from=None, stair_to=None,
                           snake_from=None, snake_to=None, move_type=None, item_title=None, item_review=None,
                           item_rating=None, item_length=None, vod_link=None):
        """Обновить информацию о ходе игрока"""
        updates = []
        params = []

        if dice_roll is not None:
            updates.append('dice_roll = ?')
            params.append(dice_roll)
        if cell_from is not None:
            updates.append('cell_from = ?')
            params.append(cell_from)
        if cell_to is not None:
            updates.append('cell_to = ?')
            params.append(cell_to)
        if stair_from is not None:
            updates.append('stair_from = ?')
            params.append(stair_from)
        if stair_to is not None:
            updates.append('stair_to = ?')
            params.append(stair_to)
        if snake_from is not None:
            updates.append('snake_from = ?')
            params.append(snake_from)
        if snake_to is not None:
            updates.append('snake_to = ?')
            params.append(snake_to)
        if move_type is not None:
            updates.append('type = ?')
            params.append(move_type)
        if item_title is not None:
            updates.append('item_title = ?')
            params.append(item_title)
        if item_review is not None:
            updates.append('item_review = ?')
            params.append(item_review)
        if item_rating is not None:
            updates.append('item_rating = ?')
            params.append(item_rating)
        if item_length is not None:
            updates.append('item_length = ?')
            params.append(item_length)
        if vod_link is not None:
            updates.append('vod_link = ?')
            params.append(vod_link)

        params.append(move_id)
        query = f'UPDATE playermoves SET {", ".join(updates)} WHERE id = ?'
        self.cursor.execute(query, params)
        self.conn.commit()

    def delete_player_move(self, move_id):
        """Удалить ход игрока по ID"""
        self.cursor.execute('DELETE FROM playermoves WHERE id = ?', (move_id,))
        self.conn.commit()

    # --- Методы для получения игроков с позицией на карте ---

    def get_all_players(self):
        """Получить всех игроков с их текущей позицией на карте"""
        query = '''
        SELECT *
        FROM users u
        WHERE u.role = 'player'
        GROUP BY u.id
        '''
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def add_player_move(self, player_id, dice_roll, cell_from, cell_to, stair_from=None, stair_to=None,
                        snake_from=None, snake_to=None, move_type=None, item_title=None, item_review=None,
                        item_rating=None, item_length=None, vod_link=None):
        """Добавить ход игрока и обновить его позицию на карте"""
        try:
            # Добавляем новый ход в playermoves
            self.cursor.execute('''
                INSERT INTO playermoves (player_id, dice_roll, cell_from, cell_to, stair_from, stair_to,
                                         snake_from, snake_to, type, item_title, item_review, item_rating, item_length, vod_link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (player_id, dice_roll, cell_from, cell_to, stair_from, stair_to, snake_from, snake_to,
                  move_type, item_title, item_review, item_rating, item_length, vod_link))

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()  # откат изменений в случае ошибки
            raise e

    def update_player_move_vod_link(self, move_id, vod_link):
        """Обновить поле vod_link в таблице playermoves"""
        self.cursor.execute('''
            UPDATE playermoves
            SET vod_link = ?
            WHERE id = ?
        ''', (vod_link, move_id))
        self.conn.commit()

    def update_player_position(self, player_id, new_position):
        """Обновить поле map_position в таблице users"""
        self.cursor.execute('''
            UPDATE users
            SET map_position = ?
            WHERE id = ?
        ''', (new_position, player_id))
        self.conn.commit()

    def update_player_stream_category(self, player_id, player_stream_current_category):
        """Обновить поле player_stream_current_category в таблице users"""
        self.cursor.execute('''
            UPDATE users
            SET player_stream_current_category = ?
            WHERE id = ?
        ''', (player_stream_current_category, player_id))
        self.conn.commit()

    def get_move_by_id(self, move_id):
        """Получить ход игрока по ID"""
        self.cursor.execute('SELECT * FROM playermoves WHERE id = ?', (move_id,))
        return self.cursor.fetchone()

    def get_last_cell_number(self, player_id):
        """Получить последнюю ячейку игрока"""
        self.cursor.execute('SELECT cell_to FROM playermoves WHERE player_id = ? ORDER BY id DESC LIMIT 1',
                            (player_id,))
        return self.cursor.fetchone()

    def get_moves_count_by_player_id(self, player_id):
        """Получить количество ходов игрока"""
        self.cursor.execute('SELECT COUNT(*) FROM playermoves WHERE player_id = ?', (player_id,))
        return self.cursor.fetchone()

    def get_games_completed_by_player_id(self, player_id):
        """Получить количество завершенных игр"""
        self.cursor.execute('SELECT COUNT(*) FROM playermoves WHERE player_id = ? AND type = "completed"',
                            (player_id,))
        return self.cursor.fetchone()

    def get_games_dropped_by_player_id(self, player_id):
        """Получить количество пропущенных игр"""
        self.cursor.execute('SELECT COUNT(*) FROM playermoves WHERE player_id = ? AND type = "drop"',
                            (player_id,))
        return self.cursor.fetchone()

    def get_games_sheikh_by_player_id(self, player_id):
        """Получить количество игр с шейхой"""
        self.cursor.execute('SELECT COUNT(*) FROM playermoves WHERE player_id = ? AND type = "sheikh"',
                            (player_id,))
        return self.cursor.fetchone()

    def get_reroll_count_by_player_id(self, player_id):
        """Получить количество рероллов"""
        self.cursor.execute('SELECT COUNT(*) FROM playermoves WHERE player_id = ? AND type = "reroll"', (player_id,))
        return self.cursor.fetchone()

    def get_movies_count_by_player_id(self, player_id):
        """Получить количество фильмов"""
        self.cursor.execute('SELECT COUNT(*) FROM playermoves WHERE player_id = ? AND type = "movie"', (player_id,))
        return self.cursor.fetchone()

    def get_ladders_count_by_player_id(self, player_id):
        """Получить количество ладдеров"""
        self.cursor.execute('SELECT COUNT(*) FROM playermoves WHERE player_id = ? AND stair_from IS NOT NULL',
                            (player_id,))
        return self.cursor.fetchone()

    def get_snakes_count_by_player_id(self, player_id):
        """Получить количество змей"""
        self.cursor.execute('SELECT COUNT(*) FROM playermoves WHERE player_id = ? AND snake_from IS NOT NULL',
                            (player_id,))
        return self.cursor.fetchone()

    def get_user_info_by_name(self, username):
        """Получить инфу пользователя по имени"""
        self.cursor.execute(
            "SELECT id, role, moder_for FROM users WHERE UPPER(username) = UPPER(?)",
            (username,),
        )
        return self.cursor.fetchone()

    def get_user_id_by_token(self, token: str):
        """Получить инфу пользователя по токену"""
        self.cursor.execute("SELECT id FROM users WHERE pointauc_token = ?", (token,))
        return self.cursor.fetchone()

    def remove_moves_by_player_name(self, username):
        """Удалить все ходы игрока"""
        player_id = self.get_user_info_by_name(username)[0]
        self.cursor.execute("DELETE FROM playermoves WHERE player_id = ?", (player_id,))
        self.conn.commit()

    def remove_moves_by_player_id(self, player_id):
        """Удалить все ходы игрока"""
        self.cursor.execute('DELETE FROM playermoves WHERE player_id = ?', (player_id,))
        self.conn.commit()

    def reset_finished_players(self):
        players = self.get_all_players()
        for i in players:
            last_cell = self.get_last_cell_number(i[0])
            if last_cell:
                if last_cell[0] > 101:
                    self.remove_moves_by_player_id(i[0])
        self.conn.commit()

        return True

    def add_image(self, player_id, url, width, height, x=0, y=0, rotation=0):
        """Добавить изображение"""
        z_index = self.cursor.execute('SELECT MAX(zIndex) FROM PlayerFiles WHERE player_id = ?',
                                      (player_id,)).fetchone()
        z_index = (z_index[0] + 1) if z_index[0] is not None else 0
        self.cursor.execute('INSERT INTO PlayerFiles (player_id, rotation, x, y, url, width, height, zIndex)'
                            ' VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                            (player_id, rotation, x, y, url, width, height, z_index))
        self.conn.commit()
        return z_index

    def get_last_image_id(self, player_id):
        """Получить ID последнего изображения игрока"""
        self.cursor.execute('SELECT id FROM PlayerFiles WHERE player_id = ? ORDER BY id DESC LIMIT 1', (player_id,))
        return self.cursor.fetchone()

    def update_current_game_by_player_id(self, player_id, game):
        self.cursor.execute('UPDATE users SET player_current_game = ? WHERE id = ?', (game, player_id))
        self.conn.commit()

    def get_player_files_by_player_id(self, player_id):
        sql = """
            SELECT id, rotation, x, y, url, width, height, zIndex, scaleX, scaleY
            FROM PlayerFiles
            WHERE player_id = ?
        """
        self.cursor.execute(sql, (player_id,))
        return self.cursor.fetchall()

    def delete_file(self, file_id):
        self.cursor.execute('DELETE FROM PlayerFiles WHERE id = ?', (file_id,))
        self.conn.commit()

    def delete_files_by_player_id(self, player_id):
        self.cursor.execute('DELETE FROM PlayerFiles WHERE player_id = ?', (player_id,))
        self.conn.commit()

    def update_player_files_by_file_id(self, file_id, width, height, x, y, rotation, z_index, scale_x=1, scale_y=1):
        self.cursor.execute(
            'UPDATE PlayerFiles SET width = ?, height = ?, x = ?, y = ?, rotation = ?, zIndex = ?, scaleX = ?, scaleY = ? WHERE id = ?',
            (width, height, x, y, rotation, z_index, scale_x, scale_y, file_id))
        self.conn.commit()

    def insert_player_files_by_player_id(self, player_id, width, height, x, y, rotation, url):
        self.cursor.execute(
            'INSERT INTO PlayerFiles (player_id, width, height, x, y, rotation, url) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (player_id, width, height, x, y, rotation, url))
        self.conn.commit()

    def update_stream_status(self, player_id, is_online, category=None):
        """Обновить поля player_is_online и player_stream_current_category в таблице users"""
        self.cursor.execute('''
            UPDATE users
            SET player_is_online = ?
            WHERE id = ?
        ''', (is_online, player_id))
        if category is not None:
            self.cursor.execute('''
                UPDATE users
                SET player_stream_current_category = ?
                WHERE id = ?
            ''', (category, player_id))
        self.conn.commit()

    def update_player_pointauc_token(self, player_id: int, token: str):
        """Обновить поле pointauc_token в таблице users"""
        self.cursor.execute(
            """
            UPDATE users
            SET pointauc_token = ?
            WHERE id = ?
        """,
            (token, player_id),
        )
        self.conn.commit()

    def close(self):
        """Закрыть соединение с базой данных"""
        self.conn.close()

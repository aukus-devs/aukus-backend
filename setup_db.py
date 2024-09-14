import sqlite3

def setup_database():
    conn = sqlite3.connect('aukus.db')
    cursor = conn.cursor()

    # Таблица users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT CHECK(role IN ('player', 'moder', 'admin')) NOT NULL,
        twitch_stream_link TEXT NOT NULL,
        player_is_online BOOLEAN NOT NULL,
        player_current_game TEXT NOT NULL,
        player_url_handle TEXT NOT NULL,
        moder_for INTEGER,
        password TEXT NOT NULL,
        vk_stream_link TEXT NOT NULL,
        donation_link TEXT NOT NULL
    )
    ''')

    # Таблица playermoves (без move_id)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS playermoves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        player_id INTEGER NOT NULL,
        dice_roll INTEGER NOT NULL,
        cell_from INTEGER NOT NULL,
        cell_to INTEGER NOT NULL,
        stair_from INTEGER,
        stair_to INTEGER,
        snake_from INTEGER,
        snake_to INTEGER,
        type TEXT CHECK(type IN ('drop', 'completed', 'sheikh', 'reroll', 'movie')) NOT NULL,
        item_title TEXT NOT NULL,
        item_review TEXT NOT NULL,
        item_rating INTEGER,
        item_length TEXT CHECK(item_length IN ('short', 'medium', 'long')),
        vod_link TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE PlayerFiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rotation REAL NOT NULL,
        player_id INTEGER NOT NULL,
        x REAL NOT NULL,
        y REAL NOT NULL,
        url TEXT NOT NULL,
        width REAL NOT NULL,
        height REAL NOT NULL);
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    setup_database()

from sqlalchemy import Integer, String
from core import db


class Game(db.Model):
    __bind__ = "games_db"
    __tablename__ = "igdb_games"

    game_id = db.Column(Integer, primary_key=True, index=True)
    name = db.Column(String, nullable=False)
    cover_url = db.Column(String)
    release_year = db.Column(Integer)
    platforms = db.Column(String)

    def __repr__(self):
        return f"<IGDBGame(game_id={self.game_id}, name='{self.name}')>"

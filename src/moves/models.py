from sqlalchemy import (
    Integer,
    Text,
    Float,
    TIMESTAMP,
    func,
)
from src.core import db


class PlayerMove(db.Model):
    __tablename__ = "player_moves"

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(
        TIMESTAMP, server_default=func.current_timestamp(), nullable=False
    )
    updated_at = db.Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )
    player_id = db.Column(Integer, nullable=False)
    dice_roll = db.Column(Integer, nullable=False)
    cell_from = db.Column(Integer, nullable=False)
    cell_to = db.Column(Integer, nullable=False)
    stair_from = db.Column(Integer, nullable=True)
    stair_to = db.Column(Integer, nullable=True)
    snake_from = db.Column(Integer, nullable=True)
    snake_to = db.Column(Integer, nullable=True)
    move_type = db.Column(Text(collation="utf8mb4_unicode_ci"), nullable=False)
    item_title = db.Column(Text(collation="utf8mb4_unicode_ci"), nullable=True)
    item_review = db.Column(Text(collation="utf8mb4_unicode_ci"), nullable=True)
    item_rating = db.Column(Float, nullable=False)
    item_length = db.Column(Text(collation="utf8mb4_unicode_ci"), nullable=True)
    vod_link = db.Column(Text(collation="utf8mb4_unicode_ci"), nullable=True)
    player_move_id = db.Column(Integer, nullable=True)

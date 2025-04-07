from sqlalchemy import (
    TIMESTAMP,
    Integer,
    String,
    Boolean,
    CheckConstraint,
    Text,
)
from src.core import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    username = db.Column(Text, nullable=False)
    role = db.Column(String, nullable=False)
    twitch_stream_link = db.Column(Text, nullable=False)
    player_is_online = db.Column(Boolean, nullable=False)
    player_current_game = db.Column(Text, nullable=False)
    player_url_handle = db.Column(Text, nullable=False)
    moder_for = db.Column(Integer, nullable=True)
    password_hash = db.Column(Text, nullable=False)
    vk_stream_link = db.Column(Text, nullable=False)
    donation_link = db.Column(Text, nullable=False)
    player_stream_current_category = db.Column(Text, nullable=True)
    pointauc_token = db.Column(Text, nullable=False)
    name = db.Column(Text, nullable=False)
    surname = db.Column(Text, nullable=False)
    telegram_link = db.Column(Text, nullable=False)
    current_game_updated_at = db.Column(
        TIMESTAMP,
        nullable=True,
    )
    is_active = db.Column(Boolean, nullable=False, default=True)
    kick_stream_link = db.Column(Text, nullable=False)
    online_count = db.Column(Integer, nullable=False, default=0)
    current_auction_total_sum = db.Column(Integer, nullable=False, default=0)
    auction_timer_started_at = db.Column(TIMESTAMP, nullable=True)

    __table_args__ = (
        CheckConstraint(
            role.in_(["player", "moder", "admin"]), name="check_role_valid"
        ),
    )

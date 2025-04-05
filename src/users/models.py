from sqlalchemy import (
    Integer,
    String,
    Boolean,
    CheckConstraint,
    Text,
)
from src.core.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(Text, nullable=False)
    role = db.Column(String, nullable=False)
    twitch_stream_link = db.Column(Text, nullable=False)
    player_is_online = db.Column(Boolean, nullable=False)
    player_current_game = db.Column(Text, nullable=False)
    player_url_handle = db.Column(Text, nullable=False)
    moder_for = db.Column(Integer, nullable=True)
    password = db.Column(Text, nullable=False)
    vk_stream_link = db.Column(Text, nullable=False)
    donation_link = db.Column(Text, nullable=False)
    player_stream_current_category = db.Column(Text, nullable=True)
    is_active = db.Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint(
            role.in_(["player", "moder", "admin"]), name="check_role_valid"
        ),
    )

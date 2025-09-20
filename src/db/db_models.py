from sqlalchemy.orm import Mapped, mapped_column  # type: ignore
from sqlalchemy.orm.decl_api import declarative_base
from sqlalchemy import Float, Integer, String, Text
from src.utils.db import utc_now_ts

DbBase = declarative_base()


class PlayerFile(DbBase):
    __tablename__ = "player_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[int] = mapped_column(Integer, default=utc_now_ts)
    updated_at: Mapped[int] = mapped_column(
        Integer, default=utc_now_ts, onupdate=utc_now_ts
    )

    rotation: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    player_slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    z_index: Mapped[int] = mapped_column("zIndex", Integer, nullable=False, default=0)
    scale_x: Mapped[int] = mapped_column("scaleX", Integer, nullable=False, default=1)
    scale_y: Mapped[int] = mapped_column("scaleY", Integer, nullable=False, default=1)


class Player(DbBase):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    color: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )


class PlayerMove(DbBase):
    __tablename__ = "player_moves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[int] = mapped_column(Integer, default=utc_now_ts)
    updated_at: Mapped[int] = mapped_column(
        Integer, default=utc_now_ts, onupdate=utc_now_ts
    )
    player_slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(255))
    item_title: Mapped[str] = mapped_column(String(255), nullable=False)
    item_duration: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    item_review: Mapped[str] = mapped_column(Text, nullable=False)
    item_rating: Mapped[float] = mapped_column(Float, nullable=False)
    item_length: Mapped[str] = mapped_column(String(255), nullable=False)
    vod_links: Mapped[str | None] = mapped_column(String(255), nullable=True)
    game_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dice_roll_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class DiceRoll(DbBase):
    __tablename__ = "dice_rolls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[int] = mapped_column(Integer, default=utc_now_ts)
    player_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_random_org_result: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    random_org_fail_reason: Mapped[str] = mapped_column(Text, nullable=True)
    json_short_data: Mapped[str] = mapped_column(Text, nullable=False)
    random_org_result: Mapped[str] = mapped_column(Text, nullable=True)
    dice_values: Mapped[str] = mapped_column(String(255), nullable=False)
    random_org_check_url: Mapped[str] = mapped_column(Text, nullable=True)


class EventSettings(DbBase):
    __tablename__ = "event_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[int] = mapped_column(Integer, default=utc_now_ts)
    updated_at: Mapped[int] = mapped_column(
        Integer, default=utc_now_ts, onupdate=utc_now_ts
    )
    key_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

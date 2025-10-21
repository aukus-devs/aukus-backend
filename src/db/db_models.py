# pyright: reportUnknownVariableType=false, reportUntypedBaseClass=false

from sqlalchemy.orm import Mapped, declarative_base, mapped_column  # pyright: ignore[reportAttributeAccessIssue]
from sqlalchemy import Float, Integer, String, Text
from .utils import utc_now_ts

DbBase = declarative_base()


class PlayerFile(DbBase):
    __tablename__: str = "player_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[int] = mapped_column(Integer, default=utc_now_ts)
    updated_at: Mapped[int] = mapped_column(
        Integer, default=utc_now_ts, onupdate=utc_now_ts
    )

    s3_file_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    rotation: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    player_slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    z_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scale_x: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    scale_y: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    attach_move_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Player(DbBase):
    __tablename__: str = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    color: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )


class PlayerMove(DbBase):
    __tablename__: str = "player_moves"

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
    item_length: Mapped[str] = mapped_column(String(255), nullable=True)
    vod_links: Mapped[str | None] = mapped_column(String(255), nullable=True)
    game_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    difficulty_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cell_from: Mapped[int] = mapped_column(Integer, nullable=False)
    cell_to: Mapped[int] = mapped_column(Integer, nullable=False)
    ladder_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ladder_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snake_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snake_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dice_roll_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dice_roll_sum: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dice_roll: Mapped[str | None] = mapped_column(String(255), nullable=True)


class EventSettings(DbBase):
    __tablename__: str = "event_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[int] = mapped_column(Integer, default=utc_now_ts)
    updated_at: Mapped[int] = mapped_column(
        Integer, default=utc_now_ts, onupdate=utc_now_ts
    )
    key_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)


class Rules(DbBase):
    __tablename__: str = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[int] = mapped_column(Integer, default=utc_now_ts, index=True)
    updated_at: Mapped[int] = mapped_column(
        Integer, default=utc_now_ts, onupdate=utc_now_ts
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False, index=True)


class Skin(DbBase):
    __tablename__: str = "skins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[int] = mapped_column(Integer, default=utc_now_ts)
    updated_at: Mapped[int] = mapped_column(
        Integer, default=utc_now_ts, onupdate=utc_now_ts
    )
    slot: Mapped[str] = mapped_column(String(255), nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)


class PlayerSkin(DbBase):
    __tablename__: str = "player_skins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[int] = mapped_column(Integer, default=utc_now_ts)
    updated_at: Mapped[int] = mapped_column(
        Integer, default=utc_now_ts, onupdate=utc_now_ts
    )
    player_slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    skin_id: Mapped[int] = mapped_column(Integer, nullable=False)
    is_equipped: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, index=True
    )


class Achievement(DbBase):
    __tablename__: str = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[int] = mapped_column(Integer, default=utc_now_ts)
    updated_at: Mapped[int] = mapped_column(
        Integer, default=utc_now_ts, onupdate=utc_now_ts
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reward_skin_id: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class PlayerAchievement(DbBase):
    __tablename__: str = "player_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[int] = mapped_column(Integer, default=utc_now_ts)
    player_slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    achievement_id: Mapped[int] = mapped_column(Integer, nullable=False)

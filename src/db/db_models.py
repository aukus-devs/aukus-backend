from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm.decl_api import declarative_base
from src.api.enums import Role, StreamPlatform
from sqlalchemy import Float, Integer, String, Text

DbBase = declarative_base()


class PlayerFile(DbBase):
    __tablename__ = "player_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rotation: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    player_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    z_index: Mapped[int] = mapped_column("zIndex", Integer, nullable=False, default=0)
    scale_x: Mapped[int] = mapped_column("scaleX", Integer, nullable=False, default=1)
    scale_y: Mapped[int] = mapped_column("scaleY", Integer, nullable=False, default=1)

class User(DbBase):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    url_handle: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(
        String(255), default=Role.PLAYER.value, nullable=False
    )
    is_online: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_game: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_game_cover: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_game_updated_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    online_count: Mapped[int] = mapped_column(Integer, default=0)
    current_auc_total_sum: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_auc_started_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pointauc_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    main_platform: Mapped[str] = mapped_column(
        String(255), default=StreamPlatform.NONE.value, nullable=False
    )
    twitch_stream_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vk_stream_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    kick_stream_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    donation_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer, default=1, index=True)
    avatar_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sector_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    maps_completed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    building_upgrade_bonus: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    color: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    moder_for: Mapped[int | None] = mapped_column(Integer, nullable=True)
    game_difficulty_level: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

from datetime import datetime
from sqlalchemy import func
from src.users.models import User
from src.core import db


def get_user_by_id(user_id: int) -> User | None:
    """Получить пользователя по ID"""
    return User.query.filter_by(id=user_id).first()


def get_user_by_login(username: str) -> User | None:
    return User.query.filter(
        func.upper(User.name) == func.upper(username), User.is_active.is_(True)
    ).first()


def get_all_users(only_is_active: bool = True) -> list[User]:
    """Получить всех пользователей"""
    query = User.query
    if only_is_active:
        query = query.filter(User.is_active.is_(True))
    return query.all()


def get_all_players() -> list[User]:
    """Получить всех игроков с их текущей позицией на карте"""
    return User.query.filter_by(role="player", is_active=True).all()


def update_player_current_game(player_id: int, title: str) -> None:
    """Обновить поле player_current_game в таблице users"""
    user = User.query.filter_by(id=player_id).first()
    if user:
        user.player_current_game = title
        db.session.commit()


def update_player_stream_category(
    player_id: int, player_stream_current_category: str
) -> None:
    """Обновить поле player_stream_current_category в таблице users"""
    user = User.query.filter_by(id=player_id).first()
    if user:
        user.player_stream_current_category = player_stream_current_category
        db.session.commit()


def get_user_by_username(username: str) -> User | None:
    """Получить инфу пользователя по имени"""
    return User.query.filter(
        func.upper(User.username) == func.upper(username), User.is_active == 1
    ).first()


def get_user_by_token(token: str) -> User | None:
    """Получить инфу пользователя по токену"""
    return User.query.filter_by(pointauc_token=token).first()


def update_last_auction_result_by_player_id(
    player_id: int, game: str | None, auc_value: int | None = 0
) -> None:
    """Обновить результат последнего аукциона для игрока по player_id"""
    player = User.query.filter_by(id=player_id).first()
    if player:
        player.player_current_game = game
        player.current_game_updated_at = datetime.utcnow()
        player.current_auction_total_sum = auc_value
        player.auction_timer_started_at = None
        db.session.commit()


def update_current_online_count_by_player_id(player_id: int, online_count: int) -> None:
    """Обновить количество онлайн игроков для игрока по player_id"""
    player = User.query.filter_by(id=player_id).first()
    if player:
        player.online_count = online_count
        db.session.commit()


def update_last_auction_date_by_player_id(player_id: int) -> None:
    """Обновить время последнего аукциона для игрока по player_id"""
    player = User.query.filter_by(id=player_id).first()
    if player:
        player.auction_timer_started_at = datetime.utcnow()
        db.session.commit()


def update_player_pointauc_token(player_id: int, token: str) -> None:
    """Обновить поле pointauc_token в таблице users"""
    player = User.query.filter_by(id=player_id).first()
    if player:
        player.pointauc_token = token
        db.session.commit()

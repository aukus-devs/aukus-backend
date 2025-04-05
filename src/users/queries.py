from sqlalchemy import func
from src.users.models import User


def get_user_by_id(user_id: int):
    """Получить пользователя по ID"""
    return User.query.filter_by(id=user_id).first()


def get_user_by_login(username: str):
    return User.query.filter(
        func.upper(User.name) == func.upper(username), User.is_active.is_(True)
    ).first()


def get_all_users(only_is_active: bool = True):
    """Получить всех пользователей"""
    query = User.query
    if only_is_active:
        query = query.filter(User.is_active.is_(True))
    return query.all()

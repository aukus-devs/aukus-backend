from sqlalchemy import func, case
from sqlalchemy.orm import aliased
from src.moves.models import PlayerMove
from src.core import db
import logging


def get_all_moves(limit: int = 50) -> list[PlayerMove]:
    """Получить все ходы"""
    return PlayerMove.query.order_by(PlayerMove.id.desc()).limit(limit).all()


def get_moves_by_player(player_id: int) -> list[PlayerMove]:
    """Получить все ходы определенного игрока"""
    return (
        PlayerMove.query.filter_by(player_id=player_id)
        .order_by(PlayerMove.id.desc())
        .all()
    )


def get_moves_by_date(date: str) -> list[PlayerMove]:
    """Получить все ходы за день"""
    return (
        PlayerMove.query.filter(func.date(PlayerMove.created_at) == date)
        .order_by(PlayerMove.id.desc())
        .all()
    )


def get_last_move_id_to_date(date: str) -> int | None:
    """Получить последний ход перед днем"""
    result = (
        PlayerMove.query.filter(func.date(PlayerMove.created_at) < date)
        .with_entities(func.max(PlayerMove.id))
        .scalar()
    )
    return result


def get_last_move_id_by_player(player_id: int) -> int | None:
    """Получить последний ход игрока"""
    result = (
        PlayerMove.query.filter_by(player_id=player_id)
        .with_entities(func.max(PlayerMove.id))
        .scalar()
    )
    return result


def get_last_move_id() -> int | None:
    """Получить последний ход"""
    result = PlayerMove.query.with_entities(func.max(PlayerMove.id)).scalar()
    return result


def update_player_move(
    move_id: int,
    dice_roll: int | None = None,
    cell_from: int | None = None,
    cell_to: int | None = None,
    stair_from: int | None = None,
    stair_to: int | None = None,
    snake_from: int | None = None,
    snake_to: int | None = None,
    move_type: str | None = None,
    item_title: str | None = None,
    item_review: str | None = None,
    item_rating: float | None = None,
    item_length: str | None = None,
    vod_link: str | None = None,
):
    """Обновить информацию о ходе игрока"""

    # Query the player move by ID
    move: PlayerMove | None = PlayerMove.query.get(move_id)

    if move:
        # Update only the fields that are not None
        if dice_roll is not None:
            move.dice_roll = dice_roll
        if cell_from is not None:
            move.cell_from = cell_from
        if cell_to is not None:
            move.cell_to = cell_to
        if stair_from is not None:
            move.stair_from = stair_from
        if stair_to is not None:
            move.stair_to = stair_to
        if snake_from is not None:
            move.snake_from = snake_from
        if snake_to is not None:
            move.snake_to = snake_to
        if move_type is not None:
            move.move_type = move_type
        if item_title is not None:
            move.item_title = item_title
        if item_review is not None:
            move.item_review = item_review
        if item_rating is not None:
            move.item_rating = item_rating
        if item_length is not None:
            move.item_length = item_length
        if vod_link is not None:
            move.vod_link = vod_link

        # Commit the changes to the database
        db.session.commit()


def add_player_move(
    player_id: int,
    dice_roll: int,
    cell_from: int,
    cell_to: int,
    stair_from: int | None = None,
    stair_to: int | None = None,
    snake_from: int | None = None,
    snake_to: int | None = None,
    move_type: str | None = None,
    item_title: str | None = None,
    item_review: str | None = None,
    item_rating: str | None = None,
    item_length: int | None = None,
    vod_link: str | None = None,
) -> None:
    """Добавить ход игрока и обновить его позицию на карте"""
    try:
        move = PlayerMove(
            player_id=player_id,
            dice_roll=dice_roll,
            cell_from=cell_from,
            cell_to=cell_to,
            stair_from=stair_from,
            stair_to=stair_to,
            snake_from=snake_from,
            snake_to=snake_to,
            move_type=move_type,
            item_title=item_title,
            item_review=item_review,
            item_rating=item_rating,
            item_length=item_length,
            vod_link=vod_link,
        )
        db.session.add(move)
        db.session.commit()
    except Exception as e:
        logging.error("add_player_move: %s", e)
        db.session.rollback()
        raise


def get_move_by_id(move_id: int) -> PlayerMove | None:
    """Получить ход игрока по ID"""
    return PlayerMove.query.get(move_id)


def get_players_last_moves() -> list[PlayerMove]:
    """Получить последние ходы игроков"""
    # Subquery to find the latest move (max ID) for each player
    subquery = (
        PlayerMove.query.with_entities(
            PlayerMove.player_id, func.max(PlayerMove.id).label("max_id")
        )
        .group_by(PlayerMove.player_id)
        .subquery()
    )

    # Main query to join the subquery and get the last move for each player
    result = (
        PlayerMove.query.join(
            subquery, PlayerMove.id == subquery.c.max_id
        ).all()  # Join with the subquery on max_id  # Get all results as model records
    )

    return result


def get_players_last_moves_before_move_id(move_id: int) -> list[PlayerMove]:
    """Получить позиции игроков на определенный ход"""
    # Subquery to find the latest move (max ID) for each player before the given move_id
    subquery = (
        PlayerMove.query.with_entities(
            PlayerMove.player_id, func.max(PlayerMove.id).label("max_id")
        )
        .filter(PlayerMove.id < move_id)
        .group_by(PlayerMove.player_id)
        .subquery()
    )

    # Main query to join the subquery and get the last move for each player before the given move_id
    result = (
        PlayerMove.query.join(
            subquery, PlayerMove.id == subquery.c.max_id
        ).all()  # Join with the subquery on max_id
    )

    return result


def remove_moves_by_player_name(username: str):
    """Удалить все ходы игрока по имени"""
    from src.users.queries import get_user_by_username

    # Get the player by username
    player = get_user_by_username(username)
    if player:
        # Delete all player moves for the given player_id
        PlayerMove.query.filter_by(player_id=player.id).delete()
        db.session.commit()  # Commit the transaction to apply changes


def remove_moves_by_player_id(player_id: int):
    """Удалить все ходы игрока по player_id"""
    # Delete all player moves for the given player_id
    PlayerMove.query.filter_by(player_id=player_id).delete()
    db.session.commit()  # Commit the transaction to apply changes


def get_players_stats(db_session):
    """Получить статистику всех игроков"""

    # Alias for subquery to get the last position (map_position) for each player
    subquery = (
        db_session.query(
            PlayerMove.player_id, func.max(PlayerMove.id).label("last_move_id")
        )
        .group_by(PlayerMove.player_id)
        .subquery()
    )

    last_move = aliased(PlayerMove, alias=subquery)

    # Main query for the players' statistics
    query = (
        db_session.query(
            PlayerMove.player_id,
            func.count().label("total_moves"),
            func.sum(case([(PlayerMove.type == "completed", 1)], else_=0)).label(
                "games_completed"
            ),
            func.sum(case([(PlayerMove.type == "drop", 1)], else_=0)).label(
                "games_dropped"
            ),
            func.sum(case([(PlayerMove.type == "sheikh", 1)], else_=0)).label(
                "sheikh_moments"
            ),
            func.sum(case([(PlayerMove.type == "reroll", 1)], else_=0)).label(
                "rerolls"
            ),
            func.sum(case([(PlayerMove.type == "movie", 1)], else_=0)).label("movies"),
            func.sum(case([(PlayerMove.stair_from != None, 1)], else_=0)).label(
                "ladders"
            ),
            func.sum(case([(PlayerMove.snake_from != None, 1)], else_=0)).label(
                "snakes"
            ),
            func.sum(
                case(
                    [
                        (
                            PlayerMove.type == "completed",
                            PlayerMove.item_length == "tiny",
                        )
                    ],
                    else_=0,
                )
            ).label("tiny_games"),
            func.sum(
                case(
                    [
                        (
                            PlayerMove.type == "completed",
                            PlayerMove.item_length == "short",
                        )
                    ],
                    else_=0,
                )
            ).label("short_games"),
            func.sum(
                case(
                    [
                        (
                            PlayerMove.type == "completed",
                            PlayerMove.item_length == "medium",
                        )
                    ],
                    else_=0,
                )
            ).label("medium_games"),
            func.sum(
                case(
                    [
                        (
                            PlayerMove.type == "completed",
                            PlayerMove.item_length == "long",
                        )
                    ],
                    else_=0,
                )
            ).label("long_games"),
            func.avg(
                case(
                    [(PlayerMove.type != "reroll", func.abs(PlayerMove.dice_roll))],
                    else_=None,
                )
            ).label("average_move"),
            func.avg(
                case(
                    [
                        (PlayerMove.cell_to > 101, None),
                        (
                            PlayerMove.item_length.in_(["tiny", "short"]),
                            func.abs(PlayerMove.dice_roll),
                        ),
                        (
                            PlayerMove.item_length == "medium",
                            PlayerMove.cell_from < 81,
                            func.abs(PlayerMove.dice_roll / 2),
                        ),
                        (
                            PlayerMove.item_length == "long",
                            PlayerMove.cell_from < 81,
                            func.abs(PlayerMove.dice_roll / 3),
                        ),
                        (
                            PlayerMove.cell_from < 81,
                            (
                                PlayerMove.type.in_(["drop", "sheikh"]),
                                func.abs(PlayerMove.dice_roll),
                            ),
                        ),
                        (
                            PlayerMove.cell_from >= 81,
                            PlayerMove.item_length.in_(["medium", "long"]),
                            func.abs(PlayerMove.dice_roll),
                        ),
                        (
                            PlayerMove.cell_from >= 81,
                            PlayerMove.type.in_(["drop", "sheikh"]),
                            func.abs(PlayerMove.dice_roll / 2),
                        ),
                    ],
                    else_=None,
                )
            ).label("average_dice_roll"),
            func.sum(
                case(
                    [
                        (
                            PlayerMove.stair_from != None,
                            PlayerMove.stair_to - PlayerMove.stair_from,
                        )
                    ],
                    else_=0,
                )
            ).label("ladders_moves_sum"),
            func.sum(
                case(
                    [
                        (
                            PlayerMove.snake_from != None,
                            PlayerMove.snake_to - PlayerMove.snake_from,
                        )
                    ],
                    else_=0,
                )
            ).label("snakes_moves_sum"),
            func.coalesce(last_move.cell_to, 0).label("map_position"),
        )
        .join(last_move, last_move.last_move_id == PlayerMove.id)
        .group_by(PlayerMove.player_id)
    )

    stats = query.all()
    return stats

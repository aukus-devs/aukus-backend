import json
import logging
from typing import cast

import httpx
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.player.models import DiceRollResult
from src.config import EVENTLAB_API_URL
from src.consts import LONGEST_LADDER, LONGEST_SNAKE
from src.db.db_models import (
    Achievement,
    Player,
    PlayerAchievement,
    PlayerMove,
    PlayerSkin,
    Skin,
)
from src.enums import DiceOption, GameLength, PlayerMoveType


def get_dice_options(move: PlayerMove) -> list[DiceOption]:
    match move.type:
        case PlayerMoveType.COMPLETED.value:
            if move.cell_from >= 81:
                return [DiceOption.D_1D6]
            match move.item_length:
                case GameLength.T_0_4.value:
                    return [DiceOption.D_1D2]
                case GameLength.T_5_10.value:
                    return [DiceOption.D_1D4]
                case GameLength.T_11_16.value:
                    return [DiceOption.D_2D4]
                case GameLength.T_17_24.value:
                    return [DiceOption.D_2D6]
                case GameLength.T_25_plus.value:
                    return [DiceOption.D_3D6]
                case _:
                    raise ValueError("Invalid item length")
        case PlayerMoveType.REROLL.value:
            return []
        case PlayerMoveType.SHIT_KICK.value:
            return []
        case PlayerMoveType.DROP.value:
            if move.cell_from >= 81:
                return [DiceOption.D_2D6]
            return [DiceOption.D_1D6]
        case PlayerMoveType.SHEIKH_MOMENT.value:
            if move.cell_from >= 81:
                return [DiceOption.D_2D6]
            return [DiceOption.D_1D6]
        case PlayerMoveType.MOVIE.value:
            return [DiceOption.D_1D4]
        case _:
            raise ValueError("Invalid move type")


async def get_dice_roll_from_eventlab(
    dice_roll_id: int, auth_token: str
) -> DiceRollResult:
    url = f"{EVENTLAB_API_URL}/api/dice-rolls/{dice_roll_id}"
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url, headers=headers)
    _ = response.raise_for_status()
    data = response.json()  # pyright: ignore[reportAny]
    return DiceRollResult(
        id=data["id"],  # pyright: ignore[reportAny]
        roll_values=data["roll_values"],  # pyright: ignore[reportAny]
    )


async def make_kick_dice_roll_from_eventlab(auth_token: str) -> DiceRollResult:
    url = f"{EVENTLAB_API_URL}/api/dice-rolls"
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with httpx.AsyncClient(timeout=5.0) as client:
        request_data = {"dice": "1d6", "used": False, "test_values": []}
        response = await client.post(url, headers=headers, json=request_data)
    _ = response.raise_for_status()
    data = response.json()  # pyright: ignore[reportAny]
    return DiceRollResult(
        id=data["id"],  # pyright: ignore[reportAny]
        roll_values=data["roll_values"],  # pyright: ignore[reportAny]
    )


def cell_row(cell: int) -> int:
    if cell > 100:
        return 11
    if cell < 1:
        return 0
    return (cell - 1) // 10 + 1


async def check_achievements_completion(
    db: AsyncSession, player: Player
) -> list[PlayerAchievement]:
    moves_query = await db.execute(
        select(PlayerMove)
        .where(PlayerMove.player_slug == player.slug)
        .order_by(PlayerMove.created_at.asc())
    )
    moves: list[PlayerMove] = moves_query.scalars().all()

    if not moves:
        return []

    unlocked_achievements_query = await db.execute(
        select(PlayerAchievement).where(PlayerAchievement.player_slug == player.slug)
    )
    unlocked_achievements: list[PlayerAchievement] = (
        unlocked_achievements_query.scalars().all()
    )
    unlocked_achievements_ids = {
        achievement.achievement_id for achievement in unlocked_achievements
    }

    locked_achievements_query = await db.execute(
        select(Achievement).where(Achievement.id.not_in(unlocked_achievements_ids))
    )
    locked_achievements: list[Achievement] = locked_achievements_query.scalars().all()

    new_achievements: list[PlayerAchievement] = []
    for achievement in locked_achievements:
        completed = check_achievement_completion(achievement, moves)
        if completed:
            new = PlayerAchievement(
                player_slug=player.slug, achievement_id=achievement.id
            )
            db.add(new)
            new_achievements.append(new)

    if new_achievements:
        new_achievements_ids = [ach.achievement_id for ach in new_achievements]
        new_skins_ids = [
            ach.reward_skin_id
            for ach in locked_achievements
            if ach.id in new_achievements_ids
        ]
        for skin_id in new_skins_ids:
            db.add(
                PlayerSkin(
                    player_slug=player.slug,
                    skin_id=skin_id,
                    is_equipped=0,
                )
            )

    return new_achievements


def check_achievement_completion(achievement: Achievement, moves: list[PlayerMove]):
    last_move = moves[-1] if moves else None
    if not last_move:
        return False

    last_move_dice_roll = cast(
        list[int], json.loads(last_move.dice_roll) if last_move.dice_roll else []
    )

    long_games = [
        move
        for move in moves
        if move.item_length == GameLength.T_25_plus.value
        and move.type == PlayerMoveType.COMPLETED.value
    ]

    tiny_games = [
        move
        for move in moves
        if move.item_length == GameLength.T_0_4.value
        and move.type == PlayerMoveType.COMPLETED.value
    ]

    movies = [move for move in moves if move.type == PlayerMoveType.MOVIE.value]

    match achievement.code:
        case "visit-1":
            return cell_row(last_move.cell_to) == 1
        case "visit-2":
            return cell_row(last_move.cell_to) == 2
        case "visit-3":
            return cell_row(last_move.cell_to) == 3
        case "visit-4":
            return cell_row(last_move.cell_to) == 4
        case "visit-5":
            return cell_row(last_move.cell_to) == 5
        case "visit-6":
            return cell_row(last_move.cell_to) == 6
        case "visit-7":
            return cell_row(last_move.cell_to) == 7
        case "visit-8":
            return cell_row(last_move.cell_to) == 8
        case "visit-9":
            return cell_row(last_move.cell_to) == 9
        case "visit-10":
            return cell_row(last_move.cell_to) == 10
        case "visit-all":
            visited_rows = set[int]()
            for move in moves:
                visited_rows.add(cell_row(move.cell_to))
            return len(visited_rows) == 10
        case "roll-all-6":
            return (
                all(roll == 6 for roll in last_move_dice_roll)
                and len(last_move_dice_roll) >= 2
            )
        case "roll-all-1":
            return (
                all(roll == 1 for roll in last_move_dice_roll)
                and len(last_move_dice_roll) >= 2
            )
        case "roll-all-same":
            return len(last_move_dice_roll) >= 2 and all(
                roll == last_move_dice_roll[0] for roll in last_move_dice_roll
            )
        case "long-games-1":
            return len(long_games) >= 1
        case "long-games-3":
            return len(long_games) >= 3
        case "tiny-games-2":
            return len(tiny_games) >= 2
        case "tiny-games-5":
            return len(tiny_games) >= 5
        case "movie-1":
            return len(movies) >= 1
        case "movie-2":
            return len(movies) >= 2
        case "complete-3":
            counter = 0
            for move in moves:
                if move.type == PlayerMoveType.COMPLETED.value:
                    counter += 1
                    if counter >= 3:
                        return True
                elif move.type == PlayerMoveType.REROLL.value:
                    continue
                else:
                    counter = 0
            return False
        case "complete-6":
            counter = 0
            for move in moves:
                if move.type == PlayerMoveType.COMPLETED.value:
                    counter += 1
                    if counter >= 6:
                        return True
                elif move.type == PlayerMoveType.REROLL.value:
                    continue
                else:
                    counter = 0
            return False
        case "drop-2":
            counter = 0
            for move in moves:
                if move.type == PlayerMoveType.DROP.value:
                    counter += 1
                    if counter >= 2:
                        return True
                elif move.type == PlayerMoveType.REROLL.value:
                    continue
                else:
                    counter = 0
            return False
        case "sheikh-1":
            return last_move.type == PlayerMoveType.SHEIKH_MOMENT.value
        case "sheikh-3":
            sheikh_moves = [
                move
                for move in moves
                if move.type == PlayerMoveType.SHEIKH_MOMENT.value
            ]
            return len(sheikh_moves) >= 3
        case "rate-10":
            return last_move.item_rating == 10
        case "rate-0":
            return last_move.item_rating == 0
        case "complete-easy":
            return (
                last_move.type == PlayerMoveType.COMPLETED.value
                and last_move.difficulty_level == -1
            )
        case "complete-very-hard":
            return (
                last_move.type == PlayerMoveType.COMPLETED.value
                and last_move.difficulty_level == 2
            )
        case "drop-easy":
            return (
                last_move.type == PlayerMoveType.DROP.value
                and last_move.difficulty_level == -1
            )
        case "drop-very-hard":
            return (
                last_move.type == PlayerMoveType.DROP.value
                and last_move.difficulty_level == 2
            )
        case "ladder-1":
            return last_move.ladder_to is not None
        case "ladder-3":
            ladders = [move for move in moves if move.ladder_to is not None]
            return len(ladders) >= 3
        case "ladder-long":
            return (
                last_move.ladder_from == LONGEST_LADDER[0]
                and last_move.ladder_to == LONGEST_LADDER[1]
            )
        case "ladder-repeat":
            ladders = set[int]()
            for move in moves:
                if move.ladder_from is not None:
                    if move.ladder_from in ladders:
                        return True
                    ladders.add(move.ladder_from)
            return False
        case "snake-1":
            return last_move.snake_to is not None
        case "snake-3":
            snakes = [move for move in moves if move.snake_to is not None]
            return len(snakes) >= 3
        case "snake-long":
            return (
                last_move.snake_from == LONGEST_SNAKE[0]
                and last_move.snake_to == LONGEST_SNAKE[1]
            )
        case "snake-repeat":
            snakes = set[int]()
            for move in moves:
                if move.snake_from is not None:
                    if move.snake_from in snakes:
                        return True
                    snakes.add(move.snake_from)
            return False
        case "drop-into-ladder":
            return (
                last_move.type == PlayerMoveType.DROP.value
                and last_move.ladder_to is not None
            )
        case "drop-into-snake":
            return (
                last_move.type == PlayerMoveType.DROP.value
                and last_move.snake_to is not None
            )
        case "fall-5+":
            max_pos = max(move.cell_to for move in moves)
            return cell_row(last_move.cell_to) <= cell_row(max_pos) - 5
        case "return-to-0":
            max_pos = max(move.cell_to for move in moves)
            return last_move.cell_to == 0 and max_pos > 0
        case _:
            return False


class StreamDurationResponse(BaseModel):
    duration: int
    sessions_count: int


class CloseCategoriesResponse(BaseModel):
    closed: int


async def fetch_stream_category_duration(
    token: str, current_user: Player, category: str
):
    duration = 0
    auth_headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            f"{EVENTLAB_API_URL}/api/streams/game-duration",
            params={"slug": current_user.slug, "game_name": category},
            headers=auth_headers,
        )
        if response.status_code == 200:
            data = StreamDurationResponse.model_validate(response.json())
            duration = data.duration
            logging.info(
                f"Got stream duration for {current_user.slug} - {category}: "
                + f"{duration}s ({data.sessions_count} sessions)"
            )

        if duration > 0:
            close_response = await client.post(
                f"{EVENTLAB_API_URL}/api/streams/close-game-categories",
                json={"slug": current_user.slug, "game_name": category},
                headers=auth_headers,
            )
            if close_response.status_code == 200:
                close_data = CloseCategoriesResponse.model_validate(
                    close_response.json()
                )
                logging.info(
                    f"Closed {close_data.closed} categories for "
                    + f"{current_user.slug} - {category}"
                )

    return duration


async def give_random_rewards(db: AsyncSession, player: Player) -> list[PlayerSkin]:
    unlocked_skins_query = await db.execute(
        select(PlayerSkin.skin_id).where(PlayerSkin.player_slug == player.slug)
    )
    unlocked_skins: list[PlayerSkin] = unlocked_skins_query.scalars().all()

    unlocked_skins_ids = [skin.skin_id for skin in unlocked_skins]

    reward_skin_query = await db.execute(
        select(Skin)
        .where(Skin.id.not_in(unlocked_skins_ids))
        .order_by(func.random())
        .limit(1)
    )
    reward_skin: Skin | None = reward_skin_query.scalars().first()
    if reward_skin:
        new_player_skin = PlayerSkin(
            player_slug=player.slug,
            skin_id=reward_skin.id,
            is_equipped=0,
        )
        db.add(new_player_skin)
        await db.flush()
        return [new_player_skin]

    return []

import httpx
from src.api.player.models import DiceRollResult
from src.config import EVENTLAB_API_URL
from src.db.db_models import PlayerMove
from src.enums import DiceOption, GameLength, PlayerMoveType


def get_dice_options(move: PlayerMove) -> list[DiceOption]:
    match move.type:
        case PlayerMoveType.COMPLETED.value:
            if move.cell_from >= 81:
                return [DiceOption.D_1D6]
            match move.item_length:
                case GameLength.T_0_3.value:
                    return [DiceOption.D_1D6]
                case GameLength.T_3_15.value:
                    return [DiceOption.D_1D6]
                case GameLength.T_15_30.value:
                    return [DiceOption.D_1D6, DiceOption.D_2D6]
                case GameLength.T_30_plus.value:
                    return [
                        DiceOption.D_1D6,
                        DiceOption.D_2D6,
                        DiceOption.D_3D6,
                    ]
                case _:
                    raise ValueError("Invalid item length")
        case PlayerMoveType.REROLL.value:
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


async def get_dice_roll_from_eventlab(dice_roll_id: int) -> DiceRollResult:
    url = f"{EVENTLAB_API_URL}/api/dice-rolls/{dice_roll_id}"
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url)
    _ = response.raise_for_status()
    data = response.json()  # pyright: ignore[reportAny]
    return DiceRollResult(
        id=data["id"],  # pyright: ignore[reportAny]
        roll_values=data["roll_values"],  # pyright: ignore[reportAny]
    )

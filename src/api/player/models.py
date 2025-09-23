from src.api.utils import ApiModel

class PlayerStatsItem(ApiModel):
    player_slug: str
    map_position: int
    total_moves: int
    games_completed: int
    games_dropped: int
    sheikh_moments: int
    rerolls: int
    movies: int
    ladders: int
    snakes: int
    tiny_games: int
    short_games: int
    medium_games: int
    long_games: int
    average_dice_roll: float
    average_move: float
    ladders_moves_sum: int
    snakes_moves_sum: int

class PlayerStatsResponse(ApiModel):
    players: list[PlayerStatsItem]

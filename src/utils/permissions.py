from fastapi import HTTPException, status

from src.db.db_models import Player, PlayerMove
from src.enums import UserRole
from src.utils.auth import TokenPayload


def can_edit_player(current_player: Player, target_player_slug: str, token_payload: TokenPayload) -> bool:
    if UserRole.ADMIN in token_payload.roles:
        return True
    
    if current_player.slug == target_player_slug:
        return True
    
    if target_player_slug in token_payload.moder_for:
        return True
    
    return False


def can_edit_move(current_player: Player, move: PlayerMove, token_payload: TokenPayload) -> bool:
    if UserRole.ADMIN in token_payload.roles:
        return True
    
    if current_player.slug == move.player_slug:
        return True
    
    if move.player_slug in token_payload.moder_for:
        return True
    
    return False


def require_edit_player_permission(current_player: Player, target_player_slug: str, token_payload: TokenPayload) -> None:
    if not can_edit_player(current_player, target_player_slug, token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this player"
        )


def require_edit_move_permission(current_player: Player, move: PlayerMove, token_payload: TokenPayload) -> None:
    if not can_edit_move(current_player, move, token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this move"
        )


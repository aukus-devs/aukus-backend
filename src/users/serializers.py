from pydantic import BaseModel


class PlayerDetailed(BaseModel):
    id: int
    name: str
    url_handle: str
    first_name: str
    last_name: str
    map_position: int

    twitch_stream_link: str
    vk_stream_link: str
    kick_stream_link: str
    donation_link: str
    telegram_link: str

    is_online: bool
    online_count: int

    stream_last_category: str
    current_auction_total_sum: int
    auction_timer_started_at: str | None
    current_game: str
    current_game_duration: int
    current_game_updated_at: str | None
    current_game_image: str | None

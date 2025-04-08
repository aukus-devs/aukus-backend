from sqlalchemy import func, case

from src.games.models import Game


def search_games_igdb(title: str) -> list[Game]:
    title = title.strip().lower()
    pattern_anywhere = f"%{title}%"
    pattern_start = f"{title}%"

    results = (
        Game.query.filter(func.lower(Game.name).like(pattern_anywhere))
        .order_by(
            case([(func.lower(Game.name).like(pattern_start), 0)], else_=1),
            func.length(Game.name).asc(),
        )
        .limit(20)
        .all()
    )

    return results


def search_games_multiple_igdb(titles: list[str]) -> list[Game]:
    if not titles:
        return []

    # Fetch all games that match the titles
    games = (
        Game.query.filter(
            func.lower(Game.name).in_([title.strip().lower() for title in titles])
        )
        .order_by(func.length(Game.name).asc())
        .all()
    )

    results = []

    # Loop over the titles and pick the first relevant game for each
    for title in titles:
        title = title.strip().lower()

        # Find the first game that matches the current title
        for game in games:
            if title in game.name.lower():
                results.append(game)
                break  # Stop after the first matching game for this title

    return results

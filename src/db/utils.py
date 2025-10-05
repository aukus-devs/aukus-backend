from datetime import datetime, timezone

from sqlalchemy import inspect  # pyright: ignore[reportUnknownVariableType]


def utc_now_ts():
    utc_now = datetime.now(timezone.utc)
    return int(utc_now.timestamp())


def model_to_dict(
    model: type, fields: list[str] | None = None
) -> dict[str, str | int | float | None]:
    if fields:
        return {field: getattr(model, field) for field in fields}
    return {c.key: getattr(model, c.key) for c in inspect(model).mapper.column_attrs}  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportUnknownVariableType]

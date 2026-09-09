import logging
import traceback
from collections.abc import Awaitable, Callable
from typing import Annotated

import httpx
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.canvas import routes as canvas
from src.api.event_data import routes as event_data
from src.api.player import routes as player
from src.api.rules import routes as rules
from src.config import (
    IS_LOCAL,
    PORT,
    TELEGRAM_ALERT_BOT_TOKEN,
    TELEGRAM_ALERT_CHAT_ID,
    TELEGRAM_ALERT_THREAD_ID,
    setup_logging,
)
from src.utils.auth import TokenPayload, get_admin_token

setup_logging()

logger = logging.getLogger(__name__)


async def send_telegram_alert(message: str) -> None:
    if not TELEGRAM_ALERT_BOT_TOKEN or not TELEGRAM_ALERT_CHAT_ID:
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_ALERT_BOT_TOKEN}/sendMessage"
        payload: dict[str, str | int] = {
            "chat_id": TELEGRAM_ALERT_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }

        if TELEGRAM_ALERT_THREAD_ID:
            payload["message_thread_id"] = int(TELEGRAM_ALERT_THREAD_ID)

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=5.0)
            if not response.is_success:
                logger.error(
                    f"Telegram API returned non-OK response: Status {response.status_code}, Body: {response.text}"
                )
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")


async def logging_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    try:
        response = await call_next(request)

        if response.status_code >= 400:
            logger.error(
                f"Failed request: {request.method} {request.url} - Status: {response.status_code}"
            )

            response_body: bytes = b""
            async for chunk in response.body_iterator:  # type: ignore[attr-defined,misc]
                response_body += chunk  # type: ignore[misc]

            body_text: str = ""
            try:
                body_text = response_body.decode()  # type: ignore[misc]
                if body_text:
                    logger.error(f"Error response body: {body_text}")
            except Exception as e:
                logger.error(f"Could not decode response body: {e}")

            if response.status_code >= 500:
                telegram_message = (
                    f"<b>Aukus 4 Backend, Server Error >=500</b>\n\n"
                    f"<b>Method:</b> {request.method}\n"
                    f"<b>URL:</b> {request.url}\n"
                    f"<b>Status:</b> {response.status_code}\n"
                )
                if body_text:
                    telegram_message += (
                        f"\n<b>Response:</b>\n<code>{body_text[:500]}</code>"
                    )

                await send_telegram_alert(telegram_message)

            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        return response
    except Exception as e:
        logger.error(f"Middleware error: {e}")
        raise


app = FastAPI(title="Aukus Backend")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    error_type = type(exc).__name__
    error_message = str(exc)

    logger.error(f"Unhandled exception: {error_type}: {error_message}")
    logger.error(traceback.format_exc())

    telegram_message = (
        f"<b>Aukus 4 Backend, Server Error</b>\n\n"
        f"<b>Method:</b> {request.method}\n"
        f"<b>URL:</b> {request.url}\n"
        f"<b>Error Type:</b> {error_type}\n"
        f"\n<b>Error:</b>\n<code>{error_message[:500]}</code>"
    )

    await send_telegram_alert(telegram_message)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_type": error_type},
    )


_ = app.middleware("http")(logging_middleware)


@app.get("/api/test/exception")
async def test_exception(
    _current_user: Annotated[TokenPayload, Depends(get_admin_token)],
):
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Test exception for Telegram alert",
    )


app.include_router(canvas.router)
app.include_router(event_data.router)
app.include_router(player.router)
app.include_router(rules.router)


def _build_allow_origin_regex() -> str:
    patterns: list[str] = []
    if IS_LOCAL:
        patterns.append(r"http://localhost(:\d+)?")
        patterns.append(r"http://127\.0\.0\.1(:\d+)?")
        patterns.append(r"https://eventlab\.dev")
        patterns.append(r"https://[a-zA-Z0-9-]+\.eventlab\.dev")
    else:
        patterns.append(r"https://eventlab\.dev")
        patterns.append(r"https://[a-zA-Z0-9-]+\.eventlab\.dev")
        patterns.append(r"http://localhost:5173")
    cors_pattern = "|".join(f"(?:{pattern})" for pattern in patterns)
    logger.info("CORS: %s", cors_pattern)
    return cors_pattern


_ = app.middleware("http")(logging_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=_build_allow_origin_regex(),
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],  # Adjust as needed for production
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)

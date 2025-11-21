from fastapi import FastAPI
import uvicorn
from src.api.event_data import routes as event_data
from src.api.canvas import routes as canvas
from src.api.player import routes as player
from src.api.rules import routes as rules
from fastapi.middleware.cors import CORSMiddleware

from src.config import IS_LOCAL, setup_logging

setup_logging()

app = FastAPI(title="Aukus Backend")
app.include_router(canvas.router)
app.include_router(event_data.router)
app.include_router(player.router)
app.include_router(rules.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8301)

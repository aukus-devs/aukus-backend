from fastapi import FastAPI
import uvicorn
from src.api.event_data import routes as event_data
from src.api.canvas import routes as canvas
from src.api.player import routes as player
from fastapi.middleware.cors import CORSMiddleware

from src.config import IS_LOCAL

app = FastAPI(title="Aukus Backend")
app.include_router(canvas.router)
app.include_router(event_data.router)
app.include_router(player.router)


if IS_LOCAL:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8381"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8301)

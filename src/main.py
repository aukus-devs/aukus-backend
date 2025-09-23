from fastapi import FastAPI
import uvicorn
from src.api.event_data import routes as event_data
from src.api.canvas import routes as canvas
from src.api.player import routes as player

app = FastAPI(title="Aukus Backend")
app.include_router(canvas.router)
app.include_router(event_data.router)
app.include_router(player.router)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

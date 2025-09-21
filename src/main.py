from fastapi import FastAPI
import uvicorn
from src.api.canvas import routes as canvas
from src.utils.auth import get_current_player_for_update
from src.config import DEBUG_NO_LOGIN
from types import SimpleNamespace

app = FastAPI(title="Aukus Backend")
app.include_router(canvas.router)

if DEBUG_NO_LOGIN:

    def _dev_user():
        return SimpleNamespace(id=1, role="admin")

    app.dependency_overrides[get_current_player_for_update] = _dev_user

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

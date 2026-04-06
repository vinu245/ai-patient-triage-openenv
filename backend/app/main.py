from __future__ import annotations

from pathlib import Path
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import SessionLocal, init_db
from app.env import OpenEnvTriage
from app.routes import router


class WebSocketManager:
    def __init__(self) -> None:
        self.connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.connections.discard(websocket)

    async def broadcast_json(self, payload: dict) -> None:
        stale = []
        for ws in self.connections:
            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)


init_db()
env = OpenEnvTriage(SessionLocal)

app = FastAPI(title="AI Patient Triage & Routing System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.env = env
app.state.ws_manager = WebSocketManager()

app.include_router(router)

static_dir = Path(__file__).resolve().parents[1] / "static"
assets_dir = static_dir / "assets"
index_file = static_dir / "index.html"

if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False, response_model=None)
async def serve_dashboard():
    if index_file.exists():
        return FileResponse(index_file)
    return {"status": "api-online", "ui": "not-built"}


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
async def spa_fallback(full_path: str):
    if full_path.startswith(("step", "reset", "state", "metrics", "health", "ws", "docs", "openapi.json")):
        raise HTTPException(status_code=404, detail="Not Found")
    if index_file.exists():
        return FileResponse(index_file)
    return {"status": "api-online", "ui": "not-built"}


@app.websocket("/ws")
async def websocket_updates(websocket: WebSocket) -> None:
    manager: WebSocketManager = app.state.ws_manager
    await manager.connect(websocket)

    try:
        await websocket.send_json(
            {
                "event": "bootstrap",
                "state": app.state.env.state().model_dump(),
                "metrics": app.state.env.metrics().model_dump(),
            }
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

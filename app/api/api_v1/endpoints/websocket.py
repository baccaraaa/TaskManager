import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError

from app.core.security import verify_token
from app.services.websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...),
):
    # Authenticate via query parameter token
    try:
        payload = verify_token(token)
        token_username = payload.get("sub")
        if not token_username:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except Exception:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive, receive messages (ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket client disconnected: user_id={user_id}")

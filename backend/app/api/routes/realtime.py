from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.dependencies import ConnectionManagerDep

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/tickets")
async def tickets_stream(websocket: WebSocket, manager: ConnectionManagerDep) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)

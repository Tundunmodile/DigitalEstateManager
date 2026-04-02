"""
WebSocket handlers for real-time chat
"""
import logging
from fastapi import WebSocket, APIRouter

from ui_layer.websocket.connection_manager import manager
from agent_layer.orchestration.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])

orchestrator = Orchestrator(enable_llm=True)


@router.websocket("/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time chat."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Process user input
            result = orchestrator.process_user_input(
                data.get("message", ""),
                data.get("user_id")
            )
            
            # Send response back
            await websocket.send_json({
                "client_id": client_id,
                "success": result["success"],
                "message": result["message"],
                "results": result.get("results"),
                "correlation_id": result["correlation_id"],
                "error": result.get("error")
            })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

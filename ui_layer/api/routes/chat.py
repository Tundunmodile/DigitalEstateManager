"""
FastAPI routes for chat API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging

from agent_layer.orchestration.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize orchestrator
orchestrator = Orchestrator(enable_llm=True)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    user_id: Optional[int] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    success: bool
    message: str
    results: Optional[List] = None
    correlation_id: str
    error: Optional[str] = None


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a chat message and get orchestrated response."""
    try:
        result = orchestrator.process_user_input(request.message, request.user_id)
        
        return ChatResponse(
            success=result["success"],
            message=result["message"],
            results=result.get("results"),
            correlation_id=result["correlation_id"],
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """Health check for chat endpoint."""
    return {"status": "ok"}

"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel
from typing import Optional, List, Any


class ChatRequest(BaseModel):
    """Chat message request."""
    message: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat message response."""
    success: bool
    message: str
    results: Optional[List[Any]] = None
    correlation_id: str
    error: Optional[str] = None


class HistoryRequest(BaseModel):
    """Chat history request."""
    user_id: int
    limit: int = 50
    offset: int = 0

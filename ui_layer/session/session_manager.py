"""
Session manager for chat sessions and history
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages chat sessions and history."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    
    def create_session(self, user_id: int, session_id: str) -> Dict:
        """Create a new chat session."""
        session = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "messages": []
        }
        self.sessions[session_id] = session
        return session
    
    def add_message(self, session_id: str, role: str, content: str, correlation_id: Optional[str] = None):
        """Add a message to a session."""
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found")
            return
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "correlation_id": correlation_id
        }
        self.sessions[session_id]["messages"].append(message)
    
    def get_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get chat history for a session."""
        if session_id not in self.sessions:
            return []
        
        messages = self.sessions[session_id]["messages"]
        return messages[-limit:]


# Global session manager
session_manager = SessionManager()

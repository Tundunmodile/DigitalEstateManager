"""
Database layer for conversation persistence
Handles storage and retrieval of conversations, sessions, and metadata
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()


class ConversationModel(Base):
    """SQLAlchemy model for storing conversations."""
    __tablename__ = "conversations"

    conversation_id = Column(String(36), primary_key=True)
    user_id = Column(String(255), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    title = Column(String(255), nullable=True)
    conv_metadata = Column(Text, default="{}")  # JSON string

    def __repr__(self):
        return f"<Conversation(id={self.conversation_id}, user={self.user_id}, created={self.created_at})>"


class MessageModel(Base):
    """SQLAlchemy model for storing conversation messages."""
    __tablename__ = "messages"

    message_id = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), index=True)
    role = Column(String(20))  # "user" or "assistant"
    content = Column(Text)
    source = Column(String(50), nullable=True)  # "company", "web", "error"
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    context_used = Column(Text, default="{}")  # JSON string with source flags

    def __repr__(self):
        return f"<Message(id={self.message_id}, conversation={self.conversation_id}, role={self.role})>"


class SessionModel(Base):
    """SQLAlchemy model for storing user sessions."""
    __tablename__ = "sessions"

    session_id = Column(String(36), primary_key=True)
    user_id = Column(String(255), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, index=True)
    is_active = Column(Boolean, default=True)
    session_metadata = Column(Text, default="{}")

    def __repr__(self):
        return f"<Session(id={self.session_id}, user={self.user_id}, active={self.is_active})>"


class QueryAnalyticsModel(Base):
    """SQLAlchemy model for storing query analytics."""
    __tablename__ = "query_analytics"

    query_id = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), index=True)
    query_text = Column(Text)
    intent = Column(String(100))  # "company_info", "general_knowledge", etc.
    source_used = Column(String(50))  # "company", "web", "both"
    processing_time = Column(Float)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<QueryAnalytics(id={self.query_id}, intent={self.intent})>"


class DatabaseManager:
    """
    Manages all database operations for persistence.
    Supports SQLite by default, can be extended to PostgreSQL/MySQL.
    """

    def __init__(self, database_url: Optional[str] = None, echo: bool = False):
        """
        Initialize database manager.

        Args:
            database_url: Database connection URL (default: sqlite:///apex_chatbot.db)
            echo: Enable SQL logging
        """
        self.database_url = database_url or "sqlite:///apex_chatbot.db"
        
        # For SQLite, use StaticPool to avoid threading issues
        if "sqlite" in self.database_url:
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=echo,
            )
        else:
            self.engine = create_engine(self.database_url, echo=echo)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Database initialized: {self.database_url}")

    @contextmanager
    def get_session(self) -> Session:
        """Context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()

    # Conversation methods
    def create_conversation(self, conversation_id: str, user_id: Optional[str] = None, title: Optional[str] = None) -> ConversationModel:
        """Create a new conversation."""
        with self.get_session() as session:
            conversation = ConversationModel(
                conversation_id=conversation_id,
                user_id=user_id,
                title=title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            )
            session.add(conversation)
            session.flush()
            logger.info(f"Created conversation: {conversation_id}")
            return conversation

    def get_conversation(self, conversation_id: str) -> Optional[ConversationModel]:
        """Get conversation by ID."""
        with self.get_session() as session:
            return session.query(ConversationModel).filter_by(conversation_id=conversation_id).first()

    def list_conversations(self, user_id: str, limit: int = 50) -> List[ConversationModel]:
        """List all conversations for a user."""
        with self.get_session() as session:
            return session.query(ConversationModel).filter_by(user_id=user_id).order_by(ConversationModel.updated_at.desc()).limit(limit).all()

    # Message methods
    def add_message(
        self,
        conversation_id: str,
        message_id: str,
        role: str,
        content: str,
        source: Optional[str] = None,
        context_used: Optional[Dict] = None,
    ) -> MessageModel:
        """Add a message to a conversation."""
        with self.get_session() as session:
            message = MessageModel(
                message_id=message_id,
                conversation_id=conversation_id,
                role=role,
                content=content,
                source=source,
                context_used=json.dumps(context_used or {}),
            )
            session.add(message)
            
            # Update conversation's updated_at timestamp
            conversation = session.query(ConversationModel).filter_by(conversation_id=conversation_id).first()
            if conversation:
                conversation.updated_at = datetime.utcnow()
            
            session.flush()
            logger.debug(f"Added message {message_id} to conversation {conversation_id}")
            return message

    def get_conversation_messages(self, conversation_id: str, limit: Optional[int] = None) -> List[MessageModel]:
        """Get all messages in a conversation."""
        with self.get_session() as session:
            query = session.query(MessageModel).filter_by(conversation_id=conversation_id).order_by(MessageModel.created_at)
            if limit:
                query = query.limit(limit)
            return query.all()

    # Query analytics methods
    def record_query_analytics(
        self,
        query_id: str,
        conversation_id: str,
        query_text: str,
        intent: str,
        source_used: str,
        processing_time: float,
    ) -> QueryAnalyticsModel:
        """Record query analytics for insights."""
        with self.get_session() as session:
            analytics = QueryAnalyticsModel(
                query_id=query_id,
                conversation_id=conversation_id,
                query_text=query_text,
                intent=intent,
                source_used=source_used,
                processing_time=processing_time,
            )
            session.add(analytics)
            session.flush()
            logger.debug(f"Recorded analytics for query {query_id}")
            return analytics

    def get_query_analytics(self, conversation_id: str) -> List[QueryAnalyticsModel]:
        """Get analytics for a conversation."""
        with self.get_session() as session:
            return session.query(QueryAnalyticsModel).filter_by(conversation_id=conversation_id).all()

    # Session methods
    def create_session(self, session_id: str, user_id: str, expires_in_hours: int = 24) -> SessionModel:
        """Create a new user session."""
        with self.get_session() as session:
            user_session = SessionModel(
                session_id=session_id,
                user_id=user_id,
                expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
            )
            session.add(user_session)
            session.flush()
            logger.info(f"Created session {session_id} for user {user_id}")
            return user_session

    def validate_session(self, session_id: str) -> bool:
        """Check if session is active and not expired."""
        with self.get_session() as session:
            user_session = session.query(SessionModel).filter_by(session_id=session_id).first()
            if not user_session:
                return False
            if not user_session.is_active:
                return False
            if user_session.expires_at < datetime.utcnow():
                user_session.is_active = False
                return False
            return True

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions. Returns number deleted."""
        with self.get_session() as session:
            expired = session.query(SessionModel).filter(SessionModel.expires_at < datetime.utcnow()).delete()
            logger.info(f"Cleaned up {expired} expired sessions")
            return expired

    # Statistics
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with self.get_session() as session:
            stats = {
                "conversations": session.query(ConversationModel).count(),
                "messages": session.query(MessageModel).count(),
                "queries_analyzed": session.query(QueryAnalyticsModel).count(),
                "active_sessions": session.query(SessionModel).filter_by(is_active=True).count(),
            }
            return stats

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages."""
        with self.get_session() as session:
            # Delete messages
            session.query(MessageModel).filter_by(conversation_id=conversation_id).delete()
            # Delete analytics
            session.query(QueryAnalyticsModel).filter_by(conversation_id=conversation_id).delete()
            # Delete conversation
            result = session.query(ConversationModel).filter_by(conversation_id=conversation_id).delete()
            logger.info(f"Deleted conversation {conversation_id}")
            return result > 0

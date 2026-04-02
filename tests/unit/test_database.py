"""Unit tests for database layer."""

import pytest
from datetime import datetime, timedelta
from chatbot.database import DatabaseManager, ConversationModel, MessageModel


class TestDatabaseManager:
    """Test suite for DatabaseManager."""

    @pytest.mark.unit
    def test_initialization(self, temp_db):
        """Test database manager initialization."""
        assert temp_db is not None
        assert temp_db.engine is not None
        assert temp_db.SessionLocal is not None

    @pytest.mark.unit
    def test_create_conversation(self, temp_db):
        """Test creating a new conversation."""
        conversation_id = "test-conv-001"
        user_id = "test-user"
        title = "Test Conversation"
        
        conv = temp_db.create_conversation(conversation_id, user_id, title)
        
        assert conv.conversation_id == conversation_id
        assert conv.user_id == user_id
        assert conv.title == title

    @pytest.mark.unit
    def test_get_conversation(self, temp_db):
        """Test retrieving a conversation."""
        conversation_id = "test-conv-002"
        temp_db.create_conversation(conversation_id, "test-user")
        
        conv = temp_db.get_conversation(conversation_id)
        
        assert conv is not None
        assert conv.conversation_id == conversation_id

    @pytest.mark.unit
    def test_get_nonexistent_conversation(self, temp_db):
        """Test getting a non-existent conversation."""
        conv = temp_db.get_conversation("nonexistent")
        assert conv is None

    @pytest.mark.unit
    def test_add_message(self, temp_db):
        """Test adding a message to a conversation."""
        conversation_id = "test-conv-003"
        temp_db.create_conversation(conversation_id)
        
        message_id = "test-msg-001"
        role = "user"
        content = "Test message"
        
        msg = temp_db.add_message(conversation_id, message_id, role, content, source="test")
        
        assert msg.message_id == message_id
        assert msg.role == role
        assert msg.content == content
        assert msg.source == "test"

    @pytest.mark.unit
    def test_get_conversation_messages(self, temp_db):
        """Test retrieving conversation messages."""
        conversation_id = "test-conv-004"
        temp_db.create_conversation(conversation_id)
        
        # Add multiple messages
        for i in range(3):
            temp_db.add_message(
                conversation_id,
                f"msg-{i}",
                "user" if i % 2 == 0 else "assistant",
                f"Message {i}"
            )
        
        messages = temp_db.get_conversation_messages(conversation_id)
        
        assert len(messages) == 3
        assert messages[0].message_id == "msg-0"
        assert messages[2].message_id == "msg-2"

    @pytest.mark.unit
    def test_record_query_analytics(self, temp_db):
        """Test recording query analytics."""
        conversation_id = "test-conv-005"
        temp_db.create_conversation(conversation_id)
        
        query_id = "query-001"
        query_text = "What is the price?"
        intent = "pricing_information"
        source_used = "company"
        processing_time = 0.5
        
        analytics = temp_db.record_query_analytics(
            query_id,
            conversation_id,
            query_text,
            intent,
            source_used,
            processing_time
        )
        
        assert analytics.query_id == query_id
        assert analytics.intent == intent
        assert analytics.source_used == source_used
        assert abs(analytics.processing_time - 0.5) < 0.01

    @pytest.mark.unit
    def test_create_session(self, temp_db):
        """Test creating a user session."""
        session_id = "sess-001"
        user_id = "user-001"
        
        session = temp_db.create_session(session_id, user_id, expires_in_hours=24)
        
        assert session.session_id == session_id
        assert session.user_id == user_id
        assert session.is_active is True

    @pytest.mark.unit
    def test_validate_session(self, temp_db):
        """Test session validation."""
        session_id = "sess-002"
        user_id = "user-002"
        
        temp_db.create_session(session_id, user_id)
        is_valid = temp_db.validate_session(session_id)
        
        assert is_valid is True

    @pytest.mark.unit
    def test_validate_nonexistent_session(self, temp_db):
        """Test validating non-existent session."""
        is_valid = temp_db.validate_session("nonexistent")
        assert is_valid is False

    @pytest.mark.unit
    def test_list_conversations(self, temp_db):
        """Test listing user conversations."""
        user_id = "user-003"
        
        # Create multiple conversations
        for i in range(3):
            temp_db.create_conversation(f"conv-{i}", user_id)
        
        conversations = temp_db.list_conversations(user_id)
        
        assert len(conversations) == 3

    @pytest.mark.unit
    def test_delete_conversation(self, temp_db):
        """Test deleting a conversation."""
        conversation_id = "test-conv-del"
        temp_db.create_conversation(conversation_id)
        
        deleted = temp_db.delete_conversation(conversation_id)
        
        assert deleted is True
        assert temp_db.get_conversation(conversation_id) is None

    @pytest.mark.unit
    def test_get_database_stats(self, temp_db):
        """Test getting database statistics."""
        conversation_id = "test-conv-stats"
        temp_db.create_conversation(conversation_id)
        temp_db.add_message(conversation_id, "msg-001", "user", "Test")
        
        stats = temp_db.get_database_stats()
        
        assert stats["conversations"] >= 1
        assert stats["messages"] >= 1

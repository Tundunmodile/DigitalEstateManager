"""Test fixtures and configurations."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from chatbot.database import DatabaseManager
from chatbot.property_database import PropertyDatabase
from chatbot.intent_classifier import get_intent_classifier
from chatbot.tools import ToolManager, setup_tools


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    db = DatabaseManager(f"sqlite:///{db_path}")
    yield db
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def property_db():
    """Create a property database instance for testing."""
    return PropertyDatabase()


@pytest.fixture
def intent_classifier():
    """Create an intent classifier for testing."""
    return get_intent_classifier()


@pytest.fixture
def tool_manager(property_db):
    """Create a tool manager with registered tools."""
    manager = ToolManager()
    setup_tools(property_db, manager)
    return manager


@pytest.fixture
def mock_tavily_client():
    """Mock Tavily web search client."""
    client = Mock()
    client.search.return_value = {
        "answer": "Test answer",
        "results": [
            {
                "title": "Test Result 1",
                "url": "https://example.com/1",
                "content": "Test content 1",
                "source": "example.com"
            }
        ]
    }
    return client


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic Claude client."""
    client = Mock()
    client.messages.create.return_value = Mock(
        content=[Mock(text="Test response from Claude")]
    )
    return client


@pytest.fixture
def sample_queries():
    """Sample test queries."""
    return {
        "company_query": "What are your pricing tiers?",
        "team_query": "Tell me about Victoria Chen",
        "pricing_query": "How much does the Premium plan cost?",
        "general_query": "Who is the president of the United States?",
        "web_query": "What is the latest technology trend?",
        "property_query": "Tell me about the property on Park Avenue",
        "maintenance_query": "What maintenance is scheduled for my property?",
    }


@pytest.fixture
def sample_conversations():
    """Sample conversation data."""
    return [
        {
            "conversation_id": "conv-001",
            "user_id": "user-001",
            "messages": [
                {"role": "user", "content": "What services do you offer?"},
                {"role": "assistant", "content": "We offer comprehensive home management services..."},
            ]
        }
    ]


class MockPremiumChatbot:
    """Mock chatbot for integration testing."""
    
    def __init__(self):
        self.conversation_history = []
        self.db = None
    
    def get_response(self, user_input, include_source=True):
        """Return mock response."""
        return {
            "response": f"Mock response to: {user_input}",
            "source": "company" if "service" in user_input.lower() else "web",
            "timestamp": "2026-04-02T10:00:00",
            "context_used": {
                "company_knowledge": True,
                "web_search": False
            }
        }
    
    def get_history(self):
        """Return mock history."""
        return self.conversation_history
    
    def clear_history(self):
        """Clear history."""
        self.conversation_history = []


@pytest.fixture
def mock_chatbot():
    """Create a mock chatbot for integration tests."""
    return MockPremiumChatbot()

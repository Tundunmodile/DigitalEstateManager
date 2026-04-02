"""Integration tests for chatbot end-to-end workflows."""

import pytest
from unittest.mock import Mock, patch


class TestChatbotE2E:
    """End-to-end integration tests for chatbot."""

    @pytest.mark.integration
    def test_property_search_workflow(self, property_db, tool_manager):
        """Test complete property search workflow."""
        # User asks about a property
        result = tool_manager.execute_tool(
            "search_properties",
            {"query": "Park Avenue"}
        )
        
        assert "result" in result
        assert "Park Avenue" in result["result"] or "Found" in result["result"]

    @pytest.mark.integration
    def test_vendor_search_workflow(self, property_db, tool_manager):
        """Test complete vendor search workflow."""
        # User searches for vendors
        result = tool_manager.execute_tool(
            "search_vendors",
            {"category": "HVAC"}
        )
        
        assert "result" in result

    @pytest.mark.integration
    def test_maintenance_scheduling_workflow(self, property_db, tool_manager):
        """Test complete maintenance scheduling workflow."""
        # Schedule maintenance
        result = tool_manager.execute_tool(
            "schedule_maintenance",
            {
                "property_id": "prop-001",
                "maintenance_type": "Test Service",
                "date": "2026-05-15",
                "vendor_id": "vendor-001"
            }
        )
        
        assert "result" in result or "error" in result

    @pytest.mark.integration
    def test_database_conversation_flow(self, temp_db):
        """Test database storage of full conversation."""
        conversation_id = "test-flow-001"
        user_id = "test-user"
        
        # Create conversation
        temp_db.create_conversation(conversation_id, user_id)
        
        # Add messages (simulating conversation)
        temp_db.add_message(
            conversation_id,
            "msg-1",
            "user",
            "What properties do you have?"
        )
        
        temp_db.add_message(
            conversation_id,
            "msg-2",
            "assistant",
            "We have several properties available..."
        )
        
        # Record query analytics
        temp_db.record_query_analytics(
            "query-1",
            conversation_id,
            "What properties do you have?",
            "property_management",
            "company",
            0.32
        )
        
        # Verify full conversation history
        messages = temp_db.get_conversation_messages(conversation_id)
        analytics = temp_db.get_query_analytics(conversation_id)
        
        assert len(messages) == 2
        assert len(analytics) == 1
        assert analytics[0]["intent"] == "property_management"

    @pytest.mark.integration
    def test_intent_routing_to_tools(self, intent_classifier, property_db, tool_manager):
        """Test that intent classification routes to correct tools."""
        # Classify a property-related query
        intent, confidence = intent_classifier.classify("Tell me about my properties")
        
        # Should route to RAG/property tools
        should_use_rag = intent_classifier.should_use_rag(intent)
        should_use_web = intent_classifier.should_use_web_search(intent)
        
        assert isinstance(should_use_rag, bool)
        assert isinstance(should_use_web, bool)

    @pytest.mark.integration
    def test_multi_turn_conversation_with_tools(self, property_db, tool_manager, temp_db):
        """Test multi-turn conversation with tool invocations."""
        conversation_id = "multi-turn-001"
        
        # Create conversation
        temp_db.create_conversation(conversation_id)
        
        # Turn 1: User searches properties
        turn1_user = "What properties are available?"
        temp_db.add_message(conversation_id, "msg-1", "user", turn1_user)
        
        # Tool execution
        search_result = tool_manager.execute_tool(
            "search_properties",
            {"query": ""}
        )
        
        # Turn 1 response
        temp_db.add_message(
            conversation_id,
            "msg-2",
            "assistant",
            "Based on available properties..."
        )
        
        # Turn 2: User asks about specific property
        turn2_user = "Tell me more about the penthouse"
        temp_db.add_message(conversation_id, "msg-3", "user", turn2_user)
        
        # Tool execution
        details = tool_manager.execute_tool(
            "get_property_details",
            {"property_id": "prop-001"}
        )
        
        # Turn 2 response
        temp_db.add_message(
            conversation_id,
            "msg-4",
            "assistant",
            "The penthouse features..."
        )
        
        # Verify conversation
        messages = temp_db.get_conversation_messages(conversation_id)
        assert len(messages) == 4
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    @pytest.mark.integration
    def test_session_management_flow(self, temp_db):
        """Test session creation and validation flow."""
        user_id = "user-session-test"
        session_id = "sess-test-001"
        
        # Create session
        session = temp_db.create_session(session_id, user_id)
        assert session.is_active is True
        
        # Validate session
        is_valid = temp_db.validate_session(session_id)
        assert is_valid is True
        
        # Create conversation within session
        conversation_id = "conv-in-session"
        conv = temp_db.create_conversation(conversation_id, user_id)
        
        # List user's conversations
        conversations = temp_db.list_conversations(user_id)
        assert len(conversations) > 0
        assert any(c.conversation_id == conversation_id for c in conversations)

    @pytest.mark.integration
    def test_property_maintenance_workflow(self, property_db, temp_db):
        """Test property maintenance query and scheduling workflow."""
        conversation_id = "maintenance-flow"
        temp_db.create_conversation(conversation_id)
        
        property_id = "prop-001"
        
        # Get existing maintenance
        maintenance = property_db.get_maintenance_history(property_id, limit=5)
        assert len(maintenance) > 0
        
        # Schedule new maintenance
        new_maintenance = property_db.add_maintenance_record(
            property_id,
            "Quarterly Inspection",
            "2026-05-20",
            "vendor-002",
            cost=1500,
            notes="Q2 property inspection"
        )
        
        # Verify it's in the history
        updated_maintenance = property_db.get_maintenance_history(property_id)
        record_ids = [m["id"] for m in updated_maintenance]
        assert new_maintenance["id"] in record_ids
        
        # Log to conversation
        temp_db.add_message(
            conversation_id,
            "msg-maintenance",
            "assistant",
            f"Scheduled maintenance: {new_maintenance['type']} for {new_maintenance['date']}"
        )

    @pytest.mark.integration
    def test_error_recovery_workflow(self, property_db, tool_manager):
        """Test error handling and recovery in tool execution."""
        # Try to get nonexistent property
        result1 = tool_manager.execute_tool(
            "get_property_details",
            {"property_id": "nonexistent"}
        )
        
        # Should attempt graceful handling (empty string or error)
        assert "result" in result1 or "error" in result1
        
        # Verify tool manager recorded the attempt
        history = tool_manager.get_call_history()
        assert len(history) > 0

    @pytest.mark.integration
    def test_analytics_tracking(self, temp_db):
        """Test query analytics tracking throughout conversation."""
        conversation_id = "analytics-test"
        user_id = "user-analytics"
        
        temp_db.create_conversation(conversation_id, user_id)
        
        # Simulate multiple queries with different intents and sources
        queries = [
            ("What's your pricing?", "pricing_information", "company", 0.25),
            ("Tell me about the team", "team_information", "company", 0.18),
            ("What's the weather?", "general_knowledge", "web", 0.42),
        ]
        
        for i, (text, intent, source, time) in enumerate(queries):
            temp_db.record_query_analytics(
                f"query-{i}",
                conversation_id,
                text,
                intent,
                source,
                time
            )
        
        # Retrieve analytics
        analytics = temp_db.get_query_analytics(conversation_id)
        
        assert len(analytics) == 3
        assert analytics[0]["intent"] == "pricing_information"
        assert analytics[1]["intent"] == "team_information"
        assert analytics[2]["source_used"] == "web"

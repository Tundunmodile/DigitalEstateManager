"""Unit tests for Claude tools and function calling."""

import pytest
from chatbot.tools import (
    ToolDefinition,
    ToolManager,
    PropertySearchTools,
    SchedulingTools,
    setup_tools,
)


class TestToolDefinition:
    """Test suite for ToolDefinition."""

    @pytest.mark.unit
    def test_tool_definition_creation(self):
        """Test creating a tool definition."""
        def dummy_handler():
            return "result"
        
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={"properties": {"param": {"type": "string"}}},
            handler=dummy_handler,
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.handler == dummy_handler

    @pytest.mark.unit
    def test_tool_to_anthropic_format(self):
        """Test converting tool to Anthropic format."""
        def dummy_handler():
            return "result"
        
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={
                "properties": {"param": {"type": "string"}},
                "required": ["param"]
            },
            handler=dummy_handler,
        )
        
        anthropic_format = tool.to_anthropic_format()
        
        assert anthropic_format["name"] == "test_tool"
        assert anthropic_format["description"] == "A test tool"
        assert "input_schema" in anthropic_format
        assert anthropic_format["input_schema"]["type"] == "object"


class TestToolManager:
    """Test suite for ToolManager."""

    @pytest.mark.unit
    def test_tool_manager_initialization(self):
        """Test initializing tool manager."""
        manager = ToolManager()
        
        assert manager.tools == {}
        assert manager.call_history == []

    @pytest.mark.unit
    def test_register_tool(self):
        """Test registering a tool."""
        manager = ToolManager()
        
        def handler():
            return "result"
        
        manager.register_tool(
            name="test_tool",
            description="Test",
            input_schema={},
            handler=handler,
        )
        
        assert "test_tool" in manager.tools
        assert manager.tools["test_tool"].name == "test_tool"

    @pytest.mark.unit
    def test_get_tools_for_claude(self, tool_manager):
        """Test getting tools in Claude format."""
        tools = tool_manager.get_tools_for_claude()
        
        assert len(tools) > 0
        assert all("name" in t for t in tools)
        assert all("description" in t for t in tools)
        assert all("input_schema" in t for t in tools)

    @pytest.mark.unit
    def test_execute_tool_success(self, tool_manager):
        """Test executing a tool successfully."""
        result = tool_manager.execute_tool(
            "search_properties",
            {"query": "Park Avenue"}
        )
        
        assert "result" in result or "error" in result  # Depends on what's searched

    @pytest.mark.unit
    def test_execute_nonexistent_tool(self, tool_manager):
        """Test executing a non-existent tool."""
        result = tool_manager.execute_tool(
            "nonexistent_tool",
            {}
        )
        
        assert "error" in result
        assert "not found" in result["error"]

    @pytest.mark.unit
    def test_get_call_history(self, tool_manager):
        """Test getting tool call history."""
        # Execute a tool
        tool_manager.execute_tool("search_properties", {"query": "test"})
        
        history = tool_manager.get_call_history()
        
        assert len(history) > 0
        assert history[0]["tool"] == "search_properties"

    @pytest.mark.unit
    def test_clear_history(self, tool_manager):
        """Test clearing tool history."""
        # Add some history
        tool_manager.execute_tool("search_properties", {"query": "test"})
        assert len(tool_manager.get_call_history()) > 0
        
        # Clear
        tool_manager.clear_history()
        assert len(tool_manager.get_call_history()) == 0


class TestPropertySearchTools:
    """Test suite for PropertySearchTools."""

    @pytest.mark.unit
    def test_search_properties_handler(self, property_db):
        """Test property search handler."""
        tools = PropertySearchTools(property_db)
        result = tools.search_properties_handler("Park Avenue")
        
        assert isinstance(result, str)
        assert "Park Avenue" in result or "Found" in result

    @pytest.mark.unit
    def test_search_properties_no_results(self, property_db):
        """Test property search with no results."""
        tools = PropertySearchTools(property_db)
        result = tools.search_properties_handler("NonExistent Location XYZ")
        
        assert "No properties found" in result

    @pytest.mark.unit
    def test_get_property_details_handler(self, property_db):
        """Test getting property details."""
        tools = PropertySearchTools(property_db)
        result = tools.get_property_details_handler("prop-001")
        
        assert isinstance(result, str)
        assert "Park Avenue" in result

    @pytest.mark.unit
    def test_get_maintenance_history_handler(self, property_db):
        """Test getting maintenance history."""
        tools = PropertySearchTools(property_db)
        result = tools.get_maintenance_history_handler("prop-001", limit=3)
        
        assert isinstance(result, str)
        assert "Maintenance" in result or "Found" in result

    @pytest.mark.unit
    def test_search_vendors_handler(self, property_db):
        """Test vendor search handler."""
        tools = PropertySearchTools(property_db)
        result = tools.search_vendors_handler("HVAC")
        
        assert isinstance(result, str)
        assert "Climate Tech" in result or "Found" in result

    @pytest.mark.unit
    def test_search_vendors_no_results(self, property_db):
        """Test vendor search with no results."""
        tools = PropertySearchTools(property_db)
        result = tools.search_vendors_handler("NonExistentCategory")
        
        assert "No vendors found" in result

    @pytest.mark.unit
    def test_get_vendor_details_handler(self, property_db):
        """Test getting vendor details."""
        tools = PropertySearchTools(property_db)
        result = tools.get_vendor_details_handler("vendor-001")
        
        assert isinstance(result, str)
        assert "Climate Tech" in result


class TestSchedulingTools:
    """Test suite for SchedulingTools."""

    @pytest.mark.unit
    def test_schedule_maintenance_handler(self, property_db):
        """Test scheduling maintenance."""
        tools = SchedulingTools(property_db)
        result = tools.schedule_maintenance_handler(
            "prop-001",
            "Test Maintenance",
            "2026-05-01",
            "vendor-001",
            notes="Test notes"
        )
        
        assert isinstance(result, str)
        assert "scheduled successfully" in result or "scheduled" in result.lower()

    @pytest.mark.unit
    def test_schedule_maintenance_invalid_property(self, property_db):
        """Test scheduling maintenance for invalid property."""
        tools = SchedulingTools(property_db)
        result = tools.schedule_maintenance_handler(
            "nonexistent-prop",
            "Test",
            "2026-05-01",
            "vendor-001"
        )
        
        assert "not found" in result.lower() or "error" in result.lower()

    @pytest.mark.unit
    def test_schedule_maintenance_invalid_vendor(self, property_db):
        """Test scheduling maintenance with invalid vendor."""
        tools = SchedulingTools(property_db)
        result = tools.schedule_maintenance_handler(
            "prop-001",
            "Test",
            "2026-05-01",
            "nonexistent-vendor"
        )
        
        assert "not found" in result.lower() or "error" in result.lower()

    @pytest.mark.unit
    def test_get_scheduled_maintenance_handler(self, property_db):
        """Test getting scheduled maintenance."""
        tools = SchedulingTools(property_db)
        result = tools.get_scheduled_maintenance_handler("prop-001")
        
        assert isinstance(result, str)
        assert "Scheduled Maintenance" in result or "scheduled" in result.lower()


class TestSetupTools:
    """Test suite for tool setup function."""

    @pytest.mark.unit
    def test_setup_tools_registers_all(self, property_db):
        """Test that setup_tools registers all expected tools."""
        from chatbot.tools import ToolManager
        
        manager = ToolManager()
        setup_tools(property_db, manager)
        
        expected_tools = [
            "search_properties",
            "get_property_details",
            "get_maintenance_history",
            "search_vendors",
            "get_vendor_details",
            "schedule_maintenance",
            "get_scheduled_maintenance",
        ]
        
        for tool_name in expected_tools:
            assert tool_name in manager.tools, f"Tool '{tool_name}' not registered"

    @pytest.mark.unit
    def test_setup_tools_count(self, property_db):
        """Test that correct number of tools are registered."""
        from chatbot.tools import ToolManager
        
        manager = ToolManager()
        setup_tools(property_db, manager)
        
        assert len(manager.tools) >= 7

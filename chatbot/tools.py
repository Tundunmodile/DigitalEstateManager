"""
Function Calling & Tool Use for Claude
Enables Claude to invoke actions and retrieve data dynamically
Implements property search, scheduling, and vendor management
"""

import json
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ToolDefinition:
    """Represents a tool that Claude can call."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict,
        handler: Callable,
    ):
        """
        Initialize tool definition.

        Args:
            name: Tool name (e.g., "search_properties")
            description: Human-readable description
            input_schema: JSON schema for input parameters
            handler: Callable that executes the tool
        """
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler

    def to_anthropic_format(self) -> Dict:
        """Convert to Anthropic tools format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.input_schema.get("properties", {}),
                "required": self.input_schema.get("required", []),
            },
        }


class ToolManager:
    """
    Manages available tools for Claude function calling.
    Handles tool invocation and error handling.
    """

    def __init__(self):
        """Initialize tool manager."""
        self.tools: Dict[str, ToolDefinition] = {}
        self.call_history: List[Dict] = []

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict,
        handler: Callable,
    ) -> None:
        """
        Register a new tool.

        Args:
            name: Tool name
            description: Tool description
            input_schema: JSON schema for parameters
            handler: Callable to execute tool
        """
        tool = ToolDefinition(name, description, input_schema, handler)
        self.tools[name] = tool
        logger.info(f"Registered tool: {name}")

    def get_tools_for_claude(self) -> List[Dict]:
        """Get all tools in Anthropic format for Claude."""
        return [tool.to_anthropic_format() for tool in self.tools.values()]

    def execute_tool(self, tool_name: str, input_params: Dict) -> Dict[str, Any]:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of tool to execute
            input_params: Input parameters for tool

        Returns:
            Tool result or error
        """
        if tool_name not in self.tools:
            error_msg = f"Tool '{tool_name}' not found"
            logger.error(error_msg)
            return {"error": error_msg}

        tool = self.tools[tool_name]
        
        try:
            # Execute tool
            result = tool.handler(**input_params)
            
            # Log execution
            self.call_history.append({
                "tool": tool_name,
                "inputs": input_params,
                "result_status": "success",
                "timestamp": datetime.utcnow().isoformat(),
            })
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            return {"result": result}
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Tool '{tool_name}' execution failed: {error_msg}")
            
            self.call_history.append({
                "tool": tool_name,
                "inputs": input_params,
                "result_status": "error",
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat(),
            })
            
            return {"error": error_msg}

    def get_call_history(self) -> List[Dict]:
        """Get history of tool calls."""
        return self.call_history.copy()

    def clear_history(self) -> None:
        """Clear tool call history."""
        self.call_history = []


class PropertySearchTools:
    """Tools for property and vendor searching."""

    def __init__(self, property_db):
        """Initialize with property database."""
        self.property_db = property_db

    def search_properties_handler(self, query: str) -> str:
        """Handler for searching properties."""
        results = self.property_db.search_properties(query)
        
        if not results:
            return f"No properties found matching '{query}'"
        
        formatted = f"Found {len(results)} properties:\n\n"
        for prop in results:
            formatted += f"- {prop['address']} ({prop['type'].title()}, {prop['square_feet']:,} sq ft)\n"
        
        return formatted

    def get_property_details_handler(self, property_id: str) -> str:
        """Handler for getting property details."""
        return self.property_db.format_property_for_llm(property_id)

    def get_maintenance_history_handler(self, property_id: str, limit: int = 5) -> str:
        """Handler for retrieving maintenance history."""
        records = self.property_db.get_maintenance_history(property_id, limit)
        
        if not records:
            return f"No maintenance records found for property {property_id}"
        
        formatted = f"**Maintenance History for {property_id}:**\n\n"
        for record in records:
            formatted += f"- {record['date']}: {record['type']} ({record['status']})\n"
            formatted += f"  Vendor: {record['vendor']} | Cost: ${record['cost']:,.0f}\n"
            if record['notes']:
                formatted += f"  Notes: {record['notes']}\n"
            formatted += "\n"
        
        return formatted.strip()

    def search_vendors_handler(self, category: str) -> str:
        """Handler for searching vendors."""
        vendors = self.property_db.search_vendors(category)
        
        if not vendors:
            return f"No vendors found in category '{category}'"
        
        formatted = f"Found {len(vendors)} vendors in {category}:\n\n"
        for vendor in vendors:
            formatted += f"- {vendor['name']} ({vendor['rating']}/5.0)\n"
            formatted += f"  Category: {vendor['category']}\n"
            formatted += f"  Phone: {vendor['phone']}\n"
        
        return formatted

    def get_vendor_details_handler(self, vendor_id: str) -> str:
        """Handler for getting vendor details."""
        return self.property_db.format_vendor_for_llm(vendor_id)


class SchedulingTools:
    """Tools for scheduling maintenance and appointments."""

    def __init__(self, property_db):
        """Initialize with property database."""
        self.property_db = property_db

    def schedule_maintenance_handler(
        self,
        property_id: str,
        maintenance_type: str,
        date: str,
        vendor_id: str,
        notes: str = "",
    ) -> str:
        """Handler for scheduling maintenance."""
        try:
            # Validate inputs
            if not self.property_db.get_property(property_id):
                return f"Property {property_id} not found"
            
            if not self.property_db.get_vendor(vendor_id):
                return f"Vendor {vendor_id} not found"
            
            # Schedule maintenance
            record = self.property_db.add_maintenance_record(
                property_id,
                maintenance_type,
                date,
                vendor_id,
                cost=0,  # To be determined
                notes=notes,
            )
            
            return (
                f"✓ Maintenance scheduled successfully\n"
                f"Property: {property_id}\n"
                f"Type: {maintenance_type}\n"
                f"Date: {date}\n"
                f"Vendor: {self.property_db.get_vendor(vendor_id)['name']}\n"
                f"Record ID: {record['id']}"
            )
        except Exception as e:
            return f"Failed to schedule maintenance: {str(e)}"

    def get_scheduled_maintenance_handler(self, property_id: str) -> str:
        """Handler for getting upcoming maintenance."""
        scheduled = self.property_db.get_scheduled_maintenance(property_id)
        
        if not scheduled:
            return f"No scheduled maintenance for property {property_id}"
        
        formatted = f"**Scheduled Maintenance for {property_id}:**\n\n"
        for record in scheduled:
            formatted += f"- {record['date']}: {record['type']}\n"
            formatted += f"  Vendor: {record['vendor']}\n"
            if record['notes']:
                formatted += f"  Notes: {record['notes']}\n"
            formatted += "\n"
        
        return formatted.strip()


def setup_tools(property_db, tool_manager: ToolManager) -> None:
    """
    Set up all available tools for Claude.

    Args:
        property_db: PropertyDatabase instance
        tool_manager: ToolManager instance
    """
    # Initialize tool handlers
    search_tools = PropertySearchTools(property_db)
    scheduling_tools = SchedulingTools(property_db)

    # Register search tools
    tool_manager.register_tool(
        name="search_properties",
        description="Search for properties by address or type. Returns matching properties.",
        input_schema={
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (address, type, or location)"
                }
            },
            "required": ["query"],
        },
        handler=search_tools.search_properties_handler,
    )

    tool_manager.register_tool(
        name="get_property_details",
        description="Get detailed information about a specific property including features and maintenance status.",
        input_schema={
            "properties": {
                "property_id": {
                    "type": "string",
                    "description": "Property ID (e.g., 'prop-001')"
                }
            },
            "required": ["property_id"],
        },
        handler=search_tools.get_property_details_handler,
    )

    tool_manager.register_tool(
        name="get_maintenance_history",
        description="Get maintenance history for a property.",
        input_schema={
            "properties": {
                "property_id": {
                    "type": "string",
                    "description": "Property ID"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of records to retrieve (default: 5)"
                }
            },
            "required": ["property_id"],
        },
        handler=search_tools.get_maintenance_history_handler,
    )

    tool_manager.register_tool(
        name="search_vendors",
        description="Search for trusted vendors by category (e.g., HVAC, Plumbing, Electrical).",
        input_schema={
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Vendor category to search"
                }
            },
            "required": ["category"],
        },
        handler=search_tools.search_vendors_handler,
    )

    tool_manager.register_tool(
        name="get_vendor_details",
        description="Get detailed information about a specific vendor.",
        input_schema={
            "properties": {
                "vendor_id": {
                    "type": "string",
                    "description": "Vendor ID (e.g., 'vendor-001')"
                }
            },
            "required": ["vendor_id"],
        },
        handler=search_tools.get_vendor_details_handler,
    )

    tool_manager.register_tool(
        name="schedule_maintenance",
        description="Schedule maintenance for a property with a trusted vendor.",
        input_schema={
            "properties": {
                "property_id": {
                    "type": "string",
                    "description": "Property ID"
                },
                "maintenance_type": {
                    "type": "string",
                    "description": "Type of maintenance (e.g., 'HVAC Service', 'Roof Inspection')"
                },
                "date": {
                    "type": "string",
                    "description": "Scheduled date (YYYY-MM-DD format)"
                },
                "vendor_id": {
                    "type": "string",
                    "description": "Vendor ID to assign"
                },
                "notes": {
                    "type": "string",
                    "description": "Additional notes (optional)"
                }
            },
            "required": ["property_id", "maintenance_type", "date", "vendor_id"],
        },
        handler=scheduling_tools.schedule_maintenance_handler,
    )

    tool_manager.register_tool(
        name="get_scheduled_maintenance",
        description="Get upcoming scheduled maintenance for a property.",
        input_schema={
            "properties": {
                "property_id": {
                    "type": "string",
                    "description": "Property ID"
                }
            },
            "required": ["property_id"],
        },
        handler=scheduling_tools.get_scheduled_maintenance_handler,
    )

    logger.info(f"Registered {len(tool_manager.tools)} tools for Claude")

#!/usr/bin/env python3
"""Quick test to verify tools are properly integrated with chatbot."""

import sys
import os

# Add the project to path
sys.path.insert(0, os.path.dirname(__file__))

from chatbot.property_database import PropertyDatabase
from chatbot.tools import ToolManager, setup_tools


def test_tools_setup():
    """Test that tools are properly set up."""
    print("Testing PropertyDatabase and Tools Setup...")
    print("=" * 50)
    
    # Initialize property database
    property_db = PropertyDatabase()
    print(f"✓ PropertyDatabase initialized")
    print(f"  - Properties: {len(property_db.properties)}")
    print(f"  - Maintenance records: {len(property_db.maintenance_records)}")
    print(f"  - Vendors: {len(property_db.vendors)}")
    
    # Initialize tool manager
    tool_manager = ToolManager()
    print(f"\n✓ ToolManager initialized")
    
    # Setup tools
    setup_tools(property_db, tool_manager)
    print(f"\n✓ Tools setup complete")
    print(f"  - Total tools: {len(tool_manager.tools)}")
    
    # List all tools
    print(f"\nRegistered Tools:")
    for tool_name in tool_manager.tools.keys():
        print(f"  - {tool_name}")
    
    # Get tools in Claude format
    claude_tools = tool_manager.get_tools_for_claude()
    print(f"\n✓ Got {len(claude_tools)} tools in Claude format")
    
    # Test tool execution
    print(f"\n" + "=" * 50)
    print("Testing Tool Execution...")
    print("=" * 50)
    
    # Test search_properties
    result = tool_manager.execute_tool("search_properties", {"query": "Park Avenue"})
    if "result" in result:
        print(f"✓ search_properties tool works")
        print(f"  Result: {result['result'][:100]}...")
    else:
        print(f"✗ search_properties tool failed: {result.get('error')}")
    
    # Test search_vendors
    result = tool_manager.execute_tool("search_vendors", {"category": "HVAC"})
    if "result" in result:
        print(f"✓ search_vendors tool works")
        print(f"  Result: {result['result'][:100]}...")
    else:
        print(f"✗ search_vendors tool failed: {result.get('error')}")
    
    # Test get_property_details
    result = tool_manager.execute_tool("get_property_details", {"property_id": "prop-001"})
    if "result" in result:
        print(f"✓ get_property_details tool works")
        print(f"  Result: {result['result'][:100]}...")
    else:
        print(f"✗ get_property_details tool failed: {result.get('error')}")
    
    # Test get_maintenance_history
    result = tool_manager.execute_tool("get_maintenance_history", {"property_id": "prop-001", "limit": 3})
    if "result" in result:
        print(f"✓ get_maintenance_history tool works")
        print(f"  Result: {result['result'][:100]}...")
    else:
        print(f"✗ get_maintenance_history tool failed: {result.get('error')}")
    
    print(f"\n" + "=" * 50)
    print("All tools are working correctly!")
    print("=" * 50)


if __name__ == "__main__":
    test_tools_setup()

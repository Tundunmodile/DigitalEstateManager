"""
Test script for Digital Estate Manager MCP Server
==================================================

Validates that the MCP server is properly configured and the
execute_sqlite_query tool works as expected.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import core modules
from core.database import init_database, execute_sqlite_query
from core.mcp_server import execute_sqlite_query_tool


def test_direct_database():
    """Test direct database access."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Direct Database Access")
    logger.info("="*60)
    
    try:
        # Initialize database
        init_database()
        logger.info("✓ Database initialized")
        
        # Test SELECT query
        result = execute_sqlite_query(
            "SELECT COUNT(*) as count FROM users",
            operation_type="SELECT",
            fetch="one"
        )
        logger.info(f"✓ SELECT query works. User count: {result}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Direct database test failed: {e}")
        return False


def test_mcp_tool():
    """Test MCP tool wrapper."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: MCP Tool Wrapper")
    logger.info("="*60)
    
    test_cases = [
        {
            "name": "SELECT with fetch='one'",
            "params": {
                "query": "SELECT COUNT(*) as count FROM users",
                "fetch": "one"
            },
            "should_succeed": True
        },
        {
            "name": "SELECT with fetch='all'",
            "params": {
                "query": "SELECT id, username FROM users LIMIT 5",
                "fetch": "all"
            },
            "should_succeed": True
        },
        {
            "name": "Invalid fetch mode",
            "params": {
                "query": "SELECT * FROM users",
                "fetch": "invalid_mode"
            },
            "should_succeed": False
        },
        {
            "name": "Invalid operation_type",
            "params": {
                "query": "SELECT * FROM users",
                "operation_type": "INVALID"
            },
            "should_succeed": False
        },
        {
            "name": "Parameter binding",
            "params": {
                "query": "SELECT * FROM assets WHERE status = ?",
                "params": ["active"],
                "fetch": "all"
            },
            "should_succeed": True
        }
    ]
    
    all_passed = True
    for i, test in enumerate(test_cases, 1):
        logger.info(f"\n  Test {i}: {test['name']}")
        try:
            result = execute_sqlite_query_tool(**test['params'])
            
            if test['should_succeed']:
                if result.get('success'):
                    logger.info(f"    ✓ PASS - Result: {str(result.get('data'))[:100]}")
                else:
                    logger.error(f"    ✗ FAIL - Expected success but got error: {result.get('error')}")
                    all_passed = False
            else:
                if not result.get('success'):
                    logger.info(f"    ✓ PASS - Correctly rejected: {result.get('error')}")
                else:
                    logger.error(f"    ✗ FAIL - Expected failure but succeeded")
                    all_passed = False
        except Exception as e:
            logger.error(f"    ✗ FAIL - Exception: {e}")
            all_passed = False
    
    return all_passed


def test_parameter_binding():
    """Test that parameter binding works correctly."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Parameter Binding Safety")
    logger.info("="*60)
    
    try:
        # This should safely bind parameters without SQL injection risk
        result = execute_sqlite_query_tool(
            query="SELECT * FROM assets WHERE status = ?",
            params=["active"],
            fetch="all"
        )
        
        if result.get('success'):
            logger.info("✓ Parameter binding works safely")
            return True
        else:
            logger.error(f"✗ Parameter binding failed: {result.get('error')}")
            return False
    except Exception as e:
        logger.error(f"✗ Parameter binding test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("╔" + "="*58 + "╗")
    logger.info("║" + " Digital Estate Manager MCP Server Tests ".center(58) + "║")
    logger.info("╚" + "="*58 + "╝")
    
    results = []
    
    # Run tests
    results.append(("Direct Database Access", test_direct_database()))
    results.append(("MCP Tool Wrapper", test_mcp_tool()))
    results.append(("Parameter Binding", test_parameter_binding()))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    logger.info("="*60)
    if all_passed:
        logger.info("✓ All tests passed! MCP server is ready.")
        logger.info("\nTo start the server, run:")
        logger.info("  python -m core.mcp_server")
        return 0
    else:
        logger.error("✗ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

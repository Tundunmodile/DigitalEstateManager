"""
MCP Server for Digital Estate Manager
======================================

Exposes database operations as Model Context Protocol tools.
Allows Claude and other MCP clients to query and manipulate the database safely.

Tool: execute_sqlite_query - Universal CRUD interface to the database
"""

import logging
from typing import Any, List, Optional, Union
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from data_layer.database import execute_sqlite_query

# Configure logging
logger = logging.getLogger(__name__)

# Initialize MCP Server
server = FastMCP("digital-estate-manager")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ExecuteQueryRequest(BaseModel):
    """Schema for execute_sqlite_query tool."""
    query: str = Field(
        description="SQL query with ? placeholders for parameters"
    )
    params: Optional[List[Any]] = Field(
        default=None,
        description="List of parameters to bind to the query (will be converted to tuple)"
    )
    operation_type: Optional[str] = Field(
        default="SELECT",
        description='Type of operation: "SELECT", "INSERT", "UPDATE", or "DELETE"'
    )
    fetch: Optional[str] = Field(
        default="all",
        description='Fetch mode: "all" (list of rows), "one" (single row), "count" (affected rows), or "lastid" (last inserted ID)'
    )


class QueryResult(BaseModel):
    """Schema for query results."""
    success: bool
    data: Any
    message: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# MCP TOOLS
# ============================================================================

@server.tool()
def execute_sqlite_query_tool(
    query: str,
    params: Optional[List[Any]] = None,
    operation_type: Optional[str] = "SELECT",
    fetch: Optional[str] = "all"
) -> dict:
    """
    Execute SQL queries against the Digital Estate Manager database.
    
    This tool provides safe, parameterized access to the SQLite database,
    preventing SQL injection through parameter binding.
    
    Args:
        query: SQL query with ? placeholders for parameters
        params: List of parameters to bind to query (bound in order)
        operation_type: Type of operation (SELECT, INSERT, UPDATE, DELETE) - used for logging
        fetch: How to return results:
            - "all": Return list of all rows as dictionaries
            - "one": Return single row as dictionary or null
            - "count": Return number of affected rows as integer
            - "lastid": Return the ID of the last inserted row
    
    Returns:
        Dictionary with success status, data/result, and optional error message
    
    Examples:
        SELECT all users:
        {
            "query": "SELECT * FROM users WHERE status = ?",
            "params": ["active"],
            "operation_type": "SELECT",
            "fetch": "all"
        }
        
        Insert a new user:
        {
            "query": "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            "params": ["john_doe", "hashed_pwd", "john@example.com"],
            "operation_type": "INSERT",
            "fetch": "lastid"
        }
        
        Update a user's email:
        {
            "query": "UPDATE users SET email = ? WHERE id = ?",
            "params": ["new@example.com", 1],
            "operation_type": "UPDATE",
            "fetch": "count"
        }
    """
    try:
        # Validate operation_type
        valid_operations = ["SELECT", "INSERT", "UPDATE", "DELETE"]
        if operation_type not in valid_operations:
            return {
                "success": False,
                "data": None,
                "error": f"Invalid operation_type '{operation_type}'. Must be one of: {', '.join(valid_operations)}"
            }
        
        # Validate fetch mode
        valid_fetch_modes = ["all", "one", "count", "lastid"]
        if fetch not in valid_fetch_modes:
            return {
                "success": False,
                "data": None,
                "error": f"Invalid fetch mode '{fetch}'. Must be one of: {', '.join(valid_fetch_modes)}"
            }
        
        # Convert params list to tuple for database function
        params_tuple = tuple(params) if params else ()
        
        # Call the underlying database function
        result = execute_sqlite_query(
            query=query,
            params=params_tuple,
            operation_type=operation_type,
            fetch=fetch
        )
        
        logger.info(f"Query executed successfully ({operation_type}): {query[:50]}...")
        
        return {
            "success": True,
            "data": result,
            "message": f"{operation_type} query executed successfully"
        }
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return {
            "success": False,
            "data": None,
            "error": f"Validation error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Database error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": f"Database error: {str(e)}"
        }


# ============================================================================
# SERVER LIFECYCLE
# ============================================================================

def run_mcp_server(host: str = "127.0.0.1", port: int = 3000):
    """
    Start the MCP server.
    
    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to listen on (default: 3000)
    """
    logger.info("=" * 60)
    logger.info("Starting Digital Estate Manager MCP Server")
    logger.info("=" * 60)
    logger.info(f"Binding to {host}:{port}")
    logger.info("Available tools:")
    logger.info("  - execute_sqlite_query: Execute SQL queries with parameter binding")
    logger.info("=" * 60)
    
    server.run()


if __name__ == "__main__":
    run_mcp_server()

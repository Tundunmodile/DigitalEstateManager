# MCP Server Setup Guide

## Overview

Your DigitalEstateManager project now has a fully functional **Model Context Protocol (MCP)** server that exposes database operations as tools. This allows Claude and other MCP clients to safely query and manipulate your SQLite database.

## Architecture

### Server Components

```
core/
├── mcp_server.py       ← MCP server (FastMCP) with tool definitions
└── database.py         ← Existing database layer (execute_sqlite_query function)
```

### Tool: `execute_sqlite_query`

The server exposes one primary tool with full CRUD capabilities:

**Function:** `execute_sqlite_query`

**Parameters:**
- `query` (string, required): SQL query with `?` placeholders for parameters
- `params` (array, optional): List of parameters to bind to the query
- `operation_type` (string, optional): Type of operation - "SELECT", "INSERT", "UPDATE", "DELETE" (for logging)
- `fetch` (string, optional): Return mode:
  - `"all"` - List of all rows as dictionaries (default)
  - `"one"` - Single row as dictionary or null
  - `"count"` - Number of affected rows as integer
  - `"lastid"` - ID of the last inserted row

**Response:**
```json
{
  "success": true,
  "data": <result>,
  "message": "<operation message>",
  "error": null
}
```

## Running the Server

### Method 1: Direct Python (Recommended)

```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
python run_mcp_server.py
```

The server will:
- Initialize the database
- Listen on stdio for MCP client connections
- Log activity to `mcp_server.log`

### Method 2: Using Python Module

```bash
source venv/bin/activate
python -m core.mcp_server
```

## Usage Examples

### Example 1: SELECT Query

```json
{
  "query": "SELECT * FROM assets WHERE status = ?",
  "params": ["active"],
  "operation_type": "SELECT",
  "fetch": "all"
}
```

Response:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "property_name": "Suburban Home",
      "address": "123 Oak Street, Springfield, IL 62701",
      "property_type": "house",
      "status": "active"
    }
  ],
  "message": "SELECT query executed successfully"
}
```

### Example 2: INSERT Query

```json
{
  "query": "INSERT INTO vendors (vendor_name, service_type, contact_name, phone) VALUES (?, ?, ?, ?)",
  "params": ["ABC Plumbing", "plumbing", "John Smith", "555-1234"],
  "operation_type": "INSERT",
  "fetch": "lastid"
}
```

Response:
```json
{
  "success": true,
  "data": 42,
  "message": "INSERT query executed successfully"
}
```

### Example 3: UPDATE Query

```json
{
  "query": "UPDATE vendors SET rating = ? WHERE id = ?",
  "params": [4.5, 42],
  "operation_type": "UPDATE",
  "fetch": "count"
}
```

Response:
```json
{
  "success": true,
  "data": 1,
  "message": "UPDATE query executed successfully"
}
```

## Integration with Claude

To use this MCP server with Claude (via VS Code Copilot or Claude desktop):

### VS Code Configuration

Add to your VS Code settings:

```json
{
  "github.copilot.chat.mcpServers": [
    {
      "name": "digital-estate-manager",
      "command": "python",
      "args": ["path/to/run_mcp_server.py"]
    }
  ]
}
```

### Claude Desktop Configuration

Add to `~/.claude-config/servers.json`:

```json
{
  "servers": {
    "digital-estate-manager": {
      "command": "python",
      "args": ["/path/to/DigitalEstateManager/run_mcp_server.py"]
    }
  }
}
```

## Testing

Run the included test suite:

```bash
source venv/bin/activate
python test_mcp_server.py
```

This validates:
- ✓ Database initialization
- ✓ Direct query execution
- ✓ MCP tool wrapper functionality
- ✓ Parameter binding safety (SQL injection prevention)
- ✓ Error handling and validation
- ✓ All fetch modes (all, one, count, lastid)

## Security Features

1. **Parameterized Queries**: All parameters are bound using SQLite's `?` placeholder system, preventing SQL injection
2. **Input Validation**: Tool validates operation types and fetch modes
3. **Error Handling**: Exceptions are caught and returned as MCP error responses
4. **Logging**: All operations are logged for auditing

## Database Schema

The server has access to the following tables:

- **users** - Application users
- **assets** - Properties/estates
- **customer_assets** - User-asset relationships
- **vendors** - Service providers
- **schedules** - Maintenance schedules and history
- **audit_logs** - Operation audit trail (if enabled)

For detailed schema, see [DATA_LAYER.md](DATA_LAYER.md)

## Troubleshooting

### Server Won't Start

Check that:
1. Python venv is activated: `source venv/bin/activate`
2. fastmcp is installed: `pip list | grep fastmcp`
3. Database path is writable: `ls -la data/`

### Tool Execution Fails

Common issues:
- **"Invalid fetch mode"**: Use one of: all, one, count, lastid
- **"Invalid operation_type"**: Use one of: SELECT, INSERT, UPDATE, DELETE
- **"no such column"**: Check your query against the schema

### MCP Client Connection Issues

1. Ensure server is running (should not exit immediately)
2. Check `mcp_server.log` for errors
3. Verify client can execute the server command: `python run_mcp_server.py`

## Next Steps

1. ✅ Run tests to verify setup: `python test_mcp_server.py`
2. ✅ Start the server: `python run_mcp_server.py`
3. ✅ Configure Claude to use the server (see Integration section)
4. → Add additional tools/resources as needed
5. → Implement authentication/authorization layer if required

## File Reference

- [core/mcp_server.py](core/mcp_server.py) - MCP server implementation
- [core/database.py](core/database.py) - Database layer
- [test_mcp_server.py](test_mcp_server.py) - Test suite
- [run_mcp_server.py](run_mcp_server.py) - Server launcher
- [DATA_LAYER.md](DATA_LAYER.md) - Database schema documentation

---

**Status**: ✅ MCP Server Implementation Complete - All tests passing

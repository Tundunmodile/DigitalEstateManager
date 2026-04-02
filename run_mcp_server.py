#!/usr/bin/env python
"""
MCP Server Launcher for Digital Estate Manager
===============================================

Starts the Model Context Protocol server that exposes database operations
as tools available to Claude and other MCP clients.

Usage:
    python run_mcp_server.py
    
Configuration:
    The server runs on stdio and is designed to be called by MCP clients
    via the model_settings.json configuration.

Environment:
    - Requires: fastmcp, sqlite3
    - Uses database at: data/estate_manager.db
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("mcp_server.log"),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

from core.mcp_server import server
from core.database import init_database


def main():
    """Initialize and run the MCP server."""
    try:
        logger.info("=" * 70)
        logger.info("Digital Estate Manager - MCP Server")
        logger.info("=" * 70)
        
        # Initialize database
        logger.info("Initializing database...")
        init_database()
        logger.info("✓ Database ready")
        
        # Start server
        logger.info("Starting MCP server on stdio...")
        logger.info("Available tools:")
        logger.info("  • execute_sqlite_query - Execute SQL queries with parameter binding")
        logger.info("Server is ready to accept connections.")
        
        server.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

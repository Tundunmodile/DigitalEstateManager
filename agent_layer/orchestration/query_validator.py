"""
Query Validator - Prevents unsafe database operations (DELETE, DROP, etc)
"""
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)


class QueryValidator:
    """Validates SQL queries for safety and compliance."""
    
    # Operations that are allowed
    ALLOWED_OPERATIONS = {"SELECT", "INSERT", "UPDATE"}
    
    # Operations that are blocked
    BLOCKED_OPERATIONS = {"DELETE", "DROP", "TRUNCATE", "CREATE", "ALTER", "PRAGMA"}
    
    # Tables that are protected (cannot be dropped/modified)
    PROTECTED_TABLES = {"users", "assets", "vendors", "schedules", "customer_assets", "event_audit"}
    
    @classmethod
    def validate(cls, query: str, params: Tuple = ()) -> Tuple[bool, str]:
        """
        Validate a SQL query for safety.
        
        Returns:
            (is_valid, error_message)
        """
        if not query:
            return False, "Query cannot be empty"
        
        query_upper = query.strip().upper()
        
        # Check for blocked operations
        for blocked_op in cls.BLOCKED_OPERATIONS:
            if blocked_op in query_upper:
                return False, f"Operation '{blocked_op}' is not allowed. Only SELECT, INSERT, and UPDATE operations are permitted."
        
        # Check for suspicious patterns
        if "--" in query or "/*" in query:
            return False, "SQL comments are not allowed"
        
        # Validate SELECT queries
        if query_upper.startswith("SELECT"):
            if "LIMIT" not in query_upper:
                logger.warning(f"SELECT query without LIMIT may return large result sets: {query[:50]}...")
        
        # Validate INSERT queries
        elif query_upper.startswith("INSERT"):
            # Check that required fields are present
            pass
        
        # Validate UPDATE queries
        elif query_upper.startswith("UPDATE"):
            # Check that WHERE clause is present
            if "WHERE" not in query_upper:
                return False, "UPDATE queries must include a WHERE clause to prevent updating all rows"
        
        return True, "Query is valid"
    
    @classmethod
    def get_operation_type(cls, query: str) -> str:
        """Determine the operation type (SELECT, INSERT, UPDATE, etc)."""
        query_upper = query.strip().upper()
        
        for op in cls.ALLOWED_OPERATIONS:
            if query_upper.startswith(op):
                return op
        
        for op in cls.BLOCKED_OPERATIONS:
            if query_upper.startswith(op):
                return op
        
        return "UNKNOWN"

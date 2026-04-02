"""
Main Orchestrator - Coordinates LLM SQL generation, validation, and execution
"""
import logging
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from data_layer.database import execute_sqlite_query, EventAuditDAO
from agent_layer.orchestration.llm_sql_generator import LLMSQLGenerator
from agent_layer.orchestration.query_validator import QueryValidator

logger = logging.getLogger(__name__)


class Orchestrator:
    """Main orchestrator for handling user input -> SQL -> execution -> response."""
    
    def __init__(self, enable_llm: bool = True):
        """
        Initialize the orchestrator.
        
        Args:
            enable_llm: If True, use LLM for SQL generation; if False, use templates
        """
        self.enable_llm = enable_llm
        self.llm_generator = LLMSQLGenerator() if enable_llm else None
        self.validator = QueryValidator()
        self.correlation_id = None
    
    def process_user_input(self, user_text: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Process raw user text input and return response.
        
        Args:
            user_text: Raw user input (e.g., "Show me all properties built after 2000")
            user_id: Optional user ID for context
        
        Returns:
            {
                "success": bool,
                "message": str,  # Human-readable response
                "sql": str,  # The SQL query that was executed
                "results": List[Dict],  # Query results
                "error": str,  # Error message if failed
                "correlation_id": str
            }
        """
        self.correlation_id = str(uuid.uuid4())
        
        logger.info(f"[{self.correlation_id}] Processing user input: {user_text[:50]}...")
        
        try:
            # Step 1: Generate SQL from natural language
            generation_result = self.llm_generator.generate(
                user_text,
                context={"user_id": user_id}
            ) if self.llm_generator else {
                "success": False,
                "error": "LLM not available"
            }
            
            if not generation_result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to generate query: {generation_result['error']}",
                    "sql": None,
                    "results": None,
                    "error": generation_result["error"],
                    "correlation_id": self.correlation_id
                }
            
            sql_query = generation_result["sql"]
            logger.info(f"[{self.correlation_id}] Generated SQL: {sql_query}")
            
            # Step 2: Validate the query
            is_valid, validation_error = self.validator.validate(sql_query)
            
            if not is_valid:
                logger.warning(f"[{self.correlation_id}] Query validation failed: {validation_error}")
                return {
                    "success": False,
                    "message": f"Query validation failed: {validation_error}",
                    "sql": sql_query,
                    "results": None,
                    "error": validation_error,
                    "correlation_id": self.correlation_id
                }
            
            # Step 3: Execute the query
            results = execute_sqlite_query(
                sql_query,
                operation_type=self.validator.get_operation_type(sql_query),
                fetch="all"
            )
            
            logger.info(f"[{self.correlation_id}] Query executed successfully. Results: {len(results) if isinstance(results, list) else 1} rows")
            
            # Step 4: Format response
            response_message = self._format_response(user_text, results, generation_result)
            
            # Log to audit trail
            self._log_audit(user_text, sql_query, results, user_id)
            
            return {
                "success": True,
                "message": response_message,
                "sql": sql_query,
                "results": results,
                "error": None,
                "correlation_id": self.correlation_id
            }
        
        except Exception as e:
            logger.error(f"[{self.correlation_id}] Orchestration error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Internal error: {str(e)}",
                "sql": None,
                "results": None,
                "error": str(e),
                "correlation_id": self.correlation_id
            }
    
    def _format_response(self, user_text: str, results: Any, generation_info: Dict) -> str:
        """Format the response message for the user."""
        if isinstance(results, list):
            if len(results) == 0:
                return "No results found."
            elif len(results) == 1:
                return f"Found 1 result: {results[0]}"
            else:
                return f"Found {len(results)} results."
        else:
            return f"Operation completed. Result: {results}"
    
    def _log_audit(self, user_text: str, sql_query: str, results: Any, user_id: Optional[int] = None):
        """Log the operation to the audit trail."""
        try:
            import json
            data = {
                "user_input": user_text,
                "sql_query": sql_query,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            EventAuditDAO.log_event(
                event_type="ORCHESTRATOR_EXECUTION",
                source="Orchestrator",
                data=json.dumps(data),
                correlation_id=self.correlation_id
            )
        except Exception as e:
            logger.warning(f"Failed to log to audit trail: {e}")

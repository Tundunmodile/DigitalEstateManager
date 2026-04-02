"""
LLM SQL Generator - Converts natural language to SQL using Claude
"""
import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class LLMSQLGenerator:
    """Generates SQL queries from natural language using Claude LLM."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize the SQL generator.
        
        Args:
            api_key: Anthropic API key (reads from ANTHROPIC_API_KEY env var if not provided)
            model: Claude model to use
        """
        self.model = model
        self.api_key = api_key
        
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key) if api_key else Anthropic()
        except ImportError:
            logger.error("anthropic package not installed. Install with: pip install anthropic")
            self.client = None
    
    def generate(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate SQL from natural language input.
        
        Args:
            user_input: Natural language query from user
            context: Optional context (e.g., schema info, recent tables)
        
        Returns:
            {
                "success": bool,
                "sql": str,  # Generated SQL query
                "explanation": str,  # Why this query was generated
                "confidence": float,  # 0-1 confidence score
                "error": str  # Error message if failed
            }
        """
        if not self.client:
            return {
                "success": False,
                "sql": None,
                "explanation": None,
                "confidence": 0,
                "error": "LLM client not initialized (anthropic package required)"
            }
        
        # Build the prompt with context and schema
        system_prompt = self._build_system_prompt(context)
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"User query: {user_input}\n\nGenerate SQL query. Respond with JSON: {{\"sql\": \"...\", \"explanation\": \"...\", \"confidence\": 0.9}}"
                    }
                ]
            )
            
            # Parse the response
            response_text = message.content[0].text
            
            # Try to extract JSON from response
            try:
                # Find JSON in response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    result = json.loads(json_str)
                    
                    return {
                        "success": True,
                        "sql": result.get("sql", ""),
                        "explanation": result.get("explanation", ""),
                        "confidence": result.get("confidence", 0.8),
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "sql": None,
                        "explanation": None,
                        "confidence": 0,
                        "error": f"Could not parse LLM response as JSON: {response_text[:200]}"
                    }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                return {
                    "success": False,
                    "sql": None,
                    "explanation": None,
                    "confidence": 0,
                    "error": f"Invalid JSON from LLM: {str(e)}"
                }
        
        except Exception as e:
            logger.error(f"LLM API error: {str(e)}")
            return {
                "success": False,
                "sql": None,
                "explanation": None,
                "confidence": 0,
                "error": f"LLM API error: {str(e)}"
            }
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build the system prompt with schema and instructions."""
        schema_info = """
You are an expert SQL query generator for a Digital Estate Manager database.

DATABASE SCHEMA:
- users: id, username, password, email, created_at, updated_at
- assets: id, property_name, address, property_type, square_footage, year_built, description, status, created_at, updated_at
- vendors: id, vendor_name, service_type, contact_name, phone, email, rating, notes, status, created_at, updated_at
- schedules: id, asset_id, vendor_id, service_type, scheduled_date, scheduled_time, completion_date, status, notes, cost, created_at, updated_at
- customer_assets: id, user_id, asset_id, relationship_type, assigned_date
- event_audit: id, event_type, source, data, correlation_id, timestamp

CONSTRAINTS:
- Only generate SELECT, INSERT, UPDATE queries (no DELETE, DROP, TRUNCATE)
- Always use parameterized queries with ? placeholders
- Include WHERE clauses in UPDATE queries
- For SELECT queries, consider adding LIMIT to prevent large result sets
- Use proper joins for multi-table queries

RESPONSE FORMAT:
Always respond with valid JSON containing:
{
    "sql": "SELECT * FROM users WHERE id = ?",
    "explanation": "Brief explanation of what this query does",
    "confidence": 0.95
}
"""
        return schema_info

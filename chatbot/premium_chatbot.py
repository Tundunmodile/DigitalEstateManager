"""
Premium Chatbot - Main Orchestrator
Handles query routing, context management, and response synthesis
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from .web_search_engine import WebSearchEngine

logger = logging.getLogger(__name__)


class PremiumChatbot:
    """
    Premium chatbot for Apex Residences.
    Uses Claude API for intelligent responses with conversation context.
    Maintains conversation history for coherent multi-turn interactions.
    """

    SYSTEM_PROMPT = """You are a sophisticated and refined concierge assistant for Apex Residences, 
a premier luxury home management service. Your communication style should be:

- Professional, elegant, and concise
- Informative without unnecessary elaboration
- Helpful and proactive in suggesting solutions
- Always maintaining the brand voice: luxury, discretion, excellence

You have access to company information below. When answering ANY questions:
- Ground all responses in the provided company knowledge
- Be precise with details about services, pricing, team members, and contact information
- Only reference information explicitly stated in the knowledge base
- For questions not covered by company knowledge, politely decline and suggest contacting the team
- Maintain discretion and professionalism at all times

Always maintain a conversational tone while preserving sophistication."""

    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        max_history: int = 5,
        knowledge_file: str = "company_info.md",
    ):
        """
        Initialize Premium Chatbot.

        Args:
            tavily_api_key: Tavily API key for web search
            max_history: Maximum conversation history exchanges to maintain
            knowledge_file: Path to markdown file with company information
        """
        # Initialize Anthropic client
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        from anthropic import Anthropic
        self.client = Anthropic(api_key=anthropic_key)
        self.model = "claude-3-haiku-20240307"
        
        # Load company knowledge base
        self.company_knowledge = self._load_knowledge_base(knowledge_file)
        
        # Build complete system prompt with company knowledge
        self.system_prompt = self._build_system_prompt()
        
        # Web search engine
        self.web_search_engine = WebSearchEngine(api_key=tavily_api_key)
        
        self.max_history = max_history
        self.conversation_history: List[Dict[str, str]] = []
        
        logger.info("Premium Chatbot initialized (Claude with company knowledge)")

    def _load_knowledge_base(self, knowledge_file: str) -> str:
        """
        Load company knowledge from markdown file.

        Args:
            knowledge_file: Path to knowledge file

        Returns:
            Content of knowledge file as string
        """
        # Try multiple paths
        for candidate in [
            knowledge_file,
            os.path.join(os.path.dirname(__file__), "..", knowledge_file),
            os.path.join(os.getcwd(), knowledge_file),
        ]:
            if os.path.exists(candidate):
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        content = f.read()
                    logger.info(f"Loaded knowledge base from {candidate}")
                    return content
                except Exception as e:
                    logger.error(f"Error reading {candidate}: {e}")
                    continue
        
        # If no file found, return empty string (graceful degradation)
        logger.warning(f"Knowledge file not found, proceeding without company knowledge")
        return ""

    def _build_system_prompt(self) -> str:
        """
        Build complete system prompt with company knowledge.

        Returns:
            Complete system prompt including company information
        """
        if self.company_knowledge:
            return f"""{self.SYSTEM_PROMPT}

---

## COMPANY KNOWLEDGE BASE

{self.company_knowledge}

---

Use the above information to ground all responses. Only reference services, pricing, and team details that are explicitly mentioned above. For any questions not covered by this knowledge base, politely indicate that you don't have that information and suggest contacting the Apex Residences team."""
        else:
            return self.SYSTEM_PROMPT



    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        Call the Anthropic Claude LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Response text from Claude
        """
        # Extract system prompt if present
        system_prompt = None
        api_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                api_messages.append(msg)
        
        # Default system prompt if not provided
        if not system_prompt:
            system_prompt = self.system_prompt
        
        # Call Anthropic API directly
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=system_prompt,
            messages=api_messages,
        )
        
        return response.content[0].text

    def get_response(self, user_input: str, include_source: bool = True) -> Dict[str, str]:
        """
        Get chatbot response to user input.

        Args:
            user_input: User's question or message
            include_source: Whether to include source attribution in response

        Returns:
            Dictionary with 'response', 'source', 'timestamp'
        """
        logger.info(f"Processing user input: {user_input[:100]}...")

        # Build messages with conversation history (using company knowledge-grounded prompt)
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": user_input})

        # Get response from Claude
        response_text = self._call_llm(messages)

        # Update conversation history
        self._update_history(user_input, response_text)

        return {
            "response": response_text,
            "source": "company",
            "timestamp": datetime.now().isoformat(),
        }

    def _update_history(self, user_input: str, assistant_response: str) -> None:
        """
        Update conversation history, maintaining max_history limit.

        Args:
            user_input: User message
            assistant_response: Assistant response
        """
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": assistant_response})

        # Keep only last max_history exchanges
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-(self.max_history * 2):]

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_history(self) -> List[Dict[str, str]]:
        """Get current conversation history."""
        return self.conversation_history.copy()

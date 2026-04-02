"""
Premium Chatbot - Main Orchestrator
Handles query routing, context management, and response synthesis
"""

import os
import logging
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from .web_search_engine import WebSearchEngine
from .rag_engine import RAGEngine

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
        api_timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize Premium Chatbot.

        Args:
            tavily_api_key: Tavily API key for web search
            max_history: Maximum conversation history exchanges to maintain
            knowledge_file: Path to markdown file with company information
            api_timeout: Timeout for API calls in seconds
            max_retries: Maximum number of retries for API calls
        """
        # Initialize Anthropic client
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        from anthropic import Anthropic
        self.client = Anthropic(api_key=anthropic_key)
        self.model = "claude-3-haiku-20240307"
        self.api_timeout = api_timeout
        self.max_retries = max_retries
        
        # Initialize RAG Engine for company knowledge retrieval
        try:
            self.rag_engine = RAGEngine(knowledge_file=knowledge_file)
            logger.info("RAG Engine initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize RAG Engine: {e}. Proceeding with static knowledge.")
            self.rag_engine = None
        
        # Load company knowledge base (as fallback)
        self.company_knowledge = self._load_knowledge_base(knowledge_file)
        
        # Build complete system prompt with company knowledge
        self.system_prompt = self._build_system_prompt()
        
        # Web search engine
        self.web_search_engine = WebSearchEngine(api_key=tavily_api_key)
        
        self.max_history = max_history
        self.conversation_history: List[Dict[str, str]] = []
        
        logger.info("Premium Chatbot initialized (Claude with RAG and web search)")

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
        Call the Anthropic Claude LLM with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Response text from Claude

        Raises:
            RuntimeError: If max retries exceeded
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
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    system=system_prompt,
                    messages=api_messages,
                    timeout=self.api_timeout,
                )
                return response.content[0].text
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"API call attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API call failed after {self.max_retries} attempts")
        
        raise RuntimeError(f"Failed to get LLM response after {self.max_retries} attempts: {last_error}")

    def get_response(self, user_input: str, include_source: bool = True) -> Dict[str, str]:
        """
        Get chatbot response to user input with RAG and web search integration.

        Args:
            user_input: User's question or message
            include_source: Whether to include source attribution in response

        Returns:
            Dictionary with 'response', 'source', 'timestamp', 'context_used'
        """
        logger.info(f"Processing user input: {user_input[:100]}...")
        
        # Determine query type and retrieve appropriate context
        is_company_query = self._is_company_question(user_input)
        rag_context = ""
        web_context = ""
        source = "company" if is_company_query else "web"
        
        try:
            if is_company_query:
                # Retrieve from company knowledge base
                rag_context, _ = self._retrieve_rag_context(user_input, top_k=3)
                logger.debug(f"Retrieved RAG context for query")
            else:
                # Retrieve from web search
                web_context = self._retrieve_web_search_context(user_input, max_results=5)
                logger.debug(f"Retrieved web search context for query")
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")

        # Build messages with conversation history and retrieved context
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self._get_history_with_relevance_filtering(user_input, max_tokens=2000))
        
        # Build enhanced user message with context
        enhanced_query = self._build_context_prompt(rag_context, web_context, user_input)
        messages.append({"role": "user", "content": enhanced_query})

        try:
            # Get response from Claude
            response_text = self._call_llm(messages)
        except RuntimeError as e:
            logger.error(f"Failed to get response: {e}")
            response_text = "I apologize, but I'm currently unable to process your request. Please try again shortly."
            source = "error"

        # Update conversation history with original input (not enhanced)
        self._update_history(user_input, response_text)

        return {
            "response": response_text,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "context_used": {
                "company_knowledge": bool(rag_context),
                "web_search": bool(web_context),
            }
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

    def _get_context_limited_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history with token-aware context management.
        Prioritizes recent exchanges while managing total context window.

        Returns:
            List of message dicts suitable for API call
        """
        # Use recent exchanges (typically 3-5 exchanges for Haiku model)
        max_exchanges = min(self.max_history, 3)  # More conservative for context window
        
        if len(self.conversation_history) > max_exchanges * 2:
            return self.conversation_history[-(max_exchanges * 2):]
        
        return self.conversation_history.copy()

    def _estimate_token_count(self, text: str) -> int:
        """
        Rough estimate of token count (assuming ~4 chars per token).
        Used for context window management.

        Args:
            text: Text to count tokens for

        Returns:
            Approximate token count
        """
        return len(text) // 4

    def _get_history_with_relevance_filtering(self, current_query: str, max_tokens: int = 2000) -> List[Dict[str, str]]:
        """
        Get conversation history with intelligent relevance filtering.
        Keeps most relevant recent messages while staying within token limit.

        Args:
            current_query: Current user query
            max_tokens: Maximum tokens available for history

        Returns:
            Filtered conversation history
        """
        if not self.conversation_history:
            return []
        
        # Always keep the most recent exchange
        filtered_history = []
        token_count = 0
        
        # Iterate backwards through history (most recent first)
        for i in range(len(self.conversation_history) - 1, -1, -1):
            message = self.conversation_history[i]
            message_tokens = self._estimate_token_count(message["content"])
            
            # Stop if we exceed token budget
            if token_count + message_tokens > max_tokens:
                break
            
            filtered_history.insert(0, message)
            token_count += message_tokens
        
        logger.debug(f"Using {len(filtered_history)} messages ({token_count} tokens) from history")
        return filtered_history

    def _retrieve_rag_context(self, query: str, top_k: int = 3) -> Tuple[str, List[float]]:
        """
        Retrieve context from company knowledge base via RAG.

        Args:
            query: User query
            top_k: Number of results to retrieve

        Returns:
            Tuple of (formatted_context, confidence_scores)
        """
        if not self.rag_engine:
            return "", []
        
        try:
            return self.rag_engine.format_context(query, top_k=top_k), [1.0] * top_k
        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            return "", []

    def _retrieve_web_search_context(self, query: str, max_results: int = 5) -> str:
        """
        Retrieve context from web search.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            Formatted web search results
        """
        if not self.web_search_engine.is_available():
            return ""
        
        try:
            return self.web_search_engine.search_and_format(query, max_results=max_results)
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return ""

    def _build_context_prompt(self, rag_context: str, web_context: str, user_query: str) -> str:
        """
        Build enhanced user message with retrieved context.

        Args:
            rag_context: Company knowledge context
            web_context: Web search context
            user_query: Original user query

        Returns:
            Enhanced query string with context
        """
        context_parts = []
        
        if rag_context:
            context_parts.append(f"**Relevant Company Information:**\n{rag_context}")
        
        if web_context:
            context_parts.append(f"**External Information:**\n{web_context}")
        
        if context_parts:
            return f"{user_query}\n\n---\n\nContext to consider:\n\n" + "\n\n---\n\n".join(context_parts)
        
        return user_query

    def _is_company_question(self, query: str) -> bool:
        """
        Determine if query is about company (use RAG) vs general knowledge (use web).

        Args:
            query: User question

        Returns:
            True if query is company-specific
        """
        company_keywords = [
            "service", "pricing", "price", "cost", "team", "staff", "contact", "hours",
            "availability", "fee", "package", "tier", "premium", "platinum", "elite",
            "offer", "specialize", "background", "experience", "expertise", "how much",
            "how many", "what service", "what do you", "do you offer", "do you provide",
            "event planning", "property management", "concierge", "vendor", "faq",
            "about", "philosophy", "mission", "values", "who is", "who are", "apex",
            "residences", "vetting", "maintenance", "security", "vendor"
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in company_keywords)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_history(self) -> List[Dict[str, str]]:
        """Get current conversation history."""
        return self.conversation_history.copy()

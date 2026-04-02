"""
Web Search Engine using Tavily API and MCP Protocol
Provides internet search capabilities for the chatbot
"""

import os
import logging
import time
from typing import List, Dict, Optional
import asyncio

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

logger = logging.getLogger(__name__)


class WebSearchEngine:
    """
    Web search engine using Tavily API.
    Handles internet searches for non-company queries with retry logic and error handling.
    """

    def __init__(self, api_key: Optional[str] = None, max_retries: int = 3, timeout: int = 30):
        """
        Initialize Web Search Engine.

        Args:
            api_key: Tavily API key (uses TAVILY_API_KEY env var if not provided)
            max_retries: Maximum number of retries for API calls
            timeout: Timeout for API calls in seconds
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.max_retries = max_retries
        self.timeout = timeout
        
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not set. Web search will be unavailable.")
            self.client = None
        else:
            if TavilyClient is None:
                logger.error("tavily-python package not installed. Install with: pip install tavily-python")
                self.client = None
            else:
                self.client = TavilyClient(api_key=self.api_key)
                logger.info("Tavily client initialized")

    def is_available(self) -> bool:
        """Check if web search is available."""
        return self.client is not None

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Execute web search using Tavily API with retry logic.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, url, snippet
        """
        if not self.client:
            logger.error("Web search not available - Tavily client not initialized")
            return []

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.search(
                    query=query,
                    max_results=max_results,
                    include_answer=True,
                    include_raw_content=False,
                )

                results = []
                if response.get("answer"):
                    results.append({
                        "type": "answer",
                        "content": response["answer"],
                        "source": "Web Search Summary",
                    })

                for result in response.get("results", [])[:max_results]:
                    results.append({
                        "type": "result",
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("content", ""),
                        "source": result.get("source", ""),
                    })

                logger.debug(f"Web search returned {len(results)} results for: {query}")
                return results

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Web search attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Web search failed after {self.max_retries} attempts: {e}")
        
        return []

    def format_results(self, results: List[Dict]) -> str:
        """
        Format search results for LLM consumption.

        Args:
            results: List of search result dictionaries

        Returns:
            Formatted string of search results
        """
        if not results:
            return ""

        formatted = "**Web Search Results:**\n\n"

        # Add answer first if available
        answer_results = [r for r in results if r.get("type") == "answer"]
        if answer_results:
            formatted += f"**Summary:** {answer_results[0]['content']}\n\n"

        # Add individual results
        result_results = [r for r in results if r.get("type") == "result"]
        for i, result in enumerate(result_results, 1):
            formatted += f"{i}. **{result['title']}** ({result['source']})\n"
            formatted += f"   {result['snippet']}\n"
            if result['url']:
                formatted += f"   [Read More]({result['url']})\n"
            formatted += "\n"

        return formatted.strip()

    def search_and_format(self, query: str, max_results: int = 5) -> str:
        """
        Execute search and return formatted results.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            Formatted search results as string
        """
        results = self.search(query, max_results)
        return self.format_results(results)

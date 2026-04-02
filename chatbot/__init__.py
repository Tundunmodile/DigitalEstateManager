"""
Apex Residences Chatbot Package
Premium home management chatbot with Claude + web search
"""

__version__ = "1.0.0"
__author__ = "Apex Residences"

from .web_search_engine import WebSearchEngine
from .premium_chatbot import PremiumChatbot

__all__ = ["WebSearchEngine", "PremiumChatbot"]

"""
Intent Classification Engine
Uses zero-shot classification for query routing without fine-tuning
Replaces keyword-based routing with ML-based classification
"""

import logging
from typing import Tuple, Dict, List
from functools import lru_cache

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    ML-based intent classifier using zero-shot classification.
    Routes queries to appropriate data sources without training.
    """

    # Define intent categories
    INTENTS = [
        "company_services",      # Company services, offerings
        "pricing_information",   # Pricing tiers, costs
        "team_information",      # Team members, staff
        "contact_information",   # How to contact, support
        "general_knowledge",     # General web search
        "technical_support",     # Technical issues
        "scheduling",            # Appointments, scheduling
        "property_management",   # Property-specific queries
    ]

    def __init__(self, model_name: str = "facebook/bart-large-mnli"):
        """
        Initialize intent classifier.

        Args:
            model_name: HuggingFace model for zero-shot classification
        """
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("transformers library not available. Intent classification disabled.")
            self.classifier = None
            return

        try:
            self.classifier = pipeline(
                "zero-shot-classification",
                model=model_name,
                device=-1,  # Use CPU (set to 0 for GPU)
            )
            logger.info(f"Intent classifier initialized with {model_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize intent classifier: {e}")
            self.classifier = None

    @lru_cache(maxsize=1000)
    def classify(self, query: str, threshold: float = 0.3) -> Tuple[str, float]:
        """
        Classify query intent using zero-shot classification.

        Args:
            query: User query
            threshold: Confidence threshold for classification

        Returns:
            Tuple of (intent, confidence_score)
        """
        if not self.classifier:
            logger.warning("Classifier not available, returning default intent")
            return "general_knowledge", 0.5

        try:
            result = self.classifier(
                query,
                self.INTENTS,
                multi_class=False,
            )
            
            intent = result["labels"][0]
            confidence = result["scores"][0]
            
            logger.debug(f"Classified '{query[:50]}...' as {intent} ({confidence:.2%})")
            return intent, confidence
        
        except Exception as e:
            logger.error(f"Error classifying query: {e}")
            return "general_knowledge", 0.5

    def should_use_rag(self, intent: str) -> bool:
        """
        Determine if company knowledge (RAG) should be used based on intent.

        Args:
            intent: Classified intent

        Returns:
            True if RAG should be used
        """
        rag_intents = {
            "company_services",
            "pricing_information",
            "team_information",
            "contact_information",
            "property_management",
        }
        return intent in rag_intents

    def should_use_web_search(self, intent: str) -> bool:
        """
        Determine if web search should be used based on intent.

        Args:
            intent: Classified intent

        Returns:
            True if web search should be used
        """
        web_intents = {
            "general_knowledge",
            "technical_support",
        }
        return intent in web_intents

    def get_all_intents(self) -> List[str]:
        """Get list of all supported intents."""
        return self.INTENTS.copy()

    def explain_classification(self, query: str) -> Dict:
        """
        Get detailed classification breakdown with scores for all intents.

        Args:
            query: User query

        Returns:
            Dictionary with all intents and their scores
        """
        if not self.classifier:
            return {"error": "Classifier not available"}

        try:
            result = self.classifier(
                query,
                self.INTENTS,
                multi_class=False,
            )
            
            explanation = {
                "query": query,
                "top_intent": result["labels"][0],
                "top_confidence": result["scores"][0],
                "all_intents": dict(zip(result["labels"], result["scores"])),
            }
            return explanation
        
        except Exception as e:
            logger.error(f"Error explaining classification: {e}")
            return {"error": str(e)}


# Fallback keyword-based classifier if transformers unavailable
class KeywordIntentClassifier:
    """
    Fallback keyword-based intent classifier.
    Used when transformers library is not available.
    """

    INTENT_KEYWORDS = {
        "company_services": [
            "service", "offering", "provide", "concierge", "property management",
            "event planning", "vendor", "what do you offer", "what services"
        ],
        "pricing_information": [
            "price", "cost", "pricing", "fee", "tier", "premium", "platinum",
            "elite", "how much", "pay", "rate", "subscription"
        ],
        "team_information": [
            "team", "staff", "member", "who is", "who are", "background",
            "experience", "expertise", "victoria", "marcus", "amelia", "james"
        ],
        "contact_information": [
            "contact", "email", "phone", "reach", "support", "hotline",
            "address", "hours", "availability", "help"
        ],
        "property_management": [
            "property", "maintenance", "monitoring", "repair", "inspection",
            "scheduling", "appointment"
        ],
        "scheduling": [
            "schedule", "appointment", "book", "booking", "when", "time",
            "available", "reserve", "calendar"
        ],
        "technical_support": [
            "bug", "error", "issue", "problem", "not working", "broken",
            "fix", "technical", "help", "support"
        ],
    }

    def classify(self, query: str, threshold: float = 0.0) -> Tuple[str, float]:
        """
        Classify query using keyword matching.

        Args:
            query: User query
            threshold: Unused (for API compatibility)

        Returns:
            Tuple of (intent, confidence_score)
        """
        query_lower = query.lower()
        scores = {}
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            scores[intent] = score
        
        if not any(scores.values()):
            return "general_knowledge", 0.5
        
        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] / 3.0, 1.0)  # Normalize to 0-1
        
        logger.debug(f"Classified '{query[:50]}...' as {best_intent} ({confidence:.2%})")
        return best_intent, confidence

    def should_use_rag(self, intent: str) -> bool:
        """Determine if RAG should be used."""
        return intent in {
            "company_services",
            "pricing_information",
            "team_information",
            "contact_information",
            "property_management",
        }

    def should_use_web_search(self, intent: str) -> bool:
        """Determine if web search should be used."""
        return intent in {
            "general_knowledge",
            "technical_support",
        }

    def get_all_intents(self) -> List[str]:
        """Get list of all supported intents."""
        return list(self.INTENT_KEYWORDS.keys())

    def explain_classification(self, query: str) -> Dict:
        """Get detailed classification breakdown."""
        query_lower = query.lower()
        scores = {}
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            scores[intent] = score / len(keywords) if keywords else 0
        
        top_intent, confidence = self.classify(query)
        return {
            "query": query,
            "top_intent": top_intent,
            "top_confidence": confidence,
            "all_intents": scores,
        }


def get_intent_classifier() -> IntentClassifier:
    """
    Factory function to get the best available intent classifier.
    Returns ML-based if transformers available, falls back to keyword-based.
    """
    if TRANSFORMERS_AVAILABLE:
        try:
            return IntentClassifier()
        except Exception as e:
            logger.warning(f"Failed to initialize ML classifier: {e}. Using keyword fallback.")
            return KeywordIntentClassifier()
    else:
        logger.info("transformers not available. Using keyword-based intent classifier.")
        return KeywordIntentClassifier()

"""Unit tests for intent classifier."""

import pytest
from chatbot.intent_classifier import (
    IntentClassifier,
    KeywordIntentClassifier,
    get_intent_classifier,
)


class TestIntentClassifier:
    """Test suite for intent classification."""

    @pytest.mark.unit
    def test_get_intent_classifier(self):
        """Test getting an intent classifier."""
        classifier = get_intent_classifier()
        assert classifier is not None

    @pytest.mark.unit
    def test_classifier_has_intents(self, intent_classifier):
        """Test that classifier has defined intents."""
        intents = intent_classifier.get_all_intents()
        assert len(intents) > 0
        assert "company_services" in intents or "general_knowledge" in intents

    @pytest.mark.unit
    def test_classify_returns_intent_and_confidence(self, intent_classifier):
        """Test that classify returns intent and confidence."""
        intent, confidence = intent_classifier.classify("What is your pricing?")
        
        assert isinstance(intent, str)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1

    @pytest.mark.unit
    def test_classify_company_query(self, intent_classifier):
        """Test classifying a company-related query."""
        intent, confidence = intent_classifier.classify("What are your pricing tiers?")
        
        # Should be a company intent (pricing_information or general knowledge, depending on classifier)
        assert intent is not None
        assert confidence > 0

    @pytest.mark.unit
    def test_classify_general_query(self, intent_classifier):
        """Test classifying a general knowledge query."""
        intent, confidence = intent_classifier.classify("Who is the president of the USA?")
        
        assert intent is not None
        assert confidence > 0

    @pytest.mark.unit
    def test_classify_team_query(self, intent_classifier):
        """Test classifying a team-related query."""
        intent, confidence = intent_classifier.classify("Tell me about Victoria Chen")
        
        assert intent is not None

    @pytest.mark.unit
    def test_should_use_rag_method(self, intent_classifier):
        """Test should_use_rag method."""
        result = intent_classifier.should_use_rag("company_services")
        assert isinstance(result, bool)

    @pytest.mark.unit
    def test_should_use_web_search_method(self, intent_classifier):
        """Test should_use_web_search method."""
        result = intent_classifier.should_use_web_search("general_knowledge")
        assert isinstance(result, bool)

    @pytest.mark.unit
    def test_explain_classification(self, intent_classifier):
        """Test getting detailed classification explanation."""
        explanation = intent_classifier.explain_classification("What's your pricing?")
        
        assert "query" in explanation
        assert "top_intent" in explanation
        assert "all_intents" in explanation or "error" in explanation

    @pytest.mark.unit
    def test_caching(self, intent_classifier):
        """Test that classification results are cached."""
        query = "Test query for caching"
        
        # First call
        intent1, conf1 = intent_classifier.classify(query)
        
        # Second call (should use cache)
        intent2, conf2 = intent_classifier.classify(query)
        
        assert intent1 == intent2
        assert conf1 == conf2


class TestKeywordIntentClassifier:
    """Test suite for keyword-based intent classifier."""

    @pytest.mark.unit
    def test_keyword_classifier_initialization(self):
        """Test keyword classifier initialization."""
        classifier = KeywordIntentClassifier()
        assert classifier is not None
        assert len(classifier.INTENT_KEYWORDS) > 0

    @pytest.mark.unit
    def test_keyword_classify_pricing(self):
        """Test classifying pricing query with keywords."""
        classifier = KeywordIntentClassifier()
        intent, confidence = classifier.classify("How much does it cost?")
        
        assert intent == "pricing_information"

    @pytest.mark.unit
    def test_keyword_classify_team(self):
        """Test classifying team query with keywords."""
        classifier = KeywordIntentClassifier()
        intent, confidence = classifier.classify("Who is Victoria Chen?")
        
        assert intent == "team_information"

    @pytest.mark.unit
    def test_keyword_classify_contact(self):
        """Test classifying contact query with keywords."""
        classifier = KeywordIntentClassifier()
        intent, confidence = classifier.classify("How do I contact support?")
        
        assert intent == "contact_information"

    @pytest.mark.unit
    def test_keyword_classify_general_fallback(self):
        """Test fallback to general knowledge for unmatched queries."""
        classifier = KeywordIntentClassifier()
        intent, confidence = classifier.classify("xyz abc def 123")
        
        assert intent == "general_knowledge"

    @pytest.mark.unit
    def test_keyword_classifier_rag_routing(self):
        """Test RAG routing with keyword classifier."""
        classifier = KeywordIntentClassifier()
        
        company_intent = "company_services"
        general_intent = "general_knowledge"
        
        assert classifier.should_use_rag(company_intent) is True
        assert classifier.should_use_rag(general_intent) is False

    @pytest.mark.unit
    def test_keyword_classifier_web_routing(self):
        """Test web search routing with keyword classifier."""
        classifier = KeywordIntentClassifier()
        
        general_intent = "general_knowledge"
        company_intent = "company_services"
        
        assert classifier.should_use_web_search(general_intent) is True
        assert classifier.should_use_web_search(company_intent) is False

    @pytest.mark.unit
    def test_keyword_explain_classification(self):
        """Test explaining classification with keywords."""
        classifier = KeywordIntentClassifier()
        explanation = classifier.explain_classification("What's your pricing?")
        
        assert "query" in explanation
        assert "top_intent" in explanation
        assert "all_intents" in explanation

    @pytest.mark.unit
    def test_keyword_get_all_intents(self):
        """Test getting all intents from keyword classifier."""
        classifier = KeywordIntentClassifier()
        intents = classifier.get_all_intents()
        
        assert len(intents) > 0
        assert "pricing_information" in intents
        assert "team_information" in intents

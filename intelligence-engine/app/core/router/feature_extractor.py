"""
Query Feature Extractor for Smart Router
Extracts linguistic and semantic features from queries
"""
import re
import string
from typing import Dict, List, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class QueryFeatures:
    """Features extracted from a query"""
    length: int
    word_count: int
    char_count: int
    has_greeting: bool
    has_question: bool
    has_technical_terms: bool
    has_numbers: bool
    has_punctuation: bool
    sentiment_indicators: List[str]
    language: str
    complexity_score: float
    urgency_indicators: bool
    entities: List[str]

class QueryFeatureExtractor:
    """
    Extract features from queries for ML classification
    """

    # Keywords for classification
    GREETINGS = {
        "it": ["ciao", "salve", "buongiorno", "buonasera", "buonanotte", "hey", "hei"],
        "en": ["hello", "hi", "hey", "good morning", "good evening"]
    }

    TECHNICAL_TERMS = [
        "workflow", "processo", "elaborazione", "node", "nodo", "webhook",
        "api", "database", "query", "sql", "json", "error", "errore",
        "execution", "esecuzione", "trigger", "pipeline", "batch"
    ]

    URGENCY_WORDS = [
        "urgente", "urgent", "subito", "immediately", "ora", "now",
        "critico", "critical", "problema", "problem", "errore", "error",
        "fallito", "failed", "bloccato", "blocked", "stuck"
    ]

    POSITIVE_SENTIMENT = [
        "buono", "good", "ottimo", "excellent", "perfetto", "perfect",
        "bene", "well", "successo", "success", "completato", "completed"
    ]

    NEGATIVE_SENTIMENT = [
        "male", "bad", "problema", "problem", "errore", "error",
        "fallito", "failed", "lento", "slow", "bug", "crash"
    ]

    def __init__(self):
        """Initialize feature extractor"""
        logger.info("QueryFeatureExtractor initialized")

    def extract(self, query: str) -> Dict[str, Any]:
        """
        Extract all features from query

        Args:
            query: Input query string

        Returns:
            Dictionary of features
        """
        if not query:
            return self._empty_features()

        query_lower = query.lower().strip()

        features = {
            # Basic metrics
            "length": len(query),
            "word_count": len(query.split()),
            "char_count": len(query.replace(" ", "")),

            # Boolean features
            "has_greeting": self._has_greeting(query_lower),
            "has_question": self._has_question(query),
            "has_technical_terms": self._has_technical_terms(query_lower),
            "has_numbers": bool(re.search(r'\d', query)),
            "has_punctuation": self._has_punctuation(query),

            # Advanced features
            "sentiment_indicators": self._get_sentiment_indicators(query_lower),
            "language": self._detect_language(query_lower),
            "complexity_score": self._calculate_complexity(query),
            "urgency_indicators": self._has_urgency(query_lower),
            "entities": self._extract_entities(query),

            # Special patterns
            "has_messaggio": "messaggio" in query_lower,
            "has_workflow_ref": any(w in query_lower for w in ["workflow", "processo", "elaborazione"]),
            "is_batch_request": self._is_batch_request(query_lower),
            "is_status_check": self._is_status_check(query_lower),
        }

        return features

    def _empty_features(self) -> Dict[str, Any]:
        """Return empty feature set"""
        return {
            "length": 0,
            "word_count": 0,
            "char_count": 0,
            "has_greeting": False,
            "has_question": False,
            "has_technical_terms": False,
            "has_numbers": False,
            "has_punctuation": False,
            "sentiment_indicators": [],
            "language": "unknown",
            "complexity_score": 0.0,
            "urgency_indicators": False,
            "entities": [],
            "has_messaggio": False,
            "has_workflow_ref": False,
            "is_batch_request": False,
            "is_status_check": False,
        }

    def _has_greeting(self, query: str) -> bool:
        """Check if query contains greeting"""
        for lang_greetings in self.GREETINGS.values():
            if any(greeting in query for greeting in lang_greetings):
                return True
        return False

    def _has_question(self, query: str) -> bool:
        """Check if query is a question"""
        question_marks = ["?", "come", "cosa", "quando", "dove", "perché", "quale",
                         "how", "what", "when", "where", "why", "which"]
        return any(marker in query.lower() for marker in question_marks)

    def _has_technical_terms(self, query: str) -> bool:
        """Check for technical terminology"""
        return any(term in query for term in self.TECHNICAL_TERMS)

    def _has_punctuation(self, query: str) -> bool:
        """Check for punctuation"""
        return bool(set(query) & set(string.punctuation))

    def _get_sentiment_indicators(self, query: str) -> List[str]:
        """Extract sentiment indicators"""
        indicators = []

        for word in self.POSITIVE_SENTIMENT:
            if word in query:
                indicators.append(f"positive:{word}")

        for word in self.NEGATIVE_SENTIMENT:
            if word in query:
                indicators.append(f"negative:{word}")

        return indicators

    def _detect_language(self, query: str) -> str:
        """Simple language detection"""
        # Count Italian vs English common words
        italian_words = ["il", "la", "di", "che", "è", "e", "un", "per", "con", "del"]
        english_words = ["the", "is", "of", "and", "to", "in", "that", "it", "for", "on"]

        it_count = sum(1 for word in italian_words if word in query.split())
        en_count = sum(1 for word in english_words if word in query.split())

        if it_count > en_count:
            return "it"
        elif en_count > it_count:
            return "en"
        else:
            # Default to Italian for this project
            return "it"

    def _calculate_complexity(self, query: str) -> float:
        """
        Calculate query complexity score (0-1)
        Higher score = more complex query
        """
        factors = []

        # Length factor
        word_count = len(query.split())
        factors.append(min(word_count / 50, 1.0))  # Normalize to 50 words max

        # Technical terms factor
        tech_count = sum(1 for term in self.TECHNICAL_TERMS if term in query.lower())
        factors.append(min(tech_count / 5, 1.0))  # Normalize to 5 terms max

        # Sentence complexity (commas, semicolons)
        punctuation_count = query.count(',') + query.count(';') + query.count(':')
        factors.append(min(punctuation_count / 3, 1.0))

        # Numbers and data references
        number_count = len(re.findall(r'\d+', query))
        factors.append(min(number_count / 5, 1.0))

        # Calculate weighted average
        if factors:
            return sum(factors) / len(factors)
        return 0.0

    def _has_urgency(self, query: str) -> bool:
        """Check for urgency indicators"""
        return any(word in query for word in self.URGENCY_WORDS)

    def _extract_entities(self, query: str) -> List[str]:
        """
        Extract potential entities (simplified NER)
        Looking for: workflow names, dates, numbers, etc.
        """
        entities = []

        # Extract quoted strings
        quoted = re.findall(r'"([^"]*)"', query)
        entities.extend([f"quoted:{q}" for q in quoted])

        # Extract dates (simple patterns)
        dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', query)
        entities.extend([f"date:{d}" for d in dates])

        # Extract times
        times = re.findall(r'\d{1,2}:\d{2}', query)
        entities.extend([f"time:{t}" for t in times])

        # Extract capitalized words (potential workflow/process names)
        words = query.split()
        for word in words:
            if word and word[0].isupper() and len(word) > 1:
                if word not in ["Il", "La", "Un", "The", "A", "An"]:
                    entities.append(f"name:{word}")

        # Extract numbers
        numbers = re.findall(r'\d+', query)
        entities.extend([f"number:{n}" for n in numbers if len(n) > 2])

        return entities

    def _is_batch_request(self, query: str) -> bool:
        """Check if request is for batch/multiple items"""
        batch_keywords = [
            "tutti", "tutte", "all", "lista", "list", "elenca",
            "mostra tutto", "show all", "completo", "complete",
            "ogni", "each", "batch", "multiplo", "multiple"
        ]
        return any(keyword in query for keyword in batch_keywords)

    def _is_status_check(self, query: str) -> bool:
        """Check if query is asking for status"""
        status_keywords = [
            "stato", "status", "come va", "how is", "tutto ok",
            "funziona", "working", "operativo", "operational",
            "health", "salute", "check", "controllo"
        ]
        return any(keyword in query for keyword in status_keywords)

    def get_feature_vector(self, query: str) -> List[float]:
        """
        Get numerical feature vector for ML models

        Args:
            query: Input query

        Returns:
            List of numerical features
        """
        features = self.extract(query)

        # Convert to numerical vector
        vector = [
            features["length"],
            features["word_count"],
            features["char_count"],
            float(features["has_greeting"]),
            float(features["has_question"]),
            float(features["has_technical_terms"]),
            float(features["has_numbers"]),
            float(features["has_punctuation"]),
            len(features["sentiment_indicators"]),
            1.0 if features["language"] == "it" else 0.0,
            features["complexity_score"],
            float(features["urgency_indicators"]),
            len(features["entities"]),
            float(features["has_messaggio"]),
            float(features["has_workflow_ref"]),
            float(features["is_batch_request"]),
            float(features["is_status_check"]),
        ]

        return vector
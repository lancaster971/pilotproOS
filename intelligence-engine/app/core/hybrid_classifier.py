"""
Rule-First Hybrid Classifier
=============================
Deterministic pattern matching with LLM fallback for ambiguous cases
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class IntentCategory(Enum):
    """Intent categories for classification"""
    BUSINESS_DATA = "BUSINESS_DATA"
    HELP = "HELP"
    GREETING = "GREETING"
    TECHNOLOGY = "TECHNOLOGY"
    UNKNOWN = "UNKNOWN"
    CLARIFICATION = "CLARIFICATION"
    MULTI_INTENT = "MULTI_INTENT"


class HybridClassifier:
    """
    Rule-First Hybrid Classifier
    Uses deterministic pattern matching, falls back to LLM only when needed
    """

    def __init__(self, config_path: str = "app/config/milhena_config.json"):
        """
        Initialize classifier with configuration

        Args:
            config_path: Path to configuration JSON file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Load patterns and compile them
        self.patterns = {}
        self._compile_patterns()

        # Statistics
        self.stats = {
            "total_classified": 0,
            "rule_matches": 0,
            "llm_fallbacks": 0,
            "ambiguous_cases": 0,
            "multi_intent_detected": 0
        }

        # Confidence threshold
        self.confidence_threshold = self.config["classifier"].get("confidence_threshold", 0.7)

    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # Return minimal default config
            return {
                "classifier": {
                    "categories": ["BUSINESS_DATA", "HELP", "GREETING", "TECHNOLOGY", "UNKNOWN"],
                    "patterns": {},
                    "confidence_threshold": 0.7
                }
            }

    def _compile_patterns(self):
        """Compile regex patterns for each category"""
        patterns_config = self.config["classifier"].get("patterns", {})

        for category, pattern_list in patterns_config.items():
            self.patterns[category] = []
            for pattern_str in pattern_list:
                try:
                    compiled = re.compile(pattern_str, re.IGNORECASE)
                    self.patterns[category].append(compiled)
                except re.error as e:
                    logger.error(f"Invalid regex pattern for {category}: {pattern_str} - {e}")

    def classify(self, text: str, use_llm_fallback: bool = True) -> Tuple[IntentCategory, float, str]:
        """
        Classify user intent using rules first, then LLM if needed

        Args:
            text: User input text to classify
            use_llm_fallback: Whether to use LLM for ambiguous cases

        Returns:
            Tuple of (category, confidence, reasoning)
        """
        if not text:
            return IntentCategory.UNKNOWN, 1.0, "Empty input"

        # Sanitize input
        text = self._sanitize_input(text)

        # Step 1: Try deterministic pattern matching
        matches = self._match_patterns(text)

        if matches:
            # Single clear match
            if len(matches) == 1:
                category = matches[0]
                self.stats["rule_matches"] += 1
                self.stats["total_classified"] += 1
                return IntentCategory[category], 1.0, f"Pattern match: {category}"

            # Multiple matches - check for multi-intent
            elif len(matches) > 1:
                self.stats["multi_intent_detected"] += 1
                self.stats["total_classified"] += 1

                # Check if one category dominates
                dominant = self._find_dominant_category(text, matches)
                if dominant:
                    return IntentCategory[dominant], 0.8, f"Dominant pattern: {dominant} among {matches}"
                else:
                    return IntentCategory.MULTI_INTENT, 0.9, f"Multiple intents detected: {matches}"

        # Step 2: Check for specific keywords (lower confidence)
        keyword_match = self._keyword_analysis(text)
        if keyword_match:
            self.stats["rule_matches"] += 1
            self.stats["total_classified"] += 1
            return IntentCategory[keyword_match], 0.6, f"Keyword match: {keyword_match}"

        # Step 3: LLM fallback for ambiguous cases
        if use_llm_fallback:
            self.stats["llm_fallbacks"] += 1
            self.stats["total_classified"] += 1
            return self._llm_classify(text)

        # No match found
        self.stats["total_classified"] += 1
        return IntentCategory.UNKNOWN, 0.5, "No pattern or keyword match"

    def _sanitize_input(self, text: str) -> str:
        """
        Sanitize user input to prevent injection attacks

        Args:
            text: Raw user input

        Returns:
            Sanitized text
        """
        # Convert to string if needed
        if not isinstance(text, str):
            text = str(text)

        # Limit length
        max_length = self.config.get("security", {}).get("max_input_length", 500)
        if len(text) > max_length:
            text = text[:max_length]

        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '{', '}', '[', ']', '|', ';', '`']
        for char in dangerous_chars:
            text = text.replace(char, '')

        # Remove common injection patterns
        blocked_patterns = self.config.get("security", {}).get("blocked_patterns", [])
        for pattern in blocked_patterns:
            if pattern.lower() in text.lower():
                logger.warning(f"Blocked pattern detected: {pattern}")
                text = text.replace(pattern, '', re.IGNORECASE)

        return text.strip()

    def _match_patterns(self, text: str) -> List[str]:
        """
        Match text against all compiled patterns

        Args:
            text: Text to match

        Returns:
            List of matching categories
        """
        matches = []

        for category, pattern_list in self.patterns.items():
            for pattern in pattern_list:
                if pattern.search(text):
                    matches.append(category)
                    break  # One match per category is enough

        return matches

    def _keyword_analysis(self, text: str) -> Optional[str]:
        """
        Simple keyword-based classification for common cases

        Args:
            text: Text to analyze

        Returns:
            Matched category or None
        """
        text_lower = text.lower()

        # Business data keywords
        business_keywords = ['users', 'data', 'metrics', 'count', 'total', 'statistics', 'report']
        if any(keyword in text_lower for keyword in business_keywords):
            return "BUSINESS_DATA"

        # Help keywords
        help_keywords = ['help', 'how', 'what', 'explain', 'guide', 'tutorial']
        if any(keyword in text_lower for keyword in help_keywords):
            return "HELP"

        # Technology keywords
        tech_keywords = ['docker', 'postgres', 'redis', 'api', 'system', 'infrastructure']
        if any(keyword in text_lower for keyword in tech_keywords):
            return "TECHNOLOGY"

        return None

    def _find_dominant_category(self, text: str, matches: List[str]) -> Optional[str]:
        """
        Find dominant category when multiple matches exist

        Args:
            text: Original text
            matches: List of matching categories

        Returns:
            Dominant category or None
        """
        # Priority order (business queries usually more important)
        priority = {
            "BUSINESS_DATA": 4,
            "TECHNOLOGY": 3,
            "HELP": 2,
            "GREETING": 1
        }

        # Find highest priority match
        best_match = None
        best_priority = 0

        for match in matches:
            if priority.get(match, 0) > best_priority:
                best_priority = priority.get(match, 0)
                best_match = match

        return best_match

    def _llm_classify(self, text: str) -> Tuple[IntentCategory, float, str]:
        """
        LLM-based classification fallback

        Args:
            text: Text to classify

        Returns:
            Classification result
        """
        # This would call the actual LLM
        # For now, return UNKNOWN as placeholder
        logger.info(f"LLM fallback would be called for: {text[:50]}...")
        return IntentCategory.UNKNOWN, 0.3, "LLM fallback not implemented"

    def get_stats(self) -> Dict:
        """Get classification statistics"""
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            "total_classified": 0,
            "rule_matches": 0,
            "llm_fallbacks": 0,
            "ambiguous_cases": 0,
            "multi_intent_detected": 0
        }

    def explain_classification(self, text: str) -> Dict:
        """
        Explain how text would be classified

        Args:
            text: Text to analyze

        Returns:
            Detailed explanation dictionary
        """
        explanation = {
            "input": text,
            "sanitized": self._sanitize_input(text),
            "pattern_matches": self._match_patterns(self._sanitize_input(text)),
            "keyword_match": self._keyword_analysis(self._sanitize_input(text)),
            "classification": None,
            "confidence": None,
            "reasoning": None
        }

        # Perform classification
        category, confidence, reasoning = self.classify(text, use_llm_fallback=False)

        explanation["classification"] = category.value
        explanation["confidence"] = confidence
        explanation["reasoning"] = reasoning

        return explanation


# Singleton instance
_instance = None

def get_classifier(config_path: str = None) -> HybridClassifier:
    """Get or create singleton instance of classifier"""
    global _instance
    if _instance is None:
        _instance = HybridClassifier(config_path or "app/config/milhena_config.json")
    return _instance


# Convenience function
def classify_intent(text: str, use_llm: bool = True) -> Tuple[str, float]:
    """Convenience function to classify text"""
    category, confidence, _ = get_classifier().classify(text, use_llm)
    return category.value, confidence
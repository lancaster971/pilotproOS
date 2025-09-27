"""
HybridMaskingLibrary - Deterministic Tech Term Masking
========================================================
Pure Python library for masking technical terms with business language
NO LLM calls - 100% deterministic and predictable
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class HybridMaskingLibrary:
    """
    Deterministic masking library - NOT an agent
    Replaces technical terms with business-friendly language
    """

    def __init__(self, config_path: str = "app/config/milhena_config.json"):
        """
        Initialize masking library with configuration

        Args:
            config_path: Path to configuration JSON file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Load masking dictionaries
        self.tech_to_business = self.config["masking"]["tech_to_business"]
        self.pattern_rules = self.config["masking"]["pattern_rules"]
        self.forbidden_keywords = set(self.config["masking"]["forbidden_keywords"])

        # Compile regex patterns for efficiency
        self.compiled_patterns = []
        for rule in self.pattern_rules:
            self.compiled_patterns.append({
                "pattern": re.compile(rule["pattern"], re.IGNORECASE),
                "replacement": rule["replacement"]
            })

        # Statistics
        self.stats = {
            "total_masked": 0,
            "terms_replaced": 0,
            "patterns_matched": 0,
            "leaks_detected": 0
        }

    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # Return minimal default config
            return {
                "masking": {
                    "tech_to_business": {
                        "postgres": "Database",
                        "redis": "Cache System",
                        "docker": "Container Platform",
                        "n8n": "Automation Platform",
                        "workflow": "Business Process"
                    },
                    "pattern_rules": [],
                    "forbidden_keywords": []
                }
            }

    def mask(self, text: str, context: Optional[str] = None) -> str:
        """
        Main masking function - deterministically replaces tech terms

        Args:
            text: Text to mask
            context: Optional context for contextual replacements

        Returns:
            Masked text with all tech terms replaced
        """
        if not text:
            return text

        original_text = text
        masked_text = text

        # Step 1: Apply pattern-based rules first (more specific)
        for rule in self.compiled_patterns:
            if rule["pattern"].search(masked_text):
                masked_text = rule["pattern"].sub(rule["replacement"], masked_text)
                self.stats["patterns_matched"] += 1

        # Handle underscore-separated terms first
        if '_' in masked_text:
            parts = masked_text.split('_')
            masked_parts = []
            for part in parts:
                # Check if this part is a tech term
                part_lower = part.lower()
                if part_lower in [t.lower() for t in self.tech_to_business.keys()]:
                    # Find the actual key (case-insensitive)
                    for key in self.tech_to_business.keys():
                        if key.lower() == part_lower:
                            replacement = self.tech_to_business[key]
                            # Preserve case
                            if part.isupper():
                                replacement = replacement.upper()
                            elif part and part[0].isupper():
                                replacement = replacement[0].upper() + replacement[1:] if len(replacement) > 1 else replacement.upper()
                            masked_parts.append(replacement)
                            self.stats["terms_replaced"] += 1
                            break
                else:
                    masked_parts.append(part)
            masked_text = '_'.join(masked_parts)

        # Step 2: Apply static dictionary replacements
        # Sort by length (longer terms first) to avoid partial replacements
        sorted_terms = sorted(self.tech_to_business.keys(), key=len, reverse=True)

        # Track replacements to avoid double-substitution
        replacements_made = []

        for tech_term in sorted_terms:
            business_term = self.tech_to_business[tech_term]

            # Case-insensitive replacement with word boundaries
            pattern = re.compile(r'\b' + re.escape(tech_term) + r'\b', re.IGNORECASE)

            # Find all matches with their positions
            matches = list(pattern.finditer(masked_text))

            if matches:
                # Process matches from end to start to maintain positions
                for match in reversed(matches):
                    start, end = match.span()

                    # Check if this position was already replaced
                    already_replaced = False
                    for prev_start, prev_end in replacements_made:
                        if (start >= prev_start and start < prev_end) or \
                           (end > prev_start and end <= prev_end):
                            already_replaced = True
                            break

                    if not already_replaced:
                        # Preserve original case
                        original = match.group()
                        if original.isupper():
                            replacement = business_term.upper()
                        elif original[0].isupper():
                            replacement = business_term[0].upper() + business_term[1:]
                        else:
                            replacement = business_term

                        # Replace this specific match
                        masked_text = masked_text[:start] + replacement + masked_text[end:]

                        # Track the replacement
                        new_end = start + len(replacement)
                        replacements_made.append((start, new_end))
                        self.stats["terms_replaced"] += 1

        # Step 3: Validate no tech terms leaked
        leaked_terms = self._detect_leaks(masked_text)
        if leaked_terms:
            logger.warning(f"Tech terms leaked: {leaked_terms}")
            # Fallback: replace with generic term
            for term in leaked_terms:
                pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
                masked_text = pattern.sub("[system component]", masked_text)
            self.stats["leaks_detected"] += len(leaked_terms)

        # Update statistics
        if masked_text != original_text:
            self.stats["total_masked"] += 1

        return masked_text

    def _detect_leaks(self, text: str) -> List[str]:
        """
        Detect any technical terms that weren't masked

        Args:
            text: Text to check for leaks

        Returns:
            List of technical terms found in text
        """
        leaked = []
        text_lower = text.lower()

        for keyword in self.forbidden_keywords:
            if keyword.lower() in text_lower:
                # Check if it's a whole word, not part of another word
                pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                if pattern.search(text):
                    leaked.append(keyword)

        return leaked

    def validate_masking(self, text: str) -> Tuple[bool, List[str]]:
        """
        Validate that text contains no technical terms

        Args:
            text: Text to validate

        Returns:
            Tuple of (is_clean, list_of_leaked_terms)
        """
        leaked_terms = self._detect_leaks(text)
        return len(leaked_terms) == 0, leaked_terms

    def get_stats(self) -> Dict:
        """Get masking statistics"""
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            "total_masked": 0,
            "terms_replaced": 0,
            "patterns_matched": 0,
            "leaks_detected": 0
        }

    def bulk_mask(self, texts: List[str]) -> List[str]:
        """
        Mask multiple texts efficiently

        Args:
            texts: List of texts to mask

        Returns:
            List of masked texts
        """
        return [self.mask(text) for text in texts]

    def explain_masking(self, text: str) -> Dict:
        """
        Explain what would be masked in the text

        Args:
            text: Text to analyze

        Returns:
            Dictionary with explanation of masking
        """
        explanation = {
            "original": text,
            "masked": self.mask(text),
            "replacements": [],
            "patterns_matched": [],
            "leaked_terms": []
        }

        # Find dictionary replacements
        for tech_term, business_term in self.tech_to_business.items():
            pattern = re.compile(r'\b' + re.escape(tech_term) + r'\b', re.IGNORECASE)
            if pattern.search(text):
                explanation["replacements"].append({
                    "from": tech_term,
                    "to": business_term,
                    "count": len(pattern.findall(text))
                })

        # Find pattern matches
        for rule in self.compiled_patterns:
            if rule["pattern"].search(text):
                explanation["patterns_matched"].append({
                    "pattern": rule["pattern"].pattern,
                    "replacement": rule["replacement"]
                })

        # Check for leaks
        masked = self.mask(text)
        explanation["leaked_terms"] = self._detect_leaks(masked)

        return explanation


# Singleton instance for easy import
_instance = None

def get_masking_library(config_path: str = None) -> HybridMaskingLibrary:
    """Get or create singleton instance of masking library"""
    global _instance
    if _instance is None:
        _instance = HybridMaskingLibrary(config_path or "app/config/milhena_config.json")
    return _instance


# Convenience function for direct masking
def mask_text(text: str, context: Optional[str] = None) -> str:
    """Convenience function to mask text using default instance"""
    return get_masking_library().mask(text, context)
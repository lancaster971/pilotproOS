"""
Hybrid Validator
================
Deterministic validation rules with LLM fallback for edge cases
Validates data responses before sending to users
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Validation result types"""
    VALID = "VALID"
    INVALID = "INVALID"
    SUSPICIOUS = "SUSPICIOUS"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass
class ValidationReport:
    """Detailed validation report"""
    result: ValidationResult
    confidence: float
    issues: List[str]
    suggestions: List[str]
    cleaned_text: Optional[str] = None


class HybridValidator:
    """
    Hybrid Validator
    Uses deterministic rules for validation, falls back to LLM for edge cases
    """

    def __init__(self, config_path: str = "app/config/milhena_config.json"):
        """
        Initialize validator with configuration

        Args:
            config_path: Path to configuration JSON file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Load validation rules
        self.forbidden_terms = self.config["validator"]["forbidden_terms"]
        self.validation_rules = self.config["validator"]["validation_rules"]
        self.numerical_bounds = self.config["validator"]["numerical_bounds"]

        # Statistics
        self.stats = {
            "total_validated": 0,
            "valid_responses": 0,
            "invalid_responses": 0,
            "suspicious_responses": 0,
            "llm_reviews": 0
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
                "validator": {
                    "forbidden_terms": {
                        "speculation": ["might be", "could be", "probably"],
                        "fake_data": ["John Doe", "Jane Smith", "Lorem ipsum"],
                        "technical": ["postgres", "docker", "redis"],
                        "unverified": ["I think", "I believe", "It seems"]
                    },
                    "validation_rules": {
                        "check_consistency": True,
                        "check_bounds": True,
                        "check_speculation": True,
                        "check_fake_data": True,
                        "check_tech_terms": True
                    },
                    "numerical_bounds": {
                        "users_min": 0,
                        "users_max": 1000000,
                        "percentage_min": 0,
                        "percentage_max": 100
                    }
                }
            }

    def validate(self, text: str, context: Optional[Dict] = None, use_llm_fallback: bool = True) -> ValidationReport:
        """
        Validate text response using rules first, then LLM if needed

        Args:
            text: Text to validate
            context: Optional context (query type, expected format, etc.)
            use_llm_fallback: Whether to use LLM for ambiguous cases

        Returns:
            ValidationReport with detailed results
        """
        if not text or not text.strip():
            return ValidationReport(
                result=ValidationResult.INVALID,
                confidence=1.0,
                issues=["Empty response"],
                suggestions=["Provide a meaningful response"]
            )

        issues = []
        suggestions = []
        cleaned_text = text

        # Step 1: Check for speculation
        if self.validation_rules.get("check_speculation", True):
            speculation_issues = self._check_speculation(text)
            if speculation_issues:
                issues.extend(speculation_issues)
                suggestions.append("Remove speculative language, provide factual data only")

        # Step 2: Check for fake data
        if self.validation_rules.get("check_fake_data", True):
            fake_data_issues = self._check_fake_data(text)
            if fake_data_issues:
                issues.extend(fake_data_issues)
                suggestions.append("Replace placeholder data with real information")

        # Step 3: Check for technical terms (should be masked)
        if self.validation_rules.get("check_tech_terms", True):
            tech_issues = self._check_technical_terms(text)
            if tech_issues:
                issues.extend(tech_issues)
                suggestions.append("Apply business terminology masking")

        # Step 4: Check data consistency
        if self.validation_rules.get("check_consistency", True) and context:
            consistency_issues = self._check_consistency(text, context)
            if consistency_issues:
                issues.extend(consistency_issues)
                suggestions.append("Ensure data consistency and logical coherence")

        # Step 5: Check numerical bounds
        if self.validation_rules.get("check_bounds", True):
            bounds_issues = self._check_numerical_bounds(text)
            if bounds_issues:
                issues.extend(bounds_issues)
                suggestions.append("Verify numerical values are within realistic bounds")

        # Step 6: Check for unverified claims
        unverified_issues = self._check_unverified_claims(text)
        if unverified_issues:
            issues.extend(unverified_issues)
            suggestions.append("Remove unverified claims, stick to database facts")

        # Determine result based on issues
        if not issues:
            result = ValidationResult.VALID
            confidence = 1.0
            self.stats["valid_responses"] += 1
        elif len(issues) <= 2 and not any("fake" in issue.lower() or "technical" in issue.lower() for issue in issues):
            result = ValidationResult.SUSPICIOUS
            confidence = 0.6
            self.stats["suspicious_responses"] += 1
        else:
            result = ValidationResult.INVALID
            confidence = 0.9
            self.stats["invalid_responses"] += 1

        # Step 7: LLM review for edge cases
        if use_llm_fallback and result == ValidationResult.SUSPICIOUS:
            self.stats["llm_reviews"] += 1
            # Would call LLM here for final review
            result = ValidationResult.NEEDS_REVIEW
            confidence = 0.5

        self.stats["total_validated"] += 1

        return ValidationReport(
            result=result,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions,
            cleaned_text=cleaned_text if result != ValidationResult.INVALID else None
        )

    def _check_speculation(self, text: str) -> List[str]:
        """Check for speculative language"""
        issues = []
        text_lower = text.lower()

        for term in self.forbidden_terms.get("speculation", []):
            if term.lower() in text_lower:
                issues.append(f"Speculative term found: '{term}'")

        return issues

    def _check_fake_data(self, text: str) -> List[str]:
        """Check for fake/placeholder data"""
        issues = []
        text_lower = text.lower()

        for term in self.forbidden_terms.get("fake_data", []):
            if term.lower() in text_lower:
                issues.append(f"Fake data detected: '{term}'")

        # Check for obvious test patterns
        test_patterns = [
            r'\btest\d+\b',
            r'\bexample\.com\b',
            r'\b123456\b',
            r'\bpassword\b'
        ]

        for pattern in test_patterns:
            if re.search(pattern, text_lower):
                issues.append(f"Test data pattern detected: {pattern}")

        return issues

    def _check_technical_terms(self, text: str) -> List[str]:
        """Check for unmasked technical terms"""
        issues = []
        text_lower = text.lower()

        for term in self.forbidden_terms.get("technical", []):
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(term.lower()) + r'\b'
            if re.search(pattern, text_lower):
                issues.append(f"Technical term not masked: '{term}'")

        return issues

    def _check_consistency(self, text: str, context: Dict) -> List[str]:
        """Check data consistency based on context"""
        issues = []

        # Example: If asking for user count, response should contain numbers
        if context.get("query_type") == "BUSINESS_DATA":
            if context.get("expects_numbers", False):
                # Check if response contains any numbers
                if not re.search(r'\d+', text):
                    issues.append("Expected numerical data not found")

        # Check for logical inconsistencies
        # Example: "0 active users out of -5 total users"
        numbers = re.findall(r'-?\d+', text)
        for num_str in numbers:
            num = int(num_str)
            if num < 0 and "error" not in text.lower() and "decrease" not in text.lower():
                issues.append(f"Negative value {num} seems incorrect")

        return issues

    def _check_numerical_bounds(self, text: str) -> List[str]:
        """Check if numerical values are within reasonable bounds"""
        issues = []

        # Extract numbers with context (including negative numbers)
        patterns = [
            (r'(-?\d+)\s*(?:users?|utenti)', 'users'),
            (r'(-?\d+)\s*(?:sessions?|sessioni)', 'sessions'),
            (r'(\d+)%', 'percentage')
        ]

        for pattern, bound_type in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = int(match.group(1))

                if bound_type == 'users':
                    min_val = self.numerical_bounds.get("users_min", 0)
                    max_val = self.numerical_bounds.get("users_max", 1000000)
                elif bound_type == 'percentage':
                    min_val = self.numerical_bounds.get("percentage_min", 0)
                    max_val = self.numerical_bounds.get("percentage_max", 100)
                else:
                    min_val = self.numerical_bounds.get(f"{bound_type}_min", 0)
                    max_val = self.numerical_bounds.get(f"{bound_type}_max", 100000)

                if value < min_val or value > max_val:
                    issues.append(f"{bound_type} value {value} outside bounds [{min_val}, {max_val}]")

        return issues

    def _check_unverified_claims(self, text: str) -> List[str]:
        """Check for unverified claims"""
        issues = []
        text_lower = text.lower()

        for term in self.forbidden_terms.get("unverified", []):
            if term.lower() in text_lower:
                issues.append(f"Unverified claim indicator: '{term}'")

        return issues

    def validate_batch(self, texts: List[str], context: Optional[Dict] = None) -> List[ValidationReport]:
        """
        Validate multiple texts

        Args:
            texts: List of texts to validate
            context: Optional context for all texts

        Returns:
            List of ValidationReports
        """
        return [self.validate(text, context) for text in texts]

    def get_stats(self) -> Dict:
        """Get validation statistics"""
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            "total_validated": 0,
            "valid_responses": 0,
            "invalid_responses": 0,
            "suspicious_responses": 0,
            "llm_reviews": 0
        }

    def explain_validation(self, text: str, context: Optional[Dict] = None) -> Dict:
        """
        Explain validation process for a text

        Args:
            text: Text to analyze
            context: Optional context

        Returns:
            Detailed explanation dictionary
        """
        explanation = {
            "input": text,
            "checks_performed": [],
            "issues_found": {},
            "validation_result": None
        }

        # Perform all checks and document
        if self.validation_rules.get("check_speculation", True):
            speculation = self._check_speculation(text)
            explanation["checks_performed"].append("speculation")
            if speculation:
                explanation["issues_found"]["speculation"] = speculation

        if self.validation_rules.get("check_fake_data", True):
            fake = self._check_fake_data(text)
            explanation["checks_performed"].append("fake_data")
            if fake:
                explanation["issues_found"]["fake_data"] = fake

        if self.validation_rules.get("check_tech_terms", True):
            tech = self._check_technical_terms(text)
            explanation["checks_performed"].append("technical_terms")
            if tech:
                explanation["issues_found"]["technical_terms"] = tech

        if self.validation_rules.get("check_bounds", True):
            bounds = self._check_numerical_bounds(text)
            explanation["checks_performed"].append("numerical_bounds")
            if bounds:
                explanation["issues_found"]["numerical_bounds"] = bounds

        # Get final validation
        report = self.validate(text, context, use_llm_fallback=False)
        explanation["validation_result"] = {
            "result": report.result.value,
            "confidence": report.confidence,
            "total_issues": len(report.issues)
        }

        return explanation


# Singleton instance
_instance = None

def get_validator(config_path: str = None) -> HybridValidator:
    """Get or create singleton instance of validator"""
    global _instance
    if _instance is None:
        _instance = HybridValidator(config_path or "app/config/milhena_config.json")
    return _instance


# Convenience function
def validate_response(text: str, context: Optional[Dict] = None) -> Tuple[bool, List[str]]:
    """Convenience function to validate text"""
    report = get_validator().validate(text, context, use_llm_fallback=False)
    return report.result == ValidationResult.VALID, report.issues
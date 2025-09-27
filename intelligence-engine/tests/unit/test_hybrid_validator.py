"""
Unit Tests for HybridValidator
===============================
Test coverage for deterministic validation functionality
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.hybrid_validator import HybridValidator, ValidationResult, ValidationReport, validate_response


class TestHybridValidator:
    """Test suite for HybridValidator"""

    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return HybridValidator()

    # ==========================================
    # VALID RESPONSE TESTS
    # ==========================================

    def test_valid_business_response(self, validator):
        """Test validation of clean business response"""
        text = "Ci sono attualmente 150 utenti attivi su un totale di 500 utenti registrati."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result == ValidationResult.VALID
        assert len(report.issues) == 0

    def test_valid_english_response(self, validator):
        """Test validation of clean English response"""
        text = "There are currently 150 active users out of 500 total registered users."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result == ValidationResult.VALID
        assert len(report.issues) == 0

    def test_valid_percentage_response(self, validator):
        """Test validation with percentages"""
        text = "Il tasso di successo è del 95% con 5% di errori."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result == ValidationResult.VALID
        assert len(report.issues) == 0

    # ==========================================
    # SPECULATION DETECTION TESTS
    # ==========================================

    def test_detect_speculation_might(self, validator):
        """Test detection of speculative language with 'might'"""
        text = "There might be 100 users in the system."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result in [ValidationResult.INVALID, ValidationResult.SUSPICIOUS]
        assert any("peculative" in issue for issue in report.issues)

    def test_detect_speculation_probably(self, validator):
        """Test detection of 'probably'"""
        text = "The count is probably around 50 users."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result in [ValidationResult.INVALID, ValidationResult.SUSPICIOUS]
        assert any("peculative" in issue for issue in report.issues)

    def test_detect_speculation_could_be(self, validator):
        """Test detection of 'could be'"""
        text = "It could be 200 sessions active."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result in [ValidationResult.INVALID, ValidationResult.SUSPICIOUS]
        assert any("peculative" in issue for issue in report.issues)

    # ==========================================
    # FAKE DATA DETECTION TESTS
    # ==========================================

    def test_detect_john_doe(self, validator):
        """Test detection of John Doe"""
        text = "User John Doe has 5 active sessions."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result == ValidationResult.INVALID
        assert any("Fake data" in issue for issue in report.issues)

    def test_detect_lorem_ipsum(self, validator):
        """Test detection of Lorem ipsum"""
        text = "Lorem ipsum dolor sit amet with 10 users."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result == ValidationResult.INVALID
        assert any("Fake data" in issue for issue in report.issues)

    def test_detect_test_email(self, validator):
        """Test detection of test email"""
        text = "User test@example.com is currently active."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result == ValidationResult.INVALID
        assert any("Test data" in issue for issue in report.issues)

    # ==========================================
    # TECHNICAL TERM DETECTION TESTS
    # ==========================================

    def test_detect_postgres(self, validator):
        """Test detection of unmasked postgres"""
        text = "The postgres database has 100 records."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result == ValidationResult.INVALID
        assert any("Technical term" in issue for issue in report.issues)

    def test_detect_docker(self, validator):
        """Test detection of unmasked docker"""
        text = "Docker container is running with 5 instances."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result == ValidationResult.INVALID
        assert any("Technical term" in issue for issue in report.issues)

    def test_detect_redis(self, validator):
        """Test detection of unmasked redis"""
        text = "Redis cache has 1000 entries."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result == ValidationResult.INVALID
        assert any("Technical term" in issue for issue in report.issues)

    # ==========================================
    # NUMERICAL BOUNDS TESTS
    # ==========================================

    def test_valid_user_count(self, validator):
        """Test valid user count within bounds"""
        text = "System has 5000 users."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result == ValidationResult.VALID

    def test_excessive_user_count(self, validator):
        """Test excessive user count"""
        text = "System has 10000000 users."
        report = validator.validate(text, use_llm_fallback=False)
        assert any("outside bounds" in issue for issue in report.issues)

    def test_negative_user_count(self, validator):
        """Test negative user count"""
        text = "There are -5 users online."
        report = validator.validate(text, use_llm_fallback=False)
        # Check that negative value is detected (either as bounds issue or consistency issue)
        assert any("outside bounds" in issue or "Negative" in issue for issue in report.issues)

    def test_invalid_percentage(self, validator):
        """Test percentage over 100%"""
        text = "Success rate is 150%."
        report = validator.validate(text, use_llm_fallback=False)
        assert any("outside bounds" in issue for issue in report.issues)

    # ==========================================
    # UNVERIFIED CLAIMS TESTS
    # ==========================================

    def test_detect_i_think(self, validator):
        """Test detection of 'I think'"""
        text = "I think there are 50 users."
        report = validator.validate(text, use_llm_fallback=False)
        assert any("Unverified" in issue for issue in report.issues)

    def test_detect_it_seems(self, validator):
        """Test detection of 'It seems'"""
        text = "It seems like we have 100 sessions."
        report = validator.validate(text, use_llm_fallback=False)
        assert any("Unverified" in issue for issue in report.issues)

    # ==========================================
    # CONSISTENCY TESTS
    # ==========================================

    def test_consistency_with_context(self, validator):
        """Test consistency check with context"""
        text = "No numerical data available."
        context = {"query_type": "BUSINESS_DATA", "expects_numbers": True}
        report = validator.validate(text, context, use_llm_fallback=False)
        assert any("numerical data not found" in issue for issue in report.issues)

    # ==========================================
    # EDGE CASES TESTS
    # ==========================================

    def test_empty_text(self, validator):
        """Test empty text validation"""
        report = validator.validate("", use_llm_fallback=False)
        assert report.result == ValidationResult.INVALID
        assert any("Empty" in issue for issue in report.issues)

    def test_whitespace_only(self, validator):
        """Test whitespace-only text"""
        report = validator.validate("   \n\t  ", use_llm_fallback=False)
        assert report.result == ValidationResult.INVALID

    def test_multiple_issues(self, validator):
        """Test text with multiple issues"""
        text = "I think postgres probably has John Doe with -10 users at 150%."
        report = validator.validate(text, use_llm_fallback=False)
        assert report.result == ValidationResult.INVALID
        assert len(report.issues) > 3

    # ==========================================
    # BATCH VALIDATION TESTS
    # ==========================================

    def test_batch_validation(self, validator):
        """Test batch validation"""
        texts = [
            "There are 100 users.",
            "Postgres has data.",
            "Success rate is 95%."
        ]
        reports = validator.validate_batch(texts)
        assert len(reports) == 3
        assert reports[0].result == ValidationResult.VALID
        assert reports[1].result == ValidationResult.INVALID  # Technical term
        assert reports[2].result == ValidationResult.VALID

    # ==========================================
    # STATISTICS TESTS
    # ==========================================

    def test_statistics_tracking(self, validator):
        """Test statistics tracking"""
        validator.reset_stats()

        validator.validate("Valid response with 100 users.", use_llm_fallback=False)
        validator.validate("Postgres database issue.", use_llm_fallback=False)
        validator.validate("Maybe 50 users.", use_llm_fallback=False)

        stats = validator.get_stats()
        assert stats["total_validated"] == 3
        assert stats["valid_responses"] >= 1
        assert stats["invalid_responses"] >= 1

    # ==========================================
    # EXPLANATION TESTS
    # ==========================================

    def test_explain_validation(self, validator):
        """Test validation explanation"""
        text = "There might be postgres with 100 users."
        explanation = validator.explain_validation(text)

        assert explanation["input"] == text
        assert "speculation" in explanation["checks_performed"]
        assert "technical_terms" in explanation["checks_performed"]
        assert len(explanation["issues_found"]) > 0

    # ==========================================
    # CONVENIENCE FUNCTION TESTS
    # ==========================================

    def test_validate_response_convenience(self):
        """Test convenience function"""
        is_valid, issues = validate_response("There are 100 active users.")
        assert is_valid == True
        assert len(issues) == 0

        is_valid, issues = validate_response("Postgres has John Doe.")
        assert is_valid == False
        assert len(issues) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
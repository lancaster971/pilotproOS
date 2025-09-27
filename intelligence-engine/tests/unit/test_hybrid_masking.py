"""
Unit Tests for HybridMaskingLibrary
====================================
Test coverage for deterministic masking functionality
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.hybrid_masking import HybridMaskingLibrary, mask_text


class TestHybridMasking:
    """Test suite for HybridMaskingLibrary"""

    @pytest.fixture
    def masking_library(self):
        """Create masking library instance"""
        return HybridMaskingLibrary()

    # ==========================================
    # BASIC TERM REPLACEMENT TESTS
    # ==========================================

    def test_basic_postgres_masking(self, masking_library):
        """Test basic PostgreSQL term masking"""
        text = "The postgres database is running"
        masked = masking_library.mask(text)
        assert "postgres" not in masked.lower()
        assert "Database" in masked

    def test_basic_redis_masking(self, masking_library):
        """Test Redis term masking"""
        text = "redis cache hit ratio is 85%"
        masked = masking_library.mask(text)
        assert "redis" not in masked.lower()
        assert "Cache System" in masked

    def test_basic_docker_masking(self, masking_library):
        """Test Docker term masking"""
        text = "docker container is healthy"
        masked = masking_library.mask(text)
        assert "docker" not in masked.lower()
        assert "Container Platform" in masked

    def test_basic_n8n_masking(self, masking_library):
        """Test n8n term masking"""
        text = "n8n workflow is executing"
        masked = masking_library.mask(text)
        assert "n8n" not in masked.lower()
        assert "Automation Platform" in masked
        assert "Business Process" in masked

    # ==========================================
    # CASE SENSITIVITY TESTS
    # ==========================================

    def test_case_preservation_uppercase(self, masking_library):
        """Test that uppercase is preserved"""
        text = "POSTGRES database"
        masked = masking_library.mask(text)
        assert "DATABASE" in masked or "Database" in masked
        assert "postgres" not in masked.lower()

    def test_case_preservation_mixed(self, masking_library):
        """Test mixed case handling"""
        text = "PostgreSQL Redis DOCKER"
        masked = masking_library.mask(text)
        assert all(term not in masked.lower() for term in ["postgresql", "redis", "docker"])

    def test_case_variations(self, masking_library):
        """Test various case variations"""
        variations = ["redis", "Redis", "REDIS", "ReDiS"]
        for variant in variations:
            text = f"The {variant} cache"
            masked = masking_library.mask(text)
            assert "redis" not in masked.lower()
            assert "Cache System" in masked

    # ==========================================
    # COMPOUND TERM TESTS
    # ==========================================

    def test_workflow_execution_masking(self, masking_library):
        """Test compound term 'workflow execution'"""
        text = "workflow execution failed"
        masked = masking_library.mask(text)
        assert "workflow" not in masked.lower()
        assert "execution" not in masked.lower()
        assert "Business Process" in masked
        assert "Process Run" in masked

    def test_api_endpoint_masking(self, masking_library):
        """Test compound term 'api endpoint'"""
        text = "The api endpoint is not responding"
        masked = masking_library.mask(text)
        assert "api" not in masked.lower()
        assert "Integration Interface" in masked

    # ==========================================
    # MULTIPLE TERMS TESTS
    # ==========================================

    def test_multiple_terms_single_sentence(self, masking_library):
        """Test masking multiple terms in one sentence"""
        text = "The n8n workflow connects to postgres via nginx"
        masked = masking_library.mask(text)

        # Check all tech terms are removed
        assert all(term not in masked.lower() for term in ["n8n", "workflow", "postgres", "nginx"])

        # Check business terms are present
        assert "Automation Platform" in masked
        assert "Business Process" in masked
        assert "Database" in masked
        assert "Web Server" in masked

    def test_all_major_components(self, masking_library):
        """Test sentence with all major components"""
        text = "Docker runs postgres, redis, nginx, and n8n"
        masked = masking_library.mask(text)

        forbidden = ["docker", "postgres", "redis", "nginx", "n8n"]
        assert all(term not in masked.lower() for term in forbidden)

    # ==========================================
    # PARTIAL MATCH PREVENTION TESTS
    # ==========================================

    def test_no_partial_replacement_workflow(self, masking_library):
        """Test that 'workflowing' is not replaced"""
        text = "workflowing is different from workflow"
        masked = masking_library.mask(text)
        assert "workflowing" in masked
        # Check that standalone 'workflow' was replaced but 'workflowing' was not
        assert "Business Process" in masked
        # The word 'workflow' as standalone should be replaced
        words = masked.lower().split()
        assert "workflow" not in words  # 'workflow' as a word should not exist

    def test_no_partial_replacement_api(self, masking_library):
        """Test that 'apikey' is not replaced"""
        text = "The apikey is not the same as api"
        masked = masking_library.mask(text)
        assert "apikey" in masked
        assert masked.count("Integration Interface") == 1  # Only 'api' replaced

    def test_word_boundaries(self, masking_library):
        """Test word boundary detection"""
        text = "redistribution is not redis, dockyard is not docker"
        masked = masking_library.mask(text)
        assert "redistribution" in masked
        assert "dockyard" in masked
        assert "Cache System" in masked
        assert "Container Platform" in masked

    # ==========================================
    # SPECIAL CHARACTERS TESTS
    # ==========================================

    def test_hyphenated_terms(self, masking_library):
        """Test terms with hyphens"""
        text = "postgres-db and redis-cache"
        masked = masking_library.mask(text)
        assert "postgres" not in masked.lower()
        assert "redis" not in masked.lower()

    def test_underscored_terms(self, masking_library):
        """Test terms with underscores"""
        text = "n8n_workflow_execution"
        masked = masking_library.mask(text)
        assert "n8n" not in masked.lower()
        assert "workflow" not in masked.lower()

    def test_punctuation_preservation(self, masking_library):
        """Test that punctuation is preserved"""
        text = "postgres, redis, and docker."
        masked = masking_library.mask(text)
        assert "," in masked
        assert "." in masked
        assert "and" in masked

    # ==========================================
    # EDGE CASES TESTS
    # ==========================================

    def test_empty_string(self, masking_library):
        """Test empty string handling"""
        assert masking_library.mask("") == ""
        assert masking_library.mask(None) == None

    def test_no_tech_terms(self, masking_library):
        """Test text with no technical terms"""
        text = "This is a normal business sentence"
        masked = masking_library.mask(text)
        assert masked == text

    def test_only_tech_terms(self, masking_library):
        """Test text with only tech terms"""
        text = "postgres redis docker"
        masked = masking_library.mask(text)
        assert all(term not in masked.lower() for term in ["postgres", "redis", "docker"])
        assert "Database" in masked
        assert "Cache System" in masked
        assert "Container Platform" in masked

    def test_repeated_terms(self, masking_library):
        """Test repeated technical terms"""
        text = "postgres postgres postgres"
        masked = masking_library.mask(text)
        assert "postgres" not in masked.lower()
        assert masked.count("Database") == 3

    # ==========================================
    # VALIDATION TESTS
    # ==========================================

    def test_validate_clean_text(self, masking_library):
        """Test validation of clean text"""
        text = "This is clean business text"
        is_clean, leaked = masking_library.validate_masking(text)
        assert is_clean == True
        assert leaked == []

    def test_validate_leaked_terms(self, masking_library):
        """Test validation detects leaked terms"""
        text = "This contains postgres and redis"
        is_clean, leaked = masking_library.validate_masking(text)
        assert is_clean == False
        assert "postgres" in leaked
        assert "redis" in leaked

    def test_leak_detection_and_fallback(self, masking_library):
        """Test that leaked terms are replaced with generic fallback"""
        # Simulate a term that might not be in dictionary
        text = "kubernetes cluster is running"
        masked = masking_library.mask(text)

        # kubernetes is in forbidden_keywords, so should be masked
        if "kubernetes" in masking_library.forbidden_keywords:
            assert "kubernetes" not in masked.lower()
            # Should be replaced with fallback
            assert "[system component]" in masked or "Container Orchestrator" in masked

    # ==========================================
    # STATISTICS TESTS
    # ==========================================

    def test_statistics_tracking(self, masking_library):
        """Test that statistics are tracked correctly"""
        masking_library.reset_stats()

        # Mask some text
        masking_library.mask("postgres and redis")
        masking_library.mask("docker and nginx")

        stats = masking_library.get_stats()
        assert stats["total_masked"] == 2
        assert stats["terms_replaced"] > 0

    # ==========================================
    # BULK OPERATIONS TESTS
    # ==========================================

    def test_bulk_masking(self, masking_library):
        """Test bulk masking operation"""
        texts = [
            "postgres database",
            "redis cache",
            "docker container",
            "n8n workflow"
        ]

        masked_texts = masking_library.bulk_mask(texts)

        assert len(masked_texts) == 4
        assert all("postgres" not in text.lower() for text in masked_texts)
        assert all("redis" not in text.lower() for text in masked_texts)
        assert all("docker" not in text.lower() for text in masked_texts)
        assert all("n8n" not in text.lower() for text in masked_texts)

    # ==========================================
    # EXPLANATION TESTS
    # ==========================================

    def test_explain_masking(self, masking_library):
        """Test masking explanation feature"""
        text = "The postgres database and redis cache"
        explanation = masking_library.explain_masking(text)

        assert explanation["original"] == text
        assert "postgres" not in explanation["masked"].lower()
        assert "redis" not in explanation["masked"].lower()

        # Check replacements are documented
        replacements = {r["from"]: r["to"] for r in explanation["replacements"]}
        assert "postgres" in replacements or "postgresql" in replacements
        assert "redis" in replacements

    # ==========================================
    # CONVENIENCE FUNCTION TESTS
    # ==========================================

    def test_mask_text_convenience_function(self):
        """Test the convenience function"""
        text = "postgres and redis"
        masked = mask_text(text)
        assert "postgres" not in masked.lower()
        assert "redis" not in masked.lower()
        assert "Database" in masked
        assert "Cache System" in masked


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
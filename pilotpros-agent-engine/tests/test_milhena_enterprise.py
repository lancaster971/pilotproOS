"""
Unit tests for Milhena Enterprise Orchestrator
Test all critical components with pytest
"""

import pytest
import asyncio
import json
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import system under test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.crews.milhena_orchestrator_enterprise import (
    PersistentConversationMemory,
    PersistentAnalyticsTracker,
    PersistentResponseCache,
    MilhenaEnterpriseOrchestrator,
    retry_on_failure
)


# ============= FIXTURES =============
@pytest.fixture
def temp_persistence_dir():
    """Create temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    original_dir = Path("milhena_persistence")

    # Monkey patch the persistence directory
    import agents.crews.milhena_orchestrator_enterprise as module
    module.PERSISTENCE_DIR = Path(temp_dir)

    yield Path(temp_dir)

    # Cleanup
    shutil.rmtree(temp_dir)
    module.PERSISTENCE_DIR = original_dir


@pytest.fixture
def memory_system(temp_persistence_dir):
    """Create memory system for testing"""
    return PersistentConversationMemory(max_size=5, user_id="test_user")


@pytest.fixture
def analytics_tracker(temp_persistence_dir):
    """Create analytics tracker for testing"""
    return PersistentAnalyticsTracker()


@pytest.fixture
def response_cache(temp_persistence_dir):
    """Create response cache for testing"""
    return PersistentResponseCache(ttl_seconds=60)


@pytest.fixture
def orchestrator(temp_persistence_dir):
    """Create orchestrator for testing"""
    return MilhenaEnterpriseOrchestrator(
        enable_memory=True,
        enable_analytics=True,
        enable_cache=True
    )


# ============= MEMORY TESTS =============
class TestPersistentConversationMemory:
    """Test memory system with persistence"""

    def test_memory_initialization(self, memory_system):
        """Test memory initializes correctly"""
        assert memory_system.user_id == "test_user"
        assert memory_system.max_size == 5
        assert len(memory_system.memory) == 0
        assert memory_system.user_profile["interactions_count"] == 0

    def test_add_interaction(self, memory_system):
        """Test adding interactions to memory"""
        memory_system.add_interaction(
            question="Test question",
            response="Test response",
            metadata={"question_type": "TEST", "language": "en"}
        )

        assert len(memory_system.memory) == 1
        assert memory_system.user_profile["interactions_count"] == 1
        assert memory_system.user_profile["preferred_language"] == "en"

    def test_memory_persistence(self, memory_system, temp_persistence_dir):
        """Test memory persists to disk"""
        # Add interaction
        memory_system.add_interaction(
            question="Persistent question",
            response="Persistent response",
            metadata={"question_type": "TEST"}
        )

        # Check files exist
        memory_file = temp_persistence_dir / f"memory_{memory_system.user_id}.json"
        profile_file = temp_persistence_dir / f"profile_{memory_system.user_id}.json"

        assert memory_file.exists()
        assert profile_file.exists()

        # Load and verify content
        with open(memory_file) as f:
            memory_data = json.load(f)
            assert len(memory_data) == 1
            assert memory_data[0]["question"] == "Persistent question"

    def test_memory_max_size(self, memory_system):
        """Test memory respects max size"""
        for i in range(10):
            memory_system.add_interaction(
                question=f"Question {i}",
                response=f"Response {i}",
                metadata={}
            )

        assert len(memory_system.memory) == 5  # Max size
        # Should have latest 5 (5-9)
        assert memory_system.memory[0]["question"] == "Question 5"
        assert memory_system.memory[-1]["question"] == "Question 9"

    def test_get_context(self, memory_system):
        """Test context generation from memory"""
        # Empty memory
        context = memory_system.get_context()
        assert context == "Prima interazione"

        # Add interactions
        for i in range(3):
            memory_system.add_interaction(
                question=f"Q{i}",
                response=f"R{i}",
                metadata={"question_type": f"TYPE{i}"}
            )

        context = memory_system.get_context()
        assert "Conversazioni recenti:" in context
        assert "Q0" in context
        assert "TYPE" in context

    def test_is_returning_user(self, memory_system):
        """Test returning user detection"""
        assert not memory_system.is_returning_user()

        memory_system.add_interaction("Q", "R", {})
        assert memory_system.is_returning_user()

    def test_clear_old_interactions(self, memory_system):
        """Test clearing old interactions"""
        # Add old interaction
        old_interaction = {
            "timestamp": (datetime.now() - timedelta(days=40)).isoformat(),
            "question": "Old question",
            "response": "Old response",
            "type": "OLD",
            "language": "it",
            "confidence": 0.9
        }
        memory_system.memory.append(old_interaction)

        # Add recent interaction
        memory_system.add_interaction("Recent", "Response", {})

        # Clear old (> 30 days)
        memory_system.clear_old_interactions(days=30)

        assert len(memory_system.memory) == 1
        assert memory_system.memory[0]["question"] == "Recent"


# ============= ANALYTICS TESTS =============
class TestPersistentAnalyticsTracker:
    """Test analytics tracking system"""

    def test_analytics_initialization(self, analytics_tracker):
        """Test analytics initializes correctly"""
        assert analytics_tracker.stats["total_requests"] == 0
        assert analytics_tracker.stats["cache_hits"] == 0
        assert analytics_tracker.stats["errors_count"] == 0

    def test_track_request(self, analytics_tracker, temp_persistence_dir):
        """Test request tracking"""
        analytics_tracker.track_request(
            question="Test question",
            question_type="GREETING",
            response_time=0.5,
            agents_used=["AGENT1", "AGENT2"],
            language="it",
            confidence=0.95,
            cache_hit=False
        )

        assert analytics_tracker.stats["total_requests"] == 1
        assert analytics_tracker.stats["question_types_count"]["GREETING"] == 1
        assert analytics_tracker.stats["languages_detected"]["it"] == 1
        assert analytics_tracker.stats["total_response_time_ms"] == 500

        # Check metrics file
        metrics_file = temp_persistence_dir / "milhena_metrics.jsonl"
        assert metrics_file.exists()

    def test_cache_hit_tracking(self, analytics_tracker):
        """Test cache hit/miss tracking"""
        analytics_tracker.track_request(
            "Q1", "TYPE", 0.1, [], "en", 0.9, cache_hit=True
        )
        analytics_tracker.track_request(
            "Q2", "TYPE", 0.2, [], "en", 0.9, cache_hit=False
        )

        assert analytics_tracker.stats["cache_hits"] == 1
        assert analytics_tracker.stats["cache_misses"] == 1

    def test_error_tracking(self, analytics_tracker):
        """Test error tracking"""
        analytics_tracker.track_request(
            "Q", "ERROR", 0.1, [], "en", 0, error="Test error"
        )

        assert analytics_tracker.stats["errors_count"] == 1

    def test_daily_stats(self, analytics_tracker):
        """Test daily statistics"""
        today = str(datetime.now().date())

        analytics_tracker.track_request(
            "Q1", "TYPE", 0.1, [], "en", 0.9
        )
        analytics_tracker.track_request(
            "Q2", "TYPE", 0.2, [], "en", 0.9
        )

        daily = analytics_tracker.stats["daily_stats"][today]
        assert daily["requests"] == 2
        assert daily["avg_response_time_ms"] == 150  # (100 + 200) / 2

    def test_get_stats(self, analytics_tracker):
        """Test statistics aggregation"""
        # Track some requests
        for i in range(5):
            analytics_tracker.track_request(
                f"Q{i}",
                "GREETING" if i < 3 else "HELP",
                0.1 * (i + 1),
                ["AGENT"],
                "it",
                0.9,
                cache_hit=(i % 2 == 0)
            )

        stats = analytics_tracker.get_stats()

        assert stats["total_requests"] == 5
        assert stats["avg_response_time_ms"] == 300  # (100+200+300+400+500)/5
        assert stats["cache_hit_rate"] == 0.6  # 3 hits, 2 misses
        assert len(stats["top_question_types"]) <= 3


# ============= CACHE TESTS =============
class TestPersistentResponseCache:
    """Test response caching system"""

    def test_cache_initialization(self, response_cache):
        """Test cache initializes correctly"""
        assert response_cache.ttl.total_seconds() == 60
        assert len(response_cache.cache) == 0
        assert response_cache.hit_count == 0
        assert response_cache.miss_count == 0

    def test_cache_set_and_get(self, response_cache):
        """Test caching and retrieval"""
        # Cache a response
        response_cache.set(
            question="Hello",
            question_type="GREETING",
            language="en",
            response="Hi there!"
        )

        # Retrieve cached response
        cached = response_cache.get("Hello", "GREETING", "en")
        assert cached == "Hi there!"
        assert response_cache.hit_count == 1

        # Miss on different question
        cached = response_cache.get("Goodbye", "GREETING", "en")
        assert cached is None
        assert response_cache.miss_count == 1

    def test_cache_expiration(self, response_cache):
        """Test cache expiration"""
        # Create expired entry
        key = response_cache._generate_key("Test", "TYPE", "en")
        expired_time = datetime.now() - timedelta(seconds=120)
        response_cache.cache[key] = ("Response", expired_time)

        # Try to get expired entry
        cached = response_cache.get("Test", "TYPE", "en")
        assert cached is None
        assert key not in response_cache.cache

    def test_cache_persistence(self, response_cache, temp_persistence_dir):
        """Test cache persistence to disk"""
        response_cache.set("Q", "GREETING", "it", "R")

        cache_file = temp_persistence_dir / "response_cache.pkl"
        assert cache_file.exists()

        # Create new cache instance and check it loads
        new_cache = PersistentResponseCache(ttl_seconds=60)
        cached = new_cache.get("Q", "GREETING", "it")
        assert cached == "R"

    def test_cache_selective(self, response_cache):
        """Test cache only caches specific types"""
        # Should cache
        response_cache.set("Q1", "GREETING", "en", "R1")
        response_cache.set("Q2", "HELP", "en", "R2")
        response_cache.set("Q3", "GENERAL", "en", "R3")

        # Should not cache
        response_cache.set("Q4", "BUSINESS_DATA", "en", "R4")
        response_cache.set("Q5", "ANALYSIS", "en", "R5")

        assert len(response_cache.cache) == 3
        assert response_cache.get("Q1", "GREETING", "en") == "R1"
        assert response_cache.get("Q4", "BUSINESS_DATA", "en") is None

    def test_clear_expired(self, response_cache):
        """Test clearing expired entries"""
        # Add mixed entries
        now = datetime.now()
        key1 = response_cache._generate_key("Q1", "TYPE", "en")
        key2 = response_cache._generate_key("Q2", "TYPE", "en")

        response_cache.cache[key1] = ("R1", now - timedelta(seconds=120))  # Expired
        response_cache.cache[key2] = ("R2", now)  # Valid

        response_cache.clear_expired()

        assert len(response_cache.cache) == 1
        assert key2 in response_cache.cache
        assert key1 not in response_cache.cache


# ============= RETRY LOGIC TESTS =============
class TestRetryLogic:
    """Test retry decorator"""

    @pytest.mark.asyncio
    async def test_retry_on_success(self):
        """Test retry decorator with successful execution"""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay_seconds=0.01)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_func()
        assert result == "success"
        assert call_count == 1  # Should succeed on first try

    @pytest.mark.asyncio
    async def test_retry_on_failure_then_success(self):
        """Test retry decorator with failure then success"""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay_seconds=0.01)
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"

        result = await failing_then_success()
        assert result == "success"
        assert call_count == 3  # Should retry and succeed on third attempt

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """Test retry decorator when all attempts fail"""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay_seconds=0.01)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise Exception("Permanent failure")

        with pytest.raises(Exception) as exc_info:
            await always_fails()

        assert str(exc_info.value) == "Permanent failure"
        assert call_count == 3  # Should try all attempts


# ============= ORCHESTRATOR TESTS =============
class TestMilhenaEnterpriseOrchestrator:
    """Test main orchestrator"""

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes correctly"""
        assert orchestrator.enable_memory is True
        assert orchestrator.analytics is not None
        assert orchestrator.cache is not None
        assert len(orchestrator.memory_store) == 0

    def test_get_or_create_memory(self, orchestrator):
        """Test memory creation for users"""
        # First call creates
        memory1 = orchestrator.get_or_create_memory("user1")
        assert memory1 is not None
        assert memory1.user_id == "user1"
        assert "user1" in orchestrator.memory_store

        # Second call returns same instance
        memory2 = orchestrator.get_or_create_memory("user1")
        assert memory1 is memory2

        # Different user gets different memory
        memory3 = orchestrator.get_or_create_memory("user2")
        assert memory3 is not memory1
        assert memory3.user_id == "user2"

    def test_language_detection(self, orchestrator):
        """Test language detection"""
        # Mock langdetect if available
        with patch('agents.crews.milhena_orchestrator_enterprise.LANGDETECT_AVAILABLE', True):
            with patch('agents.crews.milhena_orchestrator_enterprise.detect_language') as mock_detect:
                mock_detect.return_value = "en"
                lang = orchestrator.detect_user_language("Hello world")
                assert lang == "en"

                mock_detect.return_value = "it"
                lang = orchestrator.detect_user_language("Ciao mondo")
                assert lang == "it"

        # Test fallback when langdetect not available
        with patch('agents.crews.milhena_orchestrator_enterprise.LANGDETECT_AVAILABLE', False):
            lang = orchestrator.detect_user_language("Any text")
            assert lang == "it"  # Default fallback

    def test_quick_classify(self, orchestrator):
        """Test quick classification for caching"""
        assert orchestrator._quick_classify("Ciao!") == "GREETING"
        assert orchestrator._quick_classify("Hello there") == "GREETING"
        assert orchestrator._quick_classify("Cosa puoi fare?") == "HELP"
        assert orchestrator._quick_classify("Help me") == "HELP"
        assert orchestrator._quick_classify("Quanti dati abbiamo?") == "BUSINESS_DATA"
        assert orchestrator._quick_classify("Show metrics") == "BUSINESS_DATA"
        assert orchestrator._quick_classify("Analizza i trend") == "ANALYSIS"
        assert orchestrator._quick_classify("Random text") == "GENERAL"

    def test_parse_classification(self, orchestrator):
        """Test classification parsing"""
        # Valid JSON
        result = orchestrator._parse_classification('{"question_type": "GREETING", "confidence": 0.9}')
        assert result["question_type"] == "GREETING"
        assert result["confidence"] == 0.9

        # JSON embedded in text
        result = orchestrator._parse_classification('Some text {"question_type": "HELP"} more text')
        assert result["question_type"] == "HELP"

        # Invalid JSON
        result = orchestrator._parse_classification("Not JSON at all")
        assert result["question_type"] == "GENERAL"
        assert result["confidence"] == 0.5

    def test_get_agents_for_type(self, orchestrator):
        """Test agent selection by question type"""
        assert orchestrator._get_agents_for_type("GREETING") == ["CONVERSATION"]
        assert orchestrator._get_agents_for_type("HELP") == ["CONVERSATION"]
        assert orchestrator._get_agents_for_type("BUSINESS_DATA") == ["DATA", "SECURITY", "COORDINATOR"]
        assert orchestrator._get_agents_for_type("ANALYSIS") == ["DATA", "ANALYZER", "SECURITY", "COORDINATOR"]
        assert orchestrator._get_agents_for_type("UNKNOWN") == ["CONVERSATION"]

    @pytest.mark.asyncio
    async def test_analyze_question_with_cache(self, orchestrator):
        """Test question analysis with caching"""
        # Mock the crew execution
        with patch.object(orchestrator, '_execute_crew_with_retry') as mock_exec:
            mock_exec.return_value = "Mocked response"

            # First call - cache miss
            result1 = await orchestrator.analyze_question_enterprise(
                question="Ciao!",
                user_id="test_cache_user"
            )

            assert result1["success"] is True
            assert result1["cached"] is False
            assert mock_exec.call_count == 2  # One for analysis, one for execution

            # Second call - should hit cache
            result2 = await orchestrator.analyze_question_enterprise(
                question="Ciao!",
                user_id="test_cache_user"
            )

            assert result2["cached"] is True
            # Mock should not be called again for cached response

    def test_system_stats(self, orchestrator):
        """Test system statistics"""
        stats = orchestrator.get_system_stats()

        assert "persistence_dir" in stats
        assert "users_tracked" in stats
        assert stats["users_tracked"] == 0

        # Add a user
        orchestrator.get_or_create_memory("test_user")
        stats = orchestrator.get_system_stats()
        assert stats["users_tracked"] == 1


# ============= INTEGRATION TESTS =============
@pytest.mark.integration
class TestIntegration:
    """Integration tests for the complete system"""

    @pytest.mark.asyncio
    async def test_end_to_end_flow(self, orchestrator):
        """Test complete flow from question to response"""
        # Mock the CrewAI components
        with patch('agents.crews.milhena_orchestrator_enterprise.Crew') as MockCrew:
            mock_crew = MagicMock()
            mock_crew.kickoff.return_value = '{"question_type": "GREETING", "confidence": 0.95}'
            MockCrew.return_value = mock_crew

            result = await orchestrator.analyze_question_enterprise(
                question="Ciao! Come stai?",
                context="Test context",
                user_id="integration_test_user"
            )

            # Verify result structure
            assert "success" in result
            assert "response" in result
            assert "question_type" in result
            assert "language" in result
            assert "confidence" in result
            assert "cached" in result
            assert "response_time_ms" in result
            assert "user_id" in result
            assert result["user_id"] == "integration_test_user"

            # Verify memory was updated
            memory = orchestrator.get_or_create_memory("integration_test_user")
            assert memory.user_profile["interactions_count"] > 0

            # Verify analytics were tracked
            if orchestrator.analytics:
                stats = orchestrator.analytics.get_stats()
                assert stats["total_requests"] > 0


# ============= RUN TESTS =============
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
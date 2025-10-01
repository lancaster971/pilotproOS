"""
Learning System - Continuous improvement from user feedback
Tracks patterns, learns from mistakes, improves accuracy over time
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
import numpy as np
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class FeedbackEntry:
    """Single feedback entry"""
    timestamp: datetime
    query: str
    intent: str
    response: str
    feedback_type: str  # "positive", "negative", "correction"
    correction_data: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

@dataclass
class PatternLearning:
    """Learned pattern from feedback"""
    pattern: str
    correct_intent: str
    confidence: float
    occurrences: int
    last_seen: datetime
    success_rate: float

class LearningSystem:
    """
    Continuous learning system that improves from user feedback
    Tracks patterns, learns from corrections, improves accuracy
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "/tmp/milhena_learning"
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)

        # Storage files
        self.feedback_file = f"{self.storage_path}/feedback.json"
        self.patterns_file = f"{self.storage_path}/patterns.json"
        self.metrics_file = f"{self.storage_path}/metrics.json"

        # In-memory data
        self.feedback_entries: List[FeedbackEntry] = []
        self.learned_patterns: Dict[str, PatternLearning] = {}
        self.intent_corrections: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.performance_metrics = {
            "total_queries": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "corrections": 0,
            "accuracy_rate": 0.75,  # Start at 75%
            "improvement_curve": []
        }

        self._load_data()
        self._setup_auto_save()

    def _load_data(self):
        """Load learning data from storage"""
        # Load feedback
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r') as f:
                    data = json.load(f)
                    for entry in data:
                        entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                        self.feedback_entries.append(FeedbackEntry(**entry))
                logger.info(f"Loaded {len(self.feedback_entries)} feedback entries")
            except Exception as e:
                logger.error(f"Failed to load feedback: {e}")

        # Load patterns
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'r') as f:
                    data = json.load(f)
                    for pattern_key, pattern_data in data.items():
                        pattern_data['last_seen'] = datetime.fromisoformat(pattern_data['last_seen'])
                        self.learned_patterns[pattern_key] = PatternLearning(**pattern_data)
                logger.info(f"Loaded {len(self.learned_patterns)} learned patterns")
            except Exception as e:
                logger.error(f"Failed to load patterns: {e}")

        # Load metrics
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r') as f:
                    self.performance_metrics = json.load(f)
                logger.info(f"Loaded performance metrics: {self.performance_metrics['accuracy_rate']:.2%} accuracy")
            except Exception as e:
                logger.error(f"Failed to load metrics: {e}")

    def _save_data(self):
        """Save learning data to storage"""
        try:
            # Save feedback
            feedback_data = []
            for entry in self.feedback_entries[-1000:]:  # Keep last 1000 entries
                entry_dict = asdict(entry)
                entry_dict['timestamp'] = entry_dict['timestamp'].isoformat()
                feedback_data.append(entry_dict)

            with open(self.feedback_file, 'w') as f:
                json.dump(feedback_data, f, indent=2)

            # Save patterns
            patterns_data = {}
            for key, pattern in self.learned_patterns.items():
                pattern_dict = asdict(pattern)
                pattern_dict['last_seen'] = pattern_dict['last_seen'].isoformat()
                patterns_data[key] = pattern_dict

            with open(self.patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2)

            # Save metrics
            with open(self.metrics_file, 'w') as f:
                json.dump(self.performance_metrics, f, indent=2)

            logger.debug("Learning data saved")
        except Exception as e:
            logger.error(f"Failed to save learning data: {e}")

    def _setup_auto_save(self):
        """Setup automatic saving every 10 minutes"""
        async def auto_save():
            while True:
                await asyncio.sleep(600)  # 10 minutes
                self._save_data()
                self._analyze_patterns()

        # Start auto-save task in background
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(auto_save())
        except RuntimeError:
            pass

    async def record_feedback(
        self,
        query: str,
        intent: str,
        response: str,
        feedback_type: str,
        correction_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        """
        Record user feedback

        Args:
            query: Original user query
            intent: Detected intent
            response: System response
            feedback_type: "positive", "negative", or "correction"
            correction_data: Additional correction information
            session_id: Session identifier
        """
        entry = FeedbackEntry(
            timestamp=datetime.now(),
            query=query,
            intent=intent,
            response=response,
            feedback_type=feedback_type,
            correction_data=correction_data,
            session_id=session_id
        )

        self.feedback_entries.append(entry)

        # Update metrics
        self.performance_metrics["total_queries"] += 1
        if feedback_type == "positive":
            self.performance_metrics["positive_feedback"] += 1
        elif feedback_type == "negative":
            self.performance_metrics["negative_feedback"] += 1
        elif feedback_type == "correction":
            self.performance_metrics["corrections"] += 1

            # Track intent corrections
            if correction_data and "correct_intent" in correction_data:
                self.intent_corrections[intent][correction_data["correct_intent"]] += 1

        # Recalculate accuracy
        self._update_accuracy()

        # Learn from this feedback
        await self._learn_from_feedback(entry)

        # Save periodically
        if len(self.feedback_entries) % 10 == 0:
            self._save_data()

        logger.info(f"Feedback recorded: {feedback_type} for intent '{intent}'")

    def _update_accuracy(self):
        """Update accuracy rate based on feedback"""
        total = self.performance_metrics["total_queries"]
        if total > 0:
            positive = self.performance_metrics["positive_feedback"]
            # Simple accuracy calculation
            self.performance_metrics["accuracy_rate"] = positive / total

            # Add to improvement curve
            self.performance_metrics["improvement_curve"].append({
                "timestamp": datetime.now().isoformat(),
                "accuracy": self.performance_metrics["accuracy_rate"],
                "total_queries": total
            })

            # Keep only last 100 points
            self.performance_metrics["improvement_curve"] = \
                self.performance_metrics["improvement_curve"][-100:]

    async def _learn_from_feedback(self, entry: FeedbackEntry):
        """
        Learn from a single feedback entry

        Args:
            entry: Feedback entry to learn from
        """
        # Extract patterns from query
        patterns = self._extract_patterns(entry.query)

        for pattern in patterns:
            pattern_key = f"{pattern}:{entry.intent}"

            if pattern_key not in self.learned_patterns:
                self.learned_patterns[pattern_key] = PatternLearning(
                    pattern=pattern,
                    correct_intent=entry.intent,
                    confidence=0.5,
                    occurrences=0,
                    last_seen=datetime.now(),
                    success_rate=0.5
                )

            learning = self.learned_patterns[pattern_key]
            learning.occurrences += 1
            learning.last_seen = datetime.now()

            # Update confidence based on feedback
            if entry.feedback_type == "positive":
                learning.confidence = min(1.0, learning.confidence + 0.1)
                learning.success_rate = (learning.success_rate * 0.9) + (1.0 * 0.1)
            elif entry.feedback_type == "negative":
                learning.confidence = max(0.0, learning.confidence - 0.2)
                learning.success_rate = (learning.success_rate * 0.9) + (0.0 * 0.1)
            elif entry.feedback_type == "correction" and entry.correction_data:
                # Learn the correct intent
                correct_intent = entry.correction_data.get("correct_intent")
                if correct_intent:
                    learning.correct_intent = correct_intent
                    learning.confidence = 0.7  # Reset to moderate confidence

        logger.debug(f"Learned from {len(patterns)} patterns")

    def _extract_patterns(self, query: str) -> List[str]:
        """
        Extract learnable patterns from a query

        Args:
            query: User query

        Returns:
            List of patterns
        """
        patterns = []
        words = query.lower().split()

        # N-grams (2-3 word patterns)
        for n in [2, 3]:
            for i in range(len(words) - n + 1):
                pattern = " ".join(words[i:i+n])
                patterns.append(pattern)

        # Key phrases
        key_phrases = [
            "non funziona", "è rotto", "problema con",
            "errore", "aiuto", "come faccio",
            "stato di", "andamento", "report"
        ]

        for phrase in key_phrases:
            if phrase in query.lower():
                patterns.append(phrase)

        return patterns

    def suggest_intent(self, query: str) -> Optional[Tuple[str, float]]:
        """
        Suggest an intent based on learned patterns

        Args:
            query: User query

        Returns:
            Tuple of (suggested_intent, confidence) or None
        """
        patterns = self._extract_patterns(query)
        intent_scores = defaultdict(float)

        for pattern in patterns:
            for pattern_key, learning in self.learned_patterns.items():
                if pattern in pattern_key:
                    # Weight by confidence and success rate
                    score = learning.confidence * learning.success_rate
                    intent_scores[learning.correct_intent] += score

        if intent_scores:
            # Get the highest scoring intent
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            # Normalize confidence (0-1)
            confidence = min(1.0, best_intent[1] / len(patterns))
            return best_intent[0], confidence

        return None

    def get_intent_corrections(self, incorrect_intent: str) -> Dict[str, int]:
        """
        Get common corrections for an intent

        Args:
            incorrect_intent: The incorrectly detected intent

        Returns:
            Dictionary of correct intents and their frequencies
        """
        return dict(self.intent_corrections.get(incorrect_intent, {}))

    def _analyze_patterns(self):
        """
        Analyze patterns to find insights
        """
        # Remove old patterns (not seen in 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        self.learned_patterns = {
            k: v for k, v in self.learned_patterns.items()
            if v.last_seen > cutoff_date
        }

        # Find high-confidence patterns
        high_confidence = [
            p for p in self.learned_patterns.values()
            if p.confidence > 0.8 and p.occurrences > 5
        ]

        logger.info(f"High confidence patterns: {len(high_confidence)}")

    async def get_relevant_patterns(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant learned patterns for a query

        Args:
            query: User query to match patterns against
            limit: Maximum number of patterns to return

        Returns:
            List of relevant patterns with metadata
        """
        try:
            # Extract patterns from current query
            query_patterns = self._extract_patterns(query)

            # Find matching learned patterns
            relevant = []
            for pattern_key, learning in self.learned_patterns.items():
                # Check if any query pattern matches learned pattern
                for qp in query_patterns:
                    if qp.lower() in learning.pattern.lower() or learning.pattern.lower() in qp.lower():
                        relevant.append({
                            "pattern": learning.pattern,
                            "correct_intent": learning.correct_intent,
                            "confidence": learning.confidence,
                            "occurrences": learning.occurrences,
                            "success_rate": learning.success_rate
                        })
                        break

            # Sort by confidence * success_rate
            relevant.sort(key=lambda x: x["confidence"] * x["success_rate"], reverse=True)

            return relevant[:limit]

        except Exception as e:
            logger.error(f"Failed to get relevant patterns: {e}")
            return []

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get performance report

        Returns:
            Performance metrics and insights
        """
        report = {
            "metrics": self.performance_metrics,
            "pattern_count": len(self.learned_patterns),
            "high_confidence_patterns": len([
                p for p in self.learned_patterns.values()
                if p.confidence > 0.8
            ]),
            "recent_accuracy": self._calculate_recent_accuracy(),
            "top_corrections": self._get_top_corrections(),
            "improvement_trend": self._calculate_improvement_trend()
        }

        return report

    def _calculate_recent_accuracy(self, days: int = 7) -> float:
        """Calculate accuracy for recent period"""
        cutoff = datetime.now() - timedelta(days=days)
        recent = [
            e for e in self.feedback_entries
            if e.timestamp > cutoff
        ]

        if not recent:
            return self.performance_metrics["accuracy_rate"]

        positive = len([e for e in recent if e.feedback_type == "positive"])
        return positive / len(recent) if recent else 0.0

    def _get_top_corrections(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most common intent corrections"""
        corrections = []
        for incorrect, correct_map in self.intent_corrections.items():
            for correct, count in correct_map.items():
                corrections.append({
                    "incorrect": incorrect,
                    "correct": correct,
                    "count": count
                })

        # Sort by count and return top N
        corrections.sort(key=lambda x: x["count"], reverse=True)
        return corrections[:limit]

    def _calculate_improvement_trend(self) -> str:
        """Calculate improvement trend"""
        curve = self.performance_metrics["improvement_curve"]
        if len(curve) < 2:
            return "insufficient_data"

        # Compare first half to second half
        mid = len(curve) // 2
        first_half = np.mean([p["accuracy"] for p in curve[:mid]])
        second_half = np.mean([p["accuracy"] for p in curve[mid:]])

        improvement = second_half - first_half
        if improvement > 0.05:
            return "improving"
        elif improvement < -0.05:
            return "declining"
        else:
            return "stable"

    async def check_learned_clarifications(
        self,
        query: str,
        session_id: str
    ) -> Optional[str]:
        """
        Check se abbiamo già appreso cosa user intende con questa query ambigua

        Args:
            query: User query originale
            session_id: Session ID

        Returns:
            Clarification appresa se pattern forte (>= 2 occorrenze), altrimenti None
        """
        try:
            # Cerca pattern simili apprese precedentemente
            patterns = self._extract_patterns(query)

            for pattern in patterns:
                for pattern_key, learning in self.learned_patterns.items():
                    if pattern.lower() in learning.pattern.lower():
                        # Pattern forte: >= 2 occorrenze con confidence alta
                        if learning.occurrences >= 2 and learning.confidence > 0.7:
                            logger.info(
                                f"[LEARNING] Pattern forte trovato: '{query[:30]}...' → '{learning.correct_intent}' "
                                f"({learning.occurrences}x, conf: {learning.confidence:.2f})"
                            )
                            return learning.correct_intent

            return None

        except Exception as e:
            logger.error(f"[LEARNING] Error checking learned clarifications: {e}")
            return None

    async def record_clarification(
        self,
        original_query: str,
        clarification: str,
        session_id: str
    ):
        """
        Salva pattern di clarification per future learning

        Args:
            original_query: Query ambigua originale
            clarification: Risposta user con chiarimento
            session_id: Session ID
        """
        try:
            # Extract pattern dalla query originale
            patterns = self._extract_patterns(original_query)

            # Crea o aggiorna pattern appreso
            for pattern in patterns:
                pattern_key = f"{pattern}:clarification:{clarification}"

                if pattern_key not in self.learned_patterns:
                    self.learned_patterns[pattern_key] = PatternLearning(
                        pattern=pattern,
                        correct_intent=clarification,
                        confidence=0.6,  # Start moderate
                        occurrences=1,
                        last_seen=datetime.now(),
                        success_rate=0.7
                    )
                else:
                    learning = self.learned_patterns[pattern_key]
                    learning.occurrences += 1
                    learning.last_seen = datetime.now()
                    learning.confidence = min(1.0, learning.confidence + 0.1)
                    learning.success_rate = min(1.0, learning.success_rate + 0.05)

            logger.info(f"[LEARNING] Clarification pattern salvato: '{original_query[:30]}...' → '{clarification}'")

            # Save data
            self._save_data()

        except Exception as e:
            logger.error(f"[LEARNING] Error recording clarification: {e}")

    def export_training_data(self) -> Dict[str, Any]:
        """
        Export training data for fine-tuning

        Returns:
            Training data in format suitable for LLM fine-tuning
        """
        training_data = []

        # Convert positive feedback to training examples
        for entry in self.feedback_entries:
            if entry.feedback_type == "positive":
                training_data.append({
                    "input": entry.query,
                    "output": entry.intent,
                    "confidence": 1.0
                })
            elif entry.feedback_type == "correction" and entry.correction_data:
                correct_intent = entry.correction_data.get("correct_intent")
                if correct_intent:
                    training_data.append({
                        "input": entry.query,
                        "output": correct_intent,
                        "confidence": 0.9
                    })

        # Add high-confidence patterns
        for pattern_key, learning in self.learned_patterns.items():
            if learning.confidence > 0.8 and learning.occurrences > 3:
                training_data.append({
                    "pattern": learning.pattern,
                    "intent": learning.correct_intent,
                    "confidence": learning.confidence
                })

        return {
            "training_examples": training_data,
            "total_examples": len(training_data),
            "export_date": datetime.now().isoformat()
        }
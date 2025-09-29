"""
Smart LLM Router with ML Classification
Optimizes token usage by routing to the most cost-effective LLM
"""
import os
import re
import hashlib
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from langsmith import traceable

from .feature_extractor import QueryFeatureExtractor
from .router_audit import RouterAuditLogger

logger = logging.getLogger(__name__)

class ModelTier(Enum):
    """Model tiers for routing"""
    FREE_GROQ = "groq_free"
    FREE_GEMINI = "gemini_free"
    SPECIAL_NANO = "openai_nano"
    SPECIAL_MINI = "openai_mini"
    PREMIUM = "openai_premium"

@dataclass
class RouterConfig:
    """Configuration for Smart LLM Router"""
    groq_api_key: str
    openai_api_key: str
    google_api_key: str
    model_timeout: int = 10
    fallback_enabled: bool = True
    ml_confidence_threshold: float = 0.8
    cache_enabled: bool = True
    audit_enabled: bool = True

    @classmethod
    def from_env(cls) -> 'RouterConfig':
        """Create config from environment variables"""
        return cls(
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
            model_timeout=int(os.getenv("MODEL_TIMEOUT", "10")),
            fallback_enabled=os.getenv("FALLBACK_ENABLED", "true").lower() == "true",
            ml_confidence_threshold=float(os.getenv("ML_CONFIDENCE_THRESHOLD", "0.8")),
            cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            audit_enabled=os.getenv("AUDIT_ENABLED", "true").lower() == "true"
        )

@dataclass
class RoutingDecision:
    """Result of routing decision"""
    model_tier: ModelTier
    model_name: str
    confidence: float
    reasoning: str
    features: Dict[str, Any]
    estimated_tokens: int
    estimated_cost: float
    cached: bool = False

class SmartLLMRouter:
    """
    ML-based intelligent router for optimal LLM selection.
    Routes queries to the cheapest suitable model.
    """

    # Model configurations with limits and costs
    MODEL_CONFIGS = {
        ModelTier.FREE_GROQ: {
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "daily_limit": float('inf'),  # Unlimited
            "cost_per_1k": 0.0,
            "capabilities": ["general", "chat", "simple_queries"]
        },
        ModelTier.FREE_GEMINI: {
            "provider": "gemini",
            "model": "gemini-1.5-flash-8b",
            "daily_limit": 4_000_000,  # 4M tokens/min
            "cost_per_1k": 0.0,
            "capabilities": ["batch", "analysis", "multiple_items"]
        },
        ModelTier.SPECIAL_NANO: {
            "provider": "openai",
            "model": "gpt-4.1-nano",  # Hypothetical 10M token model
            "daily_limit": 10_000_000,
            "cost_per_1k": 0.0001,  # Minimal cost
            "capabilities": ["data_queries", "structured", "json"]
        },
        ModelTier.SPECIAL_MINI: {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "daily_limit": 10_000_000,
            "cost_per_1k": 0.00015,
            "capabilities": ["analysis", "complex", "reasoning"]
        },
        ModelTier.PREMIUM: {
            "provider": "openai",
            "model": "gpt-4o",
            "daily_limit": 1_000_000,
            "cost_per_1k": 0.005,
            "capabilities": ["critical", "creative", "expert"]
        }
    }

    def __init__(self, config: Optional[RouterConfig] = None):
        """Initialize router with configuration"""
        self.config = config or RouterConfig.from_env()
        self.feature_extractor = QueryFeatureExtractor()
        self.audit_logger = RouterAuditLogger() if self.config.audit_enabled else None

        # Initialize ML classifier
        self.classifier = None
        self.vectorizer = None
        self.scaler = None
        self._load_or_train_classifier()

        # Usage tracking
        self.daily_usage = {tier: 0 for tier in ModelTier}
        self.usage_date = datetime.now().date()

        # Model instances cache
        self._model_cache = {}

        logger.info("SmartLLMRouter initialized with ML classification")

    def _load_or_train_classifier(self):
        """Load pre-trained classifier or train a new one"""
        model_path = Path("models/router_classifier.pkl")
        vectorizer_path = Path("models/router_vectorizer.pkl")
        scaler_path = Path("models/router_scaler.pkl")

        if model_path.exists() and vectorizer_path.exists() and scaler_path.exists():
            try:
                self.classifier = joblib.load(model_path)
                self.vectorizer = joblib.load(vectorizer_path)
                self.scaler = joblib.load(scaler_path)
                logger.info("Loaded pre-trained router classifier")
                return
            except Exception as e:
                logger.warning(f"Failed to load classifier: {e}")

        # Train new classifier with synthetic data
        self._train_classifier()

    def _train_classifier(self):
        """Train classifier with synthetic training data"""
        # Generate synthetic training data
        training_data = self._generate_training_data()

        # Extract features
        texts = [d["query"] for d in training_data]
        labels = [d["tier"].value for d in training_data]

        # Vectorize text
        self.vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
        text_features = self.vectorizer.fit_transform(texts)

        # Extract additional features
        additional_features = []
        for query in texts:
            features = self.feature_extractor.extract(query)
            additional_features.append([
                features["length"],
                features["word_count"],
                features["has_greeting"],
                features["has_question"],
                features["has_technical_terms"],
                features["complexity_score"]
            ])

        # Combine features
        additional_features = np.array(additional_features)
        self.scaler = StandardScaler()
        additional_features_scaled = self.scaler.fit_transform(additional_features)

        combined_features = np.hstack([
            text_features.toarray(),
            additional_features_scaled
        ])

        # Train classifier
        self.classifier = LogisticRegression(
            multi_class='multinomial',
            solver='lbfgs',
            max_iter=1000,
            random_state=42
        )
        self.classifier.fit(combined_features, labels)

        # Save models
        os.makedirs("models", exist_ok=True)
        joblib.dump(self.classifier, "models/router_classifier.pkl")
        joblib.dump(self.vectorizer, "models/router_vectorizer.pkl")
        joblib.dump(self.scaler, "models/router_scaler.pkl")

        logger.info("Trained and saved new router classifier")

    def _generate_training_data(self) -> List[Dict]:
        """Generate synthetic training data for classifier"""
        return [
            # FREE_GROQ - Simple greetings and status
            {"query": "Ciao", "tier": ModelTier.FREE_GROQ},
            {"query": "Come stai?", "tier": ModelTier.FREE_GROQ},
            {"query": "Buongiorno", "tier": ModelTier.FREE_GROQ},
            {"query": "Stato sistema", "tier": ModelTier.FREE_GROQ},
            {"query": "Tutto ok?", "tier": ModelTier.FREE_GROQ},

            # FREE_GEMINI - Batch operations
            {"query": "Elenca tutti i processi attivi", "tier": ModelTier.FREE_GEMINI},
            {"query": "Mostra lista completa elaborazioni", "tier": ModelTier.FREE_GEMINI},
            {"query": "Riassumi tutte le attività di oggi", "tier": ModelTier.FREE_GEMINI},

            # SPECIAL_NANO - Data queries with "messaggio"
            {"query": "Ultimo messaggio del workflow", "tier": ModelTier.SPECIAL_NANO},
            {"query": "Mostra messaggio errore", "tier": ModelTier.SPECIAL_NANO},
            {"query": "Qual è il messaggio ricevuto?", "tier": ModelTier.SPECIAL_NANO},

            # SPECIAL_MINI - Complex analysis
            {"query": "Analizza performance ultimi 7 giorni", "tier": ModelTier.SPECIAL_MINI},
            {"query": "Confronta metriche con settimana scorsa", "tier": ModelTier.SPECIAL_MINI},
            {"query": "Identifica anomalie nei processi", "tier": ModelTier.SPECIAL_MINI},

            # PREMIUM - Critical operations
            {"query": "Genera report dettagliato per il CEO", "tier": ModelTier.PREMIUM},
            {"query": "Analisi predittiva sui ricavi", "tier": ModelTier.PREMIUM},
            {"query": "Ottimizza strategia aziendale", "tier": ModelTier.PREMIUM},
        ]

    @traceable(name="RouterDecision")
    async def route(self, query: str, force_tier: Optional[ModelTier] = None) -> RoutingDecision:
        """
        Route query to optimal model based on ML classification

        Args:
            query: User query to route
            force_tier: Optional tier to force (for testing)

        Returns:
            RoutingDecision with selected model and reasoning
        """
        # Reset daily usage if new day
        if datetime.now().date() != self.usage_date:
            self.daily_usage = {tier: 0 for tier in ModelTier}
            self.usage_date = datetime.now().date()

        # Extract features
        features = self.feature_extractor.extract(query)

        # Force tier if specified
        if force_tier:
            return self._create_decision(force_tier, 1.0, "Forced tier", features, query)

        # Check cache first
        if self.config.cache_enabled:
            cache_key = hashlib.md5(query.encode()).hexdigest()
            # TODO: Implement cache lookup

        # ML classification
        try:
            # Prepare features for classifier
            text_features = self.vectorizer.transform([query])
            additional_features = np.array([[
                features["length"],
                features["word_count"],
                features["has_greeting"],
                features["has_question"],
                features["has_technical_terms"],
                features["complexity_score"]
            ]])
            additional_features_scaled = self.scaler.transform(additional_features)

            combined_features = np.hstack([
                text_features.toarray(),
                additional_features_scaled
            ])

            # Predict with confidence
            prediction_proba = self.classifier.predict_proba(combined_features)[0]
            predicted_class = self.classifier.classes_[np.argmax(prediction_proba)]
            confidence = float(np.max(prediction_proba))

            # Use ML prediction if confident
            if confidence >= self.config.ml_confidence_threshold:
                tier = ModelTier(predicted_class)
                reasoning = f"ML Classification (confidence: {confidence:.2%})"
            else:
                # Fallback to rule-based
                tier = self._rule_based_routing(query, features)
                reasoning = f"Rule-based (ML confidence too low: {confidence:.2%})"

        except Exception as e:
            logger.warning(f"ML classification failed: {e}")
            tier = self._rule_based_routing(query, features)
            reasoning = "Fallback to rule-based (ML error)"
            confidence = 0.5

        decision = self._create_decision(tier, confidence, reasoning, features, query)

        # Audit logging
        if self.audit_logger:
            await self.audit_logger.log_decision(decision, query)

        # Update usage
        self.daily_usage[tier] += decision.estimated_tokens

        return decision

    def _rule_based_routing(self, query: str, features: Dict) -> ModelTier:
        """Fallback rule-based routing"""
        query_lower = query.lower()

        # Simple greetings -> FREE
        if features["has_greeting"] or (features["word_count"] < 5 and not features["has_technical_terms"]):
            return ModelTier.FREE_GROQ

        # Contains "messaggio" -> SPECIAL_NANO
        if "messaggio" in query_lower:
            return ModelTier.SPECIAL_NANO

        # Batch operations -> FREE_GEMINI
        if any(word in query_lower for word in ["tutti", "lista", "elenca", "batch"]):
            return ModelTier.FREE_GEMINI

        # Complex analysis -> SPECIAL_MINI
        if features["complexity_score"] > 0.7 or features["word_count"] > 20:
            return ModelTier.SPECIAL_MINI

        # Default to SPECIAL_MINI
        return ModelTier.SPECIAL_MINI

    def _create_decision(
        self,
        tier: ModelTier,
        confidence: float,
        reasoning: str,
        features: Dict,
        query: str
    ) -> RoutingDecision:
        """Create routing decision"""
        config = self.MODEL_CONFIGS[tier]

        # Estimate tokens (rough approximation)
        estimated_tokens = len(query.split()) * 2  # Input + output estimation
        estimated_cost = (estimated_tokens / 1000) * config["cost_per_1k"]

        return RoutingDecision(
            model_tier=tier,
            model_name=config["model"],
            confidence=confidence,
            reasoning=reasoning,
            features=features,
            estimated_tokens=estimated_tokens,
            estimated_cost=estimated_cost,
            cached=False
        )

    def get_model(self, tier: ModelTier) -> BaseChatModel:
        """Get LLM instance for tier"""
        if tier in self._model_cache:
            return self._model_cache[tier]

        config = self.MODEL_CONFIGS[tier]

        if config["provider"] == "groq":
            model = ChatGroq(
                model=config["model"],
                api_key=self.config.groq_api_key,
                temperature=0.1,
                timeout=self.config.model_timeout
            )
        elif config["provider"] == "gemini":
            model = ChatGoogleGenerativeAI(
                model=config["model"],
                google_api_key=self.config.google_api_key,
                temperature=0.1,
                timeout=self.config.model_timeout
            )
        elif config["provider"] == "openai":
            model = ChatOpenAI(
                model=config["model"],
                api_key=self.config.openai_api_key,
                temperature=0.1,
                timeout=self.config.model_timeout
            )
        else:
            raise ValueError(f"Unknown provider: {config['provider']}")

        self._model_cache[tier] = model
        return model

    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        total_tokens = sum(self.daily_usage.values())
        total_cost = sum(
            tokens / 1000 * self.MODEL_CONFIGS[tier]["cost_per_1k"]
            for tier, tokens in self.daily_usage.items()
        )

        return {
            "date": str(self.usage_date),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "by_tier": {
                tier.value: {
                    "tokens": tokens,
                    "cost": tokens / 1000 * self.MODEL_CONFIGS[tier]["cost_per_1k"],
                    "percentage": (tokens / total_tokens * 100) if total_tokens > 0 else 0
                }
                for tier, tokens in self.daily_usage.items()
            },
            "savings_percentage": self._calculate_savings()
        }

    def _calculate_savings(self) -> float:
        """Calculate savings vs using premium model for everything"""
        actual_cost = sum(
            tokens / 1000 * self.MODEL_CONFIGS[tier]["cost_per_1k"]
            for tier, tokens in self.daily_usage.items()
        )

        premium_cost = sum(self.daily_usage.values()) / 1000 * self.MODEL_CONFIGS[ModelTier.PREMIUM]["cost_per_1k"]

        if premium_cost > 0:
            return (1 - actual_cost / premium_cost) * 100
        return 0.0
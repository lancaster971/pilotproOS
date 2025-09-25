"""
Milhena Multi-Agent Orchestrator ENTERPRISE - Sistema Intelligente PilotProOS
Versione enterprise con persistenza, retry logic, e API REST
"""

from crewai import Agent, Task, Crew, Process
from typing import Dict, Any, Optional, List, Literal, Tuple
import logging
import json
import re
import os
import time
import hashlib
import asyncio
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from functools import lru_cache
from collections import deque
from dotenv import load_dotenv

# Import esterni opzionali
try:
    from langdetect import detect as detect_language
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# CARICA API KEYS SUBITO!
load_dotenv()

# Import tools
from tools.milhena_data_tools import PilotProMetricsTool, WorkflowAnalyzerTool
from model_selector import ModelSelector, ModelCategory

# Import sia Groq che Gemini per configurazione ibrida
try:
    from groq_fast_client import groq_classify, groq_fast_response
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq non disponibile, userò solo Gemini")

try:
    from gemini_fast_client import GeminiFastClient, HybridModelRouter
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Gemini non disponibile")

# Directory per persistenza
PERSISTENCE_DIR = Path("milhena_persistence")
PERSISTENCE_DIR.mkdir(exist_ok=True)

# Configura logging avanzato con file output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PERSISTENCE_DIR / 'milhena_analytics.log')
    ]
)
logger = logging.getLogger(__name__)

QuestionType = Literal["GREETING", "BUSINESS_DATA", "TECHNOLOGY_INQUIRY", "HELP", "ANALYSIS", "GENERAL"]
Language = Literal["it", "en", "fr", "es", "de"]

# ============= PERSISTENT MEMORY SYSTEM =============
class PersistentConversationMemory:
    """Sistema di memoria persistente con salvataggio su disco"""

    def __init__(self, max_size: int = 10, user_id: Optional[str] = None):
        self.max_size = max_size
        self.user_id = user_id or "default"
        self.memory_file = PERSISTENCE_DIR / f"memory_{self.user_id}.json"
        self.profile_file = PERSISTENCE_DIR / f"profile_{self.user_id}.json"

        # Carica memoria esistente o inizializza
        self.memory: deque = self._load_memory()
        self.user_profile: Dict[str, Any] = self._load_profile()

        logger.info(f"📚 Loaded memory for user {self.user_id}: {len(self.memory)} interactions")

    def _load_memory(self) -> deque:
        """Carica memoria da disco"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    return deque(data, maxlen=self.max_size)
            except Exception as e:
                logger.error(f"Error loading memory: {e}")
        return deque(maxlen=self.max_size)

    def _load_profile(self) -> Dict[str, Any]:
        """Carica profilo utente da disco"""
        if self.profile_file.exists():
            try:
                with open(self.profile_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading profile: {e}")
        return {
            "created_at": datetime.now().isoformat(),
            "interactions_count": 0,
            "preferences": {}
        }

    def _save_memory(self):
        """Salva memoria su disco"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(list(self.memory), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")

    def _save_profile(self):
        """Salva profilo su disco"""
        try:
            with open(self.profile_file, 'w') as f:
                json.dump(self.user_profile, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving profile: {e}")

    def add_interaction(self, question: str, response: str, metadata: Dict):
        """Aggiungi interazione e persisti"""
        self.memory.append({
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "response": response[:200],  # Limita per risparmio spazio
            "type": metadata.get("question_type"),
            "language": metadata.get("language", "it"),
            "confidence": metadata.get("confidence", 0)
        })

        # Aggiorna profilo
        self.user_profile["interactions_count"] += 1
        self.user_profile["last_interaction"] = datetime.now().isoformat()
        self.user_profile["preferred_language"] = metadata.get("language", "it")

        # Salva su disco
        self._save_memory()
        self._save_profile()

    def get_context(self) -> str:
        """Ottieni contesto dalle interazioni precedenti"""
        if not self.memory:
            return "Prima interazione"

        recent = list(self.memory)[-3:]  # Ultime 3 interazioni
        context = "Conversazioni recenti:\n"
        for interaction in recent:
            context += f"- {interaction['question'][:50]}... ({interaction['type']})\n"

        # Aggiungi info profilo
        if self.user_profile.get("interactions_count", 0) > 5:
            context += f"\nUtente frequente con {self.user_profile['interactions_count']} interazioni totali."

        return context

    def remember_user(self, key: str, value: Any):
        """Ricorda informazioni sull'utente e persisti"""
        if "preferences" not in self.user_profile:
            self.user_profile["preferences"] = {}
        self.user_profile["preferences"][key] = value
        self._save_profile()

    def is_returning_user(self) -> bool:
        """Controlla se è un utente che ritorna"""
        return len(self.memory) > 0 or self.user_profile.get("interactions_count", 0) > 0

    def clear_old_interactions(self, days: int = 30):
        """Rimuovi interazioni più vecchie di N giorni"""
        cutoff = datetime.now() - timedelta(days=days)
        self.memory = deque([
            i for i in self.memory
            if datetime.fromisoformat(i['timestamp']) > cutoff
        ], maxlen=self.max_size)
        self._save_memory()

# ============= ENHANCED ANALYTICS WITH PERSISTENCE =============
class PersistentAnalyticsTracker:
    """Sistema di analytics con persistenza su disco"""

    def __init__(self):
        self.metrics_file = PERSISTENCE_DIR / "milhena_metrics.jsonl"
        self.stats_file = PERSISTENCE_DIR / "milhena_stats.json"
        self.daily_stats_file = PERSISTENCE_DIR / f"daily_stats_{datetime.now().date()}.json"

        # Carica statistiche aggregate
        self.stats = self._load_stats()

    def _load_stats(self) -> Dict[str, Any]:
        """Carica statistiche da disco"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        return {
            "total_requests": 0,
            "question_types_count": {},
            "languages_detected": {},
            "total_response_time_ms": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors_count": 0,
            "daily_stats": {}
        }

    def _save_stats(self):
        """Salva statistiche su disco"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")

    def track_request(self,
                     question: str,
                     question_type: str,
                     response_time: float,
                     agents_used: List[str],
                     language: str,
                     confidence: float,
                     cache_hit: bool = False,
                     error: Optional[str] = None):
        """Traccia metriche con persistenza"""

        metric = {
            "timestamp": datetime.now().isoformat(),
            "date": str(datetime.now().date()),
            "hour": datetime.now().hour,
            "question_length": len(question),
            "question_type": question_type,
            "response_time_ms": response_time * 1000,
            "agents_count": len(agents_used),
            "agents": agents_used,
            "language": language,
            "confidence": confidence,
            "cache_hit": cache_hit,
            "error": error,
            "day_of_week": datetime.now().weekday()
        }

        # Salva metrica su file JSONL
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(metric) + "\n")

        # Aggiorna statistiche aggregate
        self.stats["total_requests"] += 1
        self.stats["question_types_count"][question_type] = \
            self.stats["question_types_count"].get(question_type, 0) + 1
        self.stats["languages_detected"][language] = \
            self.stats["languages_detected"].get(language, 0) + 1
        self.stats["total_response_time_ms"] += response_time * 1000

        if cache_hit:
            self.stats["cache_hits"] += 1
        else:
            self.stats["cache_misses"] += 1

        if error:
            self.stats["errors_count"] += 1

        # Aggiorna statistiche giornaliere
        today = str(datetime.now().date())
        if today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][today] = {
                "requests": 0,
                "avg_response_time_ms": 0,
                "errors": 0
            }

        daily = self.stats["daily_stats"][today]
        daily["requests"] += 1
        daily["avg_response_time_ms"] = \
            (daily["avg_response_time_ms"] * (daily["requests"] - 1) + response_time * 1000) / daily["requests"]
        if error:
            daily["errors"] += 1

        # Salva statistiche
        self._save_stats()

        # Log
        logger.info(f"📊 Tracked: {question_type} in {response_time*1000:.2f}ms (cache:{cache_hit})")

    def get_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche complete"""
        total = self.stats["total_requests"]
        if total == 0:
            return self.stats

        return {
            **self.stats,
            "avg_response_time_ms": self.stats["total_response_time_ms"] / total,
            "cache_hit_rate": self.stats["cache_hits"] / (self.stats["cache_hits"] + self.stats["cache_misses"] + 0.001),
            "error_rate": self.stats["errors_count"] / total,
            "top_question_types": sorted(
                self.stats["question_types_count"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
        }

# ============= ENHANCED CACHE WITH PERSISTENCE =============
class PersistentResponseCache:
    """Cache persistente con serializzazione su disco"""

    def __init__(self, ttl_seconds: int = 3600):
        self.cache_file = PERSISTENCE_DIR / "response_cache.pkl"
        self.ttl = timedelta(seconds=ttl_seconds)
        self.cache = self._load_cache()
        self.hit_count = 0
        self.miss_count = 0

    def _load_cache(self) -> Dict[str, Tuple[str, datetime]]:
        """Carica cache da disco"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    cache = pickle.load(f)
                    # Pulisci entries scadute
                    now = datetime.now()
                    return {
                        k: v for k, v in cache.items()
                        if now - v[1] < self.ttl
                    }
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
        return {}

    def _save_cache(self):
        """Salva cache su disco"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def _generate_key(self, question: str, question_type: str, language: str) -> str:
        """Genera chiave univoca per cache"""
        normalized = question.lower().strip()
        key_string = f"{question_type}:{language}:{normalized}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, question: str, question_type: str, language: str) -> Optional[str]:
        """Recupera risposta dalla cache se valida"""
        key = self._generate_key(question, question_type, language)

        if key in self.cache:
            response, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                self.hit_count += 1
                logger.info(f"💾 Cache HIT for: {question[:30]}...")
                return response
            else:
                # Entry scaduta
                del self.cache[key]
                self._save_cache()

        self.miss_count += 1
        return None

    def set(self, question: str, question_type: str, language: str, response: str):
        """Salva risposta in cache e persisti"""
        # Cache solo domande semplici e ripetitive
        if question_type in ["GREETING", "HELP", "GENERAL"]:
            key = self._generate_key(question, question_type, language)
            self.cache[key] = (response, datetime.now())
            self._save_cache()
            logger.info(f"💾 Cached response for: {question[:30]}...")

    def clear_expired(self):
        """Rimuovi entries scadute"""
        now = datetime.now()
        original_size = len(self.cache)
        self.cache = {
            k: v for k, v in self.cache.items()
            if now - v[1] < self.ttl
        }
        if len(self.cache) < original_size:
            self._save_cache()
            logger.info(f"🧹 Cleared {original_size - len(self.cache)} expired cache entries")

# ============= RETRY LOGIC DECORATOR =============
def retry_on_failure(max_attempts: int = 3, delay_seconds: float = 1.0):
    """Decorator per retry automatico su failure"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"⚠️ Attempt {attempt + 1}/{max_attempts} failed: {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay_seconds * (attempt + 1))  # Backoff esponenziale
                    else:
                        logger.error(f"❌ All {max_attempts} attempts failed")
            raise last_exception
        return wrapper
    return decorator

# ============= MAIN ORCHESTRATOR CLASS =============
class MilhenaEnterpriseOrchestrator:
    """
    Sistema Multi-Agent Milhena ENTERPRISE con tutte le features production-ready

    Features:
    - 🧠 Memory persistente su disco
    - 📊 Analytics con statistiche persistenti
    - 🌍 Multi-lingua con auto-detect
    - 💾 Caching persistente
    - 🎯 Confidence-based routing
    - ⚡ Parallelizzazione task
    - 🔔 Webhook notifications
    - 🔁 Retry logic automatico
    - 💿 Persistenza completa su disco
    """

    def __init__(self,
                 model_selector: Optional[ModelSelector] = None,
                 enable_memory: bool = True,
                 enable_analytics: bool = True,
                 enable_cache: bool = True,
                 enable_webhooks: bool = False,
                 webhook_urls: Optional[Dict[str, str]] = None,
                 fast_mode: bool = True):

        self.model_selector = model_selector or ModelSelector()
        self.tools = [
            PilotProMetricsTool(),
            WorkflowAnalyzerTool()
        ]

        # Inizializza router ibrido Gemini+Groq se disponibile
        self.hybrid_router = None
        if GEMINI_AVAILABLE or GROQ_AVAILABLE:
            try:
                if GEMINI_AVAILABLE:
                    self.hybrid_router = HybridModelRouter()
                    logger.info("✅ Router ibrido Gemini+Groq inizializzato")
                else:
                    logger.info("⚡ Solo Groq disponibile, no hybrid routing")
            except Exception as e:
                logger.error(f"Errore inizializzazione router: {e}")

        # Sistemi persistenti
        self.memory_store: Dict[str, PersistentConversationMemory] = {}
        self.analytics = PersistentAnalyticsTracker() if enable_analytics else None
        self.cache = PersistentResponseCache() if enable_cache else None
        self.enable_memory = enable_memory
        self.fast_mode = fast_mode  # Skip classification for speed

        # Cleanup periodico cache
        if self.cache:
            asyncio.create_task(self._periodic_cache_cleanup())

        logger.info("🚀 Milhena Enterprise Orchestrator initialized")
        logger.info(f"   📁 Persistence directory: {PERSISTENCE_DIR}")

    def get_or_create_memory(self, user_id: str) -> Optional[PersistentConversationMemory]:
        """Ottieni o crea memoria per utente specifico"""
        if not self.enable_memory:
            return None

        if user_id not in self.memory_store:
            self.memory_store[user_id] = PersistentConversationMemory(user_id=user_id)

        return self.memory_store[user_id]

    async def _periodic_cache_cleanup(self):
        """Task periodico per pulizia cache"""
        while True:
            await asyncio.sleep(3600)  # Ogni ora
            if self.cache:
                self.cache.clear_expired()

    def detect_user_language(self, text: str) -> str:
        """Rileva lingua del testo"""
        if not LANGDETECT_AVAILABLE:
            return "it"

        try:
            lang = detect_language(text)
            if lang in ["it", "en", "fr", "es", "de"]:
                return lang
            return "en"
        except:
            return "it"

    def create_question_analyzer_agent(self, language: str = "it") -> Agent:
        """QUESTION_ANALYZER multilingua"""
        # GROQ SUPER VELOCE!
        provider, model = self.model_selector.get_model(ModelCategory.GRATIS)

        return Agent(
            role=f"Question Analyzer ({language})",
            goal=f"Classify questions in {language}",
            backstory=f"I analyze and classify questions in {language}",
            verbose=False,
            allow_delegation=False,
            llm="groq/llama-3.3-70b-versatile"  # GROQ diretto!
        )

    def create_milhena_conversation_agent(self, language: str, memory_context: str = "") -> Agent:
        """MILHENA conversation con memoria"""
        # USA GROQ - VELOCISSIMO E GRATIS!
        provider, model = self.model_selector.get_model(ModelCategory.GRATIS)

        backstory = f"""I'm Milhena, your business assistant in {language}.
        {memory_context}
        I help with business processes and analytics."""

        return Agent(
            role=f"Milhena Assistant ({language})",
            goal=f"Provide helpful responses in {language}",
            backstory=backstory,
            verbose=False,
            allow_delegation=False,
            llm="groq/llama-3.3-70b-versatile"  # GROQ VELOCISSIMO!
        )

    def create_data_analyst_agent(self) -> Agent:
        """DATA_ANALYST standard"""
        provider, model = self.model_selector.get_model(ModelCategory.POTENTE)
        return Agent(
            role="Data Analyst",
            goal="Retrieve accurate business data",
            backstory="I collect and analyze business data efficiently.",
            verbose=False,
            allow_delegation=False,
            llm="groq/llama-3.3-70b-versatile"  # GROQ per velocità!
        )

    def create_security_filter_agent(self) -> Agent:
        """SECURITY_FILTER standard"""
        provider, model = self.model_selector.get_model(ModelCategory.GRATIS)
        return Agent(
            role="Security Filter",
            goal="Filter sensitive information",
            backstory="I protect sensitive technical details.",
            verbose=False,
            allow_delegation=False,
            llm="groq/llama-3.3-70b-versatile"  # GROQ!
        )

    def create_business_analyzer_agent(self) -> Agent:
        """BUSINESS_ANALYZER per analisi"""
        provider, model = self.model_selector.get_model(ModelCategory.POTENTE)
        return Agent(
            role="Business Analyst",
            goal="Provide strategic insights",
            backstory="I analyze patterns and trends.",
            verbose=False,
            allow_delegation=False,
            llm="groq/llama-3.3-70b-versatile"  # GROQ!
        )

    def create_coordinator_agent(self, language: str) -> Agent:
        """COORDINATOR finale"""
        provider, model = self.model_selector.get_model(ModelCategory.LEGGERO)
        return Agent(
            role=f"Coordinator ({language})",
            goal=f"Coordinate final response in {language}",
            backstory=f"I coordinate and finalize responses in {language}.",
            verbose=False,
            allow_delegation=False,
            llm="groq/llama-3.3-70b-versatile"  # GROQ!
        )

    @retry_on_failure(max_attempts=3, delay_seconds=1.0)
    async def _execute_crew_with_retry(self, crew: Crew) -> str:
        """Esegue crew con retry automatico"""
        result = crew.kickoff()
        return str(result)

    async def analyze_question_enterprise(self,
                                         question: str,
                                         context: Optional[str] = None,
                                         user_id: str = "default") -> Dict[str, Any]:
        """
        Analisi enterprise con persistenza e retry logic

        Args:
            question: Domanda dell'utente
            context: Contesto aggiuntivo
            user_id: ID utente per personalizzazione

        Returns:
            Risposta completa con metriche
        """

        start_time = time.time()
        error_msg = None

        try:
            # 1. LANGUAGE DETECTION
            language = self.detect_user_language(question)
            logger.info(f"🌍 Language: {language}, User: {user_id}")

            # 2. MEMORY CONTEXT
            memory = self.get_or_create_memory(user_id)
            memory_context = ""
            if memory:
                memory_context = memory.get_context()
                if memory.is_returning_user():
                    logger.info(f"👤 Returning user: {user_id}")

            # 3. CACHE CHECK AGGRESSIVO - PRIMA DI TUTTO!
            if self.cache:
                # Check cache SENZA classificazione per velocità massima
                for qtype in ["GREETING", "HELP", "BUSINESS_DATA", "ANALYSIS", "GENERAL"]:
                    cached_response = self.cache.get(question, qtype, language)
                    if cached_response:
                        response_time = time.time() - start_time

                        # Track cache hit
                        if self.analytics:
                            self.analytics.track_request(
                                question=question,
                                question_type=qtype,
                                response_time=response_time,
                                agents_used=["CACHE"],
                                language=language,
                                confidence=1.0,
                                cache_hit=True
                            )

                        logger.info(f"⚡ CACHE HIT! Response in {response_time*1000:.0f}ms")
                        return {
                            "success": True,
                            "response": cached_response,
                            "cached": True,
                            "question_type": qtype,
                            "language": language,
                            "confidence": 1.0,
                            "response_time_ms": response_time * 1000,
                            "user_id": user_id
                        }

            # 4. ULTRA FAST MODE: Router ibrido Gemini+Groq per classificazione
            if self.fast_mode:
                # Usa il router ibrido per massima affidabilità
                if hasattr(self, 'hybrid_router'):
                    logger.info("🚀 HYBRID: Classificazione con router Gemini+Groq...")
                    classification = await self.hybrid_router.classify_with_best_model(question)
                elif GROQ_AVAILABLE:
                    logger.info("⚡ ULTRA FAST: Classificazione diretta Groq...")
                    classification = await groq_classify(question)
                else:
                    # Fallback manuale se nessun LLM disponibile
                    classification = {"question_type": "GENERAL", "confidence": 0.5}
                    logger.warning("⚠️ Nessun LLM veloce disponibile, using fallback")

                question_type = classification.get("question_type", "GENERAL")
                confidence = classification.get("confidence", 0.9)
                logger.info(f"⚡ Classificato come {question_type} in {classification.get('response_time_ms', 0):.0f}ms")

                # FAST PATH per GREETING, GENERAL, HELP
                if question_type in ["GREETING", "GENERAL", "HELP"]:
                    logger.info(f"⚡ FAST PATH: Risposta veloce per {question_type}")

                    # Usa router ibrido per risposta ottimale
                    if hasattr(self, 'hybrid_router'):
                        response = await self.hybrid_router.generate_response(
                            question=question,
                            question_type=question_type,
                            use_fast=True
                        )
                    elif GROQ_AVAILABLE:
                        response = await groq_fast_response(
                            question=question,
                            question_type=question_type,
                            language=language
                        )
                    else:
                        # Fallback response
                        response = self._get_fallback_response(question_type, language)

                    # Update cache
                    if self.cache:
                        self.cache.set(question, question_type, language, response)

                    # Update memory
                    if memory:
                        memory.add_interaction(
                            question=question,
                            response=response,
                            metadata={
                                "question_type": question_type,
                                "language": language,
                                "confidence": confidence,
                                "fast_path": True
                            }
                        )

                    # Track analytics
                    response_time = time.time() - start_time
                    if self.analytics:
                        self.analytics.track_request(
                            question=question,
                            question_type=question_type,
                            response_time=response_time,
                            agents_used=["GROQ_FAST_PATH"],
                            language=language,
                            confidence=confidence,
                            cache_hit=False
                        )

                    logger.info(f"✅ FastPath completato in {response_time*1000:.0f}ms TOTALI!")

                    return {
                        "success": True,
                        "response": response,
                        "cached": False,
                        "question_type": question_type,
                        "language": language,
                        "confidence": confidence,
                        "response_time_ms": response_time * 1000,
                        "user_id": user_id,
                        "fast_path": True
                    }

                # Per BUSINESS_DATA e ANALYSIS, continua con CrewAI
                logger.info(f"📊 Tipo {question_type} richiede CrewAI flow completo")

            else:
                # SLOW MODE: Full classification
                question_analyzer = self.create_question_analyzer_agent(language)

                analysis_task = Task(
                    description=f"Classify this question: {question}",
                    agent=question_analyzer,
                    expected_output="JSON classification"
                )

                analysis_crew = Crew(
                    agents=[question_analyzer],
                    tasks=[analysis_task],
                    verbose=False
                )

                # Execute with retry
                analysis_result = await self._execute_crew_with_retry(analysis_crew)

                # Parse classification
                classification = self._parse_classification(analysis_result)
                question_type = classification.get("question_type", "GENERAL")
                confidence = classification.get("confidence", 0.5)

                # 5. CONFIDENCE ROUTING
                if confidence < 0.6:
                    logger.warning(f"⚠️ Low confidence ({confidence:.2f}), routing to GENERAL")
                    question_type = "GENERAL"

            # 6. EXECUTE BY TYPE
            response = await self._execute_by_type_with_retry(
                question_type=question_type,
                question=question,
                context=context or memory_context,
                language=language,
                memory_context=memory_context
            )

            # 7. UPDATE CACHE
            if self.cache:
                self.cache.set(question, question_type, language, response)

            # 8. UPDATE MEMORY
            if memory:
                memory.add_interaction(
                    question=question,
                    response=response,
                    metadata={
                        "question_type": question_type,
                        "language": language,
                        "confidence": confidence
                    }
                )

            # 9. TRACK ANALYTICS
            response_time = time.time() - start_time
            if self.analytics:
                self.analytics.track_request(
                    question=question,
                    question_type=question_type,
                    response_time=response_time,
                    agents_used=self._get_agents_for_type(question_type),
                    language=language,
                    confidence=confidence,
                    cache_hit=False,
                    error=None
                )

            return {
                "success": True,
                "response": response,
                "question_type": question_type,
                "language": language,
                "confidence": confidence,
                "cached": False,
                "response_time_ms": response_time * 1000,
                "user_id": user_id,
                "memory_interactions": len(memory.memory) if memory else 0
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error: {error_msg}")

            # Track error
            if self.analytics:
                self.analytics.track_request(
                    question=question,
                    question_type="ERROR",
                    response_time=time.time() - start_time,
                    agents_used=[],
                    language="unknown",
                    confidence=0,
                    cache_hit=False,
                    error=error_msg
                )

            return {
                "success": False,
                "error": error_msg,
                "fallback_response": "Mi dispiace, si è verificato un errore. Riprova tra poco.",
                "user_id": user_id
            }

    async def _execute_by_type_with_retry(self,
                                         question_type: str,
                                         question: str,
                                         context: str,
                                         language: str,
                                         memory_context: str) -> str:
        """Esegue crew basata sul tipo con retry logic"""

        if question_type == "GREETING":
            agent = self.create_milhena_conversation_agent(language, memory_context)
            task = Task(
                description=f"Respond to: {question}",
                agent=agent,
                expected_output="Friendly response"
            )
            crew = Crew(agents=[agent], tasks=[task], verbose=False)

        elif question_type == "BUSINESS_DATA":
            data_analyst = self.create_data_analyst_agent()
            security_filter = self.create_security_filter_agent()
            coordinator = self.create_coordinator_agent(language)

            tasks = [
                Task(
                    description=f"Collect data for: {question}",
                    agent=data_analyst,
                    tools=self.tools,
                    expected_output="Data"
                ),
                Task(
                    description="Filter sensitive info",
                    agent=security_filter,
                    expected_output="Filtered data"
                ),
                Task(
                    description="Create final response",
                    agent=coordinator,
                    expected_output="Response"
                )
            ]

            crew = Crew(
                agents=[data_analyst, security_filter, coordinator],
                tasks=tasks,
                verbose=False
            )

        elif question_type == "ANALYSIS":
            # Parallel execution for analysis
            data_analyst = self.create_data_analyst_agent()
            business_analyzer = self.create_business_analyzer_agent()
            security_filter = self.create_security_filter_agent()
            coordinator = self.create_coordinator_agent(language)

            tasks = [
                Task(
                    description=f"Collect data: {question}",
                    agent=data_analyst,
                    tools=self.tools,
                    expected_output="Data"
                ),
                Task(
                    description=f"Analyze: {question}",
                    agent=business_analyzer,
                    tools=self.tools,
                    expected_output="Analysis"
                ),
                Task(
                    description="Filter sensitive",
                    agent=security_filter,
                    expected_output="Filtered"
                ),
                Task(
                    description="Final response",
                    agent=coordinator,
                    expected_output="Response"
                )
            ]

            crew = Crew(
                agents=[data_analyst, business_analyzer, security_filter, coordinator],
                tasks=tasks,
                process=Process.hierarchical,  # Enable parallelization
                verbose=False
            )
            logger.info("⚡ Running ANALYSIS with parallel tasks")

        else:  # GENERAL, HELP, etc.
            agent = self.create_milhena_conversation_agent(language, memory_context)
            task = Task(
                description=f"Answer: {question}",
                agent=agent,
                expected_output="Helpful response"
            )
            crew = Crew(agents=[agent], tasks=[task], verbose=False)

        # Execute with retry
        return await self._execute_crew_with_retry(crew)

    def _quick_classify(self, question: str) -> str:
        """Quick classification for caching"""
        q_lower = question.lower()

        if any(w in q_lower for w in ["ciao", "hello", "buongiorno"]):
            return "GREETING"
        elif any(w in q_lower for w in ["aiuto", "help", "cosa puoi"]):
            return "HELP"
        elif any(w in q_lower for w in ["dati", "metriche", "quant"]):
            return "BUSINESS_DATA"
        elif any(w in q_lower for w in ["analizza", "analyze", "trend"]):
            return "ANALYSIS"
        return "GENERAL"

    def _parse_classification(self, result: str) -> Dict:
        """Parse classification safely"""
        try:
            text = str(result).strip()
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                import re
                match = re.search(r'\{.*?\}', text, re.DOTALL)
                if match:
                    return json.loads(match.group())
        except:
            pass
        return {"question_type": "GENERAL", "confidence": 0.5}

    def _get_fallback_response(self, question_type: str, language: str) -> str:
        """Risposte di fallback quando nessun LLM disponibile"""
        fallbacks = {
            "it": {
                "GREETING": "Ciao! Come posso aiutarti oggi?",
                "HELP": "Sono Milhena, il tuo assistente AI. Posso aiutarti con analisi dati, automazione processi e supporto decisionale.",
                "GENERAL": "Sto elaborando la tua richiesta. Per favore riprova tra poco.",
                "BUSINESS_DATA": "Al momento non posso accedere ai dati. Riprova più tardi.",
                "ANALYSIS": "L'analisi richiesta non è disponibile al momento."
            },
            "en": {
                "GREETING": "Hello! How can I help you today?",
                "HELP": "I'm Milhena, your AI assistant. I can help with data analysis, process automation and decision support.",
                "GENERAL": "Processing your request. Please try again shortly.",
                "BUSINESS_DATA": "Cannot access data at the moment. Please try again later.",
                "ANALYSIS": "The requested analysis is not available right now."
            }
        }

        lang = language if language in fallbacks else "it"
        return fallbacks[lang].get(question_type, fallbacks[lang]["GENERAL"])

    def _get_agents_for_type(self, q_type: str) -> List[str]:
        """Get agent list by type"""
        return {
            "GREETING": ["CONVERSATION"],
            "HELP": ["CONVERSATION"],
            "BUSINESS_DATA": ["DATA", "SECURITY", "COORDINATOR"],
            "ANALYSIS": ["DATA", "ANALYZER", "SECURITY", "COORDINATOR"],
            "GENERAL": ["CONVERSATION"]
        }.get(q_type, ["CONVERSATION"])

    def get_system_stats(self) -> Dict[str, Any]:
        """Get complete system statistics"""
        stats = {
            "persistence_dir": str(PERSISTENCE_DIR),
            "users_tracked": len(self.memory_store),
            "analytics": self.analytics.get_stats() if self.analytics else None,
            "cache": {
                "size": len(self.cache.cache) if self.cache else 0,
                "hit_rate": self.cache.hit_count / max(self.cache.hit_count + self.cache.miss_count, 1)
                           if self.cache else 0
            }
        }
        return stats


# ============= USAGE EXAMPLE =============
if __name__ == "__main__":
    import asyncio

    async def test_enterprise():
        # Initialize enterprise orchestrator
        orchestrator = MilhenaEnterpriseOrchestrator(
            enable_memory=True,
            enable_analytics=True,
            enable_cache=True
        )

        # Test with specific user
        result = await orchestrator.analyze_question_enterprise(
            question="Ciao! Quali sono le performance di oggi?",
            user_id="user_test_123"
        )

        print(f"Response: {result['response'][:100]}...")
        print(f"Stats: {orchestrator.get_system_stats()}")

    asyncio.run(test_enterprise())
"""
TechnicalMaskingEngine - Sistema enterprise per mascheramento termini tecnici
CRITICO: Mai esporre architettura sottostante
"""
from typing import Dict, Any, List
import re
import json
import logging

logger = logging.getLogger(__name__)

class TechnicalMaskingEngine:
    """
    Sistema enterprise per mascheramento termini tecnici
    CRITICO: Mai esporre architettura sottostante
    """

    def __init__(self):
        self.load_mappings()
        self.compile_patterns()

    def load_mappings(self):
        """Carica dizionari di traduzione"""
        self.mappings = {
            # Workflow → Business Process
            "workflow_terms": {
                "workflow": "processo",
                "workflows": "processi",
                "node": "passaggio",
                "nodes": "passaggi",
                "execution": "elaborazione",
                "executions": "elaborazioni",
                "trigger": "avvio",
                "webhook": "ricezione dati"
            },

            # Technical → Generic
            "tech_terms": {
                "n8n": "sistema",
                "postgresql": "archivio dati",
                "postgres": "archivio dati",
                "mysql": "archivio dati",
                "database": "archivio dati",
                "docker": "ambiente",
                "container": "ambiente",
                "kubernetes": "infrastruttura",
                "redis": "memoria veloce",
                "nginx": "gateway",
                "api": "interfaccia",
                "rest": "protocollo",
                "http": "comunicazione",
                "json": "formato dati"
            },

            # Error codes → Human messages
            "error_translations": {
                "ECONNREFUSED": "Connessione temporaneamente non disponibile",
                "ETIMEDOUT": "Tempo di risposta eccessivo",
                "404": "Risorsa non trovata",
                "500": "Errore interno del sistema",
                "503": "Servizio temporaneamente non disponibile",
                "ENOTFOUND": "Destinazione non raggiungibile",
                "EPIPE": "Interruzione della comunicazione",
                "OOM": "Risorse di sistema insufficienti"
            }
        }

    def compile_patterns(self):
        """Compila regex patterns per performance"""
        self.patterns = []

        # Pattern per termini tecnici
        for term in self.mappings["tech_terms"].keys():
            pattern = re.compile(
                r'\b' + re.escape(term) + r'\b',
                re.IGNORECASE
            )
            self.patterns.append((pattern, term))

    def mask(self, text: str) -> str:
        """
        Maschera tutti i termini tecnici nel testo

        Input: "Il workflow su PostgreSQL ha 5 nodes"
        Output: "Il processo su archivio dati ha 5 passaggi"
        """
        masked = text

        # Apply mappings
        for mapping_type, terms in self.mappings.items():
            for original, replacement in terms.items():
                # Case-insensitive replacement
                pattern = re.compile(re.escape(original), re.IGNORECASE)
                masked = pattern.sub(replacement, masked)

        # Remove any remaining technical artifacts
        masked = self._remove_technical_artifacts(masked)

        return masked

    def _remove_technical_artifacts(self, text: str) -> str:
        """Rimuove pattern tecnici residui"""

        # Remove IDs (UUID, hash, etc)
        text = re.sub(
            r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b',
            'identificativo',
            text,
            flags=re.IGNORECASE
        )

        # Remove technical file extensions
        text = re.sub(
            r'\.(json|xml|yaml|yml|sql|js|ts|py|java|go|rs)\b',
            '',
            text,
            flags=re.IGNORECASE
        )

        # Remove IP addresses
        text = re.sub(
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'indirizzo di rete',
            text
        )

        # Remove ports
        text = re.sub(
            r':(\d{2,5})\b',
            '',
            text
        )

        return text

    def mask_json(self, data: Dict) -> Dict:
        """
        Maschera ricorsivamente strutture JSON
        """
        if isinstance(data, dict):
            return {
                self.mask(k) if isinstance(k, str) else k:
                self.mask_json(v) if isinstance(v, (dict, list))
                else self.mask(v) if isinstance(v, str) else v
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self.mask_json(item) for item in data]
        elif isinstance(data, str):
            return self.mask(data)
        else:
            return data


class ResponseSanitizer:
    """
    Validazione finale prima di inviare al cliente
    """

    def __init__(self, masking_engine: TechnicalMaskingEngine):
        self.masker = masking_engine
        self.forbidden_terms = self._load_forbidden_terms()

    def _load_forbidden_terms(self) -> List[str]:
        """Termini che NON devono MAI apparire"""
        return [
            "n8n", "workflow", "node", "webhook", "postgres",
            "postgresql", "mysql", "docker", "kubernetes",
            "redis", "nginx", "localhost", "127.0.0.1",
            "error:", "exception", "stack trace", "undefined",
            "null", "none", "npm", "pip", "git"
        ]

    def sanitize(self, response: str) -> str:
        """
        Sanitizzazione finale con multiple pass
        """
        # Pass 1: Masking standard
        sanitized = self.masker.mask(response)

        # Pass 2: Check forbidden terms
        for term in self.forbidden_terms:
            if term.lower() in sanitized.lower():
                # Log per audit
                logger.warning(f"Forbidden term detected: {term}")

                # Replace con generic
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                sanitized = pattern.sub("[informazione protetta]", sanitized)

        # Pass 3: Final validation
        if self._contains_technical_info(sanitized):
            # Fallback to safe response
            return "Informazione elaborata correttamente. Per dettagli contatta il supporto."

        return sanitized

    def _contains_technical_info(self, text: str) -> bool:
        """
        Check finale per leak tecnici
        """
        technical_patterns = [
            r'\b\d+\.\d+\.\d+\.\d+\b',  # IP addresses
            r':[0-9]{2,5}\b',            # Ports
            r'\b[A-Z_]+ERROR\b',         # Error codes
            r'\/[a-z]+\/[a-z]+',         # Unix paths
            r'[A-Z]:\\',                 # Windows paths
        ]

        for pattern in technical_patterns:
            if re.search(pattern, text):
                return True

        return False


# ============================================================================
# BUSINESS TERMINOLOGY PARSER (LangChain Output Parser Pattern)
# ============================================================================

class BusinessTerminologyParser:
    """
    LangChain-compatible Output Parser per sostituire termini tecnici con business-friendly

    Best Practice (LangChain): Output Parser per validazione e trasformazione response
    Questo è il LIVELLO 2 del masking (dopo System Prompt, prima del Regex Final)

    Usage:
        parser = BusinessTerminologyParser()
        clean_response = parser.parse(llm_response)
    """

    # Dizionario completo termini tecnici → business
    TERMINOLOGY_MAP = {
        # ============ N8N WORKFLOW AUTOMATION ============
        "workflow": "processo",
        "workflows": "processi",
        "node": "passaggio",
        "nodes": "passaggi",
        "execution": "esecuzione",
        "executions": "esecuzioni",
        "trigger": "avvio automatico",
        "triggers": "avvii automatici",
        "webhook": "punto di integrazione",
        "webhooks": "punti di integrazione",
        "credential": "credenziale",
        "credentials": "credenziali",
        "connection": "collegamento",
        "connections": "collegamenti",
        "schedule": "programmazione",
        "cron": "programmazione automatica",
        "manual trigger": "avvio manuale",

        # ============ AI/LANGCHAIN ============
        "LLM": "sistema AI",
        "large language model": "sistema AI",
        "agent": "assistente intelligente",
        "agents": "assistenti intelligenti",
        "RAG": "base di conoscenza",
        "retrieval augmented generation": "ricerca documentazione",
        "embedding": "indicizzazione",
        "embeddings": "indicizzazione",
        "vector database": "archivio ricercabile",
        "prompt": "istruzione",
        "prompts": "istruzioni",
        "chain": "elaborazione",
        "langchain": "sistema elaborazione",
        "tool": "strumento",
        "tools": "strumenti",
        "checkpoint": "salvataggio stato",
        "checkpointer": "memoria conversazione",
        "supervisor": "coordinatore",
        "ReAct": "sistema decisionale",

        # ============ DATABASE/INFRASTRUCTURE ============
        "PostgreSQL": "database",
        "Postgres": "database",
        "MySQL": "database",
        "Redis": "cache",
        "ChromaDB": "archivio documenti",
        "Docker": "piattaforma",
        "container": "servizio",
        "containers": "servizi",
        "Kubernetes": "orchestratore",
        "nginx": "gateway",
        "API": "interfaccia",
        "REST API": "interfaccia dati",
        "endpoint": "punto di accesso",
        "endpoints": "punti di accesso",
        "JSON": "dati strutturati",
        "SQL": "linguaggio dati",
        "schema": "struttura dati",

        # ============ STATUS/OPERATIONS ============
        "queue": "coda elaborazione",
        "log": "registro",
        "logs": "registri",
        "debug": "diagnostica",
        "timeout": "tempo scaduto",
        "retry": "nuovo tentativo",
        "retries": "nuovi tentativi",

        # ============ TECHNICAL PATTERNS ============
        "microservice": "componente",
        "microservices": "componenti",
        "backend": "sistema interno",
        "frontend": "interfaccia utente",
        "middleware": "livello intermedio",
        "deployment": "rilascio",
        "deploy": "rilascia",
    }

    def __init__(self):
        """Initialize parser and compile regex patterns"""
        self.patterns = self._compile_patterns()
        logger.info(f"BusinessTerminologyParser initialized with {len(self.TERMINOLOGY_MAP)} term mappings")

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """
        Compila pattern regex per ogni termine (case-insensitive, word boundaries)
        Best Practice: Pre-compile per performance
        """
        patterns = {}
        for tech_term, business_term in self.TERMINOLOGY_MAP.items():
            # Use word boundaries to avoid partial matches
            # \b ensures we match whole words only
            pattern = re.compile(
                r'\b' + re.escape(tech_term) + r'\b',
                re.IGNORECASE
            )
            patterns[tech_term] = (pattern, business_term)

        return patterns

    def parse(self, text: str) -> str:
        """
        Sostituisce tutti i termini tecnici con equivalenti business

        Args:
            text: Testo da processare (response LLM)

        Returns:
            Testo pulito con terminologia business
        """
        if not text:
            return text

        result = text
        replacements_made = []

        # Apply all substitutions
        for tech_term, (pattern, business_term) in self.patterns.items():
            # Count occurrences for logging
            matches = pattern.findall(result)
            if matches:
                result = pattern.sub(business_term, result)
                replacements_made.append(f"{tech_term}→{business_term} ({len(matches)}x)")

        # Log replacements if any
        if replacements_made:
            logger.info(f"[TERMINOLOGY] Replaced: {', '.join(replacements_made)}")

        return result

    def validate(self, text: str) -> tuple[bool, List[str]]:
        """
        Valida se il testo contiene termini tecnici vietati

        Args:
            text: Testo da validare

        Returns:
            (is_clean, list_of_violations)
        """
        violations = []

        for tech_term, (pattern, _) in self.patterns.items():
            if pattern.search(text):
                violations.append(tech_term)

        is_clean = len(violations) == 0
        return is_clean, violations

    @property
    def _type(self) -> str:
        """LangChain compatibility"""
        return "business_terminology"
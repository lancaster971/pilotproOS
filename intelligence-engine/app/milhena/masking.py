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
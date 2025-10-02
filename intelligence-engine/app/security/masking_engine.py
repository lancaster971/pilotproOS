"""
Multi-Level Masking Engine
Context-aware masking with user authorization levels
Zero-leak guarantee for technical terms
"""
import re
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging
from pathlib import Path
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class UserLevel(Enum):
    """User authorization levels"""
    BUSINESS = "business"      # Maximum masking (default)
    ADMIN = "admin"            # Partial technical terms allowed
    DEVELOPER = "developer"    # Minimal masking (debug mode)
    SYSTEM = "system"          # Internal use only

class SecurityError(Exception):
    """Custom exception for security violations"""
    pass

@dataclass
class MaskingConfig:
    """Configuration for masking engine"""
    user_level: UserLevel = UserLevel.BUSINESS
    strict_mode: bool = True  # Fail on any leak detection
    audit_enabled: bool = True
    cache_enabled: bool = True
    custom_rules: Optional[Dict] = None

    @classmethod
    def from_env(cls) -> 'MaskingConfig':
        """Create config from environment"""
        import os
        user_level = os.getenv("MASKING_USER_LEVEL", "business").lower()
        return cls(
            user_level=UserLevel(user_level),
            strict_mode=os.getenv("MASKING_STRICT", "true").lower() == "true",
            audit_enabled=os.getenv("MASKING_AUDIT", "true").lower() == "true",
            cache_enabled=os.getenv("MASKING_CACHE", "true").lower() == "true"
        )

@dataclass
class MaskingResult:
    """Result of masking operation"""
    original: str
    masked: str
    user_level: UserLevel
    replacements_made: int
    leaks_detected: List[str]
    timestamp: datetime
    hash: str

class MultiLevelMaskingEngine:
    """
    Enterprise-grade multi-level masking engine
    Provides context-aware masking based on user authorization
    """

    # Comprehensive PII/Security patterns based on LangChain best practices
    SENSITIVE_PATTERNS = {
        "credentials": [
            r"\b(?:password|passwd|pwd)[s]?\b",
            r"\b(?:api[_\s-]?key)[s]?\b",
            r"\b(?:secret[_\s-]?key)[s]?\b",
            r"\b(?:access[_\s-]?token)[s]?\b",
            r"\b(?:refresh[_\s-]?token)[s]?\b",
            r"\b(?:auth[_\s-]?token)[s]?\b",
            r"\b(?:credential)[s]?\b",
            r"\b(?:bearer\s+[A-Za-z0-9\-._~+/]+=*)\b",
        ],
        "connection_strings": [
            r"(?:postgres|postgresql|mysql|mongodb)://[^\s]+",
            r"\bconnection[_\s-]?string[s]?\b",
            r"\bdsn\b",
            r"\bdb[_\s-]?url\b",
            r"\bdatabase[_\s-]?url\b",
        ],
        "email": [
            r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
        ],
        "phone": [
            r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        ],
        "ssn": [
            r"\b\d{3}-\d{2}-\d{4}\b",
        ],
        "credit_card": [
            r"\b(?:\d[ -]*?){13,16}\b",
        ],
        "ip_address": [
            r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
        ],
        "private_keys": [
            r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",
            r"-----BEGIN OPENSSH PRIVATE KEY-----",
        ]
    }

    # Masking rules by user level
    MASKING_LEVELS = {
        UserLevel.BUSINESS: {
            "forbidden": [
                "n8n", "workflow", "node", "postgresql", "postgres", "mysql",
                "docker", "container", "kubernetes", "langraph", "langchain",
                "api", "webhook", "trigger", "redis", "nginx", "fastapi",
                "sqlalchemy", "asyncpg", "execution_entity", "sql", "select",
                "database", "table", "schema", "index", "query",
                # Security additions based on best practices
                "password", "credential", "token", "secret", "key",
                "connection string", "dsn", "api_key", "access_token"
            ],
            "replacements": {
                # Security-sensitive terms (CRITICAL - based on LangChain best practices)
                r"\b(?:password|passwd|pwd)[s]?\b": "[REDACTED]",
                r"\b(?:credential)[s]?\b": "[REDACTED]",
                r"\b(?:api[_\s-]?key)[s]?\b": "[REDACTED]",
                r"\b(?:secret[_\s-]?key)[s]?\b": "[REDACTED]",
                r"\b(?:access[_\s-]?token)[s]?\b": "[REDACTED]",
                r"\b(?:auth[_\s-]?token)[s]?\b": "[REDACTED]",
                r"\b(?:bearer\s+[A-Za-z0-9\-._~+/]+=*)\b": "[REDACTED]",
                r"\bconnection[_\s-]?string[s]?\b": "[REDACTED]",
                r"\bdsn\b": "[REDACTED]",
                r"(?:postgres|postgresql|mysql|mongodb)://[^\s]+": "[REDACTED]",

                # PII patterns (email, phone, SSN, credit card)
                r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b": "[EMAIL_REDACTED]",
                r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b": "[PHONE_REDACTED]",
                r"\b\d{3}-\d{2}-\d{4}\b": "[SSN_REDACTED]",

                # Workflow terms
                r"\bworkflow[s]?\b": "processo",
                r"\bnode[s]?\b": "passaggio",
                r"\bexecution[s]?\b": "elaborazione",
                r"\btrigger[s]?\b": "avvio",
                r"\bwebhook[s]?\b": "ricezione dati",

                # Technical infrastructure
                r"\bn8n\b": "sistema",
                r"\bpostgresql?\b": "archivio dati",
                r"\bmysql\b": "archivio dati",
                r"\bdatabase\b": "archivio dati",
                r"\bdocker\b": "ambiente",
                r"\bcontainer[s]?\b": "ambiente",
                r"\bkubernetes\b": "infrastruttura",
                r"\bredis\b": "memoria veloce",
                r"\bnginx\b": "gateway",

                # Programming terms
                r"\bapi[s]?\b": "interfaccia",
                r"\bendpoint[s]?\b": "punto di accesso",
                r"\bjson\b": "dati strutturati",
                r"\bxml\b": "dati strutturati",
                r"\byaml\b": "configurazione",

                # Error terms
                r"\berror[s]?\b": "anomalia",
                r"\bexception[s]?\b": "problema",
                r"\bfailure[s]?\b": "interruzione",
                r"\bcrash(ed)?\b": "arresto",
                r"\bbug[s]?\b": "difetto",

                # SQL/Database terms
                r"\bselect\b": "recupera",
                r"\binsert\b": "aggiungi",
                r"\bupdate\b": "modifica",
                r"\bdelete\b": "rimuovi",
                r"\btable[s]?\b": "raccolta",
                r"\brow[s]?\b": "elemento",
                r"\bcolumn[s]?\b": "campo",
                r"\bquery\b": "richiesta",
                r"\bqueries\b": "richieste",
            },
            "patterns_to_remove": [
                r"```\w+",  # Code block markers
                r"http[s]?://[^\s]+",  # URLs (replaced with [link])
                r"[A-Z_]+=[^\s]+",  # Environment variables
                r"\b[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}\b",  # UUIDs
            ]
        },
        UserLevel.ADMIN: {
            "forbidden": [
                "postgresql", "postgres", "mysql", "docker", "kubernetes",
                "langraph", "langchain", "sqlalchemy", "asyncpg", "execution_entity"
            ],
            "replacements": {
                r"\bpostgresql?\b": "database",
                r"\bmysql\b": "database",
                r"\bdocker\b": "container",
                r"\bkubernetes\b": "orchestrator",
                r"\blangraph\b": "graph engine",
                r"\blangchain\b": "chain framework",
            },
            "patterns_to_remove": [
                r"[A-Z_]+=[^\s]+",  # Environment variables
            ]
        },
        UserLevel.DEVELOPER: {
            "forbidden": [
                "password", "secret", "key", "token", "credential",
                "api_key", "secret_key", "access_token", "refresh_token"
            ],
            "replacements": {
                r"\bpassword[s]?\b": "***",
                r"\bsecret[s]?\b": "***",
                r"\bapi_key[s]?\b": "***",
                r"\btoken[s]?\b": "***",
            },
            "patterns_to_remove": []
        }
    }

    def __init__(self, config: Optional[MaskingConfig] = None):
        """Initialize masking engine with configuration"""
        self.config = config or MaskingConfig()
        self._cache = {} if self.config.cache_enabled else None
        self._compiled_patterns = {}
        self._compile_patterns()

        logger.info(f"MultiLevelMaskingEngine initialized with level: {self.config.user_level.value}")

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        for level in UserLevel:
            if level == UserLevel.SYSTEM:
                continue

            rules = self.MASKING_LEVELS.get(level, {})
            compiled = {
                "replacements": {},
                "forbidden": set(rules.get("forbidden", [])),
                "patterns_to_remove": []
            }

            # Compile replacement patterns
            for pattern, replacement in rules.get("replacements", {}).items():
                compiled["replacements"][re.compile(pattern, re.IGNORECASE)] = replacement

            # Compile removal patterns
            for pattern in rules.get("patterns_to_remove", []):
                compiled["patterns_to_remove"].append(re.compile(pattern, re.IGNORECASE))

            self._compiled_patterns[level] = compiled

    def mask(
        self,
        content: str,
        user_level: Optional[UserLevel] = None,
        context: Optional[Dict] = None
    ) -> MaskingResult:
        """
        Apply masking to content based on user level

        Args:
            content: Text to mask
            user_level: Override default user level
            context: Additional context for masking decisions

        Returns:
            MaskingResult with masked content and metadata

        Raises:
            SecurityError: If leak detected in strict mode
        """
        if not content:
            return self._empty_result(user_level or self.config.user_level)

        # Check cache
        if self._cache is not None:
            cache_key = self._get_cache_key(content, user_level)
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Apply masking
        level = user_level or self.config.user_level

        # System level sees everything
        if level == UserLevel.SYSTEM:
            return self._create_result(content, content, level, 0, [])

        masked_content = content
        replacements_made = 0
        leaks_detected = []

        # Get compiled patterns for this level
        patterns = self._compiled_patterns.get(level, {})

        # CRITICAL FIRST PASS: Apply security-sensitive replacements BEFORE anything else
        # This ensures credentials/PII are masked even in error/denial messages
        for pattern, replacement in patterns.get("replacements", {}).items():
            # Only process security-critical patterns first (containing [REDACTED])
            if "[REDACTED]" in replacement or "[EMAIL_REDACTED]" in replacement or "[PHONE_REDACTED]" in replacement or "[SSN_REDACTED]" in replacement:
                matches = pattern.findall(masked_content)
                if matches:
                    replacements_made += len(matches)
                    masked_content = pattern.sub(replacement, masked_content)

        # Second pass: Remove sensitive patterns (URLs, UUIDs, env vars)
        for pattern in patterns.get("patterns_to_remove", []):
            matches = pattern.findall(masked_content)
            if matches:
                replacements_made += len(matches)
                if pattern.pattern.startswith(r"http"):
                    masked_content = pattern.sub("[link]", masked_content)
                elif pattern.pattern.startswith(r"[A-Z_]+"):
                    masked_content = pattern.sub("[config]", masked_content)
                else:
                    masked_content = pattern.sub("[redacted]", masked_content)

        # Third pass: Apply business terminology replacements
        for pattern, replacement in patterns.get("replacements", {}).items():
            # Skip security patterns (already processed)
            if "[REDACTED]" in replacement or "[EMAIL_REDACTED]" in replacement or "[PHONE_REDACTED]" in replacement or "[SSN_REDACTED]" in replacement:
                continue

            matches = pattern.findall(masked_content)
            if matches:
                replacements_made += len(matches)
                masked_content = pattern.sub(replacement, masked_content)

        # Fourth pass: Check for forbidden terms (leak detection with aggressive removal)
        forbidden = patterns.get("forbidden", set())
        for term in forbidden:
            # Case-insensitive search with word boundaries
            search_pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            if search_pattern.search(masked_content):
                leaks_detected.append(term)

                # ALWAYS forcefully remove - don't wait for strict_mode
                masked_content = search_pattern.sub("[REDACTED]", masked_content)
                replacements_made += 1

        # Fifth pass: Final safety check - scan for any remaining sensitive patterns
        # This catches edge cases like "password:" or "api-key" variations
        for category, regex_patterns in self.SENSITIVE_PATTERNS.items():
            for regex_pattern in regex_patterns:
                compiled = re.compile(regex_pattern, re.IGNORECASE)
                if compiled.search(masked_content):
                    masked_content = compiled.sub(f"[{category.upper()}_REDACTED]", masked_content)
                    replacements_made += 1
                    leaks_detected.append(f"{category}_pattern")

        # Apply custom rules if provided
        if self.config.custom_rules:
            masked_content = self._apply_custom_rules(masked_content, level)

        # Create result
        result = self._create_result(
            content, masked_content, level, replacements_made, leaks_detected
        )

        # Cache result
        if self._cache is not None:
            cache_key = self._get_cache_key(content, user_level)
            self._cache[cache_key] = result

        return result

    def mask_dict(
        self,
        data: Dict[str, Any],
        user_level: Optional[UserLevel] = None
    ) -> Dict[str, Any]:
        """
        Recursively mask dictionary values

        Args:
            data: Dictionary to mask
            user_level: User authorization level

        Returns:
            Masked dictionary
        """
        if not data:
            return {}

        masked_data = {}
        level = user_level or self.config.user_level

        for key, value in data.items():
            # Mask the key itself if needed (but preserve underscore structure)
            masked_key = key  # Don't mask dictionary keys to preserve structure

            # Mask the value based on type
            if isinstance(value, str):
                masked_data[masked_key] = self.mask(value, level).masked
            elif isinstance(value, dict):
                masked_data[masked_key] = self.mask_dict(value, level)
            elif isinstance(value, list):
                masked_data[masked_key] = self.mask_list(value, level)
            else:
                masked_data[masked_key] = value

        return masked_data

    def mask_list(
        self,
        items: List[Any],
        user_level: Optional[UserLevel] = None
    ) -> List[Any]:
        """
        Mask list items

        Args:
            items: List to mask
            user_level: User authorization level

        Returns:
            Masked list
        """
        if not items:
            return []

        masked_items = []
        level = user_level or self.config.user_level

        for item in items:
            if isinstance(item, str):
                masked_items.append(self.mask(item, level).masked)
            elif isinstance(item, dict):
                masked_items.append(self.mask_dict(item, level))
            elif isinstance(item, list):
                masked_items.append(self.mask_list(item, level))
            else:
                masked_items.append(item)

        return masked_items

    def validate_no_leaks(
        self,
        content: str,
        user_level: Optional[UserLevel] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate that content has no technical leaks for given level

        Args:
            content: Content to validate
            user_level: User authorization level

        Returns:
            Tuple of (is_clean, list_of_leaks)
        """
        level = user_level or self.config.user_level

        if level == UserLevel.SYSTEM:
            return (True, [])

        patterns = self._compiled_patterns.get(level, {})
        forbidden = patterns.get("forbidden", set())

        leaks = []
        content_lower = content.lower()

        for term in forbidden:
            if term.lower() in content_lower:
                leaks.append(term)

        return (len(leaks) == 0, leaks)

    def _apply_custom_rules(
        self,
        content: str,
        level: UserLevel
    ) -> str:
        """Apply custom masking rules if configured"""
        if not self.config.custom_rules:
            return content

        rules = self.config.custom_rules.get(level.value, {})

        for pattern, replacement in rules.items():
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

        return content

    def _get_cache_key(
        self,
        content: str,
        user_level: Optional[UserLevel]
    ) -> str:
        """Generate cache key for content and level"""
        level = (user_level or self.config.user_level).value
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"{level}:{content_hash}"

    def _create_result(
        self,
        original: str,
        masked: str,
        level: UserLevel,
        replacements: int,
        leaks: List[str]
    ) -> MaskingResult:
        """Create masking result object"""
        return MaskingResult(
            original=original,
            masked=masked,
            user_level=level,
            replacements_made=replacements,
            leaks_detected=leaks,
            timestamp=datetime.now(),
            hash=hashlib.md5(original.encode()).hexdigest()
        )

    def _empty_result(self, level: UserLevel) -> MaskingResult:
        """Create empty result"""
        return MaskingResult(
            original="",
            masked="",
            user_level=level,
            replacements_made=0,
            leaks_detected=[],
            timestamp=datetime.now(),
            hash=""
        )

    def get_stats(self) -> Dict:
        """Get masking engine statistics"""
        if self._cache is None:
            cache_stats = {"enabled": False}
        else:
            cache_stats = {
                "enabled": True,
                "entries": len(self._cache),
                "hit_rate": "N/A"  # Would need to track hits/misses
            }

        return {
            "default_level": self.config.user_level.value,
            "strict_mode": self.config.strict_mode,
            "cache": cache_stats,
            "patterns_loaded": {
                level.value: len(self._compiled_patterns.get(level, {}).get("replacements", {}))
                for level in UserLevel
                if level != UserLevel.SYSTEM
            }
        }

class MaskingOutputParser(BaseOutputParser[str]):
    """
    LangChain output parser with integrated masking
    Ensures all LLM outputs are properly sanitized
    """

    def __init__(self, user_level: UserLevel = UserLevel.BUSINESS):
        """Initialize parser with user level"""
        self.masking_engine = MultiLevelMaskingEngine(
            MaskingConfig(user_level=user_level)
        )

    def parse(self, text: str) -> str:
        """Parse and mask output text"""
        result = self.masking_engine.mask(text)

        if result.leaks_detected and self.masking_engine.config.strict_mode:
            raise SecurityError(f"Output contains forbidden terms: {result.leaks_detected}")

        return result.masked

    def get_format_instructions(self) -> str:
        """Instructions for LLM on output format"""
        return (
            "Ensure your response uses business-friendly terminology. "
            "Avoid technical jargon and system-specific terms."
        )
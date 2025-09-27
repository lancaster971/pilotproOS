"""
Simple Audit Logger - Direct JSON File Writing (NO MOCKS!)
============================================================
Direct file writing for audit logs - no complex libraries
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class AuditEventType(Enum):
    """Types of audit events"""
    CLASSIFICATION = "CLASSIFICATION"
    DB_QUERY = "DB_QUERY"
    VALIDATION = "VALIDATION"
    MASKING = "MASKING"
    CACHE_HIT = "CACHE_HIT"
    CACHE_MISS = "CACHE_MISS"
    LLM_CALL = "LLM_CALL"
    LLM_FALLBACK = "LLM_FALLBACK"
    ERROR = "ERROR"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"


class SimpleAuditLogger:
    """Simple audit logger that writes directly to JSON file"""

    def __init__(self, log_file: str = "logs/audit.jsonl"):
        """Initialize with log file path"""
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _write_event(self, event: Dict[str, Any]) -> None:
        """Write event to file"""
        # Add timestamp
        event["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Write to file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + "\n")

    def log_classification(self, query: str, category: str, confidence: float) -> None:
        """Log classification event"""
        self._write_event({
            "event_type": AuditEventType.CLASSIFICATION.value,
            "query": query[:100],  # Truncate
            "category": category,
            "confidence": confidence
        })

    def log_validation(self, text: str, result: str, issues: int) -> None:
        """Log validation event"""
        self._write_event({
            "event_type": AuditEventType.VALIDATION.value,
            "text_preview": text[:100],
            "result": result,
            "issues": issues
        })

    def log_masking(self, text: str, terms_replaced: int) -> None:
        """Log masking event"""
        self._write_event({
            "event_type": AuditEventType.MASKING.value,
            "text_preview": text[:50],
            "terms_replaced": terms_replaced
        })

    def log_error(self, error_type: str, message: str) -> None:
        """Log error event"""
        self._write_event({
            "event_type": AuditEventType.ERROR.value,
            "error_type": error_type,
            "message": message
        })

    def get_events(self, limit: int = 100) -> List[Dict]:
        """Read recent events from file"""
        if not self.log_file.exists():
            return []

        events = []
        with open(self.log_file, 'r') as f:
            lines = f.readlines()

        for line in lines[-limit:]:
            try:
                events.append(json.loads(line))
            except:
                pass

        return events
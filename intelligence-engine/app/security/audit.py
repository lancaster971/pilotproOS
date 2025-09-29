"""
Security Audit Log
Tracks all security-related events and violations
"""
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import aiofiles

logger = logging.getLogger(__name__)

class SecurityAuditLog:
    """
    Comprehensive security audit logging
    """

    def __init__(self, log_dir: str = "logs/security"):
        """Initialize audit logger"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Current log file (rotated daily)
        self.current_date = datetime.now().date()
        self.log_file = self._get_log_file()

        # Buffer for batch writing
        self.buffer = []
        self.buffer_size = 10
        self.lock = asyncio.Lock()

    def _get_log_file(self) -> Path:
        """Get current log file path"""
        date_str = self.current_date.strftime("%Y%m%d")
        return self.log_dir / f"security_audit_{date_str}.jsonl"

    async def log_masking_event(
        self,
        user_level: str,
        original_length: int,
        masked_length: int,
        replacements: int,
        leaks_detected: List[str],
        user_id: Optional[str] = None
    ):
        """Log masking operation"""
        await self._log_event({
            "type": "masking",
            "user_level": user_level,
            "original_length": original_length,
            "masked_length": masked_length,
            "replacements": replacements,
            "leaks_detected": leaks_detected,
            "user_id": user_id
        })

    async def log_security_violation(
        self,
        violation_type: str,
        details: str,
        user_id: Optional[str] = None,
        severity: str = "medium"
    ):
        """Log security violation"""
        await self._log_event({
            "type": "violation",
            "violation_type": violation_type,
            "details": details,
            "user_id": user_id,
            "severity": severity
        })

    async def log_validation_failure(
        self,
        validation_type: str,
        issues: List[str],
        data_preview: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Log validation failure"""
        await self._log_event({
            "type": "validation_failure",
            "validation_type": validation_type,
            "issues": issues,
            "data_preview": data_preview[:100] if data_preview else None,
            "user_id": user_id
        })

    async def log_sanitization(
        self,
        data_type: str,
        original_size: int,
        sanitized_size: int,
        patterns_removed: int,
        user_id: Optional[str] = None
    ):
        """Log data sanitization"""
        await self._log_event({
            "type": "sanitization",
            "data_type": data_type,
            "original_size": original_size,
            "sanitized_size": sanitized_size,
            "patterns_removed": patterns_removed,
            "user_id": user_id
        })

    async def log_access_attempt(
        self,
        resource: str,
        user_level: str,
        allowed: bool,
        reason: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Log access attempt"""
        await self._log_event({
            "type": "access_attempt",
            "resource": resource,
            "user_level": user_level,
            "allowed": allowed,
            "reason": reason,
            "user_id": user_id
        })

    async def _log_event(self, event: Dict[str, Any]):
        """Log security event"""
        # Check if we need to rotate log file
        if datetime.now().date() != self.current_date:
            await self._rotate_log_file()

        # Add timestamp
        event["timestamp"] = datetime.now().isoformat()

        async with self.lock:
            self.buffer.append(event)

            # Flush if buffer is full
            if len(self.buffer) >= self.buffer_size:
                await self._flush_buffer()

    async def _flush_buffer(self):
        """Flush buffer to file"""
        if not self.buffer:
            return

        try:
            async with aiofiles.open(self.log_file, 'a') as f:
                for event in self.buffer:
                    await f.write(json.dumps(event) + '\n')

            logger.debug(f"Flushed {len(self.buffer)} security events")
            self.buffer.clear()

        except Exception as e:
            logger.error(f"Failed to flush security audit buffer: {e}")

    async def _rotate_log_file(self):
        """Rotate log file when date changes"""
        await self._flush_buffer()
        self.current_date = datetime.now().date()
        self.log_file = self._get_log_file()
        logger.info(f"Rotated security log to: {self.log_file}")

    async def get_recent_violations(
        self,
        hours: int = 24,
        severity: Optional[str] = None
    ) -> List[Dict]:
        """Get recent security violations"""
        violations = []
        cutoff_time = datetime.now().timestamp() - (hours * 3600)

        try:
            # Read from current log file
            if self.log_file.exists():
                async with aiofiles.open(self.log_file, 'r') as f:
                    async for line in f:
                        try:
                            event = json.loads(line)
                            if event.get("type") == "violation":
                                event_time = datetime.fromisoformat(
                                    event["timestamp"]
                                ).timestamp()

                                if event_time >= cutoff_time:
                                    if not severity or event.get("severity") == severity:
                                        violations.append(event)
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Failed to read violations: {e}")

        return violations

    async def get_statistics(self, date: Optional[datetime] = None) -> Dict:
        """Get security statistics for a date"""
        if date is None:
            date = datetime.now()

        stats = {
            "date": date.isoformat(),
            "masking_operations": 0,
            "violations": 0,
            "validation_failures": 0,
            "sanitizations": 0,
            "access_attempts": {"allowed": 0, "denied": 0},
            "leaks_detected": 0
        }

        # Get log file for the date
        date_str = date.strftime("%Y%m%d")
        log_file = self.log_dir / f"security_audit_{date_str}.jsonl"

        if not log_file.exists():
            return stats

        try:
            async with aiofiles.open(log_file, 'r') as f:
                async for line in f:
                    try:
                        event = json.loads(line)
                        event_type = event.get("type")

                        if event_type == "masking":
                            stats["masking_operations"] += 1
                            stats["leaks_detected"] += len(
                                event.get("leaks_detected", [])
                            )
                        elif event_type == "violation":
                            stats["violations"] += 1
                        elif event_type == "validation_failure":
                            stats["validation_failures"] += 1
                        elif event_type == "sanitization":
                            stats["sanitizations"] += 1
                        elif event_type == "access_attempt":
                            if event.get("allowed"):
                                stats["access_attempts"]["allowed"] += 1
                            else:
                                stats["access_attempts"]["denied"] += 1

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")

        return stats

    async def close(self):
        """Close audit logger"""
        await self._flush_buffer()
        logger.info("Security audit logger closed")
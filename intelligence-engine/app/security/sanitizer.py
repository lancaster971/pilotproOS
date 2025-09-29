"""
Data Sanitizer
Cleans and sanitizes input/output data
"""
import re
import html
import json
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class DataSanitizer:
    """
    Sanitizes data for safe processing
    Prevents injection attacks and data leaks
    """

    # Patterns that might indicate injection attempts
    SUSPICIOUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # JavaScript
        r"javascript:",  # JavaScript protocol
        r"on\w+\s*=",  # Event handlers
        r"';.*?--",  # SQL injection
        r"union\s+select",  # SQL union
        r"drop\s+table",  # SQL drop
        r"\$\{.*?\}",  # Template injection
        r"\{\{.*?\}\}",  # Template injection
        r"exec\s*\(",  # Code execution
        r"eval\s*\(",  # Code evaluation
        r"__import__",  # Python import
        r"subprocess",  # Process execution
        r"os\.system",  # System commands
    ]

    def __init__(self):
        """Initialize sanitizer"""
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for performance"""
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.SUSPICIOUS_PATTERNS
        ]

    def sanitize_string(self, text: str, escape_html: bool = True) -> str:
        """
        Sanitize a string value

        Args:
            text: String to sanitize
            escape_html: Whether to escape HTML entities

        Returns:
            Sanitized string
        """
        if not text:
            return ""

        # Remove null bytes
        text = text.replace('\x00', '')

        # Escape HTML if requested
        if escape_html:
            text = html.escape(text)

        # Check for suspicious patterns
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                logger.warning(f"Suspicious pattern detected: {pattern.pattern}")
                # Replace suspicious content
                text = pattern.sub("[SANITIZED]", text)

        # Remove control characters except newline and tab
        text = ''.join(
            char for char in text
            if char == '\n' or char == '\t' or (ord(char) >= 32 and ord(char) != 127)
        )

        return text.strip()

    def sanitize_dict(
        self,
        data: Dict[str, Any],
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary

        Args:
            data: Dictionary to sanitize
            max_depth: Maximum recursion depth

        Returns:
            Sanitized dictionary
        """
        if max_depth <= 0:
            logger.warning("Max sanitization depth reached")
            return {"error": "Max depth exceeded"}

        sanitized = {}

        for key, value in data.items():
            # Sanitize the key
            safe_key = self.sanitize_string(str(key), escape_html=False)

            # Sanitize the value based on type
            if isinstance(value, str):
                sanitized[safe_key] = self.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[safe_key] = self.sanitize_dict(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[safe_key] = self.sanitize_list(value, max_depth - 1)
            elif isinstance(value, (int, float, bool, type(None))):
                sanitized[safe_key] = value
            else:
                # Convert other types to string and sanitize
                sanitized[safe_key] = self.sanitize_string(str(value))

        return sanitized

    def sanitize_list(
        self,
        items: List[Any],
        max_depth: int = 10
    ) -> List[Any]:
        """
        Sanitize list items

        Args:
            items: List to sanitize
            max_depth: Maximum recursion depth

        Returns:
            Sanitized list
        """
        if max_depth <= 0:
            logger.warning("Max sanitization depth reached")
            return ["[Max depth exceeded]"]

        sanitized = []

        for item in items:
            if isinstance(item, str):
                sanitized.append(self.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item, max_depth - 1))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item, max_depth - 1))
            elif isinstance(item, (int, float, bool, type(None))):
                sanitized.append(item)
            else:
                sanitized.append(self.sanitize_string(str(item)))

        return sanitized

    def sanitize_sql_identifier(self, identifier: str) -> str:
        """
        Sanitize SQL identifier (table/column name)

        Args:
            identifier: SQL identifier

        Returns:
            Safe identifier
        """
        # Only allow alphanumeric and underscore
        safe = re.sub(r'[^\w]', '', identifier)

        # Ensure it starts with letter or underscore
        if safe and not safe[0].isalpha() and safe[0] != '_':
            safe = '_' + safe

        return safe[:64]  # Limit length

    def sanitize_json_string(self, json_str: str) -> Optional[str]:
        """
        Sanitize JSON string

        Args:
            json_str: JSON string

        Returns:
            Sanitized JSON string or None if invalid
        """
        try:
            # Parse JSON
            data = json.loads(json_str)

            # Sanitize the data
            if isinstance(data, dict):
                data = self.sanitize_dict(data)
            elif isinstance(data, list):
                data = self.sanitize_list(data)
            else:
                data = self.sanitize_string(str(data))

            # Return as JSON
            return json.dumps(data)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return None

    def remove_pii(self, text: str) -> str:
        """
        Remove potential PII (Personal Identifiable Information)

        Args:
            text: Text to clean

        Returns:
            Text with PII removed
        """
        # Email addresses
        text = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL]',
            text
        )

        # Phone numbers (various formats)
        text = re.sub(
            r'(\+?\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            '[PHONE]',
            text
        )

        # Credit card numbers
        text = re.sub(
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            '[CARD]',
            text
        )

        # Social Security Numbers
        text = re.sub(
            r'\b\d{3}-\d{2}-\d{4}\b',
            '[SSN]',
            text
        )

        # IP addresses
        text = re.sub(
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            '[IP]',
            text
        )

        return text

    def validate_safe_content(self, content: str) -> tuple[bool, List[str]]:
        """
        Validate that content is safe

        Args:
            content: Content to validate

        Returns:
            Tuple of (is_safe, list_of_issues)
        """
        issues = []

        # Check for suspicious patterns
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                issues.append(f"Suspicious pattern: {pattern.pattern}")

        # Check for potential PII
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content):
            issues.append("Contains email address")

        if re.search(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', content):
            issues.append("Contains potential credit card number")

        return (len(issues) == 0, issues)
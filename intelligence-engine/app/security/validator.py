"""
Security Validator
Validates inputs and outputs for security compliance
"""
import re
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SecurityValidator:
    """
    Validates data against security rules
    """

    # Maximum allowed lengths
    MAX_STRING_LENGTH = 10000
    MAX_DICT_DEPTH = 10
    MAX_LIST_LENGTH = 1000

    # Forbidden file extensions
    FORBIDDEN_EXTENSIONS = [
        '.exe', '.dll', '.so', '.dylib', '.bat', '.cmd', '.ps1',
        '.sh', '.bash', '.zsh', '.fish', '.py', '.js', '.rb'
    ]

    def validate_input(
        self,
        data: Any,
        context: Optional[Dict] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate input data for security issues

        Args:
            data: Data to validate
            context: Additional context

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check data type and size
        if isinstance(data, str):
            if len(data) > self.MAX_STRING_LENGTH:
                issues.append(f"String too long: {len(data)} > {self.MAX_STRING_LENGTH}")

            # Check for path traversal
            if '../' in data or '..\\' in data:
                issues.append("Potential path traversal detected")

            # Check for null bytes
            if '\x00' in data:
                issues.append("Null bytes detected")

        elif isinstance(data, dict):
            depth = self._get_dict_depth(data)
            if depth > self.MAX_DICT_DEPTH:
                issues.append(f"Dictionary too deep: {depth} > {self.MAX_DICT_DEPTH}")

        elif isinstance(data, list):
            if len(data) > self.MAX_LIST_LENGTH:
                issues.append(f"List too long: {len(data)} > {self.MAX_LIST_LENGTH}")

        return (len(issues) == 0, issues)

    def validate_file_path(self, path: str) -> Tuple[bool, List[str]]:
        """
        Validate file path for security

        Args:
            path: File path to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for path traversal
        if '../' in path or '..\\' in path:
            issues.append("Path traversal detected")

        # Check for absolute paths (might be restricted)
        if path.startswith('/') or (len(path) > 1 and path[1] == ':'):
            issues.append("Absolute path detected")

        # Check forbidden extensions
        for ext in self.FORBIDDEN_EXTENSIONS:
            if path.lower().endswith(ext):
                issues.append(f"Forbidden file extension: {ext}")
                break

        # Check for special characters
        if re.search(r'[<>"|?*]', path):
            issues.append("Invalid characters in path")

        return (len(issues) == 0, issues)

    def validate_sql_query(self, query: str) -> Tuple[bool, List[str]]:
        """
        Validate SQL query for dangerous operations

        Args:
            query: SQL query to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        query_lower = query.lower()

        # Dangerous operations
        dangerous_keywords = [
            'drop', 'truncate', 'delete', 'alter', 'create',
            'grant', 'revoke', 'exec', 'execute', 'xp_',
            'sp_', 'shutdown', 'kill'
        ]

        for keyword in dangerous_keywords:
            if re.search(r'\b' + keyword + r'\b', query_lower):
                issues.append(f"Dangerous SQL operation: {keyword}")

        # Multiple statements
        if ';' in query and query.strip()[-1] != ';':
            issues.append("Multiple SQL statements detected")

        # Comments that might hide injection
        if '--' in query or '/*' in query:
            issues.append("SQL comments detected")

        return (len(issues) == 0, issues)

    def validate_json_structure(
        self,
        data: Dict,
        schema: Optional[Dict] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate JSON structure

        Args:
            data: JSON data as dictionary
            schema: Optional schema to validate against

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check depth
        depth = self._get_dict_depth(data)
        if depth > self.MAX_DICT_DEPTH:
            issues.append(f"JSON too deep: {depth}")

        # Check size
        json_str = str(data)
        if len(json_str) > self.MAX_STRING_LENGTH * 10:
            issues.append("JSON too large")

        # Validate against schema if provided
        if schema:
            # Simple schema validation (could use jsonschema library)
            required_fields = schema.get('required', [])
            for field in required_fields:
                if field not in data:
                    issues.append(f"Missing required field: {field}")

        return (len(issues) == 0, issues)

    def validate_api_response(
        self,
        response: Dict,
        expected_fields: Optional[List[str]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate API response structure

        Args:
            response: API response dictionary
            expected_fields: Expected fields in response

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for error indicators
        if 'error' in response or 'errors' in response:
            issues.append("Error in API response")

        # Check expected fields
        if expected_fields:
            for field in expected_fields:
                if field not in response:
                    issues.append(f"Missing expected field: {field}")

        # Check for sensitive data that shouldn't be in response
        sensitive_fields = [
            'password', 'secret', 'token', 'api_key',
            'private_key', 'credential'
        ]

        for field in sensitive_fields:
            if field in str(response).lower():
                issues.append(f"Potential sensitive data: {field}")

        return (len(issues) == 0, issues)

    def _get_dict_depth(self, d: Dict, current_depth: int = 0) -> int:
        """Get maximum depth of nested dictionary"""
        if not isinstance(d, dict) or not d:
            return current_depth

        return max(
            self._get_dict_depth(v, current_depth + 1)
            if isinstance(v, dict) else current_depth + 1
            for v in d.values()
        )

    def validate_langchain_output(
        self,
        output: str,
        max_length: int = 5000
    ) -> Tuple[bool, List[str]]:
        """
        Validate LangChain model output

        Args:
            output: Model output text
            max_length: Maximum allowed length

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check length
        if len(output) > max_length:
            issues.append(f"Output too long: {len(output)} > {max_length}")

        # Check for code execution attempts
        code_patterns = [
            r'exec\s*\(',
            r'eval\s*\(',
            r'__import__',
            r'subprocess\.',
            r'os\.system',
            r'open\s*\(',
        ]

        for pattern in code_patterns:
            if re.search(pattern, output):
                issues.append(f"Potential code execution: {pattern}")

        # Check for prompt injection indicators
        injection_patterns = [
            r'ignore previous instructions',
            r'disregard all prior',
            r'</system>',
            r'###\s*Assistant:',
        ]

        for pattern in injection_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                issues.append(f"Potential prompt injection: {pattern}")

        return (len(issues) == 0, issues)
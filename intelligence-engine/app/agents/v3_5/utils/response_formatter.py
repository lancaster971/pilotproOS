"""
ResponseFormatter - Post-processes LLM responses for consistent formatting
Ensures responses are user-friendly, properly formatted, and context-appropriate
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """
    Post-processes LLM-generated responses to ensure:
    - No repeated greetings ("Ciao!" spam)
    - Appropriate emoji based on query intent
    - Consistent number formatting
    - Proper spacing and structure
    - v3.5.1: NO automatic closing (Responder LLM handles engagement)
    """

    def __init__(self):
        """Initialize formatter with pattern definitions"""
        # Greeting patterns to detect/remove
        self.greeting_patterns = [
            r'^Ciao!?\s*',
            r'^Salve!?\s*',
            r'^Buongiorno!?\s*',
            r'^Buonasera!?\s*',
        ]

        # Intent keywords for emoji selection
        self.failure_keywords = [
            'fallimenti', 'fallisce', 'fallito',
            'problemi', 'problema', 'critico',
            'errori', 'errore', 'basso',
            'peggiori', 'peggiore'
        ]

        self.success_keywords = [
            'migliori', 'migliore', 'top',
            'successo', 'ottimo', 'eccellente',
            'performanti', 'performance'
        ]

    def format(
        self,
        response: str,
        query: str,
        intent: Optional[str] = None,
        supervisor_decision: Optional[dict] = None
    ) -> str:
        """
        Format LLM response for user display

        Args:
            response: Raw LLM-generated response
            query: Original user query
            intent: Detected intent (METRIC, STATUS, etc.)
            supervisor_decision: Supervisor classification metadata

        Returns:
            Formatted, user-friendly response
        """
        try:
            # Step 1: Remove repeated greetings (keep max 1)
            response = self._remove_greeting_spam(response)

            # Step 2: Add intent-appropriate emoji
            response = self._add_contextual_emoji(response, query, supervisor_decision)

            # Step 3: Format numbers consistently
            response = self._format_numbers(response)

            # Step 4: Ensure proper spacing/structure
            response = self._normalize_spacing(response)

            # Step 5: Ensure ends with context-aware closing formula
            response = self._ensure_closing(response, query, intent)

            # Step 6: Final validation
            response = self._validate_response(response, query)

            logger.info(f"Response formatted successfully (length: {len(response)})")
            return response

        except Exception as e:
            logger.error(f"Response formatting failed: {e}")
            # Return original if formatting fails (safety fallback)
            return response

    def _remove_greeting_spam(self, response: str) -> str:
        """
        Remove greeting if it appears at start AND response already has content

        Logic: If response starts with "Ciao! " AND has substantial content after,
        remove the greeting (user doesn't need "Ciao!" on every single response)
        """
        # Count greetings
        greeting_count = sum(
            1 for pattern in self.greeting_patterns
            if re.search(pattern, response, re.IGNORECASE)
        )

        # If response has greeting + substantial content (>50 chars after greeting)
        if greeting_count > 0:
            for pattern in self.greeting_patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    # Check if there's substantial content after greeting
                    content_after = response[match.end():].strip()
                    if len(content_after) > 50:
                        # Remove greeting
                        response = content_after
                        logger.info("Removed greeting spam from response")
                    break

        return response

    def _add_contextual_emoji(
        self,
        response: str,
        query: str,
        supervisor_decision: Optional[dict] = None
    ) -> str:
        """
        Add appropriate emoji based on query intent and content

        Rules:
        - Failure/problem queries → ⚠️ (warning)
        - Success/top performer queries → ✅ (success)
        - Neutral queries → 📊 (chart) or no emoji
        """
        # Skip if response already starts with emoji
        if re.match(r'^[\U0001F300-\U0001F9FF]', response):
            return response

        query_lower = query.lower()
        response_lower = response.lower()

        # Detect failure context
        failure_detected = any(kw in query_lower for kw in self.failure_keywords)
        failure_in_response = any(kw in response_lower for kw in ['fallisce', 'fallimenti', 'errori', 'critico'])

        # Detect success context
        success_detected = any(kw in query_lower for kw in self.success_keywords)

        # Add appropriate emoji
        if failure_detected or failure_in_response:
            if not response.startswith("⚠️"):
                response = "⚠️ " + response
                logger.info("Added warning emoji (failure context)")
        elif success_detected:
            if not response.startswith("✅"):
                response = "✅ " + response
                logger.info("Added success emoji (top performer context)")
        elif supervisor_decision and supervisor_decision.get("category") == "SIMPLE_METRIC":
            if not response.startswith("📊"):
                response = "📊 " + response
                logger.info("Added chart emoji (metric context)")

        return response

    def _format_numbers(self, response: str) -> str:
        """
        Format numbers consistently:
        - Percentages: 36% (not 36.0% or 36.00%)
        - Large numbers: 1,432 (add thousand separator)
        - Decimals: 2.5s (max 1 decimal for durations)
        """
        # Format percentages (remove unnecessary decimals)
        # 36.0% → 36%, but keep 36.5% as is
        response = re.sub(r'(\d+)\.0+%', r'\1%', response)

        # Format large numbers with thousand separators (if >999)
        def add_thousands_separator(match):
            num = match.group(0)
            if int(num) > 999:
                return f"{int(num):,}"
            return num

        response = re.sub(r'\b\d{4,}\b', add_thousands_separator, response)

        return response

    def _normalize_spacing(self, response: str) -> str:
        """
        Ensure proper spacing:
        - No more than 2 consecutive newlines
        - Bullets (•) have space after
        - Numbers in lists have space after period
        """
        # Remove excessive newlines (>2)
        response = re.sub(r'\n{3,}', '\n\n', response)

        # Ensure space after bullets
        response = re.sub(r'•(\S)', r'• \1', response)

        # Ensure space after list numbers (1. → 1. )
        response = re.sub(r'(\d+\.)(\S)', r'\1 \2', response)

        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in response.split('\n')]
        response = '\n'.join(lines)

        return response.strip()

    def _ensure_closing(self, response: str, query: str = "", intent: Optional[str] = None) -> str:
        """
        v3.5.1: DISABLED automatic closing - Responder LLM generates contextual questions

        Rationale: The new Responder prompt (v3.5.1 ENRICHED) instructs the LLM to always
        include proactive questions in the "AZIONI SUGGERITE" section. Adding a generic
        closing question here creates REDUNDANCY (2 questions at the end).

        Solution: If response already ends with "?" (LLM-generated question), skip closing.
        """
        # Check if Responder already added a question
        if response.rstrip().endswith("?"):
            logger.info("Response ends with '?' - Skipping automatic closing (LLM already asked)")
            return response

        # If no question from LLM, skip closing anyway (per user request)
        # User feedback: "elimina l'ultima non serve" - no generic closings needed
        logger.info("No automatic closing added - Responder handles engagement")
        return response

    def _validate_response(self, response: str, query: str) -> str:
        """
        Final validation to ensure response quality

        Checks:
        - Minimum length (not too short)
        - Contains actual data (not just "Altro?")
        - No forbidden fluff phrases
        """
        # Check minimum length (excluding "Altro?")
        content = response.replace("Altro?", "").strip()
        if len(content) < 20:
            logger.warning(f"Response too short ({len(content)} chars), may lack detail")

        # Check for forbidden fluff
        forbidden_fluff = [
            'spero che',
            'sono lieta',
            'ecco i dati',
            'ecco le informazioni',
            'posso confermare',
        ]

        for fluff in forbidden_fluff:
            if fluff in response.lower():
                logger.warning(f"Response contains forbidden fluff: '{fluff}'")
                # Try to remove it
                response = re.sub(
                    fluff,
                    '',
                    response,
                    flags=re.IGNORECASE
                ).strip()

        return response

    def format_workflow_name(self, name: str) -> str:
        """
        Format workflow name for display (keep readable, remove technical prefixes)

        Example:
        "GommeGo__Flow_4___Price_Margin_and_VAT_to_be_Paid_Control"
        → "Flow 4 - Price Margin and VAT Control"
        """
        # Remove double underscores
        name = name.replace('__', ' - ')
        name = name.replace('___', ' - ')
        name = name.replace('_', ' ')

        # Capitalize properly
        name = ' '.join(word.capitalize() for word in name.split())

        return name

    def format_error_message(self, error: str, workflow_name: str) -> str:
        """
        Format error message in user-friendly way

        Args:
            error: Raw error message
            workflow_name: Workflow that generated error

        Returns:
            Formatted error explanation
        """
        # Format workflow name
        formatted_name = self.format_workflow_name(workflow_name)

        # Build user-friendly error message
        response = f"⚠️ Il processo '{formatted_name}' ha riscontrato un problema.\n\n"

        # Try to extract useful info from error (without technical details)
        if "timeout" in error.lower():
            response += "• Causa: Tempo di risposta superato\n"
        elif "connection" in error.lower():
            response += "• Causa: Problema di connessione\n"
        elif "not found" in error.lower():
            response += "• Causa: Risorsa non trovata\n"
        else:
            response += "• Causa: Errore durante l'elaborazione\n"

        response += "\nContatta il supporto per assistenza.\n\nAltro?"

        return response

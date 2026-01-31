"""Translation Engine for translating text between languages.

This module provides an abstraction layer for multiple translation backends,
including Google Translate, Ollama (local LLM), and mock for testing.
"""

import asyncio
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

import httpx

from legacylipi.core.models import TextBlock, TranslationBackend, TranslationResult
from legacylipi.core.utils.language_codes import (
    LANGUAGE_NAMES,
    get_google_code,
    get_language_name,
    get_mymemory_code,
)
from legacylipi.core.utils.rate_limiter import RateLimiter
from legacylipi.core.utils.usage_tracker import UsageTracker


class TranslationError(Exception):
    """Exception raised when translation fails."""

    pass


class UsageLimitExceededError(TranslationError):
    """Raised when free tier limit would be exceeded."""

    def __init__(self, current_usage: int, limit: int, requested: int):
        self.current_usage = current_usage
        self.limit = limit
        self.requested = requested
        super().__init__(
            f"Translation would exceed free tier: {current_usage:,}/{limit:,} chars used, "
            f"requesting {requested:,} more. Use force=True to proceed (charges may apply)."
        )


@dataclass
class TranslationConfig:
    """Configuration for translation."""

    source_language: str = "mr"  # Marathi
    target_language: str = "en"  # English
    chunk_size: int = 2000  # Max characters per chunk (reduced to avoid rate limiting)
    timeout: float = 60.0  # Request timeout in seconds
    max_retries: int = 3


class TranslationBackendBase(ABC):
    """Base class for translation backends."""

    @property
    @abstractmethod
    def backend_type(self) -> TranslationBackend:
        """Get the backend type."""
        pass

    @abstractmethod
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate text from source to target language.

        Args:
            text: Text to translate.
            source_lang: Source language code (e.g., 'mr' for Marathi).
            target_lang: Target language code (e.g., 'en' for English).

        Returns:
            Translated text.

        Raises:
            TranslationError: If translation fails.
        """
        pass


class BaseHTTPTranslationBackend(TranslationBackendBase):
    """Base class for HTTP-based translation backends with shared client management."""

    def __init__(self, timeout: float = 30.0, delay_between_requests: float = 1.0):
        """Initialize HTTP backend.

        Args:
            timeout: Request timeout in seconds.
            delay_between_requests: Base delay between API calls.
        """
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._rate_limiter = RateLimiter(base_delay=delay_between_requests)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class MockTranslationBackend(TranslationBackendBase):
    """Mock translation backend for testing."""

    def __init__(self, prefix: str = "[TRANSLATED] "):
        """Initialize mock backend.

        Args:
            prefix: Prefix to add to "translated" text.
        """
        self._prefix = prefix

    @property
    def backend_type(self) -> TranslationBackend:
        return TranslationBackend.MOCK

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Mock translation - adds prefix to text."""
        # Simulate some processing delay
        await asyncio.sleep(0.01)
        return f"{self._prefix}{text}"


class GoogleTranslateBackend(BaseHTTPTranslationBackend):
    """Google Translate backend using free web API."""

    # Note: This uses the free Google Translate web API
    # For production, use the official Google Cloud Translation API

    BASE_URL = "https://translate.googleapis.com/translate_a/single"

    # Multiple user agents to rotate through
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]

    def __init__(self, timeout: float = 60.0, delay_between_requests: float = 2.0):
        """Initialize Google Translate backend.

        Args:
            timeout: Request timeout in seconds.
            delay_between_requests: Base delay between API calls to avoid rate limiting.
        """
        import random

        super().__init__(timeout=timeout, delay_between_requests=delay_between_requests)
        self._request_count = 0
        self._random = random.Random()

    @property
    def backend_type(self) -> TranslationBackend:
        return TranslationBackend.GOOGLE

    def _get_headers(self) -> dict:
        """Get headers with a random user agent."""
        user_agent = self._random.choice(self.USER_AGENTS)
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,mr;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with fresh headers."""
        # Close existing client to rotate user agent
        if self._client and not self._client.is_closed:
            await self._client.aclose()

        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            headers=self._get_headers(),
            follow_redirects=True,
        )
        return self._client

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate using Google Translate with retries."""
        if not text.strip():
            return text

        # Map language codes
        source = get_google_code(source_lang)
        target = get_google_code(target_lang)

        # Truncate text if too long for single request (max ~5000 chars)
        max_chars = 4500
        if len(text) > max_chars:
            text = text[:max_chars]

        # Retry with exponential backoff
        max_retries = 5
        last_error = None

        for attempt in range(max_retries):
            try:
                # Apply rate limiting with enhanced backoff for Google
                await self._rate_limiter.wait_with_backoff(self._request_count, factor=1.5)
                self._request_count += 1

                # Get fresh client with new user agent for each attempt
                client = await self._get_client()

                params = {
                    "client": "gtx",
                    "sl": source,
                    "tl": target,
                    "dt": "t",
                    "q": text,
                }

                response = await client.get(self.BASE_URL, params=params)

                # Handle rate limiting / blocking with retry
                if response.status_code in (403, 429):
                    wait_time = (2**attempt) * 3 + self._random.uniform(1, 5)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise TranslationError(
                            f"Google Translate API error ({response.status_code}) after {max_retries} retries. "
                            "Try using --translator ollama or --translator mock."
                        )

                response.raise_for_status()

                # Parse response - format is [[["translated","original",...],...],...]
                data = response.json()

                if not data or not data[0]:
                    raise TranslationError("Empty response from Google Translate")

                # Extract translated text from response
                translated_parts = []
                for part in data[0]:
                    if part and len(part) > 0:
                        translated_parts.append(part[0])

                return "".join(translated_parts)

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code in (403, 429):
                    wait_time = (2**attempt) * 3 + self._random.uniform(1, 5)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(wait_time)
                        continue
                raise TranslationError(f"HTTP error during translation: {e}")
            except httpx.HTTPError as e:
                last_error = e
                # Network errors - retry with backoff
                if attempt < max_retries - 1:
                    wait_time = (2**attempt) * 2 + self._random.uniform(0.5, 2)
                    await asyncio.sleep(wait_time)
                    continue
                raise TranslationError(f"HTTP error during translation: {e}")
            except (KeyError, IndexError, TypeError) as e:
                raise TranslationError(f"Failed to parse translation response: {e}")

        # Should not reach here, but just in case
        raise TranslationError(f"Translation failed after {max_retries} attempts: {last_error}")


class MyMemoryTranslationBackend(BaseHTTPTranslationBackend):
    """MyMemory translation backend - free, no API key required."""

    BASE_URL = "https://api.mymemory.translated.net/get"

    def __init__(self, timeout: float = 30.0, delay_between_requests: float = 1.0):
        """Initialize MyMemory backend.

        Args:
            timeout: Request timeout in seconds.
            delay_between_requests: Delay between API calls.
        """
        super().__init__(timeout=timeout, delay_between_requests=delay_between_requests)

    @property
    def backend_type(self) -> TranslationBackend:
        return TranslationBackend.MYMEMORY

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate using MyMemory API."""
        if not text.strip():
            return text

        await self._rate_limiter.wait()
        client = await self._get_client()

        # Map language codes
        source = get_mymemory_code(source_lang)
        target = get_mymemory_code(target_lang)

        # MyMemory has a 500 char limit per request for free tier
        max_chars = 500
        if len(text) > max_chars:
            # Split and translate in chunks
            chunks = [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
            results = []
            for chunk in chunks:
                await self._rate_limiter.wait()
                result = await self._translate_chunk(client, chunk, source, target)
                results.append(result)
            return "".join(results)

        return await self._translate_chunk(client, text, source, target)

    async def _translate_chunk(
        self,
        client: httpx.AsyncClient,
        text: str,
        source: str,
        target: str,
    ) -> str:
        """Translate a single chunk of text."""
        params = {
            "q": text,
            "langpair": f"{source}|{target}",
        }

        try:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get("responseStatus") == 200:
                return data.get("responseData", {}).get("translatedText", text)
            else:
                error_msg = data.get("responseDetails", "Unknown error")
                raise TranslationError(f"MyMemory API error: {error_msg}")

        except httpx.HTTPError as e:
            raise TranslationError(f"HTTP error during MyMemory translation: {e}")


class TranslateShellBackend(TranslationBackendBase):
    """Translation backend using translate-shell (trans) CLI tool.

    translate-shell is a command-line translator that supports multiple engines:
    - Google Translate (default)
    - Bing Translator
    - Yandex.Translate
    - Apertium

    Install: apt-get install translate-shell
    Or: wget git.io/trans && chmod +x trans
    GitHub: https://github.com/soimort/translate-shell
    """

    # Common locations where trans might be installed
    SEARCH_PATHS = [
        "./trans",
        "trans",
        "~/trans",
        "~/.local/bin/trans",
        "/usr/local/bin/trans",
        "/usr/bin/trans",
    ]

    def __init__(
        self,
        engine: str = "google",
        timeout: float = 60.0,
        brief: bool = True,
        trans_path: str | None = None,
        delay_between_requests: float = 2.0,
        max_retries: int = 3,
    ):
        """Initialize translate-shell backend.

        Args:
            engine: Translation engine ('google', 'bing', 'yandex', 'apertium').
            timeout: Command timeout in seconds.
            brief: Use brief mode (only output translation, no extra info).
            trans_path: Custom path to trans executable.
            delay_between_requests: Delay between API calls to avoid rate limiting.
            max_retries: Maximum number of retries for failed translations.
        """
        import os
        import random

        self._engine = engine
        self._timeout = timeout
        self._brief = brief
        self._delay = delay_between_requests
        self._max_retries = max_retries
        self._last_request_time: float = 0
        self._random = random.Random()

        # Find trans executable
        if trans_path:
            # Use provided path
            expanded_path = os.path.expanduser(trans_path)
            if os.path.isfile(expanded_path) and os.access(expanded_path, os.X_OK):
                self._trans_path = expanded_path
            else:
                raise TranslationError(f"trans not found at: {trans_path}")
        else:
            # Search for trans in common locations
            self._trans_path = self._find_trans()

        if not self._trans_path:
            raise TranslationError(
                "translate-shell (trans) not found. Install with:\n"
                "  apt-get install translate-shell\n"
                "Or download: wget git.io/trans && chmod +x trans\n"
                "Then specify path: --trans-path ./trans"
            )

    def _find_trans(self) -> str | None:
        """Find trans executable in common locations."""
        import os
        import shutil

        # First try PATH
        trans_in_path = shutil.which("trans")
        if trans_in_path:
            return trans_in_path

        # Search common locations
        for path in self.SEARCH_PATHS:
            expanded = os.path.expanduser(path)
            if os.path.isfile(expanded) and os.access(expanded, os.X_OK):
                return os.path.abspath(expanded)

        return None

    @property
    def backend_type(self) -> TranslationBackend:
        return TranslationBackend.TRANS

    async def _rate_limit(self) -> None:
        """Apply rate limiting with random jitter between requests."""
        import time

        now = time.time()
        elapsed = now - self._last_request_time

        # Add random jitter (0.5 to 1.5x base delay) to appear more human-like
        jitter = self._random.uniform(0.5, 1.5)
        delay = self._delay * jitter

        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)

        self._last_request_time = time.time()

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate using translate-shell CLI with retries."""
        import subprocess

        if not text.strip():
            return text

        # Build command
        cmd = [self._trans_path]

        # Add engine option
        if self._engine != "google":
            cmd.extend(["-e", self._engine])

        # Add brief mode
        if self._brief:
            cmd.append("-b")

        # Add language pair
        cmd.append(f"{source_lang}:{target_lang}")

        # Note: We pass text via stdin instead of command-line argument
        # because long text as argument causes trans to fail with HTTP 400

        last_error = None
        for attempt in range(self._max_retries):
            try:
                # Apply rate limiting before each request
                await self._rate_limit()

                # Run translate-shell with text via stdin
                result = subprocess.run(
                    cmd,
                    input=text,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                )

                if result.returncode != 0:
                    error_msg = result.stderr.strip() or "Unknown error"
                    # Clean ANSI codes from error
                    error_msg = re.sub(r"\x1b\[[0-9;]*m", "", error_msg)

                    # Check for rate limiting errors - retry with backoff
                    if (
                        "Null response" in error_msg
                        or "429" in error_msg
                        or "too many" in error_msg.lower()
                    ):
                        last_error = TranslationError(f"translate-shell error: {error_msg}")
                        if attempt < self._max_retries - 1:
                            wait_time = (2**attempt) * 3 + self._random.uniform(1, 3)
                            await asyncio.sleep(wait_time)
                            continue
                    raise TranslationError(f"translate-shell error: {error_msg}")

                output = result.stdout.strip()
                if not output:
                    last_error = TranslationError(
                        f"translate-shell returned empty output for text of length {len(text)}."
                    )
                    if attempt < self._max_retries - 1:
                        wait_time = (2**attempt) * 2 + self._random.uniform(0.5, 2)
                        await asyncio.sleep(wait_time)
                        continue
                    raise last_error

                return output

            except subprocess.TimeoutExpired:
                last_error = TranslationError(f"translate-shell timed out after {self._timeout}s")
                if attempt < self._max_retries - 1:
                    # Increase timeout for next attempt
                    self._timeout = min(self._timeout * 1.5, 180.0)
                    await asyncio.sleep(2 + self._random.uniform(0, 2))
                    continue
                raise last_error
            except FileNotFoundError:
                raise TranslationError(
                    "translate-shell (trans) not found. Install with: brew install translate-shell"
                )

        # Should not reach here, but just in case
        raise last_error or TranslationError(
            f"Translation failed after {self._max_retries} attempts"
        )

    async def close(self) -> None:
        """No cleanup needed for CLI backend."""
        pass


class OllamaTranslationBackend(BaseHTTPTranslationBackend):
    """Local LLM translation backend using Ollama."""

    DEFAULT_MODEL = "llama3.2"
    DEFAULT_HOST = "http://localhost:11434"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        host: str = DEFAULT_HOST,
        timeout: float = 120.0,
    ):
        """Initialize Ollama backend.

        Args:
            model: Ollama model to use.
            host: Ollama server host.
            timeout: Request timeout in seconds.
        """
        super().__init__(timeout=timeout, delay_between_requests=0.0)
        self._model = model
        self._host = host.rstrip("/")

    @property
    def backend_type(self) -> TranslationBackend:
        return TranslationBackend.OLLAMA

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate using Ollama local LLM."""
        if not text.strip():
            return text

        client = await self._get_client()

        # Build translation prompt
        prompt = self._build_prompt(text, source_lang, target_lang)

        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower for more consistent translations
            },
        }

        try:
            response = await client.post(
                f"{self._host}/api/generate",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            return data.get("response", "").strip()

        except httpx.ConnectError:
            raise TranslationError(
                f"Cannot connect to Ollama at {self._host}. "
                "Make sure Ollama is running (ollama serve)"
            )
        except httpx.HTTPError as e:
            raise TranslationError(f"HTTP error during Ollama translation: {e}")

    def _build_prompt(self, text: str, source_lang: str, target_lang: str) -> str:
        """Build translation prompt for the LLM."""
        source_name = get_language_name(source_lang)
        target_name = get_language_name(target_lang)

        return f"""Translate the following {source_name} text to {target_name}.
Only provide the translation, no explanations or additional text.

Text to translate:
{text}

Translation:"""


class OpenAITranslationBackend(BaseHTTPTranslationBackend):
    """OpenAI API translation backend using GPT models."""

    DEFAULT_MODEL = "gpt-4o-mini"
    API_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        timeout: float = 60.0,
        temperature: float = 0.3,
    ):
        """Initialize OpenAI backend.

        Args:
            model: OpenAI model to use (e.g., 'gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo').
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
            timeout: Request timeout in seconds.
            temperature: Model temperature (0-1, lower = more consistent).
        """
        import os

        super().__init__(timeout=timeout, delay_between_requests=0.0)
        self._model = model
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._temperature = temperature

        if not self._api_key:
            raise TranslationError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

    @property
    def backend_type(self) -> TranslationBackend:
        return TranslationBackend.OPENAI

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate using OpenAI API."""
        if not text.strip():
            return text

        client = await self._get_client()

        # Build translation messages
        source_name = get_language_name(source_lang)
        target_name = get_language_name(target_lang)

        system_prompt = (
            f"You are a professional translator specializing in {source_name} to {target_name} translation. "
            f"Translate the given text accurately while preserving the original meaning, tone, and formatting. "
            f"Only provide the translation without any explanations, notes, or additional text."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]

        # GPT-5+ models use max_completion_tokens instead of max_tokens
        token_param = "max_completion_tokens" if self._model.startswith("gpt-5") else "max_tokens"
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            token_param: 4096,
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = await client.post(
                self.API_URL,
                json=payload,
                headers=headers,
            )

            if response.status_code == 401:
                raise TranslationError("Invalid OpenAI API key")
            elif response.status_code == 429:
                raise TranslationError("OpenAI rate limit exceeded. Wait a moment and try again.")
            elif response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Bad request")
                raise TranslationError(f"OpenAI API error: {error_msg}")

            response.raise_for_status()

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise TranslationError("No response from OpenAI")

            translated_text = choices[0].get("message", {}).get("content", "").strip()
            if not translated_text:
                raise TranslationError("Empty translation from OpenAI")

            return translated_text

        except httpx.ConnectError:
            raise TranslationError("Cannot connect to OpenAI API. Check your internet connection.")
        except httpx.HTTPError as e:
            raise TranslationError(f"HTTP error during OpenAI translation: {e}")


class GCPCloudTranslateBackend(TranslationBackendBase):
    """Google Cloud Translation API v3 backend with free tier tracking."""

    FREE_TIER_LIMIT = 500_000  # chars/month

    def __init__(
        self,
        project_id: str,
        location: str = "global",
        timeout: float = 60.0,
        enforce_free_tier: bool = True,
    ):
        """Initialize GCP Cloud Translation backend.

        Args:
            project_id: GCP project ID.
            location: API location (default: "global").
            timeout: Request timeout in seconds.
            enforce_free_tier: If True, raise error when limit exceeded.
        """
        self._project_id = project_id
        self._location = location
        self._timeout = timeout
        self._enforce_free_tier = enforce_free_tier
        self._client = None  # Lazy init
        self._usage_tracker = UsageTracker()

    @property
    def backend_type(self) -> TranslationBackend:
        return TranslationBackend.GCP_CLOUD

    def _get_client(self):
        """Get or create Translation client (lazy initialization)."""
        if self._client is None:
            try:
                from google.cloud import translate_v3 as translate

                self._client = translate.TranslationServiceClient()
            except ImportError:
                raise TranslationError(
                    "google-cloud-translate not installed. Install with: "
                    "pip install google-cloud-translate"
                )
        return self._client

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        force: bool = False,
    ) -> str:
        """Translate using GCP Cloud Translation API.

        Args:
            text: Text to translate.
            source_lang: Source language code.
            target_lang: Target language code.
            force: If True, bypass free tier limit check.

        Returns:
            Translated text.

        Raises:
            UsageLimitExceededError: If limit would be exceeded and force=False.
            TranslationError: If translation fails.
        """
        if not text.strip():
            return text

        char_count = len(text)

        # Check free tier limit
        if self._enforce_free_tier and not force:
            would_exceed, current = self._usage_tracker.check_limit(
                "gcp_translate", char_count, self.FREE_TIER_LIMIT
            )
            if would_exceed:
                raise UsageLimitExceededError(current, self.FREE_TIER_LIMIT, char_count)

        try:
            import asyncio

            client = self._get_client()
            parent = f"projects/{self._project_id}/locations/{self._location}"

            # Map language codes
            from legacylipi.core.utils.language_codes import get_google_code

            source = get_google_code(source_lang)
            target = get_google_code(target_lang)

            # Run sync API call in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.translate_text(
                    request={
                        "parent": parent,
                        "contents": [text],
                        "source_language_code": source,
                        "target_language_code": target,
                        "mime_type": "text/plain",
                    }
                ),
            )

            if not response.translations:
                raise TranslationError("Empty response from GCP Translation API")

            translated_text = response.translations[0].translated_text

            # Track usage after successful translation
            self._usage_tracker.add_usage("gcp_translate", char_count)

            return translated_text

        except ImportError:
            raise TranslationError(
                "google-cloud-translate not installed. Install with: "
                "pip install google-cloud-translate"
            )
        except UsageLimitExceededError:
            raise
        except TranslationError:
            raise
        except Exception as e:
            # Import GCP exceptions for more specific error handling
            try:
                from google.api_core.exceptions import Forbidden, PermissionDenied

                if isinstance(e, (Forbidden, PermissionDenied)):
                    raise TranslationError(
                        f"GCP permission denied. Ensure Cloud Translation API is enabled "
                        f"and credentials are configured: {e}"
                    ) from e
            except ImportError:
                pass

            # Fallback to string matching for cases where google-api-core isn't available
            error_msg = str(e)
            if "403" in error_msg or "permission" in error_msg.lower():
                raise TranslationError(
                    f"GCP permission denied. Ensure Cloud Translation API is enabled "
                    f"and credentials are configured: {e}"
                ) from e
            raise TranslationError(f"GCP translation error: {e}") from e

    async def close(self) -> None:
        """Close the client."""
        self._client = None

    def get_usage_summary(self) -> dict:
        """Get current usage summary for display."""
        return self._usage_tracker.get_usage_summary("gcp_translate")


class GCPDocumentTranslationBackend(TranslationBackendBase):
    """Google Cloud Document Translation API backend.

    This backend can translate entire PDF documents directly, including scanned
    PDFs with legacy fonts. It uses Google's built-in OCR internally and preserves
    document layout - similar to Google Translate's camera feature.

    This is the recommended approach for PDFs with legacy Indian fonts that
    render incorrectly with standard text extraction.

    Requires:
        - google-cloud-translate package (v3+)
        - GOOGLE_APPLICATION_CREDENTIALS environment variable
        - Cloud Translation API enabled in GCP project

    Cost: ~$0.08 per page for document translation
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",  # Document translation requires specific location
        timeout: float = 300.0,  # Longer timeout for document processing
    ):
        """Initialize GCP Document Translation backend.

        Args:
            project_id: GCP project ID.
            location: API location (must be 'us-central1' for document translation).
            timeout: Request timeout in seconds.
        """
        self._project_id = project_id
        self._location = location
        self._timeout = timeout
        self._client = None

    @property
    def backend_type(self) -> TranslationBackend:
        return TranslationBackend.GCP_CLOUD

    def _get_client(self):
        """Get or create Translation client."""
        if self._client is None:
            try:
                from google.cloud import translate_v3beta1 as translate

                self._client = translate.TranslationServiceClient()
            except ImportError:
                raise TranslationError(
                    "google-cloud-translate not installed. Install with: "
                    "pip install google-cloud-translate"
                )
        return self._client

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate text (falls back to regular text translation).

        For document translation, use translate_document() instead.
        """
        # Fall back to regular text translation for plain text
        try:
            client = self._get_client()
            parent = f"projects/{self._project_id}/locations/{self._location}"

            from legacylipi.core.utils.language_codes import get_google_code

            source = get_google_code(source_lang)
            target = get_google_code(target_lang)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.translate_text(
                    request={
                        "parent": parent,
                        "contents": [text],
                        "source_language_code": source,
                        "target_language_code": target,
                        "mime_type": "text/plain",
                    }
                ),
            )

            if not response.translations:
                raise TranslationError("Empty response from GCP Translation API")

            return response.translations[0].translated_text

        except Exception as e:
            raise TranslationError(f"GCP translation error: {e}")

    async def translate_document(
        self,
        pdf_content: bytes,
        source_lang: str,
        target_lang: str,
    ) -> bytes:
        """Translate a PDF document directly using Document Translation API.

        This method translates the entire PDF, including scanned pages with
        legacy fonts. Google's built-in OCR extracts text from the rendered
        images, translates it, and preserves the document layout.

        Args:
            pdf_content: PDF file content as bytes.
            source_lang: Source language code (e.g., 'mr' for Marathi).
            target_lang: Target language code (e.g., 'en' for English).

        Returns:
            Translated PDF content as bytes.

        Raises:
            TranslationError: If translation fails.
        """
        try:
            from google.cloud import translate_v3beta1 as translate

            client = self._get_client()
            parent = f"projects/{self._project_id}/locations/{self._location}"

            from legacylipi.core.utils.language_codes import get_google_code

            source = get_google_code(source_lang)
            target = get_google_code(target_lang)

            # Create document input config
            document_input_config = translate.DocumentInputConfig(
                content=pdf_content,
                mime_type="application/pdf",
            )

            # Create document output config (return as bytes)
            document_output_config = translate.DocumentOutputConfig(
                mime_type="application/pdf",
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.translate_document(
                    request={
                        "parent": parent,
                        "source_language_code": source,
                        "target_language_code": target,
                        "document_input_config": document_input_config,
                        "document_output_config": document_output_config,
                    }
                ),
            )

            # Get translated document bytes
            if response.document_translation.byte_stream_outputs:
                return response.document_translation.byte_stream_outputs[0]
            else:
                raise TranslationError("No output from Document Translation API")

        except ImportError:
            raise TranslationError(
                "google-cloud-translate not installed. Install with: "
                "pip install google-cloud-translate"
            )
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "permission" in error_msg.lower():
                raise TranslationError(
                    f"GCP permission denied. Ensure Cloud Translation API is enabled "
                    f"and credentials are configured: {e}"
                )
            elif "400" in error_msg:
                raise TranslationError(
                    f"Invalid request to Document Translation API. "
                    f"Ensure the PDF is valid and under 20MB: {e}"
                )
            raise TranslationError(f"GCP document translation error: {e}")

    async def close(self) -> None:
        """Close the client."""
        self._client = None


class TranslationEngine:
    """Main translation engine with chunking and backend management."""

    # Language code to full name mapping (imported from utils)
    LANGUAGE_NAMES = LANGUAGE_NAMES

    def __init__(
        self,
        backend: TranslationBackendBase | None = None,
        config: TranslationConfig | None = None,
    ):
        """Initialize the translation engine.

        Args:
            backend: Translation backend to use. Defaults to MockTranslationBackend.
            config: Translation configuration.
        """
        self._backend = backend or MockTranslationBackend()
        self._config = config or TranslationConfig()

    @property
    def backend_type(self) -> TranslationBackend:
        """Get the current backend type."""
        return self._backend.backend_type

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into chunks for translation.

        Tries to split on paragraph/sentence boundaries.

        Args:
            text: Text to split.

        Returns:
            List of text chunks.
        """
        if len(text) <= self._config.chunk_size:
            return [text]

        chunks = []
        current_chunk = ""

        # Split by paragraphs first
        paragraphs = text.split("\n\n")

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= self._config.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += para
            else:
                # Paragraph too long, try to split by sentences
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""

                if len(para) <= self._config.chunk_size:
                    current_chunk = para
                else:
                    # Split long paragraph by sentences
                    sentences = re.split(r"([।॥.!?]+\s*)", para)
                    for i in range(0, len(sentences), 2):
                        sentence = sentences[i]
                        if i + 1 < len(sentences):
                            sentence += sentences[i + 1]

                        if len(current_chunk) + len(sentence) <= self._config.chunk_size:
                            current_chunk += sentence
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    async def translate_async(
        self,
        text: str,
        source_lang: str | None = None,
        target_lang: str | None = None,
    ) -> TranslationResult:
        """Translate text asynchronously.

        Args:
            text: Text to translate.
            source_lang: Source language code. Uses config default if None.
            target_lang: Target language code. Uses config default if None.

        Returns:
            TranslationResult with translated text.
        """
        source = source_lang or self._config.source_language
        target = target_lang or self._config.target_language

        if not text.strip():
            return TranslationResult(
                source_text=text,
                translated_text=text,
                source_language=source,
                target_language=target,
                translation_backend=self.backend_type,
            )

        # Split into chunks
        chunks = self._chunk_text(text)
        translated_chunks = []
        warnings = []

        for i, chunk in enumerate(chunks):
            try:
                translated = await self._backend.translate(chunk, source, target)
                translated_chunks.append(translated)
            except TranslationError as e:
                warnings.append(f"Chunk {i + 1} translation failed: {e}")
                # Keep original chunk on failure
                translated_chunks.append(chunk)

        # Rejoin chunks
        translated_text = "\n\n".join(translated_chunks)

        return TranslationResult(
            source_text=text,
            translated_text=translated_text,
            source_language=source,
            target_language=target,
            translation_backend=self.backend_type,
            chunk_count=len(chunks),
            warnings=warnings,
        )

    async def translate_blocks_async(
        self,
        blocks: list[TextBlock],
        source_lang: str | None = None,
        target_lang: str | None = None,
        max_concurrent: int = 3,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[TextBlock]:
        """Translate multiple text blocks concurrently for structure-preserving translation.

        Translates each block individually while preserving positional information.
        Uses a semaphore to limit concurrent API calls and avoid rate limiting.

        Args:
            blocks: List of TextBlock objects to translate.
            source_lang: Source language code. Uses config default if None.
            target_lang: Target language code. Uses config default if None.
            max_concurrent: Maximum concurrent translation requests (default 3).
            progress_callback: Optional callback(completed, total) for progress updates.

        Returns:
            Same blocks with translated_text field populated.
        """
        source = source_lang or self._config.source_language
        target = target_lang or self._config.target_language

        # Filter to blocks that have text to translate
        translatable_blocks = [b for b in blocks if (b.unicode_text or b.raw_text or "").strip()]

        if not translatable_blocks:
            return blocks

        semaphore = asyncio.Semaphore(max_concurrent)
        completed = 0
        total = len(translatable_blocks)

        failed_blocks: list[tuple[int, str]] = []  # Track (index, error_message) for failed blocks

        async def translate_single(block: TextBlock, index: int) -> None:
            nonlocal completed
            async with semaphore:
                text = block.unicode_text or block.raw_text
                if text and text.strip():
                    try:
                        block.translated_text = await self._backend.translate(
                            text.strip(), source, target
                        )
                    except TranslationError as e:
                        # Log the error and keep original text on failure
                        import logging

                        logging.warning(f"Translation failed for block {index + 1}: {e}")
                        block.translated_text = text
                        failed_blocks.append((index + 1, str(e)))
                else:
                    block.translated_text = text or ""

                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                # Yield to event loop to allow WebSocket keepalive messages to process
                # This prevents NiceGUI client disconnection during long translation operations
                # 20ms yield gives adequate time for WebSocket heartbeat processing
                await asyncio.sleep(0.02)

        # Translate all blocks concurrently (with semaphore limiting)
        await asyncio.gather(*[translate_single(b, i) for i, b in enumerate(translatable_blocks)])

        # Report failed blocks to user via logging
        if failed_blocks:
            import logging

            logging.warning(
                f"Translation completed with {len(failed_blocks)} failed block(s) out of {total}. "
                f"Failed blocks contain original (untranslated) text."
            )

        return blocks

    def translate_blocks(
        self,
        blocks: list[TextBlock],
        source_lang: str | None = None,
        target_lang: str | None = None,
        max_concurrent: int = 3,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[TextBlock]:
        """Translate multiple text blocks synchronously.

        This is a convenience wrapper around translate_blocks_async.

        Args:
            blocks: List of TextBlock objects to translate.
            source_lang: Source language code.
            target_lang: Target language code.
            max_concurrent: Maximum concurrent translation requests.
            progress_callback: Optional callback for progress updates.

        Returns:
            Same blocks with translated_text field populated.
        """
        return asyncio.run(
            self.translate_blocks_async(
                blocks, source_lang, target_lang, max_concurrent, progress_callback
            )
        )

    def translate(
        self,
        text: str,
        source_lang: str | None = None,
        target_lang: str | None = None,
    ) -> TranslationResult:
        """Translate text synchronously.

        This is a convenience wrapper around translate_async.

        Args:
            text: Text to translate.
            source_lang: Source language code.
            target_lang: Target language code.

        Returns:
            TranslationResult with translated text.
        """
        return asyncio.run(self.translate_async(text, source_lang, target_lang))

    async def close(self) -> None:
        """Close the translation engine and its backend."""
        if hasattr(self._backend, "close"):
            await self._backend.close()


def create_translator(
    backend: str = "mock",
    **kwargs,
) -> TranslationEngine:
    """Create a translation engine with the specified backend.

    Args:
        backend: Backend type ('mock', 'google', 'trans', 'mymemory', 'ollama', 'openai').
        **kwargs: Additional arguments for the backend.

    Returns:
        Configured TranslationEngine.

    Raises:
        ValueError: If backend type is not recognized.
    """
    backend_lower = backend.lower()

    if backend_lower == "mock":
        translation_backend = MockTranslationBackend(**kwargs)
    elif backend_lower == "google":
        translation_backend = GoogleTranslateBackend(**kwargs)
    elif backend_lower == "trans":
        translation_backend = TranslateShellBackend(**kwargs)
    elif backend_lower == "mymemory":
        translation_backend = MyMemoryTranslationBackend(**kwargs)
    elif backend_lower == "ollama":
        translation_backend = OllamaTranslationBackend(**kwargs)
    elif backend_lower == "openai":
        translation_backend = OpenAITranslationBackend(**kwargs)
    elif backend_lower == "gcp_cloud":
        project_id = kwargs.get("project_id")
        if not project_id:
            import os

            project_id = os.environ.get("GCP_PROJECT_ID")
        if not project_id:
            raise ValueError(
                "GCP project ID required. Set GCP_PROJECT_ID env var or pass project_id parameter."
            )
        translation_backend = GCPCloudTranslateBackend(
            project_id=project_id,
            location=kwargs.get("location", "global"),
            enforce_free_tier=kwargs.get("enforce_free_tier", True),
        )
    else:
        raise ValueError(f"Unknown translation backend: {backend}")

    config = TranslationConfig()
    if "source_language" in kwargs:
        config.source_language = kwargs["source_language"]
    if "target_language" in kwargs:
        config.target_language = kwargs["target_language"]

    return TranslationEngine(backend=translation_backend, config=config)

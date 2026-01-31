"""Tests for Translation Engine module."""

import asyncio
import shutil

import pytest

from legacylipi.core.models import TranslationBackend

# Check if translate-shell is available
TRANS_AVAILABLE = shutil.which("trans") is not None
from legacylipi.core.translator import (
    GoogleTranslateBackend,
    MockTranslationBackend,
    OllamaTranslationBackend,
    TranslationConfig,
    TranslationEngine,
    TranslationError,
    create_translator,
)
from legacylipi.core.utils.language_codes import (
    get_google_code,
    get_mymemory_code,
    get_language_name,
)


class TestTranslationConfig:
    """Tests for TranslationConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TranslationConfig()

        assert config.source_language == "mr"
        assert config.target_language == "en"
        assert config.chunk_size == 2000  # Updated default
        assert config.timeout == 60.0  # Updated default

    def test_custom_config(self):
        """Test custom configuration."""
        config = TranslationConfig(
            source_language="hi",
            target_language="ta",
            chunk_size=2000,
        )

        assert config.source_language == "hi"
        assert config.target_language == "ta"
        assert config.chunk_size == 2000


class TestMockTranslationBackend:
    """Tests for MockTranslationBackend."""

    def test_backend_type(self):
        """Test that backend type is correct."""
        backend = MockTranslationBackend()
        assert backend.backend_type == TranslationBackend.MOCK

    @pytest.mark.asyncio
    async def test_translate_basic(self):
        """Test basic mock translation."""
        backend = MockTranslationBackend()
        result = await backend.translate("Hello", "en", "hi")

        assert "[TRANSLATED]" in result
        assert "Hello" in result

    @pytest.mark.asyncio
    async def test_translate_with_custom_prefix(self):
        """Test mock translation with custom prefix."""
        backend = MockTranslationBackend(prefix="[TR] ")
        result = await backend.translate("Test", "en", "mr")

        assert result.startswith("[TR] ")
        assert "Test" in result


class TestGoogleTranslateBackend:
    """Tests for GoogleTranslateBackend."""

    def test_backend_type(self):
        """Test that backend type is correct."""
        backend = GoogleTranslateBackend()
        assert backend.backend_type == TranslationBackend.GOOGLE

    def test_language_code_mapping(self):
        """Test language code mapping using utility function."""
        # Test the utility function that backend uses
        assert get_google_code("marathi") == "mr"
        assert get_google_code("hindi") == "hi"
        assert get_google_code("english") == "en"
        assert get_google_code("MR") == "mr"
        assert get_google_code("unknown") == "unknown"

    @pytest.mark.asyncio
    async def test_translate_empty_text(self):
        """Test translating empty text."""
        backend = GoogleTranslateBackend()
        result = await backend.translate("", "mr", "en")
        assert result == ""

    @pytest.mark.asyncio
    async def test_translate_whitespace_only(self):
        """Test translating whitespace-only text."""
        backend = GoogleTranslateBackend()
        result = await backend.translate("   ", "mr", "en")
        assert result == "   "


class TestOllamaTranslationBackend:
    """Tests for OllamaTranslationBackend."""

    def test_backend_type(self):
        """Test that backend type is correct."""
        backend = OllamaTranslationBackend()
        assert backend.backend_type == TranslationBackend.OLLAMA

    def test_default_model(self):
        """Test default model configuration."""
        backend = OllamaTranslationBackend()
        assert backend._model == "llama3.2"

    def test_custom_model(self):
        """Test custom model configuration."""
        backend = OllamaTranslationBackend(model="mistral")
        assert backend._model == "mistral"

    def test_language_name(self):
        """Test language name lookup using utility function."""
        # Test the utility function that backend uses
        assert get_language_name("mr") == "Marathi"
        assert get_language_name("hi") == "Hindi"
        assert get_language_name("en") == "English"
        assert get_language_name("unknown") == "unknown"

    def test_prompt_building(self):
        """Test translation prompt construction."""
        backend = OllamaTranslationBackend()
        prompt = backend._build_prompt("नमस्ते", "mr", "en")

        assert "Marathi" in prompt
        assert "English" in prompt
        assert "नमस्ते" in prompt
        assert "Translation:" in prompt


class TestMyMemoryTranslationBackend:
    """Tests for MyMemoryTranslationBackend."""

    def test_backend_type(self):
        """Test that backend type is correct."""
        from legacylipi.core.translator import MyMemoryTranslationBackend

        backend = MyMemoryTranslationBackend()
        assert backend.backend_type == TranslationBackend.MYMEMORY

    def test_language_code_mapping(self):
        """Test language code mapping using utility function."""
        # Test the utility function that backend uses
        assert get_mymemory_code("mr") == "mr-IN"
        assert get_mymemory_code("en") == "en-GB"
        assert get_mymemory_code("hi") == "hi-IN"
        assert get_mymemory_code("unknown") == "unknown"

    @pytest.mark.asyncio
    async def test_translate_empty_text(self):
        """Test translation of empty text."""
        from legacylipi.core.translator import MyMemoryTranslationBackend

        backend = MyMemoryTranslationBackend()
        result = await backend.translate("", "mr", "en")
        assert result == ""


class TestCreateTranslatorMyMemory:
    """Tests for create_translator with MyMemory."""

    def test_create_mymemory_translator(self):
        """Test creating MyMemory translator."""
        engine = create_translator("mymemory")
        assert engine.backend_type == TranslationBackend.MYMEMORY


@pytest.mark.skipif(not TRANS_AVAILABLE, reason="translate-shell not installed")
class TestTranslateShellBackend:
    """Tests for TranslateShellBackend."""

    def test_backend_type(self):
        """Test that backend type is correct."""
        from legacylipi.core.translator import TranslateShellBackend

        backend = TranslateShellBackend()
        assert backend.backend_type == TranslationBackend.TRANS

    def test_default_engine(self):
        """Test default engine is google."""
        from legacylipi.core.translator import TranslateShellBackend

        backend = TranslateShellBackend()
        assert backend._engine == "google"

    def test_custom_engine(self):
        """Test custom engine configuration."""
        from legacylipi.core.translator import TranslateShellBackend

        backend = TranslateShellBackend(engine="bing")
        assert backend._engine == "bing"

    @pytest.mark.asyncio
    async def test_translate_empty_text(self):
        """Test translation of empty text."""
        from legacylipi.core.translator import TranslateShellBackend

        backend = TranslateShellBackend()
        result = await backend.translate("", "mr", "en")
        assert result == ""


@pytest.mark.skipif(not TRANS_AVAILABLE, reason="translate-shell not installed")
class TestCreateTranslatorTrans:
    """Tests for create_translator with translate-shell."""

    def test_create_trans_translator(self):
        """Test creating translate-shell translator."""
        engine = create_translator("trans")
        assert engine.backend_type == TranslationBackend.TRANS


class TestTranslationEngine:
    """Tests for TranslationEngine."""

    def test_default_initialization(self):
        """Test default initialization."""
        engine = TranslationEngine()
        assert engine.backend_type == TranslationBackend.MOCK

    def test_initialization_with_backend(self):
        """Test initialization with custom backend."""
        backend = GoogleTranslateBackend()
        engine = TranslationEngine(backend=backend)
        assert engine.backend_type == TranslationBackend.GOOGLE

    def test_initialization_with_config(self):
        """Test initialization with custom config."""
        config = TranslationConfig(source_language="hi", target_language="ta")
        engine = TranslationEngine(config=config)
        assert engine._config.source_language == "hi"
        assert engine._config.target_language == "ta"


class TestTranslationEngineChunking:
    """Tests for text chunking in TranslationEngine."""

    def test_no_chunking_needed(self):
        """Test that small text is not chunked."""
        engine = TranslationEngine()
        engine._config.chunk_size = 1000

        text = "Short text"
        chunks = engine._chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_by_paragraph(self):
        """Test chunking by paragraph boundaries."""
        engine = TranslationEngine()
        engine._config.chunk_size = 50

        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = engine._chunk_text(text)

        assert len(chunks) >= 2

    def test_chunk_long_paragraph(self):
        """Test chunking of long paragraphs."""
        engine = TranslationEngine()
        engine._config.chunk_size = 100

        text = "This is a sentence. " * 20  # ~400 chars
        chunks = engine._chunk_text(text)

        # Should be split into multiple chunks
        assert len(chunks) >= 2

        # Each chunk should be within size limit (approximately)
        for chunk in chunks:
            assert len(chunk) <= engine._config.chunk_size + 50  # Some tolerance

    def test_preserve_content(self):
        """Test that chunking preserves all content."""
        engine = TranslationEngine()
        engine._config.chunk_size = 100

        text = "Para 1.\n\nPara 2.\n\nPara 3."
        chunks = engine._chunk_text(text)

        # Reassemble and check content is preserved
        reassembled = "\n\n".join(chunks)
        assert "Para 1" in reassembled
        assert "Para 2" in reassembled
        assert "Para 3" in reassembled


class TestTranslationEngineAsync:
    """Tests for async translation methods."""

    @pytest.mark.asyncio
    async def test_translate_async_basic(self):
        """Test basic async translation."""
        engine = TranslationEngine()
        result = await engine.translate_async("Hello World")

        assert result.source_text == "Hello World"
        assert "[TRANSLATED]" in result.translated_text
        assert result.success is True

    @pytest.mark.asyncio
    async def test_translate_async_empty_text(self):
        """Test async translation of empty text."""
        engine = TranslationEngine()
        result = await engine.translate_async("")

        assert result.source_text == ""
        assert result.translated_text == ""

    @pytest.mark.asyncio
    async def test_translate_async_with_languages(self):
        """Test async translation with explicit languages."""
        engine = TranslationEngine()
        result = await engine.translate_async(
            "Test",
            source_lang="hi",
            target_lang="ta",
        )

        assert result.source_language == "hi"
        assert result.target_language == "ta"

    @pytest.mark.asyncio
    async def test_translate_async_chunk_count(self):
        """Test that chunk count is tracked."""
        engine = TranslationEngine()
        engine._config.chunk_size = 50

        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = await engine.translate_async(text)

        assert result.chunk_count >= 1


class TestTranslationEngineSync:
    """Tests for sync translation methods."""

    def test_translate_sync_basic(self):
        """Test basic sync translation."""
        engine = TranslationEngine()
        result = engine.translate("Hello")

        assert result.source_text == "Hello"
        assert "[TRANSLATED]" in result.translated_text

    def test_translate_sync_uses_config_defaults(self):
        """Test that sync translation uses config defaults."""
        config = TranslationConfig(source_language="mr", target_language="en")
        engine = TranslationEngine(config=config)
        result = engine.translate("Test")

        assert result.source_language == "mr"
        assert result.target_language == "en"


class TestCreateTranslator:
    """Tests for create_translator factory function."""

    def test_create_mock_translator(self):
        """Test creating mock translator."""
        engine = create_translator("mock")
        assert engine.backend_type == TranslationBackend.MOCK

    def test_create_google_translator(self):
        """Test creating Google translator."""
        engine = create_translator("google")
        assert engine.backend_type == TranslationBackend.GOOGLE

    def test_create_ollama_translator(self):
        """Test creating Ollama translator."""
        engine = create_translator("ollama")
        assert engine.backend_type == TranslationBackend.OLLAMA

    def test_create_translator_case_insensitive(self):
        """Test that backend name is case insensitive."""
        engine1 = create_translator("Mock")
        engine2 = create_translator("MOCK")
        engine3 = create_translator("mock")

        assert engine1.backend_type == TranslationBackend.MOCK
        assert engine2.backend_type == TranslationBackend.MOCK
        assert engine3.backend_type == TranslationBackend.MOCK

    def test_create_translator_invalid_backend(self):
        """Test that invalid backend raises error."""
        with pytest.raises(ValueError, match="Unknown translation backend"):
            create_translator("invalid_backend")

    def test_create_translator_with_ollama_model(self):
        """Test creating Ollama translator with custom model."""
        engine = create_translator("ollama", model="mistral")
        assert engine._backend._model == "mistral"


class TestTranslationResult:
    """Tests for TranslationResult integration."""

    def test_result_success(self):
        """Test successful translation result."""
        engine = TranslationEngine()
        result = engine.translate("Test text")

        assert result.success is True
        assert result.translation_backend == TranslationBackend.MOCK

    def test_result_with_warnings(self):
        """Test result can include warnings."""
        engine = TranslationEngine()
        result = engine.translate("Test")

        # Mock backend shouldn't produce warnings
        assert len(result.warnings) == 0


class TestLanguageNames:
    """Tests for language name constants."""

    def test_language_names_defined(self):
        """Test that language names are defined."""
        assert "mr" in TranslationEngine.LANGUAGE_NAMES
        assert "hi" in TranslationEngine.LANGUAGE_NAMES
        assert "en" in TranslationEngine.LANGUAGE_NAMES

    def test_language_names_correct(self):
        """Test that language names are correct."""
        names = TranslationEngine.LANGUAGE_NAMES

        assert names["mr"] == "Marathi"
        assert names["hi"] == "Hindi"
        assert names["en"] == "English"


class TestOpenAITranslationBackend:
    """Tests for OpenAITranslationBackend."""

    def test_backend_type(self):
        """Test that backend type is correct."""
        from legacylipi.core.translator import OpenAITranslationBackend

        backend = OpenAITranslationBackend(api_key="test-key")
        assert backend.backend_type == TranslationBackend.OPENAI

    def test_default_model(self):
        """Test default model configuration."""
        from legacylipi.core.translator import OpenAITranslationBackend

        backend = OpenAITranslationBackend(api_key="test-key")
        assert backend._model == "gpt-4o-mini"

    def test_custom_model(self):
        """Test custom model configuration."""
        from legacylipi.core.translator import OpenAITranslationBackend

        backend = OpenAITranslationBackend(api_key="test-key", model="gpt-4o")
        assert backend._model == "gpt-4o"

    def test_language_name(self):
        """Test language name lookup using utility function."""
        # Test the utility function that backend uses
        assert get_language_name("mr") == "Marathi"
        assert get_language_name("hi") == "Hindi"
        assert get_language_name("en") == "English"
        assert get_language_name("unknown") == "unknown"

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises TranslationError."""
        import os
        from legacylipi.core.translator import OpenAITranslationBackend

        # Temporarily remove env var if set
        original_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            with pytest.raises(TranslationError, match="API key not provided"):
                OpenAITranslationBackend()
        finally:
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key

    def test_reads_api_key_from_env(self):
        """Test that API key is read from environment variable."""
        import os
        from legacylipi.core.translator import OpenAITranslationBackend

        original_key = os.environ.get("OPENAI_API_KEY")
        try:
            os.environ["OPENAI_API_KEY"] = "env-test-key"
            backend = OpenAITranslationBackend()
            assert backend._api_key == "env-test-key"
        finally:
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key
            else:
                os.environ.pop("OPENAI_API_KEY", None)

    @pytest.mark.asyncio
    async def test_translate_empty_text(self):
        """Test translation of empty text."""
        from legacylipi.core.translator import OpenAITranslationBackend

        backend = OpenAITranslationBackend(api_key="test-key")
        result = await backend.translate("", "mr", "en")
        assert result == ""


class TestCreateTranslatorOpenAI:
    """Tests for create_translator with OpenAI."""

    def test_create_openai_translator(self):
        """Test creating OpenAI translator."""
        engine = create_translator("openai", api_key="test-key")
        assert engine.backend_type == TranslationBackend.OPENAI

    def test_create_openai_translator_with_model(self):
        """Test creating OpenAI translator with custom model."""
        engine = create_translator("openai", api_key="test-key", model="gpt-4o")
        assert engine._backend._model == "gpt-4o"

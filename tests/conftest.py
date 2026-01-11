"""Pytest configuration and fixtures for LegacyLipi tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_legacy_text():
    """Sample text in Shree-Lipi legacy encoding."""
    # This is how Marathi text appears when extracted from legacy-encoded PDFs
    return "´ÖÆüÖ¸üÖÂ™Òü ¸üÖ•Ö³ÖÖÂÖÖ †×¬Ö×®ÖμÖ´Ö"


@pytest.fixture
def sample_unicode_text():
    """Sample Marathi text in proper Unicode."""
    return "महाराष्ट्र राजभाषा अधिनियम"


@pytest.fixture
def sample_english_text():
    """Expected English translation."""
    return "Maharashtra Rajbhasha Act"

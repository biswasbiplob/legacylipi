"""Tests for GCP Cloud Translation backend and usage tracking."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from legacylipi.core.models import TranslationBackend
from legacylipi.core.translator import (
    GCPCloudTranslateBackend,
    UsageLimitExceededError,
    create_translator,
)
from legacylipi.core.utils.usage_tracker import UsageTracker


class TestUsageTracker:
    """Tests for UsageTracker class."""

    def test_new_tracker_returns_zero(self, tmp_path):
        """New tracker with no data should return 0 usage."""
        tracker = UsageTracker(storage_path=tmp_path / "usage.json")
        assert tracker.get_monthly_usage("gcp_translate") == 0

    def test_add_usage_increments_counter(self, tmp_path):
        """Adding usage should increment the counter."""
        tracker = UsageTracker(storage_path=tmp_path / "usage.json")

        new_total = tracker.add_usage("gcp_translate", 1000)
        assert new_total == 1000

        new_total = tracker.add_usage("gcp_translate", 500)
        assert new_total == 1500

    def test_usage_persists_to_file(self, tmp_path):
        """Usage should be persisted to JSON file."""
        storage_path = tmp_path / "usage.json"
        tracker = UsageTracker(storage_path=storage_path)

        tracker.add_usage("gcp_translate", 5000)

        # Create new tracker instance - should read persisted data
        tracker2 = UsageTracker(storage_path=storage_path)
        assert tracker2.get_monthly_usage("gcp_translate") == 5000

    def test_check_limit_returns_false_when_under(self, tmp_path):
        """check_limit should return False when under limit."""
        tracker = UsageTracker(storage_path=tmp_path / "usage.json")
        tracker.add_usage("gcp_translate", 100_000)

        would_exceed, current = tracker.check_limit("gcp_translate", 10_000, 500_000)

        assert would_exceed is False
        assert current == 100_000

    def test_check_limit_returns_true_when_over(self, tmp_path):
        """check_limit should return True when would exceed limit."""
        tracker = UsageTracker(storage_path=tmp_path / "usage.json")
        tracker.add_usage("gcp_translate", 495_000)

        would_exceed, current = tracker.check_limit("gcp_translate", 10_000, 500_000)

        assert would_exceed is True
        assert current == 495_000

    def test_check_limit_exact_boundary(self, tmp_path):
        """check_limit should handle exact boundary correctly."""
        tracker = UsageTracker(storage_path=tmp_path / "usage.json")
        tracker.add_usage("gcp_translate", 490_000)

        # Exactly at limit - should not exceed
        would_exceed, _ = tracker.check_limit("gcp_translate", 10_000, 500_000)
        assert would_exceed is False

        # One over - should exceed
        would_exceed, _ = tracker.check_limit("gcp_translate", 10_001, 500_000)
        assert would_exceed is True

    def test_get_usage_summary(self, tmp_path):
        """get_usage_summary should return formatted data."""
        tracker = UsageTracker(storage_path=tmp_path / "usage.json")
        tracker.add_usage("gcp_translate", 12345)

        summary = tracker.get_usage_summary("gcp_translate")

        assert summary["characters"] == 12345
        assert "month" in summary
        assert summary["month"] == datetime.now().strftime("%Y-%m")

    def test_separate_services(self, tmp_path):
        """Different services should have separate counters."""
        tracker = UsageTracker(storage_path=tmp_path / "usage.json")

        tracker.add_usage("gcp_translate", 1000)
        tracker.add_usage("other_service", 2000)

        assert tracker.get_monthly_usage("gcp_translate") == 1000
        assert tracker.get_monthly_usage("other_service") == 2000


class TestUsageLimitExceededError:
    """Tests for UsageLimitExceededError exception."""

    def test_error_attributes(self):
        """Error should store usage attributes."""
        error = UsageLimitExceededError(
            current_usage=450_000,
            limit=500_000,
            requested=60_000,
        )

        assert error.current_usage == 450_000
        assert error.limit == 500_000
        assert error.requested == 60_000

    def test_error_message(self):
        """Error message should contain usage details."""
        error = UsageLimitExceededError(
            current_usage=450_000,
            limit=500_000,
            requested=60_000,
        )

        msg = str(error)
        assert "450,000" in msg
        assert "500,000" in msg
        assert "60,000" in msg


class TestGCPCloudTranslateBackend:
    """Tests for GCPCloudTranslateBackend class."""

    def test_backend_type(self):
        """Backend should report correct type."""
        backend = GCPCloudTranslateBackend(project_id="test-project")
        assert backend.backend_type == TranslationBackend.GCP_CLOUD

    def test_free_tier_limit_constant(self):
        """Free tier limit should be 500,000."""
        assert GCPCloudTranslateBackend.FREE_TIER_LIMIT == 500_000

    @pytest.mark.asyncio
    async def test_raises_limit_error_when_exceeded(self, tmp_path):
        """Should raise UsageLimitExceededError when limit exceeded."""
        backend = GCPCloudTranslateBackend(project_id="test-project")
        backend._usage_tracker = UsageTracker(storage_path=tmp_path / "usage.json")

        # Pre-fill usage near limit
        backend._usage_tracker.add_usage("gcp_translate", 495_000)

        with pytest.raises(UsageLimitExceededError) as exc_info:
            await backend.translate("x" * 10_000, "mr", "en")

        assert exc_info.value.current_usage == 495_000
        assert exc_info.value.requested == 10_000

    @pytest.mark.asyncio
    async def test_force_bypasses_limit(self, tmp_path):
        """force=True should bypass limit check."""
        backend = GCPCloudTranslateBackend(project_id="test-project")
        backend._usage_tracker = UsageTracker(storage_path=tmp_path / "usage.json")
        backend._usage_tracker.add_usage("gcp_translate", 495_000)

        # Mock the GCP client
        mock_response = MagicMock()
        mock_response.translations = [MagicMock(translated_text="translated")]

        with patch.object(backend, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.translate_text.return_value = mock_response
            mock_get_client.return_value = mock_client

            # Should not raise even though over limit
            result = await backend.translate("test text", "mr", "en", force=True)
            assert result == "translated"

    @pytest.mark.asyncio
    async def test_tracks_usage_after_translation(self, tmp_path):
        """Should track usage after successful translation."""
        backend = GCPCloudTranslateBackend(project_id="test-project")
        backend._usage_tracker = UsageTracker(storage_path=tmp_path / "usage.json")

        mock_response = MagicMock()
        mock_response.translations = [MagicMock(translated_text="translated")]

        with patch.object(backend, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.translate_text.return_value = mock_response
            mock_get_client.return_value = mock_client

            text = "hello world"  # 11 chars
            await backend.translate(text, "mr", "en")

            assert backend._usage_tracker.get_monthly_usage("gcp_translate") == len(text)

    @pytest.mark.asyncio
    async def test_empty_text_returns_unchanged(self):
        """Empty text should be returned unchanged without API call."""
        backend = GCPCloudTranslateBackend(project_id="test-project")

        result = await backend.translate("", "mr", "en")
        assert result == ""

        result = await backend.translate("   ", "mr", "en")
        assert result == "   "

    def test_get_usage_summary(self, tmp_path):
        """get_usage_summary should return tracker data."""
        backend = GCPCloudTranslateBackend(project_id="test-project")
        backend._usage_tracker = UsageTracker(storage_path=tmp_path / "usage.json")
        backend._usage_tracker.add_usage("gcp_translate", 12345)

        summary = backend.get_usage_summary()
        assert summary["characters"] == 12345


class TestCreateTranslator:
    """Tests for create_translator with gcp_cloud backend."""

    def test_create_gcp_backend_with_project_id(self):
        """Should create GCP backend when project_id provided."""
        engine = create_translator("gcp_cloud", project_id="test-project")
        assert engine.backend_type == TranslationBackend.GCP_CLOUD

    def test_create_gcp_backend_from_env(self, monkeypatch):
        """Should read project_id from environment."""
        monkeypatch.setenv("GCP_PROJECT_ID", "env-project")
        engine = create_translator("gcp_cloud")
        assert engine.backend_type == TranslationBackend.GCP_CLOUD

    def test_create_gcp_backend_missing_project_raises(self, monkeypatch):
        """Should raise ValueError when project_id missing."""
        monkeypatch.delenv("GCP_PROJECT_ID", raising=False)

        with pytest.raises(ValueError) as exc_info:
            create_translator("gcp_cloud")

        assert "project id required" in str(exc_info.value).lower()

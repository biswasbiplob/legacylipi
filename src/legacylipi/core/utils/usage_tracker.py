"""Usage tracking for translation APIs with monthly limits."""

import json
import tempfile
from datetime import datetime
from pathlib import Path


class UsageTracker:
    """Track API usage with monthly limits and persistent storage.

    Stores usage data in JSON format with atomic file operations to prevent corruption.
    Automatically resets counters when a new month begins.
    """

    def __init__(self, storage_path: Path | None = None):
        """Initialize usage tracker with storage path.

        Args:
            storage_path: Path to usage JSON file. Defaults to ~/.legacylipi/usage.json
        """
        if storage_path is None:
            storage_path = Path.home() / ".legacylipi" / "usage.json"

        self.storage_path = Path(storage_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Create parent directories and initialize empty usage file if needed."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.storage_path.exists():
            self._write_data({})

    def _read_data(self) -> dict:
        """Read usage data from storage file.

        Returns:
            Dictionary with usage data, or empty dict if file doesn't exist or is invalid.
        """
        try:
            if self.storage_path.exists():
                with open(self.storage_path, encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError):
            # File corrupted or unreadable, return empty dict
            pass

        return {}

    def _write_data(self, data: dict) -> None:
        """Write usage data to storage using atomic operation.

        Args:
            data: Usage data dictionary to persist
        """
        # Write to temporary file first, then rename atomically
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.storage_path.parent, prefix=".usage_", suffix=".json.tmp"
        )

        try:
            with open(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            # Atomic rename (overwrites existing file)
            Path(temp_path).replace(self.storage_path)
        except Exception:
            # Clean up temp file on error
            Path(temp_path).unlink(missing_ok=True)
            raise

    def _get_current_month_key(self) -> str:
        """Get current month key in YYYY-MM format.

        Returns:
            Month key string like "2026-01"
        """
        return datetime.now().strftime("%Y-%m")

    def reset_if_new_month(self, service: str) -> None:
        """Reset usage counter if we've moved to a new month.

        Args:
            service: Service name (e.g., "gcp_translate")
        """
        data = self._read_data()
        current_month = self._get_current_month_key()

        if service in data:
            # Check if any existing months are not current
            existing_months = list(data[service].keys())
            if existing_months and existing_months[0] != current_month:
                # New month detected, reset service data
                data[service] = {}
                self._write_data(data)

    def get_monthly_usage(self, service: str) -> int:
        """Get character count for current month.

        Args:
            service: Service name (e.g., "gcp_translate")

        Returns:
            Number of characters used this month
        """
        self.reset_if_new_month(service)

        data = self._read_data()
        current_month = self._get_current_month_key()

        if service not in data:
            return 0

        if current_month not in data[service]:
            return 0

        return data[service][current_month].get("characters", 0)

    def add_usage(self, service: str, characters: int) -> int:
        """Add characters to monthly usage counter.

        Args:
            service: Service name (e.g., "gcp_translate")
            characters: Number of characters to add

        Returns:
            New total character count for the month
        """
        self.reset_if_new_month(service)

        data = self._read_data()
        current_month = self._get_current_month_key()

        # Initialize service if needed
        if service not in data:
            data[service] = {}

        # Initialize month if needed
        if current_month not in data[service]:
            data[service][current_month] = {
                "characters": 0,
                "last_updated": datetime.now().isoformat(),
            }

        # Add characters and update timestamp
        data[service][current_month]["characters"] += characters
        data[service][current_month]["last_updated"] = datetime.now().isoformat()

        self._write_data(data)

        return data[service][current_month]["characters"]

    def check_limit(self, service: str, chars_to_add: int, limit: int) -> tuple[bool, int]:
        """Check if adding characters would exceed monthly limit.

        Args:
            service: Service name (e.g., "gcp_translate")
            chars_to_add: Number of characters to potentially add
            limit: Monthly character limit

        Returns:
            Tuple of (would_exceed, current_usage)
        """
        current_usage = self.get_monthly_usage(service)
        would_exceed = (current_usage + chars_to_add) > limit

        return would_exceed, current_usage

    def get_usage_summary(self, service: str) -> dict:
        """Get usage statistics for display.

        Args:
            service: Service name (e.g., "gcp_translate")

        Returns:
            Dictionary with usage statistics:
            - characters: Current month character count
            - month: Current month key (YYYY-MM)
            - last_updated: ISO timestamp of last update (or None)
        """
        self.reset_if_new_month(service)

        data = self._read_data()
        current_month = self._get_current_month_key()

        if service not in data or current_month not in data[service]:
            return {"characters": 0, "month": current_month, "last_updated": None}

        month_data = data[service][current_month]
        return {
            "characters": month_data.get("characters", 0),
            "month": current_month,
            "last_updated": month_data.get("last_updated"),
        }

"""Tests for dependency installation and entry points.

Verifies that all commands work out of the box after a bare
`pip install legacylipi` / `uv tool install legacylipi`.
"""

import subprocess
import sys
import textwrap

import pytest
from click.testing import CliRunner

from legacylipi.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestCoreDepsAvailable:
    """Verify that API deps are always available (core dependencies)."""

    def test_fastapi_importable(self):
        """fastapi is a core dependency and always importable."""
        import fastapi

        assert fastapi is not None

    def test_uvicorn_importable(self):
        """uvicorn is a core dependency and always importable."""
        import uvicorn

        assert uvicorn is not None

    def test_api_main_importable(self):
        """api.main imports without errors."""
        from legacylipi.api.main import app, serve

        assert app is not None
        assert callable(serve)

    def test_app_is_fastapi_instance(self):
        """Module-level app is a FastAPI instance."""
        from legacylipi.api.main import app

        assert app.title == "LegacyLipi API"


class TestEntryPoints:
    """Verify all entry points work in a subprocess (simulates fresh install)."""

    def test_legacylipi_cli_help(self):
        """legacylipi --help works."""
        result = subprocess.run(
            [sys.executable, "-m", "legacylipi.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "LegacyLipi" in result.stdout

    def test_legacylipi_api_help(self):
        """legacylipi api --help works without import errors."""
        result = subprocess.run(
            [sys.executable, "-m", "legacylipi.cli", "api", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "--port" in result.stdout
        assert "--host" in result.stdout

    def test_legacylipi_web_importable(self):
        """legacylipi-web entry point (serve) is importable."""
        code = "from legacylipi.api.main import serve; print('OK')"
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "OK" in result.stdout

    def test_api_main_no_import_error_subprocess(self):
        """api.main loads cleanly in a fresh subprocess."""
        code = textwrap.dedent("""\
            from legacylipi.api.main import app
            assert app is not None
            print("OK")
        """)
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "OK" in result.stdout


class TestRemovedNiceGUI:
    """Verify the deprecated NiceGUI UI is fully removed."""

    def test_ui_module_removed(self):
        """The legacylipi.ui module no longer exists."""
        code = textwrap.dedent("""\
            try:
                from legacylipi.ui.app import main
                print("EXISTS")
            except (ImportError, ModuleNotFoundError):
                print("REMOVED")
        """)
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "REMOVED" in result.stdout

    def test_ui_command_shows_deprecation(self, runner):
        """'legacylipi ui' tells users to use 'legacylipi api'."""
        result = runner.invoke(main, ["ui"])
        assert result.exit_code != 0
        assert "legacylipi api" in result.output


class TestCLIApiCommand:
    """Verify the CLI api command works correctly."""

    def test_api_help(self, runner):
        """CLI 'api' command shows help."""
        result = runner.invoke(main, ["api", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.output
        assert "--host" in result.output

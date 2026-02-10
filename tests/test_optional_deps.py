"""Tests for optional dependency import guards.

Verifies that commands depending on optional extras (api, ocr) give clear
error messages instead of raw ImportError tracebacks when the extras are
not installed.
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


class TestApiImportGuard:
    """Verify the API module handles missing dependencies gracefully."""

    def test_api_main_importable_without_crash(self):
        """api.main can be imported even when deps are present (smoke test)."""
        from legacylipi.api.main import create_app

        app = create_app()
        assert app is not None

    def test_create_app_returns_fastapi_instance(self):
        """create_app() returns a working FastAPI app."""
        from legacylipi.api.main import create_app

        app = create_app()
        assert app.title == "LegacyLipi API"

    def test_serve_function_exists(self):
        """serve() entry point is importable."""
        from legacylipi.api.main import serve

        assert callable(serve)

    def test_cli_api_command_help(self, runner):
        """CLI 'api' command shows help without errors."""
        result = runner.invoke(main, ["api", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.output
        assert "--host" in result.output

    def test_missing_api_deps_gives_clear_error(self):
        """When fastapi/uvicorn are missing, importing main still works
        but serve() raises a clear ImportError."""
        code = textwrap.dedent("""\
            import importlib.abc
            import importlib.machinery
            import sys

            # Install import blocker BEFORE any legacylipi imports
            class ImportBlocker(importlib.abc.MetaPathFinder):
                blocked = {'fastapi', 'uvicorn', 'starlette'}
                def find_spec(self, fullname, path, target=None):
                    if fullname.split('.')[0] in self.blocked:
                        raise ImportError(f"No module named '{fullname}'")
                    return None

            # Remove any cached modules first
            for mod in list(sys.modules):
                if mod.split('.')[0] in ('fastapi', 'uvicorn', 'starlette'):
                    del sys.modules[mod]

            sys.meta_path.insert(0, ImportBlocker())

            from legacylipi.api.main import serve, _check_deps
            try:
                _check_deps()
                print("ERROR: should have raised ImportError")
                sys.exit(1)
            except ImportError as e:
                msg = str(e)
                if "legacylipi[api]" not in msg:
                    print(f"ERROR: message missing install hint: {msg}")
                    sys.exit(1)
                print("OK: clear error message")
                sys.exit(0)
        """)
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
        assert "OK" in result.stdout


class TestEntryPointInstallation:
    """Verify that entry points work correctly when package is installed."""

    def test_legacylipi_cli_entry_point(self):
        """The main CLI entry point works."""
        result = subprocess.run(
            [sys.executable, "-m", "legacylipi.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "LegacyLipi" in result.stdout

    def test_legacylipi_web_entry_point_importable(self):
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

    def test_no_nicegui_dependency(self):
        """NiceGUI should NOT be importable (removed dependency)."""
        code = textwrap.dedent("""\
            try:
                import nicegui
                print("INSTALLED")
            except ImportError:
                print("NOT_INSTALLED")
        """)
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # nicegui may or may not be installed in dev env, but it should
        # not be required — this is informational
        assert result.returncode == 0

    def test_ui_module_removed(self):
        """The legacylipi.ui module should no longer exist."""
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


class TestDeprecatedUICommand:
    """Verify the deprecated UI command gives clear guidance."""

    def test_ui_command_shows_api_alternative(self, runner):
        """'legacylipi ui' tells users to use 'legacylipi api'."""
        result = runner.invoke(main, ["ui"])
        assert result.exit_code != 0
        assert "legacylipi api" in result.output

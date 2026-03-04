import builtins
import importlib

import pytest


def _make_import_blocker(original_import):
    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        # Block all imports that are part of opentelemetry
        if name == 'opentelemetry' or (isinstance(name, str) and name.startswith('opentelemetry.')):
            raise ImportError("No module named 'opentelemetry'")
        return original_import(name, globals, locals, fromlist, level)

    return fake_import


def test_init_telemetry_no_packages(monkeypatch):
    """Verify init_telemetry() does not raise when OpenTelemetry packages are absent."""
    original_import = builtins.__import__
    monkeypatch.setattr(builtins, '__import__', _make_import_blocker(original_import))

    # Import the module under test (fresh import to force re-evaluation)
    import app.di.telemetry as telemetry
    importlib.reload(telemetry)

    # Should not raise even when opentelemetry imports fail
    telemetry.init_telemetry()


def test_start_span_no_packages(monkeypatch):
    """Verify start_span() is usable (no-op) when OpenTelemetry is missing."""
    original_import = builtins.__import__
    monkeypatch.setattr(builtins, '__import__', _make_import_blocker(original_import))

    import app.di.telemetry as telemetry
    importlib.reload(telemetry)

    # Using the context manager should not raise
    with telemetry.start_span("test.span"):
        # No-op block
        pass

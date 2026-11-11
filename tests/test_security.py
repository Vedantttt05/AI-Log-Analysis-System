from datetime import datetime, timezone
from types import SimpleNamespace
from analysis.security import analyze_security

def log(message, source="gateway", level="WARNING"):
    return SimpleNamespace(message=message, source=source, level=level, timestamp=datetime(2026, 11, 11, tzinfo=timezone.utc))

def test_detects_auth_failures_and_repeated_source():
    result = analyze_security([log("Login failed"), log("invalid password"), log("authentication failed"), log("Routine status", level="INFO")])
    assert result["auth_failures"] == 3
    assert result["repeated_sources"] == [{"source": "gateway", "count": 3}]
    assert len(result["signals"]) == 3

def test_does_not_flag_single_or_unrelated_messages():
    result = analyze_security([log("User logged in", level="INFO"), log("Connection reset", source="db", level="ERROR")])
    assert result["auth_failures"] == 0
    assert result["repeated_sources"] == []
    assert result["error_count"] == 1

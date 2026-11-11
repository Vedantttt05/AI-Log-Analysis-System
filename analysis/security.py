"""Small, explainable rules for surfacing suspicious log patterns."""
from collections import Counter

AUTH_FAILURE_TERMS = ("failed login", "login failed", "authentication failed", "invalid password", "access denied")

def analyze_security(logs):
    """Return deterministic security signals from normalized database Log objects."""
    failures = [log for log in logs if any(term in (log.message or "").lower() for term in AUTH_FAILURE_TERMS)]
    by_source = Counter((log.source or "Unknown") for log in failures)
    repeated = [{"source": source, "count": count} for source, count in by_source.items() if count >= 3]
    repeated.sort(key=lambda row: (-row["count"], row["source"]))
    critical = [log for log in logs if log.level == "CRITICAL"]
    errors = [log for log in logs if log.level == "ERROR"]
    return {"auth_failures": len(failures), "repeated_sources": repeated,
            "critical_count": len(critical), "error_count": len(errors),
            "signals": [{"timestamp": log.timestamp, "level": log.level, "source": log.source,
                         "message": log.message, "reason": "Repeated authentication failure"}
                        for log in failures]}

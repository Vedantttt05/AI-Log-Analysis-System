"""Normalize supported log formats into the database log schema."""
import json
import re
from datetime import datetime, timezone
from dateutil.parser import isoparse

LEVELS = {"TRACE", "DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL"}
TEXT_PATTERN = re.compile(r"^\s*(?P<timestamp>\d{4}-\d{2}-\d{2}[T ][0-9:.]+(?:Z|[+-]\d{2}:?\d{2})?)\s+(?P<level>[A-Za-z]+)\s+(?:(?:\[(?P<bracket_source>[^]]+)\])|(?P<source>[A-Za-z0-9_.-]+))\s*(?:[-:]\s*)?(?P<message>.*)$")

class MalformedLogError(ValueError):
    """Raised when a record cannot be normalized."""

def normalize_level(value):
    level = str(value or "").strip().upper()
    if level == "WARN":
        level = "WARNING"
    if level == "FATAL":
        level = "CRITICAL"
    if level not in {"INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise MalformedLogError(f"Unsupported severity: {value!r}")
    return level

def parse_timestamp(value):
    try:
        result = isoparse(str(value))
    except (ValueError, TypeError, OverflowError) as exc:
        raise MalformedLogError(f"Invalid timestamp: {value!r}") from exc
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)

def _normalize(data, raw):
    if not isinstance(data, dict):
        raise MalformedLogError("JSON log record must be an object")
    timestamp = data.get("timestamp", data.get("time", data.get("@timestamp")))
    level = data.get("level", data.get("severity"))
    message = data.get("message", data.get("msg"))
    if timestamp is None or level is None or not isinstance(message, (str, int, float)) or not str(message).strip():
        raise MalformedLogError("Record needs timestamp, severity/level, and non-empty message")
    source = data.get("source", data.get("service", data.get("logger", "Unknown")))
    return {"timestamp": parse_timestamp(timestamp), "level": normalize_level(level),
            "source": str(source or "Unknown")[:100], "message": str(message).strip(), "raw_log": raw}

def parse_text_line(line):
    match = TEXT_PATTERN.match(line)
    if not match:
        raise MalformedLogError("Expected: ISO-timestamp LEVEL source message")
    fields = match.groupdict()
    return _normalize({"timestamp": fields["timestamp"], "level": fields["level"],
                       "source": fields["bracket_source"] or fields["source"], "message": fields["message"]}, line)

def parse_json_record(record, raw=None):
    if isinstance(record, str):
        raw = record if raw is None else raw
        try:
            record = json.loads(record)
        except json.JSONDecodeError as exc:
            raise MalformedLogError(f"Invalid JSON: {exc.msg}") from exc
    return _normalize(record, raw if raw is not None else json.dumps(record, sort_keys=True))

"""Validated file ingestion with per-record error reporting."""
import json
from pathlib import Path
from parser.log_parser import MalformedLogError, parse_json_record, parse_text_line

SUPPORTED_EXTENSIONS = {".log", ".txt", ".json"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

def ingest_bytes(filename, content):
    """Return (normalized records, malformed line errors); never stores uploads on disk."""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("Only .log, .txt, and .json files are supported")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds the 10 MiB upload limit")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("File must be UTF-8 encoded") from exc
    records, errors = [], []
    if suffix == ".json":
        try:
            parsed = json.loads(text)
            items = parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError as exc:
            return [], [f"JSON document: {exc.msg} (line {exc.lineno})"]
        for index, item in enumerate(items, 1):
            raw = json.dumps(item, ensure_ascii=False, sort_keys=True)
            try:
                records.append(parse_json_record(item, raw=raw))
            except MalformedLogError as exc:
                errors.append(f"Record {index}: {exc}")
    else:
        for index, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                if line.lstrip().startswith("{"):
                    records.append(parse_json_record(line))
                else:
                    records.append(parse_text_line(line))
            except MalformedLogError as exc:
                errors.append(f"Line {index}: {exc}")
    return records, errors

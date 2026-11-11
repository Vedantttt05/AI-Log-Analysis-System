import json
from datetime import timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.db import Base
from ingestion.loader import ingest_bytes
from ingestion.service import import_records
from database.operations import count_logs

def test_text_parsing_and_normalization():
    records, errors = ingest_bytes("sample.log", b"2026-11-11T09:30:12Z WARN [api] High latency\n")
    assert not errors and len(records) == 1
    assert records[0]["level"] == "WARNING" and records[0]["source"] == "api"
    assert records[0]["timestamp"].tzinfo == timezone.utc

def test_json_array_and_bad_record():
    data = [{"timestamp":"2026-11-11T09:30:12Z","severity":"error","service":"worker","message":"Synthetic failure"}, {"message":"incomplete"}]
    records, errors = ingest_bytes("sample.json", json.dumps(data).encode())
    assert len(records) == 1 and records[0]["level"] == "ERROR"
    assert len(errors) == 1 and "Record 2" in errors[0]

def test_malformed_text_is_reported_and_good_line_kept():
    records, errors = ingest_bytes("sample.txt", b"bad line\n2026-11-11 09:30:12 INFO api started\n")
    assert len(records) == 1 and len(errors) == 1

def test_rejects_unsupported_extension():
    with pytest.raises(ValueError):
        ingest_bytes("secrets.csv", b"synthetic")

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield session
    session.close()
    engine.dispose()

def test_import_persists_records_and_skips_duplicates(db_session):
    records, errors = ingest_bytes("sample.log", b"2026-11-11T09:30:12Z INFO api started\n")
    first = import_records(db_session, "sample.log", records, errors)
    second = import_records(db_session, "sample.log", records, errors)
    assert first["created"] == 1 and second["duplicates"] == 1
    assert count_logs(db_session) == 1


import pytest

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.db import Base
from database.operations import (
    add_log,
    get_logs,
    search_logs,
    count_logs,
    count_logs_by_level,
    delete_log
)


@pytest.fixture
def db_session():

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(
        bind=engine,
        expire_on_commit=False
    )

    session = TestingSession()

    yield session

    session.close()
    engine.dispose()


def sample_log(message="Test server started", level="INFO"):

    return {
        "timestamp": datetime.now(timezone.utc),
        "level": level,
        "source": "TestServer",
        "message": message,
        "raw_log": f"{level} TestServer {message}"
    }


def test_add_log(db_session):

    log, created = add_log(
        db_session,
        **sample_log()
    )

    assert created is True
    assert log.level == "INFO"


def test_get_logs(db_session):

    add_log(db_session, **sample_log())

    logs = get_logs(db_session)

    assert len(logs) == 1


def test_duplicate_log(db_session):

    first, created_first = add_log(
        db_session,
        **sample_log()
    )

    second, created_second = add_log(
        db_session,
        **sample_log()
    )

    assert created_first is True
    assert created_second is False
    assert first.id == second.id
    assert count_logs(db_session) == 1


def test_filter_by_level(db_session):

    add_log(
        db_session,
        **sample_log("Server started", "INFO")
    )

    add_log(
        db_session,
        **sample_log("Connection failed", "ERROR")
    )

    errors = get_logs(db_session, level="ERROR")

    assert len(errors) == 1
    assert errors[0].level == "ERROR"


def test_search_logs(db_session):

    add_log(
        db_session,
        **sample_log("Database connection failed", "ERROR")
    )

    results = search_logs(db_session, "Database")

    assert len(results) == 1


def test_count_by_level(db_session):

    add_log(
        db_session,
        **sample_log("Server started", "INFO")
    )

    add_log(
        db_session,
        **sample_log("Memory warning", "WARNING")
    )

    add_log(
        db_session,
        **sample_log("Database failed", "ERROR")
    )

    counts = count_logs_by_level(db_session)

    assert counts["INFO"] == 1
    assert counts["WARNING"] == 1
    assert counts["ERROR"] == 1


def test_delete_log(db_session):

    log, created = add_log(
        db_session,
        **sample_log()
    )

    assert delete_log(db_session, log.id) is True

    db_session.flush()

    assert count_logs(db_session) == 0

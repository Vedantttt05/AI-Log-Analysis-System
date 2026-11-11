
import hashlib

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from database.models import Log


def create_fingerprint(raw_log):
    """Generate a unique hash for a log entry."""

    return hashlib.sha256(
        raw_log.encode("utf-8")
    ).hexdigest()


def add_log(
    session,
    timestamp,
    level,
    source,
    message,
    raw_log
):
    """Insert a log while avoiding duplicate records."""

    fingerprint = create_fingerprint(raw_log)

    existing_log = session.query(Log).filter_by(
        fingerprint=fingerprint
    ).first()

    if existing_log:
        return existing_log, False

    new_log = Log(
        timestamp=timestamp,
        level=level.upper(),
        source=source,
        message=message,
        raw_log=raw_log,
        fingerprint=fingerprint
    )

    session.add(new_log)

    try:
        session.flush()
        return new_log, True

    except IntegrityError:
        session.rollback()

        existing_log = session.query(Log).filter_by(
            fingerprint=fingerprint
        ).first()

        if existing_log:
            return existing_log, False

        raise


def get_logs(session, level=None, limit=100):
    """Retrieve logs, optionally filtering by severity."""

    query = session.query(Log)

    if level and level != "ALL":
        query = query.filter(Log.level == level.upper())

    return query.order_by(
        Log.timestamp.desc()
    ).limit(limit).all()


def search_logs(session, keyword):
    """Search log messages and sources."""

    return session.query(Log).filter(
        Log.message.ilike(f"%{keyword}%")
    ).order_by(Log.timestamp.desc()).all()


def count_logs(session):
    """Return the total number of log records."""

    return session.query(Log).count()


def count_logs_by_level(session):
    """Return the number of records for each severity."""

    results = (
        session.query(Log.level, func.count(Log.id))
        .group_by(Log.level)
        .all()
    )

    return {
        level: total
        for level, total in results
    }


def delete_log(session, log_id):
    """Delete a log record."""

    log = session.query(Log).filter_by(
        id=log_id
    ).first()

    if not log:
        return False

    session.delete(log)
    return True

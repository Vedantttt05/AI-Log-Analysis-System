
from datetime import datetime, timezone

from database.db import init_db, get_session
from database.operations import (
    add_log,
    get_logs,
    count_logs,
    count_logs_by_level
)


def main():

    init_db()

    sample_logs = [
        {
            "timestamp": datetime(2026, 11, 11, 9, 30, tzinfo=timezone.utc),
            "level": "INFO",
            "source": "WebServer",
            "message": "Server started successfully",
            "raw_log": "2026-11-11 09:30:00 INFO WebServer Server started successfully"
        },
        {
            "timestamp": datetime(2026, 11, 11, 9, 32, tzinfo=timezone.utc),
            "level": "WARNING",
            "source": "System",
            "message": "High memory usage detected",
            "raw_log": "2026-11-11 09:32:00 WARNING System High memory usage detected"
        },
        {
            "timestamp": datetime(2026, 11, 11, 9, 34, tzinfo=timezone.utc),
            "level": "ERROR",
            "source": "Database",
            "message": "Database connection failed",
            "raw_log": "2026-11-11 09:34:00 ERROR Database Database connection failed"
        },
        {
            "timestamp": datetime(2026, 11, 11, 9, 35, tzinfo=timezone.utc),
            "level": "CRITICAL",
            "source": "Application",
            "message": "Application unavailable",
            "raw_log": "2026-11-11 09:35:00 CRITICAL Application Application unavailable"
        }
    ]

    with get_session() as session:

        for log in sample_logs:

            record, created = add_log(
                session=session,
                **log
            )

            if created:
                print(f"Inserted: {record.level}")
            else:
                print(f"Duplicate skipped: {record.level}")

        print("\nTOTAL LOGS:", count_logs(session))

        print("\nLOG COUNTS BY LEVEL:")

        print(count_logs_by_level(session))

        print("\nSTORED LOGS:")

        for log in get_logs(session, limit=20):

            print(
                log.id,
                log.timestamp,
                log.level,
                log.source,
                log.message
            )


if __name__ == "__main__":
    main()

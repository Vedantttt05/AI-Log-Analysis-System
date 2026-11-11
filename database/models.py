
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship

from database.db import Base


class Log(Base):

    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)

    timestamp = Column(DateTime(timezone=True), nullable=False)

    level = Column(String(20), nullable=False, index=True)

    source = Column(String(100), default="Unknown")

    message = Column(Text, nullable=False)

    raw_log = Column(Text, nullable=False)

    fingerprint = Column(String(64), unique=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    security_events = relationship(
        "SecurityEvent",
        back_populates="log"
    )


class UploadedFile(Base):

    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String(255), nullable=False)

    file_type = Column(String(20))

    total_records = Column(Integer, default=0)

    upload_time = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    status = Column(String(30), default="Uploaded")


class SecurityEvent(Base):

    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)

    log_id = Column(
        Integer,
        ForeignKey("logs.id"),
        nullable=False
    )

    event_type = Column(String(100), nullable=False)

    severity = Column(String(20), nullable=False)

    description = Column(Text)

    detected_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    log = relationship(
        "Log",
        back_populates="security_events"
    )


class AnalysisResult(Base):

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)

    analysis_type = Column(String(100), nullable=False)

    total_logs = Column(Integer, default=0)

    summary = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

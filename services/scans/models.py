from datetime import datetime

from uuid import UUID, uuid4

from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db.base import Base

class Scan(Base):
    __tablename__ = 'scans'

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    user_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True
    )

    repository_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default='pending',
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # RELATIONSHIPS:
    # This relationship is kept intact becuase it's exclusive to the scans module.

    findings: Mapped[list['ScanFinding']] = relationship(
        back_populates='scan',
        cascade='all, delete-orphan'
    )

class ScanFinding(Base):
    __tablename__ = 'scan_findings'

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    scan_id: Mapped[UUID] = mapped_column(
        ForeignKey('scans.id', ondelete='CASCADE'),
        nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    line_number: Mapped[int] = mapped_column(
        nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    algorithm: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    line_content: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )

    # Agent Fields:
    is_false_positive: Mapped[bool] = mapped_column(
        default=False
    )

    agent_explanation: Mapped[str] = mapped_column(
        String(),
        nullable=True
    )

    suggested_explanation: Mapped[str] = mapped_column(
        String(),
        nullable=True
    )

    # Relationships
    scan: Mapped['Scan'] = relationship(
        back_populates='findings'
    )

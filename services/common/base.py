# common/base.py — Shared SQLAlchemy declarative base for all domains
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """
    All domain models' shared base class.
    1. Provides standard ID, created_at, updated_at, deleted_at, is_deleted fields.
    2. Supports async attribute access.
    """

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="PK")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="updated"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, comment="soft delete"
    )
    is_deleted: Mapped[bool] = mapped_column(default=False, comment="deleted flag")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"

"""SQLAlchemy ORM models reflecting the domain entities.

These are not yet wired into the runtime; initial purpose is to
establish the database schema and allow migrations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    phone: Mapped[str] = mapped_column(String(32), index=True)
    region: Mapped[str] = mapped_column(String(128))
    crop: Mapped[str] = mapped_column(String(128))
    stage: Mapped[str] = mapped_column(String(128))
    language: Mapped[str] = mapped_column(String(8), default="ko")
    opt_in: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    briefs: Mapped[list["Brief"]] = relationship(back_populates="profile")


class Brief(Base):
    __tablename__ = "briefs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    horizon_days: Mapped[int] = mapped_column(Integer, default=14)
    link_id: Mapped[str] = mapped_column(String(64), index=True)
    date_range: Mapped[str] = mapped_column(String(64))
    triggers: Mapped[Optional[list[str]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    profile: Mapped["Profile"] = relationship(back_populates="briefs")
    actions: Mapped[list["BriefAction"]] = relationship(back_populates="brief", cascade="all, delete-orphan")
    signals: Mapped[list["BriefSignal"]] = relationship(back_populates="brief", cascade="all, delete-orphan")
    draft_reports: Mapped[list["DraftReport"]] = relationship(back_populates="brief", cascade="all, delete-orphan")


class BriefAction(Base):
    __tablename__ = "brief_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brief_id: Mapped[str] = mapped_column(ForeignKey("briefs.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(256))
    timing_window: Mapped[str] = mapped_column(String(128))
    trigger: Mapped[str] = mapped_column(String(256))
    icon: Mapped[Optional[str]] = mapped_column(String(64))
    source_name: Mapped[str] = mapped_column(String(256))
    source_year: Mapped[str] = mapped_column(String(16))

    brief: Mapped["Brief"] = relationship(back_populates="actions")


class BriefSignal(Base):
    __tablename__ = "brief_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brief_id: Mapped[str] = mapped_column(ForeignKey("briefs.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(16))  # climate | pest
    code: Mapped[str] = mapped_column(String(64))
    severity: Mapped[Optional[str]] = mapped_column(String(32))
    notes: Mapped[Optional[str]] = mapped_column(String(256))

    brief: Mapped["Brief"] = relationship(back_populates="signals")


class DraftReport(Base):
    __tablename__ = "draft_reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    brief_id: Mapped[str] = mapped_column(ForeignKey("briefs.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    brief: Mapped["Brief"] = relationship(back_populates="draft_reports")
    refined_report: Mapped[Optional["RefinedReport"]] = relationship(back_populates="draft", cascade="all, delete-orphan", uselist=False)


class RefinedReport(Base):
    __tablename__ = "refined_reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    draft_id: Mapped[str] = mapped_column(ForeignKey("draft_reports.id", ondelete="CASCADE"), unique=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    draft: Mapped["DraftReport"] = relationship(back_populates="refined_report")


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    phone: Mapped[str] = mapped_column(String(32), index=True)
    keyword: Mapped[str] = mapped_column(String(32))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    response: Mapped[Optional[str]] = mapped_column(Text)


"""Pydantic models representing core domain entities."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Sequence

from pydantic import BaseModel, Field, HttpUrl


class Action(BaseModel):
    title: str = Field(..., min_length=1)
    timing_window: str
    trigger: str
    icon: str | None = None
    source_name: str
    source_year: int | str


class Signal(BaseModel):
    type: Literal["climate", "pest"]
    code: str
    severity: str | None = None
    notes: str | None = None


class Profile(BaseModel):
    id: str
    phone: str
    region: str
    crop: str
    stage: str
    language: Literal["ko"] = "ko"
    opt_in: bool = True


class Brief(BaseModel):
    id: str
    profile_id: str
    horizon_days: int = 14
    actions: Sequence[Action]
    triggers: Sequence[str]
    link_id: str
    date_range: str
    created_at: datetime


class Interaction(BaseModel):
    id: str
    phone: str
    keyword: str
    received_at: datetime
    response: str | None = None


class DraftReport(BaseModel):
    id: str
    brief_id: str
    content: str
    created_at: datetime


class RefinedReport(BaseModel):
    id: str
    draft_id: str
    content: str
    created_at: datetime


class Link(BaseModel):
    link_id: str
    url: HttpUrl


__all__ = [
    "Action",
    "Signal",
    "Profile",
    "Brief",
    "Interaction",
    "DraftReport",
    "RefinedReport",
    "Link",
]

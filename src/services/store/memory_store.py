"""In-memory storage used during the hackathon demo."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from typing import List

from src.lib.models import Brief, DraftReport, Profile, RefinedReport, Signal


@dataclass(slots=True)
class StoredBrief:
    profile: Profile
    brief: Brief
    draft_report: DraftReport
    refined_report: RefinedReport
    sms_body: str
    signals: List[Signal]


class MemoryStore:
    """Volatile in-memory store for briefs, links, and opt-out state."""

    def __init__(self) -> None:
        self._briefs: Dict[str, StoredBrief] = {}
        self._links: Dict[str, str] = {}
        self._latest_brief_by_phone: Dict[str, str] = {}
        self._opt_out: Dict[str, datetime] = {}
        self._profiles: Dict[str, "Profile"] = {}
        self._pending_change: Dict[str, str] = {}

    def save_brief(self, stored: StoredBrief) -> None:
        self._briefs[stored.brief.id] = stored
        self._latest_brief_by_phone[stored.profile.id] = stored.brief.id
        self._profiles[stored.profile.id] = stored.profile

    def get_brief(self, brief_id: str) -> Optional[StoredBrief]:
        return self._briefs.get(brief_id)

    def get_latest_brief_for_profile(self, profile_id: str) -> Optional[StoredBrief]:
        brief_id = self._latest_brief_by_phone.get(profile_id)
        if not brief_id:
            return None
        return self._briefs.get(brief_id)

    def save_link(self, link_id: str, brief_id: str) -> None:
        self._links[link_id] = brief_id

    def resolve_link(self, link_id: str) -> Optional[StoredBrief]:
        brief_id = self._links.get(link_id)
        if not brief_id:
            return None
        return self._briefs.get(brief_id)

    def set_opt_out(self, profile_id: str) -> None:
        self._opt_out[profile_id] = datetime.utcnow()

    def clear_opt_out(self, profile_id: str) -> None:
        self._opt_out.pop(profile_id, None)

    def is_opted_out(self, profile_id: str) -> bool:
        return profile_id in self._opt_out

    def save_profile(self, profile: "Profile") -> None:
        self._profiles[profile.id] = profile

    def get_profile(self, profile_id: str):
        return self._profiles.get(profile_id)

    def set_pending_change(self, profile_id: str, prompt: str) -> None:
        self._pending_change[profile_id] = prompt

    def pop_pending_change(self, profile_id: str) -> str | None:
        return self._pending_change.pop(profile_id, None)

    def get_pending_change(self, profile_id: str) -> str | None:
        return self._pending_change.get(profile_id)


GLOBAL_STORE = MemoryStore()


def get_store() -> MemoryStore:
    return GLOBAL_STORE


__all__ = ["MemoryStore", "StoredBrief", "get_store"]

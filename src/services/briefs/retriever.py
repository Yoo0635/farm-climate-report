"""Retrieve the latest brief for a profile."""

from __future__ import annotations

from src.services.store.memory_store import StoredBrief, get_store


def get_latest_brief(profile_id: str) -> StoredBrief | None:
    store = get_store()
    return store.get_latest_brief_for_profile(profile_id)


__all__ = ["get_latest_brief"]

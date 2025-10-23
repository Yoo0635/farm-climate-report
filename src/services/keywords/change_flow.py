"""Handles CHANGE keyword mini-wizard interactions."""

from __future__ import annotations

from src.lib.models import Profile
from src.services.store.memory_store import MemoryStore


INSTRUCTION = "지역, 작물, 생육단계를 쉼표로 보내 주세요 (예: 전남 순천, 딸기, 개화기)"


class ChangeFlow:
    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def start(self, profile_id: str) -> str:
        self._store.set_pending_change(profile_id, "awaiting-details")
        return INSTRUCTION

    def complete(self, profile_id: str, message: str) -> str:
        parts = [part.strip() for part in message.replace("/", ",").split(",") if part.strip()]
        if len(parts) != 3:
            self._store.set_pending_change(profile_id, "awaiting-details")
            return "형식이 맞지 않습니다. 다시 한번: " + INSTRUCTION

        profile = self._store.get_profile(profile_id)
        if not profile:
            self._store.set_pending_change(profile_id, "awaiting-details")
            return "프로필 정보를 찾을 수 없습니다. 다시 시도해 주세요."

        updated: Profile = profile.model_copy(update={"region": parts[0], "crop": parts[1], "stage": parts[2]})
        self._store.save_profile(updated)
        self._store.pop_pending_change(profile_id)
        return f"변경 완료: {updated.region}, {updated.crop}, {updated.stage}"


__all__ = ["ChangeFlow"]

"""Generate and resolve public detail links."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from src.services.store.memory_store import get_store


@dataclass(slots=True)
class LinkRecord:
    link_id: str
    url: str


class LinkService:
    def __init__(self, base_url: str = "https://example.com/public/briefs") -> None:
        self._base_url = base_url.rstrip("/")
        self._store = get_store()

    def create_link(self, brief_id: str) -> LinkRecord:
        link_id = uuid4().hex
        self._store.save_link(link_id, brief_id)
        return LinkRecord(link_id=link_id, url=f"{self._base_url}/{link_id}")

    def resolve(self, link_id: str):
        return self._store.resolve_link(link_id)

    def build_url(self, link_id: str) -> str:
        return f"{self._base_url}/{link_id}"


__all__ = ["LinkService", "LinkRecord"]

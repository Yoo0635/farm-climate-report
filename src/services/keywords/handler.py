"""Keyword dispatch logic for inbound SMS."""

from __future__ import annotations

import os

from src.services.briefs.retriever import get_latest_brief
from src.services.briefs.summarizer import summarize_brief
from src.services.keywords.change_flow import ChangeFlow
from src.services.links.link_service import LinkService
from src.services.store.memory_store import get_store


class KeywordHandler:
    def __init__(self, link_service: LinkService | None = None) -> None:
        self._store = get_store()
        self._link_service = link_service or LinkService(
            base_url=os.environ.get(
                "DETAIL_BASE_URL", "https://parut.com/public/briefs"
            )
        )
        self._change_flow = ChangeFlow(self._store)

    def handle(self, profile_id: str, message: str) -> str:
        normalized = message.strip().upper()
        pending = self._store.get_pending_change(profile_id)
        if pending:
            return self._change_flow.complete(profile_id, message)

        if normalized == "STOP":
            self._store.set_opt_out(profile_id)
            return "수신 중지 처리되었습니다. 다시 받으려면 REPORT 라고 답장해 주세요."

        if self._store.is_opted_out(profile_id):
            return "수신 중지 상태입니다. REPORT 라고 답장하면 다시 시작합니다."

        if normalized == "CHANGE":
            return self._change_flow.start(profile_id)

        latest = get_latest_brief(profile_id)
        if not latest:
            return "최근 브리프가 없습니다. REPORT 를 나중에 다시 시도해 주세요."

        if normalized == "1":
            url = self._link_service.build_url(latest.brief.link_id)
            return f"상세 안내 링크: {url}"

        if normalized == "REPORT":
            summary = summarize_brief(latest)
            url = self._link_service.build_url(latest.brief.link_id)
            return f"{summary}\n{url}"

        return "지원되는 키워드: 1, REPORT, CHANGE, STOP"


__all__ = ["KeywordHandler"]

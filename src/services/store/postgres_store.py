"""Postgres-backed store implementing the MemoryStore interface.

Notes:
- Pending-change prompts remain in-memory (same behavior as MemoryStore).
- Link mapping is stored via `briefs.link_id`; `save_link` is a no-op.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from src.db.models import Base, Brief as ORMBrief, BriefAction as ORMAction, BriefSignal as ORMSignal, DraftReport as ORMDraft, Profile as ORMProfile, RefinedReport as ORMRefined
from src.db.session import get_session_maker
from src.lib.models import Action, Brief, DraftReport, Profile, RefinedReport, Signal


@dataclass(slots=True)
class StoredBrief:
    profile: Profile
    brief: Brief
    draft_report: DraftReport
    refined_report: RefinedReport
    sms_body: str
    signals: list[Signal]


class PostgresStore:
    def __init__(self) -> None:
        self._session_maker = get_session_maker()
        self._pending_change: dict[str, str] = {}

    # Profile APIs
    def save_profile(self, profile: Profile) -> None:
        with self._session_maker() as session:
            self._upsert_profile(session, profile)
            session.commit()

    def get_profile(self, profile_id: str) -> Optional[Profile]:
        with self._session_maker() as session:
            row = session.get(ORMProfile, profile_id)
            if not row:
                return None
            return Profile(
                id=row.id,
                phone=row.phone,
                region=row.region,
                crop=row.crop,
                stage=row.stage,
                language=row.language,
                opt_in=row.opt_in,
            )

    def set_opt_out(self, profile_id: str) -> None:
        with self._session_maker() as session:
            row = session.get(ORMProfile, profile_id)
            if row:
                row.opt_in = False
                row.updated_at = datetime.utcnow()
                session.commit()

    def clear_opt_out(self, profile_id: str) -> None:
        with self._session_maker() as session:
            row = session.get(ORMProfile, profile_id)
            if row:
                row.opt_in = True
                row.updated_at = datetime.utcnow()
                session.commit()

    def is_opted_out(self, profile_id: str) -> bool:
        with self._session_maker() as session:
            row = session.get(ORMProfile, profile_id)
            return bool(row and not row.opt_in)

    # Brief APIs
    def save_brief(self, stored: StoredBrief) -> None:
        with self._session_maker() as session:
            self._upsert_profile(session, stored.profile)
            b = ORMBrief(
                id=stored.brief.id,
                profile_id=stored.brief.profile_id,
                horizon_days=stored.brief.horizon_days,
                link_id=stored.brief.link_id,
                date_range=stored.brief.date_range,
                triggers=list(stored.brief.triggers),
                created_at=stored.brief.created_at,
            )
            session.add(b)
            for a in stored.brief.actions:
                session.add(
                    ORMAction(
                        brief_id=b.id,
                        title=a.title,
                        timing_window=a.timing_window,
                        trigger=a.trigger,
                        icon=a.icon,
                        source_name=a.source_name,
                        source_year=str(a.source_year),
                    )
                )
            for s in stored.signals:
                session.add(
                    ORMSignal(
                        brief_id=b.id,
                        type=s.type,
                        code=s.code,
                        severity=s.severity,
                        notes=s.notes,
                    )
                )
            d = ORMDraft(id=stored.draft_report.id, brief_id=b.id, content=stored.draft_report.content, created_at=stored.draft_report.created_at)
            session.add(d)
            session.add(
                ORMRefined(
                    id=stored.refined_report.id,
                    draft_id=d.id,
                    content=stored.refined_report.content,
                    created_at=stored.refined_report.created_at,
                )
            )
            session.commit()

    def get_brief(self, brief_id: str) -> Optional[StoredBrief]:
        with self._session_maker() as session:
            return self._load_stored_brief_by(session, brief_id=brief_id)

    def get_latest_brief_for_profile(self, profile_id: str) -> Optional[StoredBrief]:
        with self._session_maker() as session:
            stmt = select(ORMBrief).where(ORMBrief.profile_id == profile_id).order_by(desc(ORMBrief.created_at)).limit(1)
            row = session.scalar(stmt)
            if not row:
                return None
            return self._load_stored_brief_by(session, brief_id=row.id)

    # Link APIs
    def save_link(self, link_id: str, brief_id: str) -> None:  # no-op, link_id persisted on brief
        return None

    def resolve_link(self, link_id: str) -> Optional[StoredBrief]:
        with self._session_maker() as session:
            stmt = select(ORMBrief).where(ORMBrief.link_id == link_id).limit(1)
            row = session.scalar(stmt)
            if not row:
                return None
            return self._load_stored_brief_by(session, brief_id=row.id)

    # Pending change (in-memory, process-local)
    def set_pending_change(self, profile_id: str, prompt: str) -> None:
        self._pending_change[profile_id] = prompt

    def pop_pending_change(self, profile_id: str) -> Optional[str]:
        return self._pending_change.pop(profile_id, None)

    def get_pending_change(self, profile_id: str) -> Optional[str]:
        return self._pending_change.get(profile_id)

    # Internals
    def _upsert_profile(self, session: Session, profile: Profile) -> None:
        row = session.get(ORMProfile, profile.id)
        if row:
            row.phone = profile.phone
            row.region = profile.region
            row.crop = profile.crop
            row.stage = profile.stage
            row.language = profile.language
            row.opt_in = profile.opt_in
            row.updated_at = datetime.utcnow()
        else:
            session.add(
                ORMProfile(
                    id=profile.id,
                    phone=profile.phone,
                    region=profile.region,
                    crop=profile.crop,
                    stage=profile.stage,
                    language=profile.language,
                    opt_in=profile.opt_in,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

    def _load_stored_brief_by(self, session: Session, *, brief_id: str) -> Optional[StoredBrief]:
        b = session.get(ORMBrief, brief_id)
        if not b:
            return None
        p = session.get(ORMProfile, b.profile_id)
        actions = session.scalars(select(ORMAction).where(ORMAction.brief_id == brief_id)).all()
        signals = session.scalars(select(ORMSignal).where(ORMSignal.brief_id == brief_id)).all()
        draft = session.scalar(select(ORMDraft).where(ORMDraft.brief_id == brief_id).order_by(ORMDraft.created_at.desc()).limit(1))
        refined = session.scalar(select(ORMRefined).join(ORMDraft, ORMRefined.draft_id == ORMDraft.id).where(ORMDraft.brief_id == brief_id).limit(1))

        profile = Profile(
            id=p.id,
            phone=p.phone,
            region=p.region,
            crop=p.crop,
            stage=p.stage,
            language=p.language,
            opt_in=p.opt_in,
        )
        brief = Brief(
            id=b.id,
            profile_id=b.profile_id,
            horizon_days=b.horizon_days,
            actions=[
                Action(
                    title=a.title,
                    timing_window=a.timing_window,
                    trigger=a.trigger,
                    icon=a.icon,
                    source_name=a.source_name,
                    source_year=a.source_year,
                )
                for a in actions
            ],
            triggers=b.triggers or [],
            link_id=b.link_id,
            date_range=b.date_range,
            created_at=b.created_at,
        )
        draft_report = DraftReport(id=draft.id, brief_id=draft.brief_id, content=draft.content, created_at=draft.created_at) if draft else DraftReport(id="", brief_id=b.id, content="", created_at=datetime.utcnow())
        refined_report = (
            RefinedReport(id=refined.id, draft_id=refined.draft_id, content=refined.content, created_at=refined.created_at)
            if refined
            else RefinedReport(id="", draft_id=draft_report.id, content="", created_at=datetime.utcnow())
        )
        sig_models = [Signal(type=s.type, code=s.code, severity=s.severity, notes=s.notes) for s in signals]
        return StoredBrief(profile=profile, brief=brief, draft_report=draft_report, refined_report=refined_report, sms_body="", signals=sig_models)


__all__ = ["PostgresStore", "StoredBrief"]


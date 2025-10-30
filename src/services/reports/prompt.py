"""Prompt builder for Evidence Pack → LLM-1 detailed report.

Keeps content simple: include climate daily snapshot, NPMS filtered text,
and deterministic pest hints. No extra normalization/heuristics.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from src.services.aggregation.models import AggregateEvidencePack, ClimateDaily


def _format_daily_lines(daily: Iterable[ClimateDaily]) -> list[str]:
    lines: list[str] = []
    for d in daily:
        parts: list[str] = [
            f"{d.date.isoformat()}",
            f"tmin/tmax={d.tmin_c}°C/{d.tmax_c}°C" if d.tmin_c is not None or d.tmax_c is not None else None,
            f"precip_mm={d.precip_mm}" if d.precip_mm is not None else None,
            f"wind_ms={d.wind_ms}" if d.wind_ms is not None else None,
            f"summary={d.summary}" if d.summary else None,
            f"pop={d.precip_probability_pct}%" if d.precip_probability_pct is not None else None,
        ]
        line = " | ".join(p for p in parts if p)
        if line:
            lines.append(f"- {line}")
    return lines


def build_evidence_prompt(pack: AggregateEvidencePack) -> str:
    profile = pack.profile
    issued = pack.issued_at
    header = (
        f"지역: {profile.region}\n작물: {profile.crop} / 생육 단계: {profile.stage}\n"
        f"자료 기준 시각: {issued} (KST)\n"
    )

    # Climate snapshot (daily)
    climate_header = "\n[기상 요약]\n"
    daily_lines = _format_daily_lines(pack.climate.daily)
    climate_body = "\n".join(daily_lines[:11])  # D0–D10 최대 11줄 표시
    provenance = ", ".join(pack.climate.provenance or [])
    climate_tail = f"\n출처: {provenance}" if provenance else ""

    # NPMS observations (filtered list text)
    npms_header = "\n\n[병해충 관측(필터링)]\n"
    npms_body = pack.text.strip()

    # Deterministic pest hints
    hints_header = "\n\n[참고 힌트]\n"
    hint_lines = "\n".join(f"- {h}" for h in (pack.pest_hints or [])) or "- (없음)"

    instructions = (
        "\n\n[작성 지침]\n"
        "- 한국어로 간결하고 실용적인 보고서를 작성하세요.\n"
        "- 상위 3가지 권고를 제시하고, 각 권고마다 시기(언제)와 트리거(무엇)를 명확히 하세요.\n"
        "- 최소 1개 이상의 출처+연도를 괄호로 인용하세요 (예: KMA 2025, NPMS 2025).\n"
        "- 의학적/약제 직접 지시를 피하고, 필요 시 '검토 권고' 형태로 표현하세요.\n"
        "- 원시 기상/관측 데이터가 힌트와 상충하면 원시 데이터를 우선하세요.\n"
    )

    return header + climate_header + climate_body + climate_tail + npms_header + npms_body + hints_header + hint_lines + instructions


__all__ = ["build_evidence_prompt"]


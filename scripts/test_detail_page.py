"""Test script to create a sample brief and get its detail link.

This creates a test brief and prints the detail page URL.

Usage:
    python scripts/test_detail_page.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lib.models import Brief, DraftReport, Profile, RefinedReport, Signal, Action
from src.services.links.link_service import LinkService
from src.services.store.memory_store import StoredBrief, get_store


def create_test_brief() -> str:
    """Create a test brief and return its detail page URL."""
    
    # Create test profile
    profile = Profile(
        id="+821012345678",
        phone="+821012345678",
        region="안동시",
        crop="사과",
        stage="개화기",
        language="ko",
        opt_in=True,
    )
    
    # Create test signals
    signals = [
        Signal(
            code="FROST_RISK",
            type="climate",
            severity="high",
            description="서리 위험 높음",
        ),
        Signal(
            code="PEST_ALERT",
            type="pest",
            severity="medium",
            description="복숭아순나방 포획 증가",
        ),
    ]
    
    # Create test actions
    actions = [
        Action(
            title="개화기 서리 피해 최소화",
            timing_window="11/2 오후 준비, 11/3~11/5 새벽 운영",
            trigger="최저기온 예보 0°C 이하 + 맑음/약한 바람",
            source_name="USU Extension",
            source_year="2012",
        ),
        Action(
            title="개화기 병해 사전 억제",
            timing_window="11/6 오후~11/7",
            trigger="11/8 강우 예보(7.8 mm) + 온난 조건",
            source_name="KMA",
            source_year="2025",
        ),
    ]
    
    # Create brief
    brief_id = str(uuid4())
    brief = Brief(
        id=brief_id,
        profile_id=profile.id,
        horizon_days=14,
        actions=actions,
        triggers=[signal.code for signal in signals],
        link_id="",  # Will be set by link service
        date_range="2025-10-31 ~ 2025-11-14",
        created_at=datetime.utcnow(),
    )
    
    # Create link
    link_service = LinkService(base_url="https://parut.duckdns.org/public/briefs")
    link_record = link_service.create_link(brief_id)
    brief.link_id = link_record.link_id
    
    # Create reports
    draft = DraftReport(
        id=str(uuid4()),
        brief_id=brief_id,
        content="상세 보고서 내용 (LLM 생성)",
        created_at=datetime.utcnow(),
    )
    
    refined = RefinedReport(
        id=str(uuid4()),
        draft_id=draft.id,
        content="압축된 보고서 내용",
        created_at=datetime.utcnow(),
    )
    
    # Store brief
    stored = StoredBrief(
        profile=profile,
        brief=brief,
        draft_report=draft,
        refined_report=refined,
        sms_body="테스트 SMS 본문",
        signals=signals,
    )
    
    store = get_store()
    store.save_profile(profile)
    store.save_brief(stored)
    
    return link_record.url


if __name__ == "__main__":
    print("=" * 60)
    print("Creating Test Brief...")
    print("=" * 60)
    
    url = create_test_brief()
    
    print(f"\n✅ Test brief created successfully!")
    print(f"\n📄 Detail Page URL:")
    print(f"   {url}")
    print(f"\n🌐 Local Test URL:")
    print(f"   http://localhost:8000{url.replace('https://parut.duckdns.org', '')}")
    print("\n" + "=" * 60)
    print("Run the API server and visit the URL above to test.")
    print("=" * 60)

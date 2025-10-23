# Farm Climate Reporter (MVP)

한국 농가 대상 2주 행동 브리프를 문자(SMS)로 전달하고, 상세 내용은 단일 공개 링크에서 확인하는 해커톤용 단일 모놀리식 서비스입니다. 핵심 목표는 “빠른 학습과 검증”이며, KISS/YAGNI 원칙을 따릅니다.

## 핵심 기능

- 개인화 축: 지역 · 작물 · 생육 단계에 따른 Top‑3 행동 + 시기 + 트리거
- 전달 방식: 1건의 SMS + 1개의 공개 링크(상세 페이지)
- 양방향 키워드: `1`(상세 링크), `REPORT`(최근 브리프 요약), `CHANGE`(프로필 변경 1–2 프롬프트), `STOP`(수신중지)
- LLM 파이프라인: LLM‑1(OpenAI)로 상세 보고서 초안 → LLM‑2(Gemini)로 쉬운 한국어 정제
- 신뢰/안전: 농약/의학적 처방 금지, 관측/환경/작업 중심, 각 행동은 출처+연도 표기

## 아키텍처 개요

- FastAPI 단일 앱(모놀리식) + Jinja2 템플릿(상세 페이지)
- SMS 벤더: SOLAPI(공식 Python SDK)
- RAG: Vector Store + file_search/web_search(현재 스텁 수준, 해커톤 범위)
- 배포: Cloud Run(백엔드) + Firebase Hosting(프론트 라우팅/프록시)

## 빠른 시작(로컬)

### 1) 필수 요구사항

- Python 3.12 (3.11+ 호환)
- 가상환경 권장(venv)

### 2) 설치

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3) 환경 변수(.env)

`.env.sample`를 복사해 `.env`를 만든 뒤 값 채우기:

```ini
OPENAI_API_KEY=...
GEMINI_API_KEY=...
SOLAPI_ACCESS_KEY=...
SOLAPI_SECRET_KEY=...
SOLAPI_SENDER_NUMBER=010XXXXXXXX  # 또는 +82형식
# 데모용 수신자(선택):
DEMO_RECIPIENT_NUMBER=+8210XXXXXXXX
# 데모시 실제 발송 방지(선택): 1/true/yes
SOLAPI_DRY_RUN=1
# 상세 페이지 베이스 URL(선택):
DETAIL_BASE_URL=https://example.com/public/briefs
```

### 4) 실행

```bash
uvicorn src.api.app:app --reload
```

### 5) 데모 스모크 테스트

```bash
API_BASE=http://127.0.0.1:8000 ./scripts/demo_smoke.sh
# 필요 시 1회성 오버라이드
PHONE="+8210XXXXXXXX" API_BASE=http://127.0.0.1:8000 ./scripts/demo_smoke.sh
```

- 스크립트는 `.env`를 자동 로드합니다.
- `SOLAPI_DRY_RUN=1`이면 SOLAPI 네트워크 발송 없이 경로만 검증합니다.
- LLM 키가 존재하면 `/api/briefs` 호출에서 실제 LLM이 수행됩니다.

## 주요 엔드포인트

- POST `/api/briefs`
  - 본문 예시:
    ```json
    {"phone":"+8210XXXXYYYY","region":"KR/Seoul","crop":"Strawberry","stage":"Flowering","scenario":"HEATWAVE"}
    ```
  - 동작: RAG → LLM‑1 → LLM‑2 → 링크 생성 → SMS 1건 발송
- POST `/api/sms/webhook`
  - 예시:
    ```json
    {"from":"+8210XXXXYYYY","to":"+8210ZZZZZZZZ","message":"REPORT"}
    ```
  - 동작: 키워드 처리(1/REPORT/CHANGE/STOP) → 필요 시 답장 SMS 발송
- GET `/public/briefs/{link_id}`
  - 상세 페이지 렌더링(3줄 상황 요약, 체크리스트, Plan B, 출처/연도)
- OpenAPI 계약: `specs/001-send-sms-brief/contracts/openapi.yaml`

## 디렉터리 구조(요약)

```
src/
  api/               # FastAPI 라우트(/api/briefs, /api/sms/webhook, /public/...)
  lib/               # 데이터 모델/포맷/정책
  services/          # LLM, RAG, 링크, SMS(SOLAPI), 저장소(인메모리)
  templates/         # 상세 페이지(Jinja2 + CSS)
scripts/             # demo_smoke.sh
specs/001-send-sms-brief/  # 스펙, 플랜, 계약서, 퀵스타트
```

## 개발 메모

- SOLAPI: 공식 Python SDK 사용. HTTP fallback 없음.
- 데이터 저장: 해커톤 범위에서 인메모리(`MemoryStore`) 사용(지속성/동시성 제한)
- 한국어 고령 사용자 친화 문장 구성(간결/쉬운 어휘)

## 배포 참고

- Dockerfile / cloudrun.yaml 포함(환경변수는 런타임에 주입)
- Firebase Hosting로 공개 링크 라우팅/프록시 설정(firebase.json)

## 문제 해결(FAQ)

- LLM 키가 없을 때: `/api/briefs`가 실패할 수 있습니다(OPENAI/GEMINI 키 필요).
- 실제 발송 방지: `.env`에 `SOLAPI_DRY_RUN=1`
- 번호 형식: `010…`은 자동으로 `+82…`로 변환(데모 스크립트)


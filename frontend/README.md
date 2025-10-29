# React Console (Vite + TypeScript)

운영자/개발자용 간단 콘솔입니다. `/api/briefs/preview`와 `/api/briefs`를 호출해 LLM 파이프라인 프리뷰/발송을 수행합니다.

## 개발

```bash
cd frontend
npm i
npm run dev
# 포트: 5173. /api/** 호출은 Vite dev 서버가 127.0.0.1:8000으로 프록시
```

- 별도 설정 없이 상대 경로(`/api/...`)로 호출됩니다.
- 직접 API 베이스를 바꾸려면 `VITE_API_BASE` 환경변수를 지정하세요.

## 빌드

```bash
npm run build
# 산출물: frontend/dist
```

배포 시 FastAPI에 정적 폴더로 연결하면 `/console` 경로에서 접근할 수 있습니다.

## 주요 기능
- 폼 입력: phone, region, crop, stage, scenario(선택)
- 전화번호 정규화: `010…` → `+82…`, E.164 포맷 유효성 검사
- 프리뷰: POST `/api/briefs/preview`
- 발송: POST `/api/briefs`
- 상태/에러 표시, 최근 입력값 localStorage 저장

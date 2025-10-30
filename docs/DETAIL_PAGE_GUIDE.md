# 상세 보고서 페이지 가이드

## 개요

Farm Climate Reporter는 2주 작형 액션 리포트를 웹 페이지로 제공합니다.

**URL 형식:**
```
https://parut.duckdns.org/public/briefs/{link_id}
```

**예시:**
```
https://parut.duckdns.org/public/briefs/b2008f29ec03432786765752f12f073d
```

---

## 페이지 구성

### 1. 헤더
- **보고서 제목**: "사내 내부용 2주 작형 액션 리포트 (지역 · 작물 · 생육단계)"
- **기준 시각**: 자료 생성 시각 표시

### 2. 기상·생육 리스크 요약
- 서리/한냉 위험
- 강풍/수분 영향
- 강우/병 발생창
- 토양수분 상태

### 3. 병해충 관측 요약 및 해석
- 트랩 포획 현황
- 병해충별 시사점
- 방제 권고사항

### 4. 상위 3가지 권고
각 권고마다:
- **언제**: 실행 시기
- **트리거**: 실행 조건
- **조치 요약**: 구체적 행동 항목

### 5. 2주 운영 체크리스트
- 일자별 세부 작업 항목
- 날씨 조건에 따른 조치

### 6. 현장 유의·운영 팁
- 벌 보호
- 살포 기상창
- 영양·관수
- 기록 관리

### 7. 근거·출처
- 기상 데이터 출처
- 병해충 정보 출처
- 관리 지침 출처

### 8. 메모
- 활용 시 유의사항

---

## 로컬 테스트

### 1. API 서버 실행
```powershell
uvicorn src.api.app:app --reload
```

### 2. 테스트 Brief 생성
```powershell
python scripts/test_detail_page.py
```

출력 예시:
```
============================================================
Creating Test Brief...
============================================================

✅ Test brief created successfully!

📄 Detail Page URL:
   https://parut.duckdns.org/public/briefs/abc123...

🌐 Local Test URL:
   http://localhost:8000/public/briefs/abc123...

============================================================
Run the API server and visit the URL above to test.
============================================================
```

### 3. 브라우저에서 확인
출력된 로컬 URL을 브라우저에서 열어 확인

---

## 실제 사용 플로우

### Brief 생성 API 호출
```bash
curl -X POST https://parut.duckdns.org/api/briefs \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+821012345678",
    "region": "안동시",
    "crop": "사과",
    "stage": "개화기",
    "scenario": "FROST_RISK"
  }'
```

### 응답에서 link_id 추출
```json
{
  "brief_id": "abc123...",
  "message_preview": "📊 안동시 사과 개화기 기후 리포트..."
}
```

### SMS로 전송되는 링크
```
📊 안동시 사과 개화기 기후 리포트
서리 주의: 11/3 -2.0°C 예상

상세보기: https://parut.duckdns.org/public/briefs/{link_id}
```

---

## 스타일링

### 모바일 최적화
- 반응형 디자인
- 768px 이하에서 레이아웃 조정
- 터치 친화적 버튼/링크 크기

### 색상 체계
- **헤더**: 청록색 그라디언트 (#0f766e → #14b8a6)
- **리스크**: 노란색 (#fef3c7, 좌측 주황색 보더)
- **권고사항**: 파란색 (#dbeafe, 좌측 파란색 보더)
- **체크리스트**: 회색 (#f1f5f9, 좌측 회색 보더)

### 폰트
- 기본: Noto Sans KR
- Fallback: system fonts (Apple, Windows)

---

## 커스터마이징

### 템플릿 수정
파일: `src/templates/report_detail.html`

**동적 데이터 주입 예시:**
```html
<div class="header">
  <h1>{{ report_title }}</h1>
  <p class="meta">{{ metadata }}</p>
</div>
```

### 라우트 수정
파일: `src/api/routes/public.py`

**컨텍스트 데이터 추가:**
```python
return templates.TemplateResponse(
    "report_detail.html",
    {
        "request": request,
        "title": report_title,
        "report_title": report_title,
        "metadata": metadata,
        # 추가 데이터...
    },
)
```

---

## 주의사항

### 1. Link ID 보안
- Link ID는 UUID 형식
- 추측 불가능하지만 공유 가능
- 민감한 개인정보는 포함하지 말 것

### 2. 캐싱
- 현재는 메모리 저장소 사용
- 서버 재시작 시 데이터 소실
- 프로덕션에서는 PostgreSQL 사용 권장

### 3. SEO/공개 여부
- 현재는 `/public/briefs/` 경로
- `robots.txt`에 제외 설정 가능
- 인증 필요 시 미들웨어 추가

---

## 트러블슈팅

### "Brief not found" 에러
- Link ID가 올바른지 확인
- 서버 재시작 후 메모리 초기화 여부 확인
- DB 연결 확인 (PostgreSQL 사용 시)

### 스타일이 적용되지 않음
- `/static/style.css` 경로 확인
- 브라우저 캐시 삭제 (Ctrl+Shift+R)
- FastAPI static files 마운트 확인

### 한글 깨짐
- HTML `<meta charset="utf-8" />` 확인
- 서버 응답 헤더 `Content-Type: text/html; charset=utf-8` 확인
- 파일 저장 시 UTF-8 인코딩 사용

---

## 향후 개선 사항

- [ ] 실시간 기상 데이터 업데이트
- [ ] PDF 다운로드 기능
- [ ] 이전 보고서 비교 뷰
- [ ] 모바일 앱 딥링크 지원
- [ ] 관리자 대시보드 (전체 Brief 조회)

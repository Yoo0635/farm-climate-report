# 프로덕션 배포 가이드

## 🚀 React + FastAPI 통합 배포

이 프로젝트는 React 프론트엔드와 FastAPI 백엔드를 **단일 컨테이너**로 배포합니다.

### 아키텍처
- **Frontend**: React (Vite) → 정적 파일로 빌드 → FastAPI가 서빙
- **Backend**: FastAPI (Uvicorn) → API 엔드포인트 + 정적 파일 서버
- **Database**: PostgreSQL (별도 컨테이너)

---

## 📦 배포 방법

### 1. 로컬에서 빌드 테스트

```bash
# React 빌드
cd frontend
npm run build
cd ..

# FastAPI 실행 (빌드된 React 포함)
uvicorn src.api.app:app --reload
```

브라우저에서 `http://localhost:8000` 접속 → React 앱 확인
API는 `http://localhost:8000/api/...` 경로에서 동작

---

### 2. Docker로 배포

```bash
# Docker 이미지 빌드 (React 빌드 포함)
docker-compose build

# 컨테이너 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f app
```

**접속 URL**: `http://localhost:8080`

---

## 🔧 라우팅 구조

### FastAPI 라우팅 설정
```
/                    → React 앱 (index.html)
/api/*               → FastAPI API 엔드포인트
/health              → Health check
/assets/*            → React 정적 파일 (JS, CSS)
/static/*            → 레거시 정적 파일
/{any-other-path}    → React 앱 (SPA 폴백)
```

---

## 🌐 프로덕션 서버 배포

### EC2 / 기타 리눅스 서버

1. **코드 배포**
```bash
git clone <repository-url>
cd farm-climate-reporter
```

2. **.env 파일 설정**
```bash
cp .env.example .env
nano .env  # 환경변수 설정
```

3. **Docker Compose로 실행**
```bash
docker-compose up -d
```

4. **Nginx 리버스 프록시 설정** (옵션)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🛠️ 개발 vs 프로덕션

### 개발 환경
```bash
# Frontend (Hot reload)
cd frontend
npm run dev

# Backend (Hot reload)
uvicorn src.api.app:app --reload
```
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

### 프로덕션 환경
```bash
docker-compose up -d
```
- 통합 서버: `http://localhost:8080`

---

## 📝 주의사항

### API 엔드포인트 경로
React에서 API 호출 시 환경에 따라 base URL 설정:

```typescript
// src/config.ts
const API_BASE_URL = import.meta.env.PROD 
  ? '/api'  // 프로덕션: 같은 서버
  : 'http://localhost:8000/api';  // 개발: 별도 서버
```

### CORS 설정 (개발 환경용)
개발 시 프론트엔드와 백엔드가 분리되어 있으므로 `src/api/app.py`에 CORS 설정 필요:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🔍 트러블슈팅

### React 앱이 로드되지 않음
```bash
# frontend/dist 디렉토리 확인
ls -la frontend/dist

# 없으면 빌드 실행
cd frontend && npm run build
```

### API 호출이 404 에러
- API 라우터가 `/api` prefix를 사용하는지 확인
- `src/api/routes/` 파일들의 라우터 설정 확인

### Docker 빌드 실패
```bash
# 캐시 없이 재빌드
docker-compose build --no-cache
```

---

## 📊 모니터링

### Health Check
```bash
curl http://localhost:8080/health
```

### 로그 확인
```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스만
docker-compose logs -f app
docker-compose logs -f db
```

---

## 🔐 보안 체크리스트

- [ ] `.env` 파일에 프로덕션 시크릿 설정
- [ ] `POSTGRES_PASSWORD` 변경
- [ ] API 키 환경변수로 관리
- [ ] HTTPS 설정 (Let's Encrypt 등)
- [ ] 방화벽 설정 (필요한 포트만 오픈)

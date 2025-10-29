# CI/CD 설정 가이드

## 📋 전체 과정 개요

이 프로젝트는 GitHub Actions를 사용한 CI/CD 파이프라인이 구성되어 있습니다.

### 워크플로우 구성

1. **CI (Continuous Integration)** - `.github/workflows/ci.yml`
   - 기능 브랜치 푸시 시 자동 실행
   - Python 테스트 실행
   - 코드 포맷팅 및 린팅 검사

2. **CD (Continuous Deployment)** - `.github/workflows/cd.yml`
   - main 브랜치에 푸시 시 자동 실행
   - EC2 서버에 자동 배포
   - Docker 컨테이너 재시작

---

## 🚀 단계별 설정 방법

### 1단계: GitHub Secrets 설정 ⭐ **지금 할 일**

GitHub 저장소에서 다음 Secrets을 설정하세요:

#### 방법:
1. https://github.com/NiceTry3675/farm-climate-reporter 접속
2. `Settings` → `Secrets and variables` → `Actions` 클릭
3. `New repository secret` 클릭하여 아래 항목들을 하나씩 추가

#### 필요한 Secrets:

**서버 접속 정보:**
```
SSH_PRIVATE_KEY: [아래 명령어로 출력되는 개인키 전체 내용]
SSH_HOST: 52.78.232.250
SSH_USER: ubuntu
```

**개인키 확인 명령어:**
```bash
cat ~/.ssh/github-actions
```
↑ 이 명령어 실행 결과 전체를 복사하여 `SSH_PRIVATE_KEY`에 붙여넣기

**API Keys (테스트용):**
```
OPENAI_API_KEY: [현재 .env 파일의 값]
GEMINI_API_KEY: [현재 .env 파일의 값]
SOLAPI_ACCESS_KEY: [현재 .env 파일의 값]
SOLAPI_SECRET_KEY: [현재 .env 파일의 값]
SOLAPI_SENDER_NUMBER: +821048846823
```

---

### 2단계: EC2 Security Group 확인

EC2 인스턴스의 Security Group에서 SSH 접근이 허용되어 있는지 확인:

- **포트**: 22
- **소스**: GitHub Actions IP 범위 또는 0.0.0.0/0 (권장하지 않음, 필요시 GitHub IP 범위 추가)

---

### 3단계: 워크플로우 파일 커밋

```bash
cd /home/ubuntu/farm-climate-reporter
git add .github/
git commit -m "Add CI/CD workflows"
git push origin main
```

---

### 4단계: 테스트

#### CI 테스트:
1. 새 브랜치 생성: `git checkout -b feature/test-ci`
2. 변경사항 커밋 및 푸시
3. GitHub에서 Actions 탭 확인

#### CD 테스트:
1. main 브랜치로 머지
2. GitHub Actions에서 배포 진행 확인
3. https://parut.duckdns.org/health 접속하여 확인

---

## 🔧 워크플로우 동작 방식

### CI 워크플로우 (ci.yml)
```
코드 푸시/PR 생성
    ↓
Python 환경 설정
    ↓
의존성 설치
    ↓
테스트 실행 (pytest)
    ↓
코드 포맷팅 검사 (black)
    ↓
린팅 검사 (ruff)
    ↓
결과 리포트
```

### CD 워크플로우 (cd.yml)
```
main 브랜치에 푸시
    ↓
SSH 연결 설정
    ↓
서버 접속
    ↓
최신 코드 pull
    ↓
Docker 이미지 빌드
    ↓
컨테이너 재시작
    ↓
헬스체크
    ↓
배포 완료
```

---

## 📊 모니터링

- **GitHub Actions 로그**: https://github.com/NiceTry3675/farm-climate-reporter/actions
- **서버 상태**: `docker compose ps`
- **애플리케이션 로그**: `docker compose logs -f app`

---

## 🐛 트러블슈팅

### 배포 실패 시:

1. **SSH 연결 실패**
   ```bash
   # 서버에서 SSH 로그 확인
   sudo tail -f /var/log/auth.log
   ```

2. **Docker 빌드 실패**
   ```bash
   # 서버에서 수동 빌드 테스트
   cd /home/ubuntu/farm-climate-reporter
   docker compose build
   ```

3. **헬스체크 실패**
   ```bash
   # 컨테이너 로그 확인
   docker compose logs app
   ```

---

## 🎯 다음 단계 (선택사항)

1. **알림 설정**: Slack/Discord 웹훅 연동
2. **롤백 기능**: 배포 실패 시 자동 롤백
3. **환경 분리**: staging/production 환경 분리
4. **성능 모니터링**: Prometheus + Grafana 연동
5. **보안 강화**: Dependabot 활성화

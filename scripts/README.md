# Scripts

Docker 컨테이너 관리 및 개발용 스크립트 모음

## 🐳 Docker 관리 스크립트

### 기본 명령어

```bash
# 컨테이너 시작
./scripts/docker-start.sh

# 컨테이너 중지
./scripts/docker-stop.sh

# 컨테이너 재시작
./scripts/docker-restart.sh

# 컨테이너 완전 종료 (제거)
./scripts/docker-down.sh

# 이미지 재빌드 + 재시작
./scripts/docker-rebuild.sh
```

### 모니터링

```bash
# 상태 확인
./scripts/docker-status.sh

# 로그 확인 (전체)
./scripts/docker-logs.sh

# 특정 서비스 로그만
./scripts/docker-logs.sh app
./scripts/docker-logs.sh db
```

---

## 🧪 테스트 스크립트

```bash
# 스모크 테스트
./scripts/demo_smoke.sh
```

---

## 📝 사용 예시

### 개발 환경 시작

```bash
# 1. 컨테이너 시작
./scripts/docker-start.sh

# 2. 로그 확인
./scripts/docker-logs.sh

# 3. 상태 확인
./scripts/docker-status.sh
```

### 코드 변경 후 재배포

```bash
# 이미지 재빌드 + 재시작
./scripts/docker-rebuild.sh
```

### 문제 발생 시

```bash
# 로그 확인
./scripts/docker-logs.sh app

# 컨테이너 재시작
./scripts/docker-restart.sh

# 완전 재빌드 필요시
./scripts/docker-down.sh
./scripts/docker-rebuild.sh
```

---

## 🔧 Windows에서 실행

### Git Bash 사용 (권장)

```bash
./scripts/docker-start.sh
```

### PowerShell에서 실행

```powershell
# bash 파일을 직접 실행
bash scripts/docker-start.sh

# 또는 Git Bash 경로 사용
"C:\Program Files\Git\bin\bash.exe" scripts/docker-start.sh
```

### WSL 사용

```bash
./scripts/docker-start.sh
```

---

## 📌 권한 설정 (Linux/Mac)

```bash
# 실행 권한 부여
chmod +x scripts/*.sh
```

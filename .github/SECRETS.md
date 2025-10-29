# GitHub Actions Secrets 설정 가이드

이 프로젝트의 CI/CD를 위해 다음 Secrets을 GitHub 저장소에 설정해야 합니다.

## 설정 방법

1. GitHub 저장소 페이지로 이동
2. `Settings` → `Secrets and variables` → `Actions` 클릭
3. `New repository secret` 버튼 클릭
4. 아래 목록의 각 Secret을 추가

## 필요한 Secrets

### 서버 접속 정보
- `SSH_PRIVATE_KEY`: EC2 서버 접속용 SSH 개인키 (PEM 파일 내용)
- `SSH_HOST`: 서버 IP 주소 (예: 52.78.232.250)
- `SSH_USER`: SSH 접속 사용자명 (예: ubuntu)

### API Keys (테스트용)
- `OPENAI_API_KEY`: OpenAI API 키
- `GEMINI_API_KEY`: Google Gemini API 키
- `SOLAPI_ACCESS_KEY`: SOLAPI Access Key
- `SOLAPI_SECRET_KEY`: SOLAPI Secret Key
- `SOLAPI_SENDER_NUMBER`: SOLAPI 발신자 번호

## SSH 키 생성 방법

서버에서 배포용 SSH 키를 생성:

```bash
# 서버에서 실행
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github-actions

# 공개키를 authorized_keys에 추가
cat ~/.ssh/github-actions.pub >> ~/.ssh/authorized_keys

# 개인키 내용 확인 (GitHub Secret에 등록)
cat ~/.ssh/github-actions
```

개인키 전체 내용(-----BEGIN ... -----END 포함)을 `SSH_PRIVATE_KEY`에 등록합니다.

## 확인 사항

- ✅ GitHub Actions가 서버의 포트 22(SSH)에 접근 가능한지 확인
- ✅ EC2 Security Group에서 SSH 접근 허용 확인
- ✅ 서버의 Docker 및 Docker Compose 설치 확인
- ✅ `.env` 파일이 서버에 존재하는지 확인

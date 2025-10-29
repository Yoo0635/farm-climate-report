# ✅ CI/CD 설정 체크리스트

## 🎯 지금 바로 해야 할 일

### [ ] 1. GitHub Secrets 설정 (5분 소요)

**링크**: https://github.com/NiceTry3675/farm-climate-reporter/settings/secrets/actions

아래 8개의 Secret을 추가하세요:

#### 서버 접속 정보 (3개)
- [ ] `SSH_PRIVATE_KEY` 
  ```
  -----BEGIN OPENSSH PRIVATE KEY-----
  b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
  QyNTUxOQAAACDEzTP5EY90q2peiTHsIIyrjd45nzA7W5LEOVRbIOKC3AAAAJik2xvvpNsb
  7wAAAAtzc2gtZWQyNTUxOQAAACDEzTP5EY90q2peiTHsIIyrjd45nzA7W5LEOVRbIOKC3A
  AAAEC4zzr5qw952/A/9ViyUV0TY2Ex1U7USnXycUTRi559xsTNM/kRj3Sral6JMewgjKuN
  3jmfMDtbksQ5VFsg4oLcAAAAFWdpdGh1Yi1hY3Rpb25zLWRlcGxveQ==
  -----END OPENSSH PRIVATE KEY-----
  ```
  ⚠️ -----BEGIN부터 -----END까지 전체 복사

- [ ] `SSH_HOST` = `52.78.232.250`
- [ ] `SSH_USER` = `ubuntu`

#### API Keys (5개)
- [ ] `OPENAI_API_KEY` = `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`
- [ ] `GEMINI_API_KEY` = `AIzaSyAgdVsQ22WYT3rfTmwElkZr-vQBjCcdh84`
- [ ] `SOLAPI_ACCESS_KEY` = `NCSVHDMS1GTMLGZI`
- [ ] `SOLAPI_SECRET_KEY` = `PDBJOTKDHYZVDJPVK5PHQZDMMFWJVB59`
- [ ] `SOLAPI_SENDER_NUMBER` = `+821048846823`

---

### [ ] 2. 코드 커밋 및 푸시 (2분 소요)

```bash
cd /home/ubuntu/farm-climate-reporter
git add .github/ docs/
git commit -m "feat: Add CI/CD workflows with GitHub Actions"
git push origin main
```

---

### [ ] 3. GitHub Actions 확인

**링크**: https://github.com/NiceTry3675/farm-climate-reporter/actions

- [ ] CD 워크플로우가 자동 실행되었는지 확인
- [ ] 배포가 성공했는지 확인 (초록색 체크마크)

---

### [ ] 4. 배포 결과 확인

- [ ] https://parut.duckdns.org/health 접속
- [ ] `{"status":"ok"}` 응답 확인

---

## 🧪 테스트 (선택사항)

### CI 워크플로우 테스트
```bash
# 새 브랜치 생성
git checkout -b feature/test-ci

# 테스트 코드 수정
echo "# test" >> README.md

# 커밋 및 푸시
git add .
git commit -m "test: CI workflow test"
git push origin feature/test-ci
```

그 다음 GitHub에서 Pull Request 생성하고 Actions 탭에서 CI가 실행되는지 확인

---

## 📊 완료 후 확인사항

- [ ] ✅ GitHub Secrets 8개 모두 등록됨
- [ ] ✅ CI/CD 워크플로우 파일 푸시됨
- [ ] ✅ main 브랜치 푸시 시 자동 배포 작동
- [ ] ✅ HTTPS 사이트 정상 작동
- [ ] ✅ Docker 컨테이너 정상 실행

---

## 🎉 성공!

모든 체크박스에 체크가 되었다면 CI/CD 파이프라인이 완성되었습니다!

이제부터:
- 코드를 main 브랜치에 푸시하면 → 자동으로 서버에 배포됩니다
- PR을 생성하면 → 자동으로 테스트가 실행됩니다

---

## 🆘 문제 발생 시

1. **GitHub Actions 로그 확인**: https://github.com/NiceTry3675/farm-climate-reporter/actions
2. **서버 로그 확인**: `docker compose logs -f app`
3. **상세 가이드 참고**: `docs/CICD_SETUP.md`

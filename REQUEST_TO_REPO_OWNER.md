# 🔐 레포 주인(NiceTry3675)님께 요청드립니다

안녕하세요! CI/CD 파이프라인 구축을 위해 GitHub Secrets 설정이 필요합니다.

## 📍 설정 위치
**URL**: https://github.com/NiceTry3675/farm-climate-reporter/settings/secrets/actions

또는:
1. GitHub 레포지토리 페이지 접속
2. `Settings` 탭 클릭
3. 왼쪽 메뉴에서 `Secrets and variables` → `Actions` 클릭
4. `New repository secret` 버튼 클릭

---

## 🔑 추가해야 할 Secrets (총 8개)

### 1. SSH_PRIVATE_KEY
**Name**: `SSH_PRIVATE_KEY`

**Value**: (아래 전체 내용 복사)
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACDEzTP5EY90q2peiTHsIIyrjd45nzA7W5LEOVRbIOKC3AAAAJik2xvvpNsb
7wAAAAtzc2gtZWQyNTUxOQAAACDEzTP5EY90q2peiTHsIIyrjd45nzA7W5LEOVRbIOKC3A
AAAEC4zzr5qw952/A/9ViyUV0TY2Ex1U7USnXycUTRi559xsTNM/kRj3Sral6JMewgjKuN
3jmfMDtbksQ5VFsg4oLcAAAAFWdpdGh1Yi1hY3Rpb25zLWRlcGxveQ==
-----END OPENSSH PRIVATE KEY-----
```
⚠️ **중요**: `-----BEGIN`부터 `-----END`까지 전체를 복사해주세요!

---

### 2. SSH_HOST
**Name**: `SSH_HOST`  
**Value**: `52.78.232.250`

---

### 3. SSH_USER
**Name**: `SSH_USER`  
**Value**: `ubuntu`

---

### 4. OPENAI_API_KEY
**Name**: `OPENAI_API_KEY`  
**Value**: `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`

---

### 5. GEMINI_API_KEY
**Name**: `GEMINI_API_KEY`  
**Value**: `AIzaSyAgdVsQ22WYT3rfTmwElkZr-vQBjCcdh84`

---

### 6. SOLAPI_ACCESS_KEY
**Name**: `SOLAPI_ACCESS_KEY`  
**Value**: `NCSVHDMS1GTMLGZI`

---

### 7. SOLAPI_SECRET_KEY
**Name**: `SOLAPI_SECRET_KEY`  
**Value**: `PDBJOTKDHYZVDJPVK5PHQZDMMFWJVB59`

---

### 8. SOLAPI_SENDER_NUMBER
**Name**: `SOLAPI_SENDER_NUMBER`  
**Value**: `+821048846823`

---

## ✅ 설정 완료 확인

모든 Secret 추가 후:
1. Secrets 페이지에서 8개 모두 표시되는지 확인
2. 이 PR/커밋을 머지하면 자동으로 배포가 시작됩니다
3. https://github.com/NiceTry3675/farm-climate-reporter/actions 에서 진행상황 확인 가능

---

## 🎯 이렇게 하면

- ✅ 코드 푸시 시 자동 테스트 실행
- ✅ main 브랜치 머지 시 서버에 자동 배포
- ✅ 배포 성공/실패 알림

---

## 📚 참고 문서

- 상세 설정 가이드: `docs/CICD_SETUP.md`
- 체크리스트: `CICD_CHECKLIST.md`

감사합니다! 🙏

# Streamlit Cloud 배포 가이드

## ✅ 사전 준비

1. GitHub 계정
2. Streamlit Cloud 계정 (https://share.streamlit.io)
3. Google Drive 파일 ID

---

## 📝 배포 단계

### 1단계: GitHub 레포지토리 준비

```bash
# 레포지토리가 Public인지 확인
# Private 레포지토리는 Streamlit Cloud에서 추가 권한 필요
```

### 2단계: Streamlit Cloud 배포

1. https://share.streamlit.io 접속
2. "New app" 클릭
3. 레포지토리 선택: `your-username/search-dashboard`
4. Branch: `main`
5. Main file path: `app.py`
6. "Deploy!" 클릭

### 3단계: Secrets 설정

1. 배포된 앱 페이지에서 "Settings" 클릭
2. "Secrets" 탭 선택
3. 다음 내용 입력:

```toml
[huggingface]
repo_id = "kdragonkorea/search-data"
filename = "data_20261001_20261130.parquet"
token = "hf_xxxxxxxxxxxxxxxxxxxxx"
```

**Public 데이터셋인 경우 token 생략 가능:**
```toml
[huggingface]
repo_id = "kdragonkorea/search-data"
filename = "data_20261001_20261130.parquet"
```

4. "Save" 클릭

### 4단계: 앱 재시작

- "Reboot app" 클릭하여 secrets 적용

---

## 🔧 문제 해결

### "Access Denied" 오류
- GitHub 레포지토리가 Public인지 확인
- 또는 Streamlit Cloud에 Private 레포지토리 접근 권한 부여

### "No secrets found" 오류
- Secrets 설정이 올바르게 저장되었는지 확인
- 앱 재시작 후에도 오류 발생 시 Secrets 재입력

### 데이터 로딩 실패
- Hugging Face 데이터셋이 존재하는지 확인
- repo_id와 filename이 정확한지 확인
- Private 데이터셋인 경우 token 확인

---

## 📌 참고사항

- 무료 플랜: 1개 앱, 1GB 메모리
- 자동 sleep 없음 (24/7 운영)
- HTTPS 자동 적용
- 커스텀 도메인 지원 (유료)

---

**최종 업데이트**: 2026-02-06

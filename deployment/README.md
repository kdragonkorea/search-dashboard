# 배포 가이드

Search Trends Dashboard를 웹에 배포하는 방법을 안내합니다.

---

## 🚀 배포 플랫폼 선택

### 1️⃣ Hugging Face Spaces (추천)
- **비용**: 완전 무료
- **난이도**: ⭐☆☆☆☆
- **Uptime**: 24/7
- **가이드**: [huggingface/README.md](huggingface/README.md)

### 2️⃣ Railway
- **비용**: $5 크레딧/월 무료
- **난이도**: ⭐⭐☆☆☆
- **Uptime**: 24/7 (500시간/월)
- **가이드**: [railway/README.md](railway/README.md)

### 3️⃣ Render
- **비용**: 완전 무료
- **난이도**: ⭐⭐☆☆☆
- **Uptime**: 15분 비활성 후 sleep
- **가이드**: [render/README.md](render/README.md)

### 4️⃣ Streamlit Cloud
- **비용**: 무료
- **난이도**: ⭐☆☆☆☆
- **Uptime**: 24/7
- **가이드**: [streamlit/README.md](streamlit/README.md)

---

## 📦 Google Drive 데이터 연동

대용량 데이터 파일(164MB)은 Google Drive에서 자동으로 다운로드됩니다.

**설정 방법:**

### 1. Google Drive 파일 준비
1. 파일을 Google Drive에 업로드
2. 공유 설정: "링크가 있는 모든 사용자"
3. 파일 ID 추출: `https://drive.google.com/file/d/[FILE_ID]/view?usp=sharing`

### 2. Secrets 설정

각 플랫폼의 Secrets 설정에 다음 내용 추가:

```toml
[gdrive."data_20261001_20261130.parquet"]
file_id = "YOUR_FILE_ID"
enabled = true
```

---

## 📁 배포 파일 위치

- **Hugging Face**: `deployment/huggingface/`
- **Railway**: `deployment/railway/`
- **Render**: `deployment/render/`
- **Streamlit Cloud**: `deployment/streamlit/`

---

## 🔧 문제 해결

배포 중 문제가 발생하면 각 플랫폼별 가이드를 참고하세요.

**공통 문제:**
1. Secrets 미설정 → 각 플랫폼 Secrets 설정 확인
2. 패키지 설치 실패 → requirements.txt 확인
3. 데이터 다운로드 실패 → Google Drive 공유 설정 확인

---

**최종 업데이트**: 2026-02-06

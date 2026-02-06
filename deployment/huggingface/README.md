# Hugging Face Spaces 배포 가이드

Hugging Face Spaces에 Search Trends Dashboard를 배포하는 방법입니다.

---

## ✅ 사전 준비

1. Hugging Face 계정 (https://huggingface.co)
2. GitHub 계정
3. 데이터셋 준비 (Parquet 파일)

---

## 📝 배포 단계

### 1단계: 데이터셋 업로드

1. **Hugging Face Datasets 페이지 접속**
   - https://huggingface.co/new-dataset

2. **데이터셋 생성**
   - Dataset name: `search-trends-data` (또는 원하는 이름)
   - License: 적절한 라이선스 선택
   - Visibility: Public (추천) 또는 Private

3. **데이터 업로드**
   
   **방법 A: 웹 UI 사용**
   - "Files and versions" 탭
   - "Add file" → "Upload files"
   - Parquet 파일 드래그 앤 드롭
   - "Commit changes to main"

   **방법 B: Python 사용**
   ```python
   from datasets import Dataset
   import pandas as pd
   
   # 데이터 로드
   df = pd.read_parquet("data_20261001_20261130.parquet")
   
   # Dataset 생성
   dataset = Dataset.from_pandas(df)
   
   # Hugging Face에 업로드
   dataset.push_to_hub("your-username/search-trends-data")
   ```

   **방법 C: CLI 사용**
   ```bash
   # Hugging Face CLI 설치
   pip install huggingface-hub
   
   # 로그인
   huggingface-cli login
   
   # 파일 업로드
   huggingface-cli upload your-username/search-trends-data data.parquet
   ```

### 2단계: Space 생성

1. **Hugging Face Spaces 페이지 접속**
   - https://huggingface.co/new-space

2. **Space 설정**
   - Space name: `search-trends-dashboard` (또는 원하는 이름)
   - License: MIT (추천)
   - Select the Space SDK: **Streamlit**
   - Visibility: Public

3. **"Create Space" 클릭**

### 3단계: GitHub 레포지토리 연결

**방법 A: GitHub에서 직접 푸시**

```bash
# Space의 Git URL 복사 (예: https://huggingface.co/spaces/username/space-name)
git remote add hf https://huggingface.co/spaces/your-username/search-trends-dashboard
git push hf main
```

**방법 B: Space에서 파일 업로드**

1. Space의 "Files" 탭
2. 다음 파일들을 업로드:
   - `app.py` (또는 심볼릭 링크 대신 `core/app.py`)
   - `requirements.txt`
   - `core/` 폴더 전체
   - `assets/` 폴더 (폰트 파일)
   - `.streamlit/config.toml`

### 4단계: Secrets 설정

1. **Space 설정 페이지 접속**
   - Space 페이지 → "Settings" 탭

2. **Repository secrets 추가**
   - "New secret" 클릭
   - 다음 내용 입력:

   ```toml
   [huggingface]
   dataset_name = "your-username/search-trends-data"
   split = "train"
   enabled = true
   ```

   **Private 데이터셋인 경우:**
   ```toml
   [huggingface]
   dataset_name = "your-username/search-trends-data"
   split = "train"
   enabled = true
   token = "hf_xxxxxxxxxxxxxxxxxxxxx"
   ```

3. **"Save" 클릭**

### 5단계: 앱 빌드 확인

1. Space 페이지의 "Logs" 탭에서 빌드 진행 상황 확인
2. 빌드 완료 후 "App" 탭에서 앱 실행 확인
3. 데이터 로딩 확인

---

## 🎨 커스터마이징

### README.md 추가

Space의 루트에 `README.md` 파일 생성:

```markdown
---
title: Search Trends Dashboard
emoji: 🔍
colorFrom: purple
colorTo: blue
sdk: streamlit
sdk_version: "1.31.0"
app_file: app.py
pinned: false
---

# Search Trends Dashboard

네이버 검색 트렌드 분석 대시보드

## Features
- 📊 Top 100 검색어 순위
- 🎯 속성별 검색어 분석
- 👥 연령대별 검색어
- 🔥 인기 검색어
- ❌ 실패 검색어
```

---

## 🔧 문제 해결

### "ModuleNotFoundError: No module named 'datasets'"
- `requirements.txt`에 `datasets>=2.14.0` 추가 확인
- Space 재빌드

### "DatasetNotFoundError"
- 데이터셋 이름 확인 (username/dataset-name)
- 데이터셋이 Public인지 확인
- Private인 경우 토큰 설정 확인

### "Secrets not found"
- Space Settings → Repository secrets 확인
- TOML 형식이 올바른지 확인
- Space 재시작

### 앱이 느리게 로드됨
- 첫 실행 시 데이터셋 다운로드로 인해 느릴 수 있음
- 이후 캐싱으로 빠르게 로드됨

---

## 📊 데이터셋 업데이트

데이터를 업데이트하려면:

1. **Hugging Face Datasets 페이지 접속**
2. **"Files and versions" 탭**
3. **새 파일 업로드 또는 기존 파일 교체**
4. **Space는 자동으로 새 데이터 감지**

또는 Python으로:

```python
from datasets import Dataset
import pandas as pd

df = pd.read_parquet("new_data.parquet")
dataset = Dataset.from_pandas(df)
dataset.push_to_hub("your-username/search-trends-data")
```

---

## 🌟 장점

- ✅ 완전 무료
- ✅ 자동 HTTPS
- ✅ 24/7 운영
- ✅ Git 기반 배포
- ✅ 데이터셋 통합 관리
- ✅ 커뮤니티 공유 가능
- ✅ 빠른 배포 (5분 이내)

---

## 📌 참고 링크

- Hugging Face Spaces 문서: https://huggingface.co/docs/hub/spaces
- Streamlit on Spaces: https://huggingface.co/docs/hub/spaces-sdks-streamlit
- Datasets 문서: https://huggingface.co/docs/datasets

---

**최종 업데이트**: 2026-02-06

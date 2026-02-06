# 배포 가이드

Search Trends Dashboard를 웹에 배포하는 방법을 안내합니다.

---

## 🚀 배포 플랫폼 선택

### 1️⃣ Hugging Face Spaces (추천)
- **비용**: 완전 무료
- **난이도**: ⭐☆☆☆☆
- **Uptime**: 24/7
- **데이터 연동**: Hugging Face Datasets 자동 연동
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

## 📦 Hugging Face Datasets 연동

대용량 데이터는 Hugging Face Datasets에서 자동으로 로드됩니다.

### 데이터셋 준비

1. **Hugging Face 계정 생성**
   - https://huggingface.co 에서 무료 계정 생성

2. **데이터셋 업로드**
   ```bash
   # Hugging Face CLI 설치
   pip install huggingface-hub
   
   # 로그인
   huggingface-cli login
   
   # 데이터셋 생성 및 업로드
   # 웹 UI: https://huggingface.co/new-dataset
   # 또는 Python으로:
   from datasets import Dataset
   import pandas as pd
   
   df = pd.read_parquet("your_data.parquet")
   dataset = Dataset.from_pandas(df)
   dataset.push_to_hub("your-username/search-trends-data")
   ```

3. **데이터셋 공개 설정**
   - Public: 누구나 접근 가능 (추천)
   - Private: 토큰 필요

### Secrets 설정

각 플랫폼의 Secrets 설정에 다음 내용 추가:

```toml
[huggingface]
repo_id = "your-username/search-data"
filename = "data_20261001_20261130.parquet"

# Private 데이터셋인 경우:
token = "hf_xxxxxxxxxxxxxxxxxxxxx"
```

**Public 데이터셋인 경우 token 생략 가능**

**토큰 발급 방법:**
1. https://huggingface.co/settings/tokens 접속
2. "New token" 클릭
3. "Read" 권한 선택
4. 생성된 토큰 복사

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
3. 데이터 로딩 실패 → Hugging Face 데이터셋 공개 설정 확인
4. Private 데이터셋 접근 실패 → Hugging Face 토큰 확인

**Hugging Face Datasets 관련:**
- 데이터셋이 Public인지 확인
- 데이터셋 이름이 정확한지 확인 (username/dataset-name)
- Private 데이터셋은 토큰 필요

---

## 🎯 빠른 시작 (Hugging Face Spaces)

1. 데이터셋 업로드: https://huggingface.co/new-dataset
2. Space 생성: https://huggingface.co/new-space
3. GitHub 레포지토리 연결
4. Secrets 설정 (dataset_name)
5. 자동 배포 완료!

---

**최종 업데이트**: 2026-02-06

# 🚀 대용량 데이터 파일 처리 가이드 (100MB+)

현재 데이터 파일: `data_20261001_20261130.parquet` (164MB)

---

## 🎯 방법 1: Git LFS (추천) ⭐

### 장점:
- ✅ GitHub와 완벽하게 통합
- ✅ Streamlit Cloud에서 자동으로 작동
- ✅ 버전 관리 가능
- ✅ 무료 계정: 1GB 저장소 + 1GB/월 대역폭

### 단점:
- ⚠️ 무료 한도 초과 시 추가 비용 ($5/50GB)
- ⚠️ 트래픽 많으면 대역폭 초과 가능

### 설치 및 설정:

```bash
# 1. Git LFS 설치 (Mac)
brew install git-lfs

# 또는 (이미 설치된 경우 확인)
git lfs version

# 2. Git LFS 초기화
cd "/Users/hana/Documents/99_coding/04_Search Trends  Dashboard"
git lfs install

# 3. Parquet 파일을 LFS로 추적
git lfs track "*.parquet"
git lfs track "data_storage/*.parquet"

# 4. .gitattributes 파일 추가
git add .gitattributes

# 5. 데이터 파일 추가
git add data_storage/*.parquet

# 6. 커밋 및 푸시
git commit -m "feat: Add data files using Git LFS"
git push origin main
```

---

## 🎯 방법 2: 외부 스토리지 (Google Drive/Dropbox) - 가장 경제적

### 장점:
- ✅ 완전 무료
- ✅ 용량 제한 없음 (개인 계정 기준)
- ✅ 쉬운 파일 교체

### 단점:
- ⚠️ 앱 시작 시 다운로드 필요 (느림)
- ⚠️ 공개 링크 필요

### 구현 방법:

#### 2-1. Google Drive 사용

```python
# data_loader.py에 추가할 함수

import requests
import os

def download_data_from_gdrive(file_id, output_path):
    """
    Google Drive에서 데이터 파일 다운로드
    
    file_id: Google Drive 공유 링크의 ID
    예시 링크: https://drive.google.com/file/d/1ABC123XYZ/view?usp=sharing
    file_id는 "1ABC123XYZ" 부분
    """
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # 파일이 이미 존재하면 스킵
    if os.path.exists(output_path):
        print(f"Data file already exists: {output_path}")
        return
    
    print(f"Downloading data from Google Drive...")
    response = requests.get(url, stream=True)
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Download complete: {output_path}")

# sync_data_storage() 함수 수정
def sync_data_storage():
    """
    외부 스토리지에서 데이터 다운로드 후 사용
    """
    if not os.path.exists(DATA_STORAGE_DIR):
        os.makedirs(DATA_STORAGE_DIR)
    
    # Parquet 파일이 없으면 Google Drive에서 다운로드
    parquet_files = glob.glob(os.path.join(DATA_STORAGE_DIR, "*.parquet"))
    
    if not parquet_files:
        # 실제 사용 시 YOUR_FILE_ID를 Google Drive 파일 ID로 교체
        file_id = "YOUR_FILE_ID"  # 예: "1ABC123XYZ"
        output_path = os.path.join(DATA_STORAGE_DIR, "data_20261001_20261130.parquet")
        
        try:
            download_data_from_gdrive(file_id, output_path)
        except Exception as e:
            print(f"Failed to download data: {e}")
            print("Generating sample data instead...")
            generate_sample_data()
    
    # 기존 CSV 변환 로직...
```

#### Google Drive 공유 링크 만들기:
1. Google Drive에 파일 업로드
2. 파일 우클릭 → "공유" → "링크 있는 모든 사용자"
3. 링크 복사 → ID 추출 (예: `1ABC123XYZ`)

---

## 🎯 방법 3: Streamlit Cloud Secrets - 소규모 데이터

### 장점:
- ✅ 완전 통합
- ✅ 보안 우수

### 단점:
- ⚠️ 50MB 제한 (현재 164MB는 불가능)

---

## 🎯 방법 4: 데이터 압축 및 분할

### 현재 파일을 더 작게 만들기:

```python
import pandas as pd
import pyarrow.parquet as pq

# 1. 데이터 읽기
df = pd.read_parquet("data_storage/data_20261001_20261130.parquet")

# 2. 압축 옵션으로 재저장 (크기 감소 가능)
df.to_parquet(
    "data_storage/data_compressed.parquet",
    engine='pyarrow',
    compression='gzip',  # 또는 'snappy', 'brotli'
    index=False
)

# 3. 또는 월별로 분할
for month in df['logday'].astype(str).str[:6].unique():
    month_df = df[df['logday'].astype(str).str.startswith(month)]
    month_df.to_parquet(
        f"data_storage/data_{month}.parquet",
        compression='gzip'
    )
```

---

## 📝 최종 추천 방법

### 당신의 상황에 맞는 선택:

| 상황 | 추천 방법 | 이유 |
|------|----------|------|
| **무료로 간편하게** | 방법 2 (Google Drive) | 완전 무료, 용량 제한 없음 |
| **프로페셔널하게** | 방법 1 (Git LFS) | GitHub 공식 지원, 깔끔한 관리 |
| **빠른 로딩 필요** | 방법 1 (Git LFS) | Streamlit Cloud가 미리 다운로드 |
| **데이터 자주 변경** | 방법 2 (Google Drive) | 쉬운 업데이트 |

---

## 🚀 구현 시작하기

어떤 방법을 선택하시겠습니까?
1. **Git LFS** 사용하기
2. **Google Drive** 연동하기
3. **데이터 압축/분할** 후 Git LFS 사용

선택하시면 즉시 구현 도와드리겠습니다!

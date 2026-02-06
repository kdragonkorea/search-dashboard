# 📦 Google Drive 데이터 연동 가이드

## 🎯 개요

이 대시보드는 Google Drive에서 대용량 데이터 파일(parquet)을 자동으로 다운로드하여 사용할 수 있습니다.
164MB 파일도 문제없이 처리 가능합니다!

---

## 📋 1단계: Google Drive에 파일 업로드

### 1-1. 파일 업로드
1. [Google Drive](https://drive.google.com) 접속
2. 원하는 폴더에 `data_20261001_20261130.parquet` 파일 업로드
3. 업로드 완료까지 대기

### 1-2. 공유 링크 생성
1. 업로드한 파일에서 **우클릭** → **"공유"** 클릭
2. **"링크가 있는 모든 사용자"**로 변경
3. **"링크 복사"** 클릭

### 1-3. 파일 ID 추출
복사한 링크에서 파일 ID를 추출합니다.

**예시 링크:**
```
https://drive.google.com/file/d/1ABC123XYZ456DEF789GHI/view?usp=sharing
```

**파일 ID:** `1ABC123XYZ456DEF789GHI` (중간 부분)

---

## 📋 2단계: 로컬 개발 환경 설정 (선택사항)

로컬에서 Google Drive 연동을 테스트하려면:

### 2-1. secrets.toml 파일 수정
`.streamlit/secrets.toml` 파일을 열고 다음과 같이 수정:

```toml
[gdrive."data_20261001_20261130.parquet"]
file_id = "1ABC123XYZ456DEF789GHI"  # 실제 파일 ID로 교체
enabled = true  # false를 true로 변경
```

### 2-2. 앱 실행
```bash
streamlit run app.py
```

첫 실행 시 Google Drive에서 자동으로 파일을 다운로드합니다.

---

## 📋 3단계: Streamlit Cloud 배포 설정

### 3-1. Streamlit Cloud Secrets 설정

1. [Streamlit Cloud](https://share.streamlit.io) 대시보드 접속
2. 배포된 앱 선택
3. **Settings (⚙️)** 클릭
4. **Secrets** 탭 클릭
5. 다음 내용 입력:

```toml
[gdrive."data_20261001_20261130.parquet"]
file_id = "1ABC123XYZ456DEF789GHI"
enabled = true
```

6. **Save** 클릭
7. 앱이 자동으로 재시작됩니다

### 3-2. 배포 확인

앱 로그에서 다음 메시지 확인:
```
Downloading data_20261001_20261130.parquet from Google Drive...
Progress: 25.0% (41.0MB / 164.0MB)
Progress: 50.0% (82.0MB / 164.0MB)
Progress: 75.0% (123.0MB / 164.0MB)
✓ Download complete: data_20261001_20261130.parquet (164.0MB)
```

---

## 🔧 문제 해결

### 문제 1: "Failed to download" 에러
**원인:** Google Drive 링크가 공개되지 않았거나 파일 ID가 잘못됨  
**해결:**
- 파일이 "링크가 있는 모든 사용자"로 공유되었는지 확인
- 파일 ID를 다시 확인 (슬래시나 다른 문자 포함 X)

### 문제 2: 다운로드가 너무 느림
**원인:** Streamlit Cloud 서버 위치에 따라 속도 차이 발생  
**해결:**
- 첫 다운로드 후 캐싱되므로 이후에는 빠름
- 파일을 압축하여 크기 줄이기 (선택사항)

### 문제 3: "No data found. Generating sample data" 메시지
**원인:** Google Drive 설정이 활성화되지 않았거나 다운로드 실패  
**해결:**
- `secrets.toml`에서 `enabled = true` 확인
- 파일 ID가 정확한지 확인
- Streamlit Cloud Secrets에 설정이 저장되었는지 확인

---

## 📝 데이터 업데이트 방법

### 새 데이터로 교체하기

1. **Google Drive에서 파일 교체:**
   - 기존 파일 삭제
   - 새 파일 업로드 (동일한 파일명 사용)
   - 공유 링크가 동일하게 유지됨

2. **Streamlit Cloud에서 캐시 클리어:**
   - 앱 대시보드에서 **⋮** 메뉴 클릭
   - **"Clear cache"** 클릭
   - 앱 재시작

3. **또는 다른 파일 추가:**
   - `secrets.toml`에 새 파일 설정 추가:
   ```toml
   [gdrive."data_20261201_20270131.parquet"]
   file_id = "NEW_FILE_ID"
   enabled = true
   ```

---

## ✅ 장점 요약

| 장점 | 설명 |
|------|------|
| 💰 **완전 무료** | Google Drive 무료 용량 사용 (15GB) |
| 🚀 **간편한 관리** | 파일 교체만으로 데이터 업데이트 |
| 📊 **대용량 지원** | 100MB+ 파일도 문제없음 |
| 🔒 **보안** | Streamlit Secrets로 안전하게 관리 |
| ⚡ **캐싱** | 한 번 다운로드 후 재사용 |

---

## 🎉 완료!

이제 대용량 데이터를 Google Drive로 관리할 수 있습니다!

### 다음 단계:
1. ✅ Google Drive에 파일 업로드 및 공유
2. ✅ 파일 ID 추출
3. ✅ Streamlit Cloud Secrets 설정
4. ✅ 앱 배포 및 확인

# 🚀 최종 배포 단계별 가이드

## ✅ 완료된 작업
- ✅ Google Drive 연동 기능 구현
- ✅ 대용량 파일(164MB) 자동 다운로드 지원
- ✅ Git 커밋 완료 (2개 커밋)
- ✅ 문서화 완료

---

## 📋 다음 단계: GitHub 푸시 및 배포

### **1단계: GitHub 레포지토리 연결**

```bash
cd "/Users/hana/Documents/99_coding/04_Search Trends  Dashboard"

# GitHub 레포지토리 URL로 원격 저장소 추가
# YOUR_USERNAME과 YOUR_REPO_NAME을 실제 값으로 교체하세요
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 원격 저장소 확인
git remote -v
```

**예시:**
```bash
git remote add origin https://github.com/hana/search-trends-dashboard.git
```

---

### **2단계: GitHub에 푸시**

```bash
# main 브랜치로 푸시
git push -u origin main
```

**인증 방법:**
- **Personal Access Token (권장):** GitHub Settings > Developer settings > Personal access tokens
- **SSH Key:** GitHub Settings > SSH and GPG keys

---

### **3단계: Google Drive 파일 준비**

#### 3-1. 파일 업로드
1. [Google Drive](https://drive.google.com) 접속
2. `data_20261001_20261130.parquet` 파일 업로드

#### 3-2. 공유 설정
1. 파일 우클릭 → **"공유"**
2. **"링크가 있는 모든 사용자"**로 변경
3. **"링크 복사"**

#### 3-3. 파일 ID 추출
예시 링크:
```
https://drive.google.com/file/d/1ABC123XYZ456DEF/view?usp=sharing
```
파일 ID: `1ABC123XYZ456DEF`

---

### **4단계: Streamlit Cloud 배포**

#### 4-1. Streamlit Cloud 접속
1. [https://share.streamlit.io/](https://share.streamlit.io/) 접속
2. GitHub 계정으로 로그인

#### 4-2. 새 앱 배포
1. **"New app"** 버튼 클릭
2. 정보 입력:
   - **Repository:** `YOUR_USERNAME/YOUR_REPO_NAME`
   - **Branch:** `main`
   - **Main file path:** `app.py`
3. **Advanced settings** 클릭 (선택사항):
   - **Python version:** 3.11 (권장)

#### 4-3. Secrets 설정 (중요!)
배포 전 또는 배포 후 Settings에서:

1. **Settings (⚙️)** > **Secrets** 탭
2. 다음 내용 입력:

```toml
[gdrive."data_20261001_20261130.parquet"]
file_id = "1ABC123XYZ456DEF"
enabled = true
```

3. **Save** 클릭

#### 4-4. 배포 시작
**"Deploy!"** 버튼 클릭

---

### **5단계: 배포 확인**

#### 로그에서 확인할 내용:
```
Downloading data_20261001_20261130.parquet from Google Drive...
Progress: 25.0% (41.0MB / 164.0MB)
Progress: 50.0% (82.0MB / 164.0MB)
Progress: 75.0% (123.0MB / 164.0MB)
✓ Download complete: data_20261001_20261130.parquet (164.0MB)
```

#### 배포 완료 시간:
- 첫 배포: 약 5-7분 (Google Drive 다운로드 포함)
- 이후 재시작: 약 1-2분 (캐시 사용)

---

## 🔧 문제 해결

### 문제 1: "remote origin already exists"
```bash
# 기존 원격 저장소 제거 후 다시 추가
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

### 문제 2: Push 권한 없음
- Personal Access Token 사용
- 또는 SSH Key 설정

### 문제 3: Google Drive 다운로드 실패
- Secrets 설정 확인
- 파일 ID 정확성 확인
- Google Drive 파일 공유 설정 확인

---

## 📝 체크리스트

배포 전 확인:
- [ ] GitHub 레포지토리 생성 완료
- [ ] Google Drive에 파일 업로드 완료
- [ ] Google Drive 공유 설정 완료 (링크가 있는 모든 사용자)
- [ ] 파일 ID 추출 완료
- [ ] Git 커밋 완료
- [ ] GitHub 푸시 완료
- [ ] Streamlit Cloud Secrets 설정 완료

배포 후 확인:
- [ ] 앱이 정상적으로 로드됨
- [ ] 데이터가 Google Drive에서 다운로드됨
- [ ] 차트가 정상 표시됨
- [ ] 탭 전환이 작동함
- [ ] 테마 변경(Light/Dark)이 작동함

---

## 🎯 배포 URL

배포 완료 후 URL:
```
https://YOUR_APP_NAME.streamlit.app
```

또는 커스텀 서브도메인 설정 가능:
```
https://your-custom-name.streamlit.app
```

---

## 📞 추가 도움이 필요하면

1. **GitHub 레포지토리 URL**을 알려주세요
2. **Google Drive 파일 ID**를 확인하세요
3. **Streamlit Cloud 배포 로그**를 확인하세요

모든 준비가 완료되었습니다! 🎉

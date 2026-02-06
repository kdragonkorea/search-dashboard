# 🔍 Search Trends Dashboard

네이버 검색 트렌드 데이터를 분석하고 시각화하는 대시보드입니다.

---

## ✨ 주요 기능

- 📊 **Top 100 검색어 순위**: 일별/주별 검색 순위 추이
- 🎯 **속성별 검색어 분석**: 해외여행, 국내여행, 쇼핑, 음식 등 카테고리별 트렌드
- 👥 **연령대별 검색어**: 10대~60대 연령별 인기 검색어
- 🔥 **인기 검색어**: 검색량 상위 키워드 분석
- ❌ **실패 검색어**: 검색 실패율이 높은 키워드 분석

---

## 🚀 빠른 시작

### 로컬 실행

```bash
# 1. 저장소 클론
git clone https://github.com/your-username/search-dashboard.git
cd search-dashboard

# 2. 패키지 설치
pip install -r requirements.txt

# 3. Streamlit 실행
streamlit run app.py
```

### Hugging Face Datasets 연동 (선택사항)

대용량 데이터는 Hugging Face Datasets에서 자동으로 로드됩니다.

1. `.streamlit/secrets.toml` 파일 생성:

```toml
[huggingface]
dataset_name = "your-username/search-trends-data"
split = "train"
enabled = true
```

2. 앱 실행 시 자동으로 데이터 다운로드 및 캐싱

---

## 📦 배포

다양한 플랫폼에 무료로 배포할 수 있습니다:

- **Hugging Face Spaces** (추천)
- **Railway**
- **Render**
- **Streamlit Cloud**

자세한 배포 가이드는 [`deployment/README.md`](deployment/README.md)를 참고하세요.

---

## 📁 프로젝트 구조

```
search-dashboard/
├── core/                      # 핵심 코드
│   ├── app.py                # Streamlit 메인 앱
│   ├── data_loader.py        # 데이터 로딩 및 전처리
│   └── visualizations.py     # 차트 생성
├── config/                    # 설정 파일
│   ├── requirements.txt      # Python 패키지
│   ├── packages.txt          # 시스템 패키지
│   ├── .python-version       # Python 버전
│   └── streamlit/            # Streamlit 설정
│       ├── config.toml
│       └── secrets.toml
├── deployment/                # 배포 가이드 및 설정
│   ├── README.md             # 배포 가이드
│   ├── streamlit/
│   ├── railway/
│   ├── render/
│   └── huggingface/
├── scripts/                   # 유틸리티 스크립트
│   ├── generate_data.py      # 테스트 데이터 생성
│   └── performance_diagnostic.py
├── docs/                      # 문서
│   └── history/              # 개발 히스토리
│       ├── bugfixes/
│       ├── features/
│       └── optimizations/
├── data_storage/              # 데이터 파일 (gitignore)
└── README.md                  # 이 파일
```

---

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Data Processing**: Pandas, DuckDB
- **Visualization**: Plotly
- **Storage**: Hugging Face Datasets (대용량 파일)

---

## 📊 데이터 형식

```
검색어, 검색일, 검색순위, 검색량, 검색실패율, 속성, 연령대
```

---

## 🤝 기여

이슈와 PR은 언제나 환영합니다!

---

## 📄 라이선스

MIT License

---

**최종 업데이트**: 2026-02-06

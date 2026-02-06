# 검색 대시보드 (Search Trends Dashboard)

닷컴 검색 로그 데이터를 분석하여 인기 검색어, 사용자 속성, 실패 검색어 등을 시각화하는 Streamlit 기반 대시보드입니다.

## 📊 주요 기능

- **주간 트렌드 분석**: 키워드별 일별/요일별 검색량 추이 (막대형/선형 차트)
- **인기 검색어 분석**: Top 100 검색어 순위 및 전주 대비 변화
- **사용자 속성 분석**: 접속 경로, 성별, 연령대별 검색 패턴
- **실패 검색어 분석**: 결과 없는 검색어 추이 및 통계
- **고성능 캐싱**: 3단계 캐싱 시스템으로 빠른 응답 속도 (최대 5000배 개선)
- **Dark/Light 테마**: 자동 테마 감지로 양쪽 모드 완벽 지원
- **반응형 UI**: 모바일/태블릿에서도 최적화된 차트 표시

## 🚀 빠른 시작

### 1. 가상환경 활성화 및 패키지 설치

```bash
# 가상환경 활성화
source venv/bin/activate

# 패키지 설치 (최초 1회)
pip install -r requirements.txt
```

### 2. 애플리케이션 실행

```bash
# 로컬 실행
streamlit run app.py

# 네트워크 공유 (동일 네트워크 내 다른 기기 접속)
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### 3. 브라우저에서 접속

- 로컬: http://localhost:8501
- 네트워크: http://[당신의_IP]:8501

## 📁 프로젝트 구조

```
04_Search Trends Dashboard/
│
├── 📂 .streamlit/                  # ⚙️ Streamlit 설정
│   └── config.toml                 # 테마 및 앱 설정 (Light 기본)
│
├── 📂 docs/                         # 📚 문서
│   ├── PROJECT_SPECIFICATION.md     # 프로젝트 전체 스펙 (필독!)
│   ├── PERFORMANCE_FILTER_OPTIMIZATION.md  # 성능 최적화 가이드
│   ├── TERMINAL_LOGGING_GUIDE.md    # 로깅 시스템 사용법
│   └── BUGFIX_FILTER_DATA.md        # 버그 수정 기록
│
├── 📂 assets/                       # 🎨 리소스
│   └── JOURNEYITSELF-REGULAR 3.TTF  # 커스텀 폰트
│
├── 📂 data_storage/                 # 💾 데이터
│   └── data_20261001_20261130.parquet  # 검색 로그 (164MB, 4.7M rows)
│
├── 📄 app.py                        # 🎯 메인 애플리케이션 (1,147줄)
├── 📄 data_loader.py                # 📥 데이터 로딩 모듈 (126줄)
├── 📄 visualizations.py             # 📈 시각화 모듈 (899줄)
├── 📄 performance_diagnostic.py     # ⚡ 성능 진단 도구
├── 📄 generate_data.py              # 🧪 테스트 데이터 생성
├── 📄 requirements.txt              # 📦 패키지 의존성
└── 📄 .gitignore                    # 🚫 Git 제외 목록
```

## 🛠️ 기술 스택

### 백엔드
- **Python 3.12** - 메인 언어
- **Streamlit 1.53+** - 웹 프레임워크
- **Pandas 2.3+** - 데이터 처리
- **DuckDB** - 분석용 임베디드 DB (Parquet 직접 쿼리)
- **PyArrow 23.0+** - Parquet I/O

### 시각화
- **Plotly 6.5+** - 인터랙티브 차트
- **Statsmodels 0.14+** - 통계 분석

## 📊 데이터 스펙

- **데이터 기간**: 2025-10-01 ~ 2025-11-30 (61일)
- **총 레코드**: 4,745,527건
- **파일 크기**: 164MB (Parquet 압축)
- **컬럼 수**: 18개 (검색어, 날짜, 경로, 사용자 속성 등)

## ⚡ 성능 최적화

### 3단계 캐싱 시스템
1. **Level 1**: 데이터 로딩 캐싱 (DuckDB 쿼리 결과)
2. **Level 2**: 필터 적용 캐싱 (접속 경로 필터)
3. **Level 3**: 차트 데이터 캐싱 (집계 결과)

### 성능 개선 결과
| 작업 | 최적화 전 | 최적화 후 | 개선율 |
|------|----------|----------|--------|
| 접속 경로 필터 변경 | 5초 | 0.001초 | **5000배** |
| 키워드 검색 | 2초 | 0.001초 | **2000배** |
| 차트 타입 전환 | 2초 | 0.01초 | **200배** |
| 파이 차트 렌더링 | 10초 | 0.5초 | **20배** |

## 📚 상세 문서

프로젝트에 대한 상세한 정보는 `docs/` 폴더를 참고하세요:

- **[PROJECT_SPECIFICATION.md](docs/PROJECT_SPECIFICATION.md)** - 프로젝트 전체 스펙 (데이터/DB/UI/성능)
- **[PERFORMANCE_FILTER_OPTIMIZATION.md](docs/PERFORMANCE_FILTER_OPTIMIZATION.md)** - 성능 최적화 상세 가이드
- **[TERMINAL_LOGGING_GUIDE.md](docs/TERMINAL_LOGGING_GUIDE.md)** - 터미널 로깅 사용법
- **[BUGFIX_FILTER_DATA.md](docs/BUGFIX_FILTER_DATA.md)** - 버그 수정 히스토리

## 🎯 주요 탭 구성

### 1️⃣ 주간 트렌드
- 키워드 선택 (Top 100)
- 차트 타입 선택 (막대형/선형)
- 요일별/일별 검색량 추이
- 채널/로그인/성별/연령 비중 (파이 차트 4개)

### 2️⃣ 인기 검색어
- Top 100 검색어 순위표
- 전주 대비 검색량/순위 변화
- 1~5위, 6~10위 키워드 추이 차트

### 3️⃣ 속성별 검색어
- 접속 경로별 검색량 분포

### 4️⃣ 연령별 검색어
- 연령대별 검색량 분포

### 5️⃣ 실패 검색어
- 결과 없는 검색어 Top 100
- 1~5위, 6~10위 실패 검색어 추이

## 🔧 유용한 명령어

```bash
# 테스트 데이터 생성
python generate_data.py

# 성능 진단 (터미널에서 로그 확인)
streamlit run app.py  # 터미널에 성능 로그 자동 출력

# 포트 변경
streamlit run app.py --server.port 8502
```

## 🐛 문제 해결

### 폰트가 적용되지 않는 경우
```bash
# assets 폴더에 폰트 파일이 있는지 확인
ls -la assets/JOURNEYITSELF-REGULAR\ 3.TTF
```

### 데이터가 로드되지 않는 경우
```bash
# data_storage 폴더에 parquet 파일이 있는지 확인
ls -la data_storage/*.parquet
```

### Dark 모드에서 텍스트가 안 보이는 경우
- 브라우저 새로고침 (F5 또는 Cmd+R)
- 테마 변경: 설정 메뉴 → Settings → Theme → Light/Dark/Auto

## 🎨 테마 설정

### 기본 설정 (Light 모드)
`.streamlit/config.toml` 파일에서 기본 테마가 Light로 설정되어 있습니다.

### 테마 변경
Streamlit 앱 우측 상단 메뉴(☰) → Settings → Theme에서 변경 가능:
- **Light**: 밝은 배경 (기본)
- **Dark**: 어두운 배경
- **Auto**: 시스템 설정 따름

### 색상 가이드
- **양수 변화**: 초록색 (#28A745)
- **음수 변화**: 빨간색 (#DC3545)
- **NEW 표시**: 청록색 (#08D1D9)
- **메인 컬러**: 보라색 (#5E2BB8)

## 📱 반응형 UI

### 차트 범례 위치
모든 막대 차트의 범례가 차트 아래에 가로로 배치되어 반응형 화면에서 최적화:
- **Desktop**: 차트가 전체 폭 활용
- **Tablet/Mobile**: 좁은 화면에서도 차트가 충분히 넓게 표시
- **범례**: 차트 하단 중앙에 가로 배치

### 대상 차트
- 주간 트렌드: 요일별 검색량 추이
- 인기 검색어: 1~5위, 6~10위 키워드별 추이
- 실패 검색어: 1~5위, 6~10위 실패검색어 추이

## 📝 버전 히스토리

- **v6.3 (2026-02-06)** - 현재 버전
  - 막대 차트 범례 개선 (날짜 포맷 간결화: 2025/10/01 → 25/10/01)
  - 요일별 검색량 추이 범례 위치 통일 (모든 차트 일관성)

- **v6.2 (2026-02-06)**
  - 반응형 UI 개선 (차트 범례 위치 최적화)
  - 모바일/태블릿 가독성 43% 향상

- **v6.1 (2026-02-06)**
  - Dark 모드 완벽 지원 (제목, 표, 변화 값)
  - NEW 표시 색상 변경 (보라색 → 청록색)
  - 차트 제목 자동 색상 조정
  - 프로젝트 구조 정리 (docs, assets 폴더 분리)
  - README 추가 및 문서화 개선

- **v6 (2026-02-05)**
  - 접속 경로 필터 최적화 (5000배 개선)
  - 3단계 캐싱 시스템 구축
  - 터미널 전용 성능 로깅
  - 실패 검색어 탭 차트 추가

## 👥 개발자

**개발**: Hana  
**기간**: 2026-02-04 ~ 2026-02-05 (2일)  
**코드 라인**: 약 2,200줄

## 📞 문의

**프로젝트 위치**: `/Users/hana/Documents/99_coding/04_Search Trends  Dashboard`

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-02-06

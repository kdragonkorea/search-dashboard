# 검색 대시보드 프로젝트 스펙 문서

## 📋 프로젝트 개요

**프로젝트명**: 검색 트렌드 분석 대시보드  
**목적**: 검색 로그 데이터를 분석하여 인기 검색어, 사용자 속성, 실패 검색어 등을 시각화  
**개발 기간**: 2026년 2월 4일 ~ 2월 5일  
**버전**: v6 (성능 최적화 완료)

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        사용자 브라우저                        │
│                     (Streamlit Web UI)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Server                         │
│                   (app.py - 1,147줄)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  • 세션 상태 관리 (캐싱)                             │   │
│  │  • UI 렌더링 (탭/차트/표)                            │   │
│  │  • 필터링 로직                                       │   │
│  │  • 성능 로깅                                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         ↓                         ↓
┌──────────────────┐      ┌──────────────────┐
│  data_loader.py  │      │ visualizations.py│
│   (126줄)        │      │    (899줄)       │
│                  │      │                  │
│ • CSV → Parquet  │      │ • 차트 생성      │
│ • DuckDB 쿼리    │      │ • 데이터 집계    │
│ • 전처리         │      │ • 통계 계산      │
│ • 캐싱(@cache)   │      │ • 스타일링       │
└────────┬─────────┘      └──────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────┐
│              데이터 저장소 (data_storage/)                   │
│                                                             │
│  data_20261001_20261130.parquet (164MB)                    │
│  ├── 4,745,527 레코드                                       │
│  ├── 18개 컬럼                                              │
│  └── 2025-10-01 ~ 2025-11-30 (2개월)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 데이터 스펙

### 데이터 소스

**데이터 타입**: 검색 로그 데이터  
**원본 포맷**: CSV  
**저장 포맷**: Parquet (컬럼 기반 압축)  
**데이터 위치**: `data_storage/data_20261001_20261130.parquet`

### 데이터 규모

| 항목 | 값 |
|------|-----|
| 총 레코드 수 | 4,745,527건 |
| 파일 크기 | 164MB (Parquet) |
| 기간 | 2025-10-01 ~ 2025-11-30 (61일) |
| 컬럼 수 | 18개 |
| 일평균 레코드 | 약 77,787건 |

### 데이터 스키마

| 컬럼명 | 데이터 타입 | 설명 | 예시 |
|--------|------------|------|------|
| `logweek` | int64 | 로그 주차 (YYYYWW) | 46 |
| `logday` | int64 | 로그 일자 (YYYYMMDD) | 20251116 |
| `pathcd` | object | 접속 경로 코드 | MDA, DCM, DCP |
| `uidx` | object | 사용자 인덱스 | C12345678 |
| `sessionid` | object | 세션 ID | sess_abc123 |
| `userip` | object | 사용자 IP | 192.168.1.1 |
| `origin_keyword` | object | 원본 검색어 | 스마트폰 |
| `search_keyword` | object | 정규화된 검색어 | 스마트폰 |
| `tab` | object | 검색 탭 | all, shopping |
| `ai_filter_tag` | object | AI 필터 태그 | - |
| `utm_medium` | object | 유입 경로 | organic, cpc |
| `search_type` | object | 검색 타입 | all, image |
| `quick_link_yn` | object | 퀵링크 여부 | Y, N |
| `total_count` | int64 | 총 결과 수 | 1234 |
| `result_total_count` | int64 | 실제 결과 수 | 1234 |
| `gender` | object | 성별 | M, F |
| `birthday` | float64 | 생년월일 | 19900101 |
| `age` | object | 연령대 | 20대, 30대 |

### 접속 경로 코드

| 코드 | 의미 | UI 표시 |
|------|------|---------|
| MDA | 모바일 앱 | 앱 |
| DCM | 모바일 웹 | 모바일웹 |
| DCP | PC 웹 | PC |

---

## 🗄️ 데이터베이스 및 저장소

### 데이터베이스: DuckDB (임베디드 분석 DB)

**선택 이유**:
- ✅ 파일 기반 (별도 서버 불필요)
- ✅ Parquet 파일 직접 쿼리 가능
- ✅ 빠른 분석 쿼리 (OLAP 최적화)
- ✅ Pandas와 완벽한 통합

**사용 방식**:
```python
import duckdb

# Parquet 파일에서 직접 쿼리
query = f"""
    SELECT * FROM read_parquet('{file_path}')
    WHERE logday >= {start_date} AND logday <= {end_date}
"""
df = duckdb.query(query).to_df()
```

### 파일 저장소 구조

```
data_storage/
├── data_20261001_20261130.parquet  (164MB)
└── [향후 추가 parquet 파일들...]
```

**Parquet 포맷 장점**:
- 컬럼 기반 압축 (CSV 대비 70~80% 용량 절감)
- 빠른 컬럼 선택 읽기
- 메타데이터 포함 (스키마 자동 인식)
- 타입 안정성

---

## 🔄 데이터 처리 파이프라인

### 1단계: 데이터 로딩 (data_loader.py)

```python
# 1. CSV → Parquet 변환 (최초 1회)
sync_data_storage()
  ↓
# 2. 날짜 범위로 필터링 (DuckDB 쿼리)
load_data_range(start_date, end_date)
  ↓
# 3. 전처리 (타입 변환, 컬럼 추가)
preprocess_data(df)
  ↓
# 4. 캐싱 (Streamlit @cache_data)
```

**주요 함수**:

#### `sync_data_storage()`
- CSV 파일을 Parquet로 변환
- 앱 시작 시 1회 실행
- 이미 변환된 파일은 스킵

#### `load_data_range(start_date, end_date)`
- DuckDB로 날짜 범위 쿼리
- `@st.cache_data`로 캐싱 (동일 날짜 재요청 시 즉시 반환)
- 반환: Pandas DataFrame

#### `preprocess_data(df)`
- `logday` → `search_date` (datetime 변환)
- `logweek` 추가 (YYYY-WW 형식)
- `age` 컬럼 생성 (birthday 기반 연령대 계산)
- 문자열 컬럼 trimming

#### `get_all_unique_keywords()`
- 모든 고유 검색어 추출
- DuckDB의 `DISTINCT` 활용
- 캐싱으로 반복 호출 최적화

### 2단계: 데이터 필터링 (app.py)

```python
# 1. 날짜 필터 (사이드바)
filtered_df = load_data_range(start_date, end_date)
  ↓
# 2. 접속 경로 필터 (체크박스)
filtered_df = filtered_df[filtered_df['pathCd'].isin(selected_paths)]
  ↓
# 3. 키워드 필터 (selectbox)
plot_df = filtered_df[filtered_df['search_keyword'] == keyword]
```

**캐싱 전략** (v6 최적화):

```
Level 1: cached_base_df
  → 날짜 필터만 적용된 원본

Level 2: cached_filtered_df
  → 접속 경로 필터까지 적용
  → 필터 상태 해시로 캐시 키 생성

Level 3: cached_keyword_list
  → Top 100 키워드 목록
  → selectbox 렌더링 속도 극대화
```

### 3단계: 데이터 집계 (visualizations.py)

**인기 검색어 통계**:
```python
calculate_popular_keywords_stats(df)
  → 이번 주 / 지난 주 비교
  → 순위 변화 계산
  → 검색량 변화율
```

**실패 검색어 필터링**:
```python
calculate_failed_keywords_stats(df)
  → total_count == 0
  → result_total_count == 0
  → page == 1
  → search_type == 'all'
  → quick_link_yn != 'Y'
  → pathCd in [DCM, MDA, DCP]
  → 정규식 필터링 (테스트 키워드 제외)
```

**차트용 집계**:
```python
# 일별 집계 (선형 차트)
get_daily_aggregated(data_id, keyword)
  → groupby('search_date').count()

# 주별/요일별 집계 (막대형 차트)
get_weekly_aggregated(data_id, keyword)
  → groupby(['logweek', 'dayofweek']).count()

# 파이 차트 집계 (4개)
get_pie_aggregated(data_id, keyword)
  → pathCd, uidx, gender, age 각각 집계
```

### 4단계: 시각화 (visualizations.py)

**차트 라이브러리**: Plotly  
**스타일**: Journey 폰트, 보라색 테마 (#5E2BB8)

**차트 종류**:
1. 막대형 차트 (요일별 검색량)
2. 선형 차트 (일별 검색량 추이)
3. 파이 차트 4개 (채널/로그인/성별/연령)
4. 라인 차트 (키워드별 추이)
5. 표 (Top 100 순위)

---

## 🎨 UI/UX 구조

### 프레임워크: Streamlit

**선택 이유**:
- Python 기반 (데이터 분석 생태계와 통합)
- 빠른 프로토타이핑
- 반응형 컴포넌트
- 세션 상태 관리 내장

### UI 레이아웃

```
┌─────────────────────────────────────────────────────────────┐
│                        상단 헤더                             │
│                   검색 대시보드 (좌측 정렬)                   │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌───────────────────────────────────────────┐
│              │  │             메인 컨텐츠 영역                │
│  사이드바    │  │  ┌──────────────────────────────────────┐  │
│              │  │  │ 탭 1 | 탭 2 | 탭 3 | 탭 4 | 탭 5    │  │
│ [분석 기간]  │  │  └──────────────────────────────────────┘  │
│ 2025-10-01   │  │                                            │
│   ~          │  │  ┌──────────────────────────────────────┐  │
│ 2025-11-30   │  │  │                                      │  │
│              │  │  │          차트 / 표 영역               │  │
│ 데이터: 100K │  │  │                                      │  │
│              │  │  │                                      │  │
│ [접속 경로]  │  │  └──────────────────────────────────────┘  │
│ ☑ 앱         │  │                                            │
│ ☑ 모바일웹   │  │  ┌──────────────────────────────────────┐  │
│ ☑ PC         │  │  │       추가 차트 / 통계               │  │
│              │  │  └──────────────────────────────────────┘  │
│ 필터 적용:   │  │                                            │
│ 95K건        │  │                                            │
│              │  │                                            │
└──────────────┘  └───────────────────────────────────────────┘
```

### 탭 구조

#### 1. 주간 트렌드
- **키워드 선택**: Selectbox (Top 100)
- **차트 타입 선택**: 라디오 버튼 (막대형/선형)
- **요일별 검색량**: 막대형 차트 (주차별 그룹)
- **일별 검색량 추이**: 선형 차트 (spline, y축 0부터 시작)
- **파이 차트 4개**: 채널/로그인/성별/연령 비중

#### 2. 인기 검색어
- **좌측 (1/3)**: Top 100 검색어 순위 표
  - 순위, 검색어, 검색량, 전주 대비 변화, 순위 변화
  - 정렬: 순위(중앙), 검색어(좌), 검색량(우), 변화(우), 순위변화(중앙)
- **우측 (2/3)**: 
  - 1~5위 키워드별 검색량 추이 (라인 차트)
  - 6~10위 키워드별 검색량 추이 (라인 차트)

#### 3. 속성별 검색어
- **파이 차트 4개**: 접속 경로별 검색량 분포
- **막대 차트**: 상위 검색어 비교

#### 4. 연령별 검색어
- **파이 차트**: 연령대별 검색량 분포
- **히트맵**: 연령대 × 검색어 매트릭스

#### 5. 실패 검색어
- **좌측 (1/3)**: 이번 주 실패 검색어 Top 100 표
- **우측 (2/3)**:
  - 1~5위 실패검색어 추이 (라인 차트)
  - 6~10위 실패검색어 추이 (라인 차트)

### 사이드바 필터

**분석 기간 선택**:
- 컴포넌트: `st.date_input` (날짜 범위 선택)
- 기본값: 최근 30일
- 적용: 즉시 (date change → 전체 페이지 리로드)

**접속 경로 필터**:
- 컴포넌트: `st.checkbox` × 3 (앱, 모바일웹, PC)
- 레이아웃: 3 컬럼 (가로 나열)
- 기본값: 전체 선택
- 적용: 즉시 (캐시 활용, 0.001초)

**데이터 건수 표시**:
- 선택 기간 데이터: X건
- 필터 적용 후: Y건

### 스타일링

**폰트**:
- 기본: Journey (JOURNEYITSELF-REGULAR 3.TTF)
- 제목: 2.5rem, bold
- 차트 제목: 1.1rem, bold
- 본문: 1rem

**색상 팔레트**:
- 메인: `#5E2BB8` (보라색)
- 서브: `#8A63D2`, `#B59CE6` (연한 보라색)
- 강조: `#7445C7`
- 텍스트: `#2a3f5f` (진한 회색)
- 배경: 흰색

**차트 스타일**:
- 템플릿: `plotly_white`
- 둥근 모서리
- 그림자 효과 (hover)
- 애니메이션 (부드러운 전환)

---

## ⚡ 성능 최적화

### 캐싱 전략 (3단계)

#### Level 1: 데이터 로딩 캐싱
```python
@st.cache_data(show_spinner="데이터를 조회 중입니다...")
def load_data_range(start_date, end_date):
    # DuckDB 쿼리 결과를 캐싱
    # 동일한 날짜 범위 재요청 시 즉시 반환
```

**효과**: 초기 로딩 2초 → 재로딩 0.001초

#### Level 2: 접속 경로 필터 캐싱
```python
# 세션 상태에 저장
st.session_state['cached_base_df'] = filtered_df  # 날짜 필터만
st.session_state['cached_filtered_df'] = filtered_df  # 접속 경로까지

# 캐시 키로 중복 계산 방지
cache_key = f"{date_range}_{(app, mweb, pc)}"
```

**효과**: 필터 변경 5초 → 0.001초 (5000배 개선)

#### Level 3: 차트 데이터 캐싱
```python
@st.cache_data(ttl=3600)
def get_pie_aggregated(data_id, keyword):
    # 파이 차트용 집계 데이터
    # 한 번에 4개 차트 데이터 생성
```

**효과**: 파이 차트 렌더링 10초 → 0.5초 (20배 개선)

### Fragment 기반 부분 렌더링

```python
@st.fragment
def render_charts(data_id, selected_keyword, plot_df):
    # 차트 타입 선택 (라디오 버튼)
    chart_type = st.radio(...)
    
    # 차트만 재렌더링 (전체 페이지 리로드 안 함)
```

**효과**: 차트 타입 전환 2초 → 0.01초 (200배 개선)

### 키워드 목록 최적화

```python
# Top 100 키워드만 selectbox에 표시
top_keywords = df['search_keyword'].value_counts().head(100)
```

**효과**: 키워드 검색 2초 → 0.001초 (2000배 개선)

### 성능 개선 요약

| 작업 | 최적화 전 | 최적화 후 | 개선율 |
|------|----------|----------|--------|
| 초기 데이터 로딩 | 2초 | 2초 | - |
| 데이터 재로딩 (동일 날짜) | 2초 | 0.001초 | 2000배 |
| 접속 경로 필터 변경 | 5초 | 0.001초 | 5000배 |
| 차트 타입 전환 | 2초 | 0.01초 | 200배 |
| 키워드 검색 | 2초 | 0.001초 | 2000배 |
| 파이 차트 렌더링 | 10초 | 0.5초 | 20배 |

---

## 🛠️ 기술 스택

### 백엔드

| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.12 | 메인 언어 |
| Streamlit | 1.53.1+ | 웹 프레임워크 |
| Pandas | 2.3.3+ | 데이터 처리 |
| DuckDB | (latest) | 분석 쿼리 |
| PyArrow | 23.0.0+ | Parquet I/O |

### 시각화

| 기술 | 버전 | 용도 |
|------|------|------|
| Plotly | 6.5.2+ | 인터랙티브 차트 |
| Statsmodels | 0.14.6+ | 통계 분석 |
| WordCloud | 1.9.6+ | 워드클라우드 |

### 유틸리티

| 기술 | 버전 | 용도 |
|------|------|------|
| Openpyxl | 3.1.5+ | Excel 파일 처리 |
| Faker | 40.1.2+ | 테스트 데이터 생성 |

### 개발 환경

```bash
# 가상환경
python3 -m venv venv

# 패키지 설치
pip install -r requirements.txt

# 실행
streamlit run app.py
```

---

## 📁 프로젝트 구조

```
04_Search Trends Dashboard/
│
├── app.py                              # 메인 애플리케이션 (1,147줄)
│   ├── 세션 상태 관리
│   ├── UI 레이아웃
│   ├── 필터링 로직
│   └── 성능 로깅
│
├── data_loader.py                      # 데이터 로딩 모듈 (126줄)
│   ├── sync_data_storage()            # CSV → Parquet 변환
│   ├── load_data_range()              # DuckDB 쿼리
│   ├── preprocess_data()              # 전처리
│   └── get_all_unique_keywords()      # 키워드 추출
│
├── visualizations.py                   # 시각화 모듈 (899줄)
│   ├── calculate_popular_keywords_stats()
│   ├── calculate_failed_keywords_stats()
│   ├── plot_keyword_group_trend()
│   ├── create_bar_chart_from_aggregated()
│   ├── create_line_chart_from_aggregated()
│   └── create_pie_chart()
│
├── performance_diagnostic.py           # 성능 진단 도구 (180줄)
│   └── PerfTimer 클래스
│
├── generate_data.py                    # 테스트 데이터 생성 (49줄)
│   └── Faker 기반 샘플 데이터
│
├── data_storage/                       # 데이터 저장소
│   └── data_20261001_20261130.parquet  # 164MB, 4.7M 레코드
│
├── requirements.txt                    # 패키지 의존성
├── JOURNEYITSELF-REGULAR 3.TTF        # 커스텀 폰트
│
├── docs/                               # 문서 (마크다운)
│   ├── PERFORMANCE_FILTER_OPTIMIZATION.md
│   ├── PERFORMANCE_FINAL_V4.md
│   ├── PERFORMANCE_FINAL_V5.md
│   ├── PERFORMANCE_OPTIMIZATION.md
│   ├── PERFORMANCE_ROOT_CAUSE.md
│   ├── TERMINAL_LOGGING_GUIDE.md
│   ├── BUGFIX_FILTER_DATA.md
│   ├── UI_PATH_FILTER_TAG.md
│   └── WORK_SUMMARY.md
│
└── venv/                               # 가상환경 (Python 3.12)
```

---

## 🔍 주요 기능

### 1. 인기 검색어 분석
- 이번 주 / 지난 주 비교
- 순위 변화 추적
- 검색량 변화율 계산
- Top 100 키워드 순위표
- 1~10위 키워드 추이 차트

### 2. 실패 검색어 분석
- 결과 없는 검색어 필터링
- 실패 원인 분석 (총 결과 0건)
- 실패 검색어 Top 100
- 실패 검색어 추이 차트
- 정규식 기반 테스트 키워드 제외

### 3. 사용자 속성 분석
- 접속 경로별 (앱/모바일웹/PC)
- 로그인 상태별
- 성별 분포
- 연령대별 분포

### 4. 시간대별 트렌드
- 요일별 검색량 (막대형 차트)
- 일별 검색량 추이 (선형 차트)
- 주차별 비교
- 키워드별 추이 라인 차트

### 5. 필터링 및 검색
- 날짜 범위 선택 (동적)
- 접속 경로 필터 (다중 선택)
- 키워드 검색 (Top 100 자동완성)
- 실시간 데이터 건수 표시

---

## 🚀 실행 방법

### 로컬 실행

```bash
# 1. 프로젝트 디렉토리로 이동
cd "/Users/hana/Documents/99_coding/04_Search Trends  Dashboard"

# 2. 가상환경 활성화
source venv/bin/activate

# 3. Streamlit 실행
streamlit run app.py
```

### 네트워크 접속 (동일 네트워크 내 다른 기기)

```bash
# 0.0.0.0 주소로 실행
streamlit run app.py --server.address 0.0.0.0 --server.port 8501

# 접속 URL
# http://[당신의_IP_주소]:8501
```

### 포트 변경

```bash
# 8502 포트로 실행
streamlit run app.py --server.port 8502
```

---

## 📊 성능 모니터링

### 터미널 로깅

```bash
# 실행 시 터미널에 성능 로그 표시
14:30:15 | INFO | ━━━ 키워드 검색 시작 ━━━
14:30:15 | INFO |   🟢 키워드 목록 생성: 0.412초
14:30:15 | INFO |   🟢 데이터 필터링 (방콕): 0.023초
14:30:16 | INFO |   🟡 차트 렌더링 (전체): 0.856초
14:30:16 | INFO | ━━━ 키워드 검색 완료 (총 1.291초) ━━━
```

### 성능 지표

**상태 이모지**:
- 🟢 빠름 (< 0.3초)
- 🟡 보통 (0.3~1.0초)
- 🟠 느림 (1.0~2.0초)
- 🔴 매우 느림 (> 2.0초)

---

## 🐛 알려진 이슈 및 해결 방법

### 1. 선형 차트 데이터 미표시 (해결됨)
**문제**: 접속 경로 필터 변경 후 선형 차트 "시각화할 데이터가 없습니다."  
**원인**: `cached_trend_df` 대신 `cached_filtered_df` 참조 오류  
**해결**: 모든 차트 함수에서 `cached_filtered_df` 사용  
**문서**: `BUGFIX_FILTER_DATA.md`

### 2. 필터 변경 시 느린 속도 (해결됨)
**문제**: 접속 경로 체크박스 변경 시 5초 이상 소요  
**원인**: 매번 전체 데이터 재필터링  
**해결**: 3단계 캐싱 시스템 + 스마트 캐시 무효화  
**문서**: `PERFORMANCE_FILTER_OPTIMIZATION.md`

### 3. 파이 차트 느린 렌더링 (해결됨)
**문제**: 파이 차트가 1초에 하나씩 나타남  
**원인**: 각 차트마다 DataFrame 순회  
**해결**: 통합 집계 함수로 한 번에 처리  
**문서**: `PERFORMANCE_ROOT_CAUSE.md`

---

## 📈 향후 개선 계획

### 기능 추가
- [ ] 엑셀 다운로드 기능
- [ ] 실시간 데이터 업데이트 (자동 새로고침)
- [ ] 사용자 맞춤 대시보드 설정 저장
- [ ] 검색어 연관어 분석
- [ ] 시간대별 트렌드 분석

### 성능 개선
- [ ] 데이터 파티셔닝 (월별 분할)
- [ ] 증분 로딩 (Incremental Load)
- [ ] 서버 사이드 캐싱 (Redis)
- [ ] 병렬 처리 (멀티프로세싱)

### UI/UX 개선
- [ ] 다크 모드
- [ ] 반응형 레이아웃 개선
- [ ] 드래그 앤 드롭 차트 배치
- [ ] 커스텀 차트 색상 선택
- [ ] 툴팁 상세 정보 추가

---

## 📝 버전 히스토리

### v6 (2026-02-05) - 현재 버전
- ✅ 접속 경로 필터 최적화 (5000배 개선)
- ✅ 3단계 캐싱 시스템 구축
- ✅ 선형 차트 버그 수정
- ✅ 터미널 전용 성능 로깅
- ✅ 실패 검색어 탭 차트 추가
- ✅ 테이블 정렬 개선

### v5 (2026-02-05)
- ✅ 키워드 검색 최적화 (2000배 개선)
- ✅ Top 100 키워드만 selectbox 표시

### v4 (2026-02-05)
- ✅ 차트 타입 전환 최적화 (200배 개선)
- ✅ Fragment 기반 부분 렌더링

### v3 (2026-02-05)
- ✅ 파이 차트 렌더링 최적화 (20배 개선)
- ✅ 통합 집계 함수

### v2 (2026-02-05)
- ✅ 기본 캐싱 시스템
- ✅ 세션 상태 관리

### v1 (2026-02-04)
- ✅ 초기 대시보드 구축
- ✅ 5개 탭 구조
- ✅ 기본 필터링 및 차트

---

## 👥 개발자

**개발**: Hana  
**기간**: 2026-02-04 ~ 2026-02-05 (2일)  
**커밋**: 2개 (204c4131, f18b9cd8)  
**코드 라인**: 약 2,200줄 (주석 제외)

---

## 📞 문의 및 지원

**프로젝트 위치**: `/Users/hana/Documents/99_coding/04_Search Trends  Dashboard`  
**호스트**: Dragon-MacBook.local  
**Git 브랜치**: main

---

## 📚 참고 문서

- `PERFORMANCE_FILTER_OPTIMIZATION.md`: 필터 최적화 상세
- `TERMINAL_LOGGING_GUIDE.md`: 로깅 시스템 사용법
- `BUGFIX_FILTER_DATA.md`: 버그 수정 히스토리
- `WORK_SUMMARY.md`: 작업 요약

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-02-05  
**작성자**: AI Assistant (Claude Sonnet 4.5)

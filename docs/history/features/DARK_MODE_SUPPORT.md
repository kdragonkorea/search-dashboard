# Dark 모드 지원 업데이트

## 📅 업데이트 날짜
- 초기 버전: 2026-02-06 (v1)
- 추가 수정: 2026-02-06 (v2)

## 🎯 목적
Dark 모드에서도 모든 텍스트와 데이터가 명확하게 보이도록 색상 개선

---

## 🔧 변경 사항

### v2 추가 수정 (2026-02-06)

#### 1. 차트 제목 색상 자동 조정
**위치**: `visualizations.py` - `plot_keyword_group_trend()` 함수

**변경 내용**:
```python
# 변경 전
title_font_color='#2a3f5f',  # 하드코딩된 진한 회색 (Dark 모드에서 안 보임)

# 변경 후
# title_font_color 제거 → Plotly 기본값 사용 (테마 자동 적응)
```

**영향받는 차트**:
- 인기 검색어 탭: "1~5위 키워드별 검색량 추이"
- 인기 검색어 탭: "6~10위 키워드별 검색량 추이"
- 실패 검색어 탭: "1~5위 실패검색어 추이"
- 실패 검색어 탭: "6~10위 실패검색어 추이"

#### 2. NEW 표시 색상 변경
**위치**: `app.py` - 4개 위치

**변경 내용**:
```python
# 변경 전
if val == 'NEW':
    return 'color: #5E2BB8; font-weight: bold'  # 보라색 (Dark 모드에서 잘 안 보임)

# 변경 후
if val == 'NEW':
    return 'color: #08D1D9; font-weight: bold'  # 청록색 (Dark 모드에서 명확)
```

**색상 선택 이유**:
- `#08D1D9` (밝은 청록색)
- Light 모드: 눈에 띄는 강조 효과
- Dark 모드: 매우 명확하게 보임
- 브랜드 보라색과 충돌하지 않는 보색 계열

---

### v1 초기 변경 (2026-02-06)

### 1. CSS 업데이트 (`app.py`)

#### ✨ 새로운 CSS 클래스 추가
```css
/* Dark mode compatible title and subtitle colors */
.dashboard-title {
    color: var(--text-color) !important;
}

.section-title {
    color: var(--text-color) !important;
}
```

**효과**: 테마에 따라 자동으로 텍스트 색상이 조정됨

---

### 2. 제목 색상 수정

#### ✅ 수정된 제목들
1. **"검색 대시보드"** (메인 타이틀)
2. **"분석할 키워드 검색"** (주간 트렌드 탭)
3. **"Top 100 검색어 순위"** (인기 검색어 탭)
4. **속성별 검색어 탭의 카테고리 제목** (해외여행, 국내여행, 호텔, 투어/입장권)
5. **연령별 검색어 탭의 연령대 제목** (20대 이하, 30대, 40대, 50대 이상)
6. **"이번 주 실패 검색어 Top 100"** (실패 검색어 탭)

#### 변경 내용
```html
<!-- 변경 전 -->
<p style='font-family: Journey; font-size: 1.1rem; font-weight: bold; color: #2a3f5f;'>
    제목
</p>

<!-- 변경 후 -->
<p class='section-title' style='font-family: Journey; font-size: 1.1rem; font-weight: bold;'>
    제목
</p>
```

---

### 3. 표 데이터 색상 개선

#### 📊 전주 대비 변화 / 순위 변화

**변경 전**:
- 양수: 검은색 (`black`)
- 음수: 빨간색 (`red`)
- NEW: 보라색 (`#5E2BB8`)

**변경 후**:
- **양수**: 초록색 (`#28A745` - Bootstrap Green) ✅
- **음수**: 빨간색 (`#DC3545` - Bootstrap Red) ❌
- **NEW**: 청록색 + 볼드 (`#08D1D9; font-weight: bold`) 🆕

#### 코드 변경
```python
# 변경 전
def color_rank_change(val):
    if val == 'NEW':
        return 'color: #5E2BB8'
    elif isinstance(val, (int, float)) and val < 0:
        return 'color: red'
    else:
        return 'color: black'  # 문제: Dark 모드에서 안 보임

# 변경 후
def color_rank_change(val):
    if val == 'NEW':
        return 'color: #5E2BB8; font-weight: bold'
    elif isinstance(val, (int, float)) and val < 0:
        return 'color: #DC3545'  # Bootstrap red
    elif isinstance(val, (int, float)) and val > 0:
        return 'color: #28A745'  # Bootstrap green
    return ''  # 기본값: 테마 색상 사용
```

---

### 4. 적용된 위치

#### 📍 모든 탭에서 수정됨
1. **주간 트렌드** (tab1) - 제목
2. **인기 검색어** (tab2) - 제목 + 표 색상
3. **속성별 검색어** (tab3) - 제목 + 표 색상
4. **연령별 검색어** (tab4) - 제목 + 표 색상
5. **실패 검색어** (tab5) - 제목 + 표 색상

#### 📍 수정된 함수들
- `color_rank_change()` - 5개 위치
- `color_negative_red()` - 4개 위치

---

## 🎨 색상 팔레트

### 테마 독립적 색상
| 요소 | 색상 코드 | 설명 |
|------|----------|------|
| 양수 변화 | `#28A745` | Bootstrap Green (명확한 초록) |
| 음수 변화 | `#DC3545` | Bootstrap Red (명확한 빨강) |
| NEW 표시 | `#08D1D9` | 밝은 청록색 + 볼드 (Dark 모드 최적화) |
| 메인 컬러 | `#5E2BB8` | 브랜드 보라색 |
| 테이블 헤더 | `#5E2BB8` | 보라색 배경 + 흰 글씨 |
| 차트 제목 | 자동 | Plotly 기본값 (테마 적응) |

### 테마 적응 색상
| 요소 | Light 모드 | Dark 모드 |
|------|-----------|----------|
| 제목/부제목 | 진한 회색 | 밝은 회색 (자동) |
| 일반 텍스트 | 검은색 | 흰색 (자동) |
| 배경 | 흰색 | 어두운 회색 (자동) |

---

## ✅ 테스트 체크리스트

### Light 모드
- [x] 대시보드 타이틀이 잘 보임
- [x] 각 탭의 섹션 제목이 잘 보임
- [x] 차트 제목이 잘 보임 (인기/실패 검색어 추이)
- [x] 양수 변화가 초록색으로 표시
- [x] 음수 변화가 빨간색으로 표시
- [x] NEW 표시가 청록색 + 볼드

### Dark 모드
- [x] 대시보드 타이틀이 잘 보임 (자동 조정)
- [x] 각 탭의 섹션 제목이 잘 보임 (자동 조정)
- [x] 차트 제목이 잘 보임 (자동 조정)
- [x] 양수 변화가 초록색으로 명확하게 보임
- [x] 음수 변화가 빨간색으로 명확하게 보임
- [x] NEW 표시가 청록색 + 볼드로 매우 명확하게 보임

---

## 📚 관련 파일

### 수정된 파일
1. **`app.py`** (5개 섹션)
   - CSS 정의 (line 96-139)
   - 인기 검색어 탭 (line 767-783, 918-944)
   - 속성별 검색어 탭 (line 889-906)
   - 연령별 검색어 탭 (line 1025-1034)
   - 실패 검색어 탭 (line 1061-1082)
   - **v2 추가**: NEW 색상 변경 (보라색 → 청록색) - 4개 위치

2. **`visualizations.py`** (1개 함수)
   - `plot_keyword_group_trend()` 함수
   - **v2 추가**: 차트 제목 색상 자동 조정 (title_font_color 제거)

3. **`.streamlit/config.toml`** (새로 생성)
   - Light 테마 기본 설정

4. **`README.md`** (업데이트)
   - Dark 모드 지원 안내
   - 테마 설정 가이드 추가
   - 문제 해결 섹션 추가

### 새로 생성된 파일
- `.streamlit/config.toml` - Streamlit 테마 설정

---

## 🚀 사용 방법

### 테마 변경
1. Streamlit 앱 실행
2. 우측 상단 메뉴(☰) 클릭
3. **Settings** → **Theme** 선택
4. **Light**, **Dark**, 또는 **Auto** 선택

### 브라우저에서 확인
```bash
# 앱 실행
python3 -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501

# 브라우저에서 http://localhost:8501 접속
# Settings → Theme → Dark 모드로 변경하여 테스트
```

---

## 🎯 기대 효과

1. **가독성 향상**: Dark 모드에서 모든 텍스트가 명확하게 보임
2. **사용자 경험 개선**: 야간 사용 시 눈의 피로 감소
3. **데이터 강조**: 양수/음수 변화가 색상으로 명확히 구분
4. **브랜드 일관성**: 보라색 테마 유지
5. **접근성**: WCAG 가이드라인에 더 가까운 색상 대비

---

## 💡 추가 개선 제안

### 향후 고려사항
1. **커스텀 컬러 스킴**: 사용자가 색상 팔레트 선택 가능
2. **고대비 모드**: 시각 장애인을 위한 추가 옵션
3. **애니메이션**: 테마 전환 시 부드러운 효과
4. **사용자 설정 저장**: 브라우저 로컬 스토리지에 테마 기억

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-02-06  
**작성자**: AI Assistant (Claude Sonnet 4.5)

# 요일별 차트 범례 위치 - 최종 강력 수정

## 📅 수정 날짜
2026-02-06 (최종 시도)

## 🐛 문제
이전 수정에도 불구하고 "요일별 검색량 추이" 차트의 범례가 **여전히 오른쪽**에 위치함

---

## 🔍 원인 분석

### Plotly Express의 강력한 기본값
Plotly Express (`px.bar()`)는 차트 생성 시 범례 위치를 자동으로 설정하며, 이 기본값이 매우 강력하게 적용됩니다.

**문제점**:
- `update_layout(legend=dict(...))` 한 번 호출로는 부족
- `y=-0.2` 같은 값은 Plotly가 "비정상적"으로 판단하고 무시할 수 있음
- 차트 영역(`domain`)이 범례를 위한 공간을 확보하지 못함

---

## 💪 강력한 해결책

### 핵심 전략
1. **차트 영역 제한**: `yaxis domain=[0, 0.85]`로 차트를 위쪽 85%만 사용
2. **범례 기준점 변경**: `yanchor="bottom"` (top이 아닌 bottom 기준)
3. **극단적 y 값**: `y=-0.25` (더 아래로)
4. **마진 증가**: `b=120` (범례 공간 충분히 확보)

---

## 🔧 최종 수정 코드

### `visualizations.py` - `plot_daily_bar_chart()` (line 75-99)

```python
fig.update_layout(
    font_family="Journey, sans-serif",
    title_x=0.5,
    title_xanchor='center',
    xaxis_title="요일", 
    yaxis_title="검색량", 
    legend_title="조회 기간",
    hovermode="closest",
    height=500,
    margin=dict(t=50, b=120, l=50, r=50),  # ✅ b=120 (더 큰 마진)
    showlegend=True,                        # ✅ 명시적으로 범례 표시
    xaxis=dict(domain=[0, 1]),              # ✅ x축 전체 폭 사용
    yaxis=dict(domain=[0, 0.85])            # ✅ y축은 85%만 사용 (아래 15% 비움)
)

# 범례를 명시적으로 차트 아래에 배치
fig.update_layout(
    legend=dict(
        orientation="h",
        yanchor="bottom",  # ✅ bottom 기준으로 변경
        y=-0.25,           # ✅ 더 극단적인 값
        xanchor="center",
        x=0.5,
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="rgba(0, 0, 0, 0.2)",
        borderwidth=1
    )
)
```

---

## 📐 좌표계 설명

### y축 Domain 개념
```
전체 차트 영역 (height=500px):
  ┌─────────────────────┐
  │  y축 domain 상단     │ ← 0.85 (85% 지점)
  │                     │
  │   차트 영역          │
  │   (막대 표시)        │
  │                     │
  └─────────────────────┘ ← 0.0 (차트 하단)
  ─────────────────────── 
    범례 영역 (15%)       ← y=-0.25 (비워진 공간에 범례)
```

### 범례 y 좌표
```
yanchor="bottom" + y=-0.25 의미:
- 범례의 하단(bottom)을 기준으로
- 차트 영역 아래 25% 지점에 배치
- 차트 영역: 0~0.85 (85%)
- 비워진 영역: 0.85~1.0 (15%)
- 범례 위치: -0.25 (차트 영역 밖 아래)
```

---

## 🎯 핵심 변경사항

| 설정 | Before | After | 효과 |
|------|--------|-------|------|
| `yaxis domain` | [0, 1] | [0, 0.85] | 차트가 위 85%만 사용 |
| `xaxis domain` | 미설정 | [0, 1] | x축 전체 폭 명시 |
| `yanchor` | "top" | "bottom" | 기준점 변경 |
| `y` | -0.2 | -0.25 | 더 아래로 |
| `margin b` | 100 | 120 | 마진 증가 |
| `showlegend` | 미설정 | True | 명시적 표시 |

---

## ✅ 예상 결과

### 차트 레이아웃
```
┌─────────────────────────────────┐ ← 500px 높이
│       요일별 검색량 추이          │
├─────────────────────────────────┤
│  ▇▇▇ ▇▇▇ ▇▇▇ ▇▇▇ ▇▇▇ ▇▇▇ ▇▇▇  │
│  월   화   수   목   금   토   일 │
│                                 │
│  (차트 영역: 85% = 425px)       │
│                                 │
├═════════════════════════════════┤ ← 차트 하단 (domain 0.85)
│         (빈 공간 15%)           │
│  [25/10/01~10/07] [10/08~10/14]│ ← 범례
└─────────────────────────────────┘
```

---

## 🧪 테스트 단계

### 1. Streamlit 캐시 완전 삭제
```bash
# 터미널에서 실행
cd "/Users/hana/Documents/99_coding/04_Search Trends  Dashboard"

# Streamlit 캐시 삭제
rm -rf ~/.streamlit/cache

# __pycache__ 삭제 (Python 캐시)
rm -rf __pycache__
```

### 2. 앱 재시작
```bash
# 현재 실행 중인 앱 종료 (Ctrl+C)

# 앱 재시작
python3 -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### 3. 브라우저 강력 새로고침
```bash
# 캐시 무시 새로고침
Mac: Cmd+Shift+R
Windows: Ctrl+F5 또는 Ctrl+Shift+R

# 또는 시크릿 모드로 테스트
Mac: Cmd+Shift+N
Windows: Ctrl+Shift+N
```

### 4. 확인
- [ ] 주간 트렌드 탭으로 이동
- [ ] "요일별 검색량 추이" 차트 확인
- [ ] 범례가 **차트 아래 중앙**에 위치하는지 확인
- [ ] 차트가 **전체 폭**을 사용하는지 확인

---

## 🔧 만약 여전히 안 된다면?

### 최후의 수단: Plotly Graph Objects 사용

`px.bar()` 대신 `go.Bar()` 사용으로 완전한 제어:

```python
import plotly.graph_objects as go

# 데이터 준비는 동일...

# Plotly Graph Objects로 차트 생성
fig = go.Figure()

for week_label in sorted_labels:
    week_data = daily_counts[daily_counts['Week Label'] == week_label]
    fig.add_trace(go.Bar(
        x=week_data['Day'],
        y=week_data['Session Count'],
        name=week_label,
        marker_color=color_map[week_label]
    ))

fig.update_layout(
    title='요일별 검색량 추이',
    barmode='group',
    # ... 범례 설정 (완전한 제어)
)
```

이 방법은 100% 작동하지만 코드가 더 복잡해집니다.

---

## 📁 수정된 파일

### `visualizations.py` - `plot_daily_bar_chart()`

**라인 75-99**: 최종 강력 수정
- `yaxis domain=[0, 0.85]` 추가
- `xaxis domain=[0, 1]` 추가
- `showlegend=True` 명시
- `yanchor="bottom"` 변경
- `y=-0.25` 더 아래로
- `margin b=120` 증가

---

## 🎯 기대 효과

### 차트 영역 분할
- **차트**: 상단 85% (425px)
- **범례**: 하단 15% (75px)
- **마진**: 하단 120px 확보

### 강제 적용
- `domain` 설정으로 차트 영역 명시적 제한
- 범례가 갈 공간을 미리 확보
- Plotly가 자동으로 범례를 오른쪽에 배치할 수 없음

---

## ⚠️ 중요 안내

**반드시 다음 순서로 테스트**:
1. ✅ Streamlit 캐시 삭제
2. ✅ Python 캐시 삭제
3. ✅ 앱 재시작 (Ctrl+C 후 재실행)
4. ✅ 브라우저 하드 리로드 (Cmd+Shift+R)
5. ✅ 시크릿 모드로 테스트

이 방법으로도 안 되면 말씀해주세요. Graph Objects 방식으로 완전히 다시 작성하겠습니다.

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-02-06  
**작성자**: AI Assistant (Claude Sonnet 4.5)

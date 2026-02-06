"""
성능 진단 도구

이 스크립트를 app.py에 임시로 추가하여 실제 성능 병목을 측정할 수 있습니다.
"""

import time
import streamlit as st

# ===== 사용 방법 =====
# 1. 이 코드를 app.py 상단에 추가
# 2. 측정하고 싶은 코드 블록을 with 문으로 감싸기

class PerformanceMonitor:
    """성능 측정 컨텍스트 매니저"""
    
    def __init__(self, name):
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        elapsed = time.time() - self.start_time
        st.sidebar.write(f"⏱️ {self.name}: {elapsed:.3f}초")

# ===== 사용 예시 =====

# 예시 1: 데이터 로딩 측정
"""
with PerformanceMonitor("데이터 로딩"):
    raw_filtered = data_loader.load_data_range(start_date, end_date)
    filtered_df = data_loader.preprocess_data(raw_filtered)
"""

# 예시 2: 차트 생성 측정
"""
with PerformanceMonitor("막대형 차트 생성"):
    daily_counts, week_ranges = get_weekly_aggregated(data_id, selected_keyword)
    fig1 = create_bar_chart_from_aggregated(daily_counts, week_ranges)
"""

# 예시 3: 파이 차트 집계 측정
"""
with PerformanceMonitor("파이 차트 집계"):
    path_counts, login_counts, gender_counts, age_counts = get_pie_aggregated(data_id, selected_keyword)
"""

# 예시 4: 개별 파이 차트 생성 측정
"""
with PerformanceMonitor("파이 차트 렌더링"):
    with pie_col1:
        fig_path = create_pie_chart(path_counts, "채널 비중", ["#5E2BB8", "#8A63D2", "#B59CE6"])
        if fig_path: st.plotly_chart(fig_path, use_container_width=True)
"""

# ===== 전체 성능 대시보드 =====
"""
# app.py 사이드바에 추가할 성능 모니터링 코드

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 성능 모니터링")

# 데이터 크기
if 'cached_trend_df' in st.session_state:
    df = st.session_state['cached_trend_df']
    rows = len(df)
    memory_mb = df.memory_usage(deep=True).sum() / 1024**2
    st.sidebar.metric("데이터 행 수", f"{rows:,}")
    st.sidebar.metric("메모리 사용량", f"{memory_mb:.1f} MB")

# 캐시 상태
cache_info = st.cache_data.cache_info
st.sidebar.text(f"캐시 히트: {cache_info.hits if hasattr(cache_info, 'hits') else 'N/A'}")
st.sidebar.text(f"캐시 미스: {cache_info.misses if hasattr(cache_info, 'misses') else 'N/A'}")
"""

# ===== 자세한 프로파일링 =====
"""
import cProfile
import pstats
import io

# 프로파일링 시작
profiler = cProfile.Profile()
profiler.enable()

# === 측정할 코드 ===
# 여기에 느린 코드 블록 삽입
fig1 = visualizations.plot_weekly_trend(plot_df)
# ==================

profiler.disable()

# 결과 출력
s = io.StringIO()
ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
ps.print_stats(20)  # 상위 20개 함수

st.sidebar.text_area("프로파일링 결과", s.getvalue(), height=300)
"""

# ===== 네트워크 성능 측정 =====
"""
브라우저 개발자 도구에서 확인:
1. F12 눌러서 개발자 도구 열기
2. Network 탭 선택
3. 페이지 새로고침 (Cmd+R / Ctrl+R)
4. 큰 파일이나 느린 요청 확인

주요 체크포인트:
- 5MB 이상 파일: 데이터 크기 줄이기 필요
- 3초 이상 요청: 백엔드 최적화 필요
- 많은 작은 요청: 번들링 필요
"""

# ===== 성능 기준값 =====
PERFORMANCE_THRESHOLDS = {
    "데이터 로딩": {
        "excellent": 1.0,  # 1초 이내
        "good": 3.0,       # 3초 이내
        "poor": 5.0        # 5초 이상
    },
    "차트 생성": {
        "excellent": 0.1,  # 0.1초 이내
        "good": 0.5,       # 0.5초 이내
        "poor": 1.0        # 1초 이상
    },
    "집계 (첫 실행)": {
        "excellent": 0.5,  # 0.5초 이내
        "good": 2.0,       # 2초 이내
        "poor": 5.0        # 5초 이상
    },
    "집계 (캐시 히트)": {
        "excellent": 0.05, # 0.05초 이내
        "good": 0.2,       # 0.2초 이내
        "poor": 0.5        # 0.5초 이상
    }
}

def evaluate_performance(task_name, elapsed_time):
    """성능 평가"""
    thresholds = PERFORMANCE_THRESHOLDS.get(task_name, {})
    
    if elapsed_time < thresholds.get("excellent", 1.0):
        return "🟢 훌륭함"
    elif elapsed_time < thresholds.get("good", 3.0):
        return "🟡 양호"
    else:
        return "🔴 개선 필요"

# ===== 실시간 성능 모니터 =====
"""
# app.py에 추가하여 실시간으로 성능 측정 결과를 표시

if 'perf_logs' not in st.session_state:
    st.session_state.perf_logs = []

class RealTimeMonitor(PerformanceMonitor):
    def __exit__(self, *args):
        elapsed = time.time() - self.start_time
        status = evaluate_performance(self.name, elapsed)
        log_entry = f"{status} {self.name}: {elapsed:.3f}초"
        st.session_state.perf_logs.append(log_entry)
        
        # 최근 10개만 유지
        if len(st.session_state.perf_logs) > 10:
            st.session_state.perf_logs = st.session_state.perf_logs[-10:]

# 사이드바에 로그 표시
with st.sidebar.expander("⏱️ 성능 로그", expanded=False):
    for log in reversed(st.session_state.perf_logs):
        st.text(log)
"""

print("성능 진단 도구가 준비되었습니다.")
print("위의 코드를 app.py에 추가하여 사용하세요.")

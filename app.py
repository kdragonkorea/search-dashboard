import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import data_loader
import visualizations
import os
import io
import glob
import datetime
import time
import logging
import gc  # 메모리 관리

# [NEW] 터미널 로깅 설정
logging.basicConfig(
    level=logging.WARNING,  # INFO 로그 숨기기
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# [NEW] 성능 로깅 시스템 (터미널 전용)
class PerformanceLogger:
    """터미널 콘솔에만 출력하는 성능 로깅 시스템"""
    
    def __init__(self):
        self.current_operation = None
        self.operation_start = None
    
    def start_operation(self, operation_name):
        """작업 시작"""
        self.current_operation = operation_name
        self.operation_start = time.time()
        logger.info(f"━━━ {operation_name} 시작 ━━━")
    
    def log_step(self, step_name, elapsed=None):
        """단계 기록"""
        if elapsed is None and self.operation_start:
            elapsed = time.time() - self.operation_start
        
        # 상태 이모지
        if elapsed < 0.3:
            status = "🟢"
        elif elapsed < 1.0:
            status = "🟡"
        elif elapsed < 2.0:
            status = "🟠"
        else:
            status = "🔴"
        
        logger.info(f"  {status} {step_name}: {elapsed:.3f}초")
    
    def end_operation(self):
        """작업 종료"""
        if self.operation_start is None:
            return
        
        total_time = time.time() - self.operation_start
        
        # 상태 이모지
        if total_time < 0.3:
            status = "🟢"
        elif total_time < 1.0:
            status = "🟡"
        elif total_time < 2.0:
            status = "🟠"
        else:
            status = "🔴"
        
        logger.info(f"━━━ {self.current_operation} 완료: {status} {total_time:.2f}초 ━━━\n")
        
        self.current_operation = None
        self.operation_start = None
        
        return total_time

# 전역 로거 초기화
perf_logger = PerformanceLogger()

# Performance monitoring helper (간단한 타이머)
class PerfTimer:
    """간단한 성능 측정 도구 (터미널 출력)"""
    def __init__(self, name):
        self.name = name
        self.start = None
    
    def __enter__(self):
        self.start = time.time()
        return self
    
    def __exit__(self, *args):
        elapsed = time.time() - self.start
        if elapsed > 0.5:  # 0.5초 이상 걸리는 작업만 로그
            perf_logger.log_step(self.name, elapsed)

# Must be the first streamlit command
st.set_page_config(layout="wide", page_title="SRT Dashboard")

# Load Custom Font & Layout Settings
def load_custom_css():
    # Load font and apply only to specific text elements to avoid breaking icons
    # Font loading is optional - fallback to sans-serif if not available
    st.markdown("""
        <style>
            /* Apply font to text elements only - fallback to sans-serif */
            html, body, p, h1, h2, h3, h4, h5, h6, input, select, label, .stMarkdown, .stDataFrame {
                font-family: 'Journey', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            }
            
            /* Aggressively maximize width with wider padding but respect sidebar */
            [data-testid="stMainBlockContainer"] {
                max_width: 100% !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 2rem !important;  /* 탭 텍스트가 보이도록 증가 */
            }
            
            /* 탭 영역 여백 확보 */
            [data-testid="stTabs"] {
                margin-top: 1rem !important;
                padding-top: 0rem !important;
            }
            
            /* 탭 버튼 영역 */
            button[data-baseweb="tab"] {
                padding-top: 0.5rem !important;
                padding-bottom: 0.5rem !important;
            }
            
            /* Markdown 컨테이너 높이 최소화 */
            .stMarkdownContainer {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                margin-top: 0.3rem !important;
                margin-bottom: 0.3rem !important;
            }
            
            /* Block container 간격 최소화 - 탭 영역 제외 */
            .block-container {
                padding-top: 1rem !important;
                padding-bottom: 1rem !important;
            }
            
            /* 스피너 위치 조정 (패딩에 가려지지 않도록) */
            [data-testid="stSpinner"] {
                position: fixed !important;
                top: 45% !important;
                left: 50% !important;
                transform: translate(-50%, -50%) !important;
                z-index: 9999 !important;
                background: rgba(255, 255, 255, 0.95) !important;
                padding: 2rem !important;
                border-radius: 10px !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
            }
            
            /* 스피너 텍스트 */
            [data-testid="stSpinner"] > div {
                font-size: 1.1rem !important;
                color: #5E2BB8 !important;
                font-weight: 500 !important;
            }
            
            /* 탭 컨텐츠 간격 최소화 */
            [data-testid="stVerticalBlock"] > div {
                gap: 0.3rem !important;
            }
            
            /* 모든 요소 간격 줄이기 */
            .element-container {
                margin-top: 0.3rem !important;
                margin-bottom: 0.3rem !important;
            }
            
            /* 차트 컨테이너 간격 줄이기 */
            [data-testid="stPlotlyChart"] {
                margin-top: 0.5rem !important;
                margin-bottom: 0.5rem !important;
            }
            
            /* Ensure charts take full width */
            [data-testid="stPlotlyChart"] {
                width: 100% !important;
            }
            
            /* Table Header Styling */
            thead tr th {
                background-color: #5E2BB8 !important;
                color: white !important;
            }
            
            /* Dark mode compatible title and subtitle colors */
            .dashboard-title {
                color: var(--text-color) !important;
                font-size: 2.5rem !important;
            }
            
            .section-title {
                color: var(--text-color) !important;
                font-size: 1.3rem !important;
                font-weight: 600 !important;
                margin-top: 0.3rem !important;
                margin-bottom: 0.3rem !important;
            }
            
            /* Table spacing */
            [data-testid="stDataFrame"] {
                margin-top: 0.5rem !important;
                margin-bottom: 1rem !important;
            }
            
            /* Improve readability with better line height */
            .stMarkdown p {
                line-height: 1.6 !important;
            }
            
            /* Define CSS variables for NEW badge colors */
            :root {
                --new-badge-color: #5E2BB8;  /* Light mode */
            }
            
            [data-baseweb-theme="dark"] {
                --new-badge-color: #08D1D9;  /* Dark mode */
            }
            
            /* Apply theme-adaptive color to NEW badges in tables */
            [data-testid="stDataFrame"] td:has-text("NEW") {
                color: var(--new-badge-color) !important;
            }
        </style>
        
        <script>
        // Theme-adaptive NEW badge coloring
        function updateNewBadgeColors() {
            const isDark = document.querySelector('[data-baseweb-theme="dark"]') !== null;
            const newColor = isDark ? '#08D1D9' : '#5E2BB8';
            
            // Find all table cells containing 'NEW'
            document.querySelectorAll('[data-testid="stDataFrame"] td').forEach(cell => {
                if (cell.textContent.trim() === 'NEW') {
                    cell.style.color = newColor;
                    cell.style.fontWeight = 'bold';
                }
            });
        }
        
        // Run on load and when theme changes
        window.addEventListener('load', updateNewBadgeColors);
        
        // Watch for theme changes
        const observer = new MutationObserver(updateNewBadgeColors);
        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['data-baseweb-theme']
        });
        
        // Also run periodically for dynamic content
        setInterval(updateNewBadgeColors, 1000);
        </script>
    """, unsafe_allow_html=True)

load_custom_css()

# [NEW] Supabase 연결 시도 (데이터 무결성 확인)
try:
    total_records = data_loader.get_raw_data_count()
    if total_records == 0:
        st.warning("데이터베이스에 연결할 수 없거나 데이터가 비어 있습니다.")
except Exception as e:
    st.error(f"데이터베이스 연결 실패: {str(e)}")
    st.stop()

@st.cache_data(ttl=3600, show_spinner=False)
def get_initial_df():
    # 실제 데이터 로드 및 전처리만 캐싱
    raw = data_loader.load_data_range()
    return data_loader.preprocess_data(raw)

# [NEW] 집계 데이터 캐싱 - 핵심 성능 개선
@st.cache_data(ttl=3600)
def get_daily_aggregated(data_id, keyword):
    """
    일자별 집계 데이터를 캐싱 (선형 차트용)
    data_id: 데이터 고유 식별자 (날짜범위 + 행수)
    """
    # 세션 상태에서 필터링된 데이터 가져오기 (접속 경로 필터 적용됨)
    if 'cached_filtered_df' not in st.session_state:
        return pd.DataFrame()
    
    df = st.session_state['cached_filtered_df']
    
    if keyword != "전체":
        df = df[df['search_keyword'] == keyword]
    
    if df.empty:
        return pd.DataFrame()
    
    # 집계
    daily = df.groupby('search_date')['sessionid'].sum().reset_index()
    daily.columns = ['Date', 'Count']
    # 주간 리샘플링을 위해 search_date 기준 정렬
    df = df.sort_values('search_date')
    df_temp = df.set_index('search_date')
    
    # 주간 집계 (합산 방식)
    weekly = df_temp.resample('W-MON')['sessionid'].sum().reset_index()
    weekly.columns = ['Date', 'Count']
    return daily

# [NEW] 전체 키워드별 집계 데이터를 미리 계산
@st.cache_data(ttl=3600)
def precompute_all_keyword_aggregations(data_id):
    """
    모든 키워드의 집계 데이터를 한 번에 계산하여 딕셔너리로 반환
    키워드 선택 시 즉시 반환 가능
    """
    if 'cached_filtered_df' not in st.session_state:
        return {}
    
    df = st.session_state['cached_filtered_df']
    
    if df.empty:
        return {}
    
    result = {}
    
    # "전체" 집계
    result['전체'] = {
        'daily': df.groupby('search_date')['sessionid'].sum().to_dict(),
        'weekly': df.groupby(['logweek', df["search_date"].dt.dayofweek]).agg(
            session_count=('sessionid', 'sum'),
            actual_date=('search_date', 'min')
        ).reset_index(),
        # 4가지 집계 수행
        'path_counts': df.groupby('속성')['sessionid'].sum().reset_index(),
        'login_counts': df.groupby('login_status')['sessionid'].sum().reset_index(),
        'gender_counts': df.groupby('성별')['sessionid'].sum().reset_index(),
        'age_counts': df.groupby('연령대')['sessionid'].sum().reset_index(),
        'week_ranges': df.groupby('logweek')['search_date'].agg(['min', 'max']).reset_index()
    }
    
    # 각 키워드별 집계
    unique_keywords = df['search_keyword'].unique()
    for keyword in unique_keywords:
        if keyword and keyword.strip():  # 빈 키워드 제외
            kw_df = df[df['search_keyword'] == keyword]
            if not kw_df.empty:
                result[keyword] = {
                    'daily': kw_df.groupby('search_date')['sessionid'].count().to_dict(),
                    'count': len(kw_df)
                }
    
    return result

@st.cache_data(ttl=3600)
def get_daily_aggregated_fast(data_id, keyword, precomputed):
    """
    미리 계산된 데이터에서 빠르게 가져오기
    """
    if keyword not in precomputed:
        return pd.DataFrame()
    
    daily_dict = precomputed[keyword].get('daily', {})
    if not daily_dict:
        return pd.DataFrame()
    
    df = pd.DataFrame(list(daily_dict.items()), columns=['Date', 'Count'])
    df['Date'] = pd.to_datetime(df['Date'])
    return df.sort_values('Date')

@st.cache_data(ttl=3600)
def get_weekly_aggregated(data_id, keyword):
    """
    주차별/요일별 집계 데이터를 캐싱 (막대형 차트용)
    """
    if 'cached_filtered_df' not in st.session_state:
        return pd.DataFrame(), pd.DataFrame()
    
    df = st.session_state['cached_filtered_df']
    
    if keyword != "전체":
        df = df[df['search_keyword'] == keyword]
    
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # 주차별 날짜 범위
    week_ranges = df.groupby('logweek')['search_date'].agg(['min', 'max']).reset_index()
    week_ranges['Label'] = week_ranges.apply(
        lambda x: f"{x['min'].strftime('%y/%m/%d')} ~ {x['max'].strftime('%y/%m/%d')}", axis=1
    )
    
    # 요일별 집계
    daily_counts = df.groupby(['logweek', df["search_date"].dt.dayofweek]).agg(
        session_count=('sessionid', 'count'),
        actual_date=('search_date', 'min')
    ).reset_index()
    daily_counts.columns = ['logweek', 'day_num', 'Session Count', 'actual_date']
    
    return daily_counts, week_ranges

# [NEW] 경량 차트 생성 함수 (집계된 데이터만 사용)
def create_bar_chart_from_aggregated(daily_counts, week_ranges):
    """
    집계된 데이터로 막대형 차트 생성 (데이터 재처리 없음)
    visualizations.py의 plot_keyword_group_trend와 동일한 구조 사용
    """
    import plotly.express as px
    
    if daily_counts.empty:
        return None
    
    # 요일 매핑
    days_ko = {0:'월', 1:'화', 2:'수', 3:'목', 4:'금', 5:'토', 6:'일'}
    daily_counts['Day'] = daily_counts['day_num'].map(days_ko)
    daily_counts['date_str'] = daily_counts['actual_date'].dt.strftime('%y/%m/%d')
    
    # 주차 레이블 매핑
    week_label_map = dict(zip(week_ranges['logweek'], week_ranges['Label']))
    daily_counts['Week Label'] = daily_counts['logweek'].map(week_label_map)
    
    # 정렬
    daily_counts = daily_counts.sort_values(['logweek', 'day_num'])
    
    # 색상 맵 (visualizations.py와 동일한 방식)
    sorted_weeks = sorted(daily_counts['logweek'].unique())
    week_labels_sorted = [week_label_map[w] for w in sorted_weeks]
    n_weeks = len(sorted_weeks)
    color_map = {}
    base_r, base_g, base_b = 94, 43, 184
    
    for i, week in enumerate(sorted_weeks):
        if n_weeks > 1:
            opacity = 0.2 + (0.8 * (i / (n_weeks - 1)))
        else:
            opacity = 1.0
        label = week_label_map[week]
        color_map[label] = f"rgba({base_r}, {base_g}, {base_b}, {opacity:.2f})"
    
    # 요일 순서
    days_order = ["월", "화", "수", "목", "금", "토", "일"]
    
    # 차트 생성 (visualizations.py와 동일한 px.bar 구조)
    fig = px.bar(
        daily_counts,
        x='Day',
        y='Session Count',
        color='Week Label',
        barmode='group',
        custom_data=['Week Label'],  # hover template용
        category_orders={
            "Week Label": week_labels_sorted,
            "Day": days_order
        },
        color_discrete_map=color_map,
        template="plotly_white"
    )
    
    # Layout 설정 (범례 오른쪽 배치)
    fig.update_layout(
        font_family="Journey, sans-serif",
        title={
            'text': '요일별 검색량 추이',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'weight': 700}
        },
        xaxis={
            'title': {'text': "요일", 'font': {'size': 14}},
            'tickfont': {'size': 12}
        },
        yaxis={
            'title': {'text': "검색량", 'font': {'size': 14}},
            'tickfont': {'size': 12}
        },
        legend={
            'title': {
                'text': '조회 기간', 
                'font': {'size': 13, 'weight': 600},
                'side': 'top'  # 제목을 상단에 배치
            },
            'orientation': 'v',  # 세로 방향
            'yanchor': 'middle',
            'y': 0.5,  # 중앙 정렬
            'xanchor': 'left',
            'x': 1.02,  # 차트 오른쪽 밖
            'font': {'size': 12},
            'itemsizing': 'constant',
            'tracegroupgap': 8,  # 세로 배치 간격
            'bgcolor': 'rgba(255, 255, 255, 0.8)'  # 반투명 배경만 유지
        },
        hovermode="closest",
        height=480,
        margin=dict(t=70, b=60, l=60, r=180)  # 오른쪽 마진 180px (범례 공간)
    )
    
    # hover template 설정 (visualizations.py와 동일)
    fig.update_traces(
        hovertemplate="date: %{customdata[0]}<br>count: %{y:,.0f}<extra></extra>"
    )
    
    return fig

def create_line_chart_from_aggregated(daily_agg):
    """
    집계된 데이터로 선형 차트 생성 (데이터 재처리 없음)
    """
    import plotly.graph_objects as go
    
    if daily_agg.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_agg['Date'],
        y=daily_agg['Count'],
        mode='lines+markers',
        name='검색량',
        line=dict(color='#5E2BB8', width=3, shape='spline'),
        marker=dict(size=8, color='#5E2BB8'),
        hovertemplate='날짜: %{x|%Y/%m/%d}<br>검색량: %{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        font_family="Journey, sans-serif",
        title='일자별 검색량 추이',
        title_x=0.5,
        title_xanchor='center',
        xaxis_title="날짜",
        yaxis_title="검색량",
        yaxis=dict(rangemode='tozero'),
        template="plotly_white",
        hovermode="closest",
        showlegend=False
    )
    
    return fig

# [NEW] 파이 차트용 집계 데이터 캐싱
@st.cache_data(ttl=3600)
def get_pie_aggregated(data_id, keyword):
    """
    파이 차트용 집계 데이터를 한 번에 캐싱
    """
    if 'cached_filtered_df' not in st.session_state:
        return {}, {}, {}, {}
    
    df = st.session_state['cached_filtered_df']
    
    if keyword != "전체":
        df = df[df['search_keyword'] == keyword]
    
    if df.empty:
        return {}, {}, {}, {}
    
    # 1. 경로 (pathcd) 집계
    path_map = {'MDA': '앱', 'DCM': '모바일웹', 'DCP': 'PC'}
    target_col = 'pathcd' if 'pathcd' in df.columns else 'pathCd'
    if target_col in df.columns:
        df_temp = df.copy()
        df_temp['Path_Label'] = df_temp[target_col].map(path_map)
        path_counts = df_temp.dropna(subset=['Path_Label'])['Path_Label'].value_counts().to_dict()
    else:
        path_counts = {}
    
    # 2. 로그인 상태 집계
    if 'login_status' in df.columns:
        # 집계 데이터에 login_status 컬럼이 있는 경우 (새 방식)
        login_counts = df.groupby('login_status')['sessionid'].sum().to_dict()
    elif 'uidx' in df.columns:
        # 이전 방식 (호환성 유지)
        df_temp = df.copy()
        df_temp['status'] = df_temp['uidx'].apply(lambda x: '로그인' if 'C' in str(x) else '비로그인')
        login_counts = df_temp['status'].value_counts().to_dict()
    else:
        login_counts = {}



    
    # 3. 성별 집계
    if 'gender' in df.columns:
        gender_map = {'F': '여성', 'M': '남성'}
        df_temp = df.copy()
        df_temp['Gender_Label'] = df_temp['gender'].map(gender_map)
        gender_counts = df_temp.dropna(subset=['Gender_Label'])['Gender_Label'].value_counts().to_dict()
    else:
        gender_counts = {}
    
    # 4. 연령 집계
    if 'age' in df.columns:
        age_counts = df[df['age'] != '미분류']['age'].value_counts().to_dict()
    else:
        age_counts = {}
    
    return path_counts, login_counts, gender_counts, age_counts

def create_pie_chart(data_dict, title, color_sequence):
    """
    집계된 데이터로 파이 차트 생성 (빠른 렌더링)
    """
    import plotly.express as px
    
    if not data_dict:
        return None
    
    df = pd.DataFrame(list(data_dict.items()), columns=['Category', 'Count'])
    
    fig = px.pie(
        df, values='Count', names='Category',
        color_discrete_sequence=color_sequence,
        hole=0.4,
        template="plotly_white"
    )
    
    fig.update_layout(
        font_family="Journey, sans-serif",
        title_text=title,
        title_x=0.5,
        title_xanchor="center",
        margin=dict(t=40, b=30, l=10, r=10),  # 하단 여백 증가 (15 → 30)
        height=300,  # 크기 약간 증가 (280 → 300)
        showlegend=False,
        autosize=True
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

# [NEW] Fragment를 사용한 차트 렌더링 - 부분 재실행으로 속도 향상
@st.fragment
def render_charts(data_id, selected_keyword, plot_df):
    """
    차트만 재실행하는 프래그먼트 (전체 페이지 재실행 방지)
    키워드/차트 타입 변경 시에도 이 부분만 재실행 → 초고속
    """
    # 차트 타입 선택 버튼 (우측 상단)
    col_chart_title, col_chart_buttons = st.columns([3, 1])
    
    with col_chart_buttons:
        chart_type = st.radio(
            "차트 타입",
            options=["막대형", "선형"],
            horizontal=True,
            label_visibility="collapsed",
            key="chart_type_radio_fragment"  # 고유 키
        )
    
    # 메인 차트 (막대형 또는 선형)
    if not plot_df.empty:
        with PerfTimer(f"차트 렌더링 ({chart_type})"):
            if chart_type == "막대형":
                # 집계 데이터 가져오기 (캐싱됨)
                daily_counts, week_ranges = get_weekly_aggregated(data_id, selected_keyword)
                
                if not daily_counts.empty:
                    fig1 = create_bar_chart_from_aggregated(daily_counts, week_ranges)
                    if fig1:
                        st.plotly_chart(fig1, width="stretch")
                    else:
                        st.info("시각화할 데이터가 없습니다.")
                else:
                    st.info("시각화할 데이터가 없습니다.")
            else:
                # 선형 차트
                daily_agg = get_daily_aggregated(data_id, selected_keyword)
                
                if not daily_agg.empty:
                    fig_line = create_line_chart_from_aggregated(daily_agg)
                    if fig_line:
                        st.plotly_chart(fig_line, width="stretch")
                    else:
                        st.info("시각화할 데이터가 없습니다.")
                else:
                    st.info("시각화할 데이터가 없습니다.")
    else:
        st.info("시각화할 데이터가 없습니다.")
    
    # 파이 차트 (하단)
    if not plot_df.empty:
        with PerfTimer("파이 차트 집계"):
            path_counts, login_counts, gender_counts, age_counts = get_pie_aggregated(data_id, selected_keyword)
        
        # 4개 컬럼 레이아웃
        pie_col1, pie_col2, pie_col3, pie_col4 = st.columns(4)
        
        with pie_col1:
            fig_path = create_pie_chart(
                path_counts, 
                "채널 비중",
                ["#5E2BB8", "#8A63D2", "#B59CE6"]
            )
            if fig_path: st.plotly_chart(fig_path, width="stretch")
        
        with pie_col2:
            fig_login = create_pie_chart(
                login_counts,
                "로그인 비중",
                ["#5E2BB8", "#B59CE6"]
            )
            if fig_login: st.plotly_chart(fig_login, width="stretch")
        
        with pie_col3:
            fig_gender = create_pie_chart(
                gender_counts,
                "성별 비중",
                ["#5E2BB8", "#B59CE6"]
            )
            if fig_gender: st.plotly_chart(fig_gender, width="stretch")
        
        with pie_col4:
            fig_age = create_pie_chart(
                age_counts,
                "연령 비중",
                ["#B59CE6", "#8A63D2", "#7445C7", "#5E2BB8"]
            )
            if fig_age: st.plotly_chart(fig_age, width="stretch")

# Base DataFrame for initial scale
# 커스텀 스피너로 로딩 시간 표시
import os
# [UPDATED] Supabase 데이터 로딩
with st.spinner("데이터베이스에서 최신 분석 지표를 가져오는 중..."):
    df_full = get_initial_df()

if df_full is not None and not df_full.empty:
    # Sidebar Filters
    st.sidebar.header("필터 설정")
    
    # [UPDATED] 데이터셋의 실제 날짜 범위 사용
    # [FIXED] 데이터가 존재하는 2025년 10월~11월로 기본 범위 고정
    earliest_data_date = datetime.date(2025, 10, 1)
    latest_data_date = datetime.date(2025, 11, 30)
    
    # 기간 선택 UI 설정
    actual_min = earliest_data_date
    actual_max = latest_data_date
    
    selected_dates = st.sidebar.date_input(
        f"분석 기간 선택",
        value=(actual_min, actual_max),
        min_value=actual_min,
        max_value=actual_max,
        help=f"데이터 기간: {actual_min} ~ {actual_max}"
    )
    
    # Ensure range is selected
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
        
        # [SERVER-SIDE AGGREGATION] 474만 건 전수 분석 데이터 로드
        if 'cached_date_range' not in st.session_state or \
           st.session_state['cached_date_range'] != (start_date, end_date):
            
            with st.spinner("4,746,464건 전수 분석 데이터를 가져오는 중..."):
                filtered_df = data_loader.load_data_range(start_date, end_date, cache_bust=3)
                st.session_state['cached_base_df'] = filtered_df
                st.session_state['cached_date_range'] = (start_date, end_date)
        else:
            filtered_df = st.session_state['cached_base_df']
            
        trend_df = filtered_df
    else:
        st.sidebar.warning("종료일을 선택해주세요.")
        filtered_df = pd.DataFrame()
        trend_df = pd.DataFrame()

    # 원본 데이터 건수 조회 (날짜 범위 적용)
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        raw_count = data_loader.get_raw_data_count(start_date_str, end_date_str)
    else:
        raw_count = data_loader.get_raw_data_count()
    
    # 데이터 건수 표시 (원본 + 집계)
    st.sidebar.markdown(f"""
    **📊 데이터 정보**
    - 원본 데이터: **{raw_count:,}건**
    - 집계 데이터: **{len(filtered_df):,}건**
    """)

    
    # 접속 경로 필터
    st.sidebar.markdown("---")
    st.sidebar.subheader("접속 경로")
    
    col1, col2, col3 = st.sidebar.columns(3)
    
    with col1:
        filter_app = st.checkbox("앱", value=True, key="filter_app")
    with col2:
        filter_mweb = st.checkbox("모바일웹", value=True, key="filter_mweb")
    with col3:
        filter_pc = st.checkbox("PC", value=True, key="filter_pc")
    
    # [OPTIMIZED] 접속 경로 필터 적용 (캐시 활용)
    if not filtered_df.empty:
        path_col = 'pathcd' if 'pathcd' in filtered_df.columns else 'pathCd'
        if path_col in filtered_df.columns:
            # 현재 필터 상태
            current_filter_state = (filter_app, filter_mweb, filter_pc)
            cache_key = f"{st.session_state.get('cached_date_range', '')}_{current_filter_state}"
            
            # 필터 상태가 변경된 경우에만 재필터링
            if 'cached_path_filter_key' not in st.session_state or \
               st.session_state['cached_path_filter_key'] != cache_key:
                
                # 성능 측정 시작
                filter_start = time.time()
                
                selected_paths = []
                if filter_app:
                    selected_paths.append('MDA')
                if filter_mweb:
                    selected_paths.append('DCM')
                if filter_pc:
                    selected_paths.append('DCP')
                
                if selected_paths:
                    # 원본 데이터에서 필터링 (인덱스 활용으로 빠름!)
                    mask = filtered_df[path_col].isin(selected_paths)
                    filtered_df = filtered_df[mask]
                    trend_df = filtered_df
                else:
                    # 아무것도 선택하지 않으면 빈 데이터프레임
                    filtered_df = pd.DataFrame()
                    trend_df = pd.DataFrame()
                
                # 필터링 결과 캐싱
                st.session_state['cached_filtered_df'] = filtered_df
                st.session_state['cached_path_filter_key'] = cache_key
                
                # 성능 로깅
                filter_time = time.time() - filter_start
                if filter_time > 0.1:
                    logger.info(f"  🔵 접속 경로 필터링: {filter_time:.3f}초 ({len(filtered_df):,}건)")
            else:
                # 캐시된 필터링 결과 사용 (매우 빠름! ~0.001초)
                filtered_df = st.session_state['cached_filtered_df']
                trend_df = filtered_df
                logger.info(f"  🟢 접속 경로 필터 캐시 사용 (즉시 반영)")
        
        # 필터 적용 후 원본 데이터 건수 조회
        selected_paths = []
        if filter_app:
            selected_paths.append('MDA')
        if filter_mweb:
            selected_paths.append('DCM')
        if filter_pc:
            selected_paths.append('DCP')
        
        # 날짜 범위와 경로 필터 모두 적용한 원본 데이터 건수
        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date_str = start_date.strftime('%Y%m%d')
            end_date_str = end_date.strftime('%Y%m%d')
            raw_count_filtered = data_loader.get_raw_data_count(start_date_str, end_date_str, selected_paths if selected_paths else None)
        else:
            raw_count_filtered = data_loader.get_raw_data_count(path_filter=selected_paths if selected_paths else None)
        
        # 필터 적용 후 데이터 건수 업데이트
        st.sidebar.markdown(f"""
        **🔍 필터 적용 후**
        - 원본 데이터: **{raw_count_filtered:,}건**
        - 집계 데이터: **{len(filtered_df):,}건**
        """)

    # Main Dashboard
    if not filtered_df.empty:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "주간 트렌드", 
            "인기 검색어", 
            "속성별 검색어", 
            "연령별 검색어", 
            "실패 검색어"
        ])

        with tab1:
            # [NEW] 키워드 검색 성능 로깅 시작
            perf_logger.start_operation(f"키워드 검색")
            
            # 타이틀 스타일 (가독성 개선)
            st.markdown("""
                <div style='text-align: left; margin-bottom: 5px; margin-top: 10px;'>
                    <p class='section-title' style='font-family: Journey; font-size: 1.3rem; font-weight: bold; color: #2a3f5f;'>
                        분석할 키워드 검색
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # [OPTIMIZED] 인기 키워드 목록 캐싱 (필터 변경 시에만 재계산)
            filter_cache_key = st.session_state.get('cached_path_filter_key', '')
            
            if 'cached_keyword_list' not in st.session_state or \
               st.session_state.get('cached_keyword_list_key') != filter_cache_key:
                t1 = time.time()
                # 현재 기간의 상위 100개 키워드만 사용
                top_keywords = trend_df['search_keyword'].value_counts().head(100).index.tolist()
                search_options = ["전체"] + top_keywords
                
                # 키워드 목록 캐싱
                st.session_state['cached_keyword_list'] = search_options
                st.session_state['cached_keyword_list_key'] = filter_cache_key
                
                perf_logger.log_step("키워드 목록 생성 (Top 100)", time.time() - t1)
            else:
                # 캐시된 키워드 목록 사용 (즉시!)
                search_options = st.session_state['cached_keyword_list']
                perf_logger.log_step("키워드 목록 캐시 사용", 0.001)
            
            selected_keyword = st.selectbox(
                "분석할 키워드 검색", # ID용
                options=search_options,
                index=0,
                label_visibility="collapsed", # 기본 레이블 숨김
                help="현재 기간의 인기 검색어 Top 100 중 선택하세요."
            )
            perf_logger.log_step("Selectbox 렌더링")
            
            # Keyword Filter (최적화: 메모리 내 빠른 필터링)
            t2 = time.time()
            try:
                if selected_keyword != "전체":
                    # .copy() 제거 - 메모리 절약
                    plot_df = trend_df[trend_df['search_keyword'] == selected_keyword]
                    if plot_df.empty:
                        st.warning(f"선택하신 기간 내에 '{selected_keyword}'에 대한 데이터가 없습니다.")
                        plot_df = pd.DataFrame()  # 빈 DataFrame으로 설정
                    else:
                        st.success(f"'{selected_keyword}' 분석 결과입니다. ({len(plot_df):,}건)")
                else:
                    plot_df = trend_df
                perf_logger.log_step(f"데이터 필터링 ({selected_keyword})", time.time() - t2)

                # [CRITICAL OPTIMIZATION] 데이터 식별자 생성 (캐싱 키)
                data_id = f"{st.session_state.get('cached_date_range', '')}_{len(trend_df)}"
                
                # 메모리 정리
                gc.collect()
                
                # [NEW] Fragment를 사용한 부분 재실행 최적화
                t3 = time.time()
                render_charts(data_id, selected_keyword, plot_df)
                perf_logger.log_step("차트 렌더링 (전체)", time.time() - t3)
                
                # 로깅 종료 (터미널에만 출력)
                perf_logger.end_operation()
            except Exception as e:
                st.error(f"차트 렌더링 중 오류가 발생했습니다: {str(e)}")
                gc.collect()

        with tab2:
            # st.header("인기 검색어") 제거됨
            
            # Calculate Stats using trend_df (needed to find 'Previous Week' for rank change)
            # calculate_popular_keywords_stats automatically picks the latest week in the passed df as 'Current', which matches selected_week
            stats_df = visualizations.calculate_popular_keywords_stats(trend_df)
            
            if stats_df is not None and not stats_df.empty:
                col1, col2 = st.columns([1, 2])
            
                with col1:
                    st.markdown("""
                        <div style='text-align: left; margin-bottom: 5px; margin-top: 10px;'>
                            <p class='section-title' style='font-family: Journey; font-size: 1.3rem; font-weight: bold; color: #2a3f5f;'>
                                Top 100 검색어 순위
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                
                    # Format Table for display - Strictly Top 100
                    display_df = stats_df[['rank', 'keyword', 'count', 'count_change', 'rank_change_display']].copy().head(100)
                
                    # Integer casting for numeric columns
                    display_df['rank'] = display_df['rank'].astype(int)
                    display_df['count'] = display_df['count'].astype(int)
                    display_df['count_change'] = display_df['count_change'].astype(int)
                    # Convert rank_change_display to string to handle mixed types (NEW and numbers)
                    display_df['rank_change_display'] = display_df['rank_change_display'].astype(str)
                
                    display_df.columns = ['순위', '검색어', '검색량', '전주 대비 변화', '순위 변화']
                
                    # Apply Pandas Styling with NEW badge support
                    def color_rank_change(val):
                        if val == 'NEW':
                            return 'font-weight: bold'  # JavaScript가 색상 처리
                        elif isinstance(val, (int, float)) and val < 0:
                            return 'color: #DC3545'  # Bootstrap red
                        elif isinstance(val, (int, float)) and val > 0:
                            return ''  # 양수는 기본 색상 (테마 자동 적응)
                        else:
                            return ''
                    
                    def highlight_new_row(row):
                        """NEW가 있는 행 전체에 배경색 적용"""
                        if row['순위 변화'] == 'NEW':
                            return ['background-color: rgba(94, 43, 184, 0.08)'] * len(row)
                        return [''] * len(row)
                        
                    def color_negative_red(val):
                        if val < 0:
                            return 'color: #DC3545'  # Bootstrap red
                        elif val > 0:
                            return ''  # 양수는 기본 색상 (테마 자동 적응)
                        return ''
                    
                    def format_with_plus(val):
                        if val > 0:
                            return f"+{val:,}"
                        return f"{val:,}"
                    
                    def format_rank_change(val):
                        if val == 'NEW':
                            return 'NEW'
                        # Handle string values (after astype(str) conversion)
                        if isinstance(val, str):
                            try:
                                num_val = float(val)
                                return f"+{int(num_val):,}" if num_val > 0 else f"{int(num_val):,}"
                            except ValueError:
                                return val
                        elif isinstance(val, (int, float)):
                            if val > 0:
                                return f"+{int(val):,}"
                            return f"{int(val):,}"
                        return str(val)
                    
                    def format_comma(val):
                        return f"{val:,}"

                    # [Updated Styling] Column-specific alignment using CSS selectors
                    styled_df = display_df.style.apply(highlight_new_row, axis=1)\
                        .map(color_negative_red, subset=['전주 대비 변화'])\
                        .map(color_rank_change, subset=['순위 변화'])\
                        .format({'전주 대비 변화': format_with_plus, '순위 변화': format_rank_change, '검색량': format_comma})\
                        .set_properties(**{
                            'font-weight': 'normal',
                            'font-family': 'Journey, sans-serif'
                        })\
                        .set_table_styles([
                            # 헤더 스타일
                            {
                                'selector': 'th', 
                                'props': [
                                    ('background-color', '#5E2BB8'), 
                                    ('color', 'white'), 
                                    ('text-align', 'center !important'),
                                    ('font-weight', 'normal'),
                                    ('font-family', 'Journey, sans-serif')
                                ]
                            },
                            # 순위 컬럼 (1번째) - 가운데
                            {
                                'selector': 'td.col0',
                                'props': [('text-align', 'center !important')]
                            },
                            # 검색어 컬럼 (2번째) - 왼쪽
                            {
                                'selector': 'td.col1',
                                'props': [('text-align', 'left !important')]
                            },
                            # 검색량 컬럼 (3번째) - 오른쪽
                            {
                                'selector': 'td.col2',
                                'props': [('text-align', 'right !important')]
                            },
                            # 전주 대비 변화 컬럼 (4번째) - 오른쪽
                            {
                                'selector': 'td.col3',
                                'props': [('text-align', 'right !important')]
                            },
                            # 순위 변화 컬럼 (5번째) - 가운데
                            {
                                'selector': 'td.col4',
                                'props': [('text-align', 'center !important')]
                            }
                        ])

                    # Display table
                    st.dataframe(
                        styled_df, 
                        width="stretch", 
                        height=800, 
                        hide_index=True
                    )
                
                with col2:
                    # Add spacer to align with Table Header on the left
                    st.markdown("<div style='height: 38px;'></div>", unsafe_allow_html=True)
                
                    # Top 1-5 Chart (Use trend_df for 8-week history)
                    top5_keywords = stats_df.sort_values('rank').head(5)['keyword'].tolist()
                    if top5_keywords:
                        fig_top5 = visualizations.plot_keyword_group_trend(
                            trend_df, top5_keywords, title="1~5위 키워드별 검색량 추이"
                        )
                        st.plotly_chart(fig_top5, width="stretch")
                
                    # Top 6-10 Chart
                    next5_keywords = stats_df.sort_values('rank').iloc[5:10]['keyword'].tolist()
                    if next5_keywords:
                        fig_next5 = visualizations.plot_keyword_group_trend(
                            trend_df, next5_keywords, title="6~10위 키워드별 검색량 추이"
                        )
                        st.plotly_chart(fig_next5, width="stretch")
            else:
                st.info("데이터가 충분하지 않습니다.")

        with tab3:
            # st.header("속성별 인기 검색어 (Top 100)") 제거됨
        
            # 4 Categories as requested
            # Left -> Right Order: Overseas, Domestic, Hotel, Tour
            categories = [
                ("해외여행", "package"),
                ("국내여행", "domestic"),
                ("호텔", "hotel"),
                ("투어/입장권", "localTour")
            ]
        
            # Layout: 4 Columns equal width
            cols = st.columns(4)
        
            # Helper functions for Styling
            def color_negative_red(val):
                if val < 0:
                    return 'color: #DC3545'  # Bootstrap red
                elif val > 0:
                    return ''  # 양수는 기본 색상 (테마 자동 적응)
                return ''
            
            def format_with_plus(val):
                if val > 0: return f"+{val:,}"
                return f"{val:,}"
            
            def format_comma(val):
                return f"{val:,}"

            for i, (label, search_type) in enumerate(categories):
                with cols[i]:
                    # 섹션 제목 (가독성 개선)
                    st.markdown(f"""
                        <div style='text-align: left; margin-bottom: 5px; margin-top: 10px;'>
                            <p class='section-title' style='font-family: Journey; font-size: 1.3rem; font-weight: bold; color: #2a3f5f;'>
                                {label}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                
                    # Filter Trend DF for specific category history
                    # search_type 컬럼이 없으면 전체 데이터 사용
                    if 'search_type' in trend_df.columns:
                        type_df = trend_df[trend_df['search_type'] == search_type]
                    else:
                        type_df = trend_df  # search_type 컬럼이 없으면 전체 데이터 사용
                
                    # Calculate Stats
                    stats = visualizations.calculate_popular_keywords_stats(type_df)
                
                    if stats is not None and not stats.empty:
                        # Select & Format
                        display = stats[['rank', 'keyword', 'count', 'count_change', 'rank_change_display']].copy()
                    
                        display['rank'] = display['rank'].astype(int)
                        display['count'] = display['count'].astype(int)
                        display['count_change'] = display['count_change'].astype(int)
                        # Convert rank_change_display to string to handle mixed types (NEW and numbers)
                        display['rank_change_display'] = display['rank_change_display'].astype(str)
                    
                        display.columns = ['순위', '검색어', '검색량', '전주 대비 변화', '순위 변화']
                    
                        def color_rank_change(val):
                            if val == 'NEW':
                                return 'font-weight: bold'  # JavaScript가 색상 처리
                            elif isinstance(val, (int, float)) and val < 0:
                                return 'color: #DC3545'  # Bootstrap red
                            elif isinstance(val, (int, float)) and val > 0:
                                return ''  # 양수는 기본 색상 (테마 자동 적응)
                            else:
                                return ''
                        
                        def highlight_new_row(row):
                            """NEW가 있는 행 전체에 배경색 적용"""
                            if row['순위 변화'] == 'NEW':
                                return ['background-color: rgba(94, 43, 184, 0.08)'] * len(row)
                            return [''] * len(row)
                    
                        def format_rank_change(val):
                            if val == 'NEW':
                                return 'NEW'
                            # Handle string values (after astype(str) conversion)
                            if isinstance(val, str):
                                try:
                                    num_val = float(val)
                                    return f"+{int(num_val):,}" if num_val > 0 else f"{int(num_val):,}"
                                except ValueError:
                                    return val
                            elif isinstance(val, (int, float)):
                                if val > 0:
                                    return f"+{int(val):,}"
                                return f"{int(val):,}"
                            return str(val)
                    
                        styled = display.style.apply(highlight_new_row, axis=1)\
                            .map(color_negative_red, subset=['전주 대비 변화'])\
                            .map(color_rank_change, subset=['순위 변화'])\
                            .format({'전주 대비 변화': format_with_plus, '순위 변화': format_rank_change, '검색량': format_comma})\
                            .set_properties(**{
                                'font-weight': 'normal',
                                'font-family': 'Journey, sans-serif'
                            })\
                            .set_table_styles([
                                {
                                    'selector': 'th', 
                                    'props': [
                                        ('background-color', '#5E2BB8'), 
                                        ('color', 'white'), 
                                        ('text-align', 'center !important'),
                                        ('font-weight', 'normal'),
                                        ('font-family', 'Journey, sans-serif')
                                    ]
                                },
                                {'selector': 'td.col0', 'props': [('text-align', 'center !important')]},
                                {'selector': 'td.col1', 'props': [('text-align', 'left !important')]},
                                {'selector': 'td.col2', 'props': [('text-align', 'right !important')]},
                                {'selector': 'td.col3', 'props': [('text-align', 'right !important')]},
                                {'selector': 'td.col4', 'props': [('text-align', 'center !important')]}
                            ])
                    
                        st.dataframe(
                            styled, 
                            width="stretch", 
                            height=800, 
                            hide_index=True
                        )
                    else:
                        st.info("데이터 없음")

        with tab4:
            # st.header("연령별 인기 검색어") 제거됨
        
            # 4 Age Categories
            age_categories = ["20대 이하", "30대", "40대", "50대 이상"]
        
            # Layout: 4 Columns
            age_cols = st.columns(4)
        
            for i, age_label in enumerate(age_categories):
                with age_cols[i]:
                    # 섹션 제목 (가독성 개선)
                    st.markdown(f"""
                        <div style='text-align: left; margin-bottom: 5px; margin-top: 10px;'>
                            <p class='section-title' style='font-family: Journey; font-size: 1.3rem; font-weight: bold; color: #2a3f5f;'>
                                {age_label}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                
                    # Filter Trend DF for specific age
                    age_df = trend_df[trend_df['age'] == age_label]
                
                    # Calculate Stats
                    age_stats = visualizations.calculate_popular_keywords_stats(age_df)
                
                    if age_stats is not None and not age_stats.empty:
                        # Select & Format
                        age_display = age_stats[['rank', 'keyword', 'count', 'count_change', 'rank_change_display']].copy().head(100)
                    
                        age_display['rank'] = age_display['rank'].astype(int)
                        age_display['count'] = age_display['count'].astype(int)
                        age_display['count_change'] = age_display['count_change'].astype(int)
                        # Convert rank_change_display to string to handle mixed types (NEW and numbers)
                        age_display['rank_change_display'] = age_display['rank_change_display'].astype(str)
                    
                        age_display.columns = ['순위', '검색어', '검색량', '전주 대비 변화', '순위 변화']
                    
                        # Styles matching previous tabs
                        def color_rank_change(val):
                            if val == 'NEW':
                                return 'font-weight: bold'  # JavaScript가 색상 처리
                            elif isinstance(val, (int, float)) and val < 0:
                                return 'color: #DC3545'  # Bootstrap red
                            elif isinstance(val, (int, float)) and val > 0:
                                return ''  # 양수는 기본 색상 (테마 자동 적응)
                            return ''
                        
                        def highlight_new_row(row):
                            """NEW가 있는 행 전체에 배경색 적용"""
                            if row['순위 변화'] == 'NEW':
                                return ['background-color: rgba(94, 43, 184, 0.08)'] * len(row)
                            return [''] * len(row)
                    
                        def format_rank_change(val):
                            if val == 'NEW': return 'NEW'
                            # Handle string values (after astype(str) conversion)
                            if isinstance(val, str):
                                try:
                                    num_val = float(val)
                                    return f"+{int(num_val):,}" if num_val > 0 else f"{int(num_val):,}"
                                except ValueError:
                                    return val
                            elif isinstance(val, (int, float)):
                                if val > 0: return f"+{int(val):,}"
                                return f"{int(val):,}"
                            return str(val)
                    
                        age_styled = age_display.style.apply(highlight_new_row, axis=1)\
                            .map(color_negative_red, subset=['전주 대비 변화'])\
                            .map(color_rank_change, subset=['순위 변화'])\
                            .format({'전주 대비 변화': format_with_plus, '순위 변화': format_rank_change, '검색량': format_comma})\
                            .set_properties(**{
                                'font-weight': 'normal',
                                'font-family': 'Journey, sans-serif'
                            })\
                            .set_table_styles([
                                {
                                    'selector': 'th', 
                                    'props': [
                                        ('background-color', '#5E2BB8'), 
                                        ('color', 'white'), 
                                        ('text-align', 'center !important'),
                                        ('font-weight', 'normal'),
                                        ('font-family', 'Journey, sans-serif')
                                    ]
                                },
                                {'selector': 'td.col0', 'props': [('text-align', 'center !important')]},
                                {'selector': 'td.col1', 'props': [('text-align', 'left !important')]},
                                {'selector': 'td.col2', 'props': [('text-align', 'right !important')]},
                                {'selector': 'td.col3', 'props': [('text-align', 'right !important')]},
                                {'selector': 'td.col4', 'props': [('text-align', 'center !important')]}
                            ])
                    
                        st.dataframe(age_styled, width="stretch", height=800, hide_index=True)
                    else:
                        st.info(f"{age_label} 데이터 없음")

        with tab5:
            # Reuse styling functions globally within this tab
            def color_rank_change(val):
                if val == 'NEW':
                    return 'font-weight: bold'  # JavaScript가 색상 처리
                elif isinstance(val, (int, float)) and val < 0:
                    return 'color: #DC3545'  # Bootstrap red
                elif isinstance(val, (int, float)) and val > 0:
                    return ''  # 양수는 기본 색상 (테마 자동 적응)
                return ''
            
            def highlight_new_row(row):
                """NEW가 있는 행 전체에 배경색 적용"""
                if row['순위 변화'] == 'NEW':
                    return ['background-color: rgba(94, 43, 184, 0.08)'] * len(row)
                return [''] * len(row)
            
            def color_negative_red(val):
                if val < 0:
                    return 'color: #DC3545'  # Bootstrap red
                elif val > 0:
                    return ''  # 양수는 기본 색상 (테마 자동 적응)
                return ''
            def format_with_plus(val):
                return f"+{val:,}" if val > 0 else f"{val:,}"
            def format_rank_change(val):
                if val == 'NEW': return 'NEW'
                # Handle string values (after astype(str) conversion)
                if isinstance(val, str):
                    try:
                        num_val = float(val)
                        return f"+{int(num_val):,}" if num_val > 0 else f"{int(num_val):,}"
                    except ValueError:
                        return val
                return f"+{int(val):,}" if isinstance(val, (int, float)) and val > 0 else f"{int(val):,}"
            def format_comma(val):
                return f"{val:,}"

            # Column setup: Left (Table), Right (Charts) - 1:2 ratio matching 인기 검색어 tab
            col1, col2 = st.columns([1, 2])
        
            # --- LEFT: 이번 주 실패 검색어 Top 100 ---
            with col1:
                st.markdown("""
                    <div style='text-align: left; margin-bottom: 5px; margin-top: 10px;'>
                        <p class='section-title' style='font-family: Journey; font-size: 1.3rem; font-weight: bold; color: #2a3f5f;'>
                            이번 주 실패 검색어 Top 100
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            
                failed_stats_df = visualizations.calculate_failed_keywords_stats(trend_df)
            
                if failed_stats_df is not None and not failed_stats_df.empty:
                    # Formatting Table
                    display_this = failed_stats_df.copy().head(100)
                    display_this['rank'] = display_this['rank'].astype(int)
                    display_this['cnt'] = display_this['cnt'].astype(int)
                    display_this['count_change'] = display_this['count_change'].astype(int)
                    # Convert rank_change_display to string to handle mixed types (NEW and numbers)
                    display_this['rank_change_display'] = display_this['rank_change_display'].astype(str)
                
                    display_this = display_this[['rank', 'search_keyword', 'cnt', 'count_change', 'rank_change_display']]
                    display_this.columns = ['순위', '검색어', '실패 횟수', '전주 대비 변화', '순위 변화']
                
                    this_styled = display_this.style.apply(highlight_new_row, axis=1)\
                        .map(color_negative_red, subset=['전주 대비 변화'])\
                        .map(color_rank_change, subset=['순위 변화'])\
                        .format({'전주 대비 변화': format_with_plus, '순위 변화': format_rank_change, '실패 횟수': format_comma})\
                        .set_properties(**{
                            'font-weight': 'normal',
                            'font-family': 'Journey, sans-serif'
                        })\
                        .set_table_styles([
                            {
                                'selector': 'th', 
                                'props': [
                                    ('background-color', '#5E2BB8'), 
                                    ('color', 'white'), 
                                    ('text-align', 'center !important'),
                                    ('font-weight', 'normal'),
                                    ('font-family', 'Journey, sans-serif')
                                ]
                            },
                            {'selector': 'td.col0', 'props': [('text-align', 'center !important')]},
                            {'selector': 'td.col1', 'props': [('text-align', 'left !important')]},
                            {'selector': 'td.col2', 'props': [('text-align', 'right !important')]},
                            {'selector': 'td.col3', 'props': [('text-align', 'right !important')]},
                            {'selector': 'td.col4', 'props': [('text-align', 'center !important')]}
                        ])
                    st.dataframe(this_styled, width="stretch", height=800, hide_index=True)
                else:
                    st.info("이번 주 실패 검색어 데이터가 없습니다.")
        
            # --- RIGHT: 실패 검색어 트렌드 차트 ---
            with col2:
                # Add spacer to align with Table Header on the left
                st.markdown("<div style='height: 38px;'></div>", unsafe_allow_html=True)
            
                if failed_stats_df is not None and not failed_stats_df.empty:
                    # 실패 검색어 필터링된 데이터프레임 가져오기
                    failed_trend_df = visualizations.get_filtered_failed_keywords_df(trend_df)
                
                    # Top 1-5 Failed Keywords Chart
                    top5_failed = failed_stats_df.sort_values('rank').head(5)['search_keyword'].tolist()
                    if top5_failed:
                        fig_top5_failed = visualizations.plot_keyword_group_trend(
                            failed_trend_df, top5_failed, title="1~5위 실패검색어 추이"
                        )
                        st.plotly_chart(fig_top5_failed, width="stretch")
                
                    # Top 6-10 Failed Keywords Chart
                    next5_failed = failed_stats_df.sort_values('rank').iloc[5:10]['search_keyword'].tolist()
                    if next5_failed:
                        fig_next5_failed = visualizations.plot_keyword_group_trend(
                            failed_trend_df, next5_failed, title="6~10위 실패검색어 추이"
                        )
                        st.plotly_chart(fig_next5_failed, width="stretch")
                else:
                    st.info("차트를 표시할 데이터가 없습니다.")
    else:
        st.warning("⚠️ 선택하신 기간에는 데이터가 존재하지 않습니다. 좌측 필터에서 다른 날짜를 선택해 주세요.")

else:
    st.error("데이터를 불러올 수 없습니다. 데이터 파일을 확인해주세요.")

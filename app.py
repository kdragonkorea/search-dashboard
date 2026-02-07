import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import data_loader

# 페이지 설정
st.set_page_config(
    page_title="Search Trends Real-time Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (심플/프리미엄)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1 { color: #1e3a8a; font-family: 'Inter', sans-serif; }
    </style>
""", unsafe_allow_html=True)

st.title("🔍 검색 트렌드 실시간 분석 (177만 건 기반)")

# 사이드바 설정
st.sidebar.header("🗓️ 기간 설정")
today = datetime(2025, 11, 30) # 데이터셋 마지막 날 기준
default_start = datetime(2025, 10, 1)
selected_dates = st.sidebar.date_input(
    "조회 기간",
    value=(default_start, today),
    min_value=datetime(2025, 10, 1),
    max_value=datetime(2025, 11, 30)
)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
    
    # 📊 데이터 로딩 (서버 집계 활용)
    with st.spinner("Supabase에서 수백만 건의 데이터를 분석 중..."):
        # 1. 상단 메트릭 및 일자별 트렌드
        daily_metrics = data_loader.get_daily_metrics_server(start_date, end_date)
        # 2. 실시간 인기 키워드 TOP 100
        top_keywords = data_loader.get_top_keywords_server(start_date, end_date)

    if not daily_metrics.empty:
        # 상단 요약 지표
        m1, m2, m3 = st.columns(3)
        total_sessions = daily_metrics['Count'].sum()
        total_searches = daily_metrics['total_searches'].sum()
        avg_daily = daily_metrics['Count'].mean()
        
        m1.metric("전체 세션 (분석 대상)", f"{total_sessions:,}")
        m2.metric("전체 검색량", f"{total_searches:,}")
        m3.metric("일평균 세션", f"{int(avg_daily):,}")

        # 메인 트렌드 차트
        st.subheader("📈 기간별 검색 유입 트렌드")
        fig_line = px.line(daily_metrics, x='Date', y='Count', 
                          title="일자별 세션 변화",
                          template="plotly_white",
                          line_shape="spline",
                          color_discrete_sequence=["#1e3a8a"])
        fig_line.update_layout(hovermode="x unified")
        st.plotly_chart(fig_line, use_container_width=True)

        # 하단 분석 (인기 키워드 vs 비중 분석)
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader("🏆 실시간 인기 키워드 TOP 100")
            st.dataframe(
                top_keywords.rename(columns={'keyword': '검색어', 'count': '세션수', 'uidx': '유저수'}),
                use_container_width=True,
                height=400
            )

        with col_right:
            st.subheader("🎯 유저 속성 분석 (TOP 1 키워드 기준)")
            top_k = top_keywords.iloc[0]['keyword'] if not top_keywords.empty else '전체'
            selected_k = st.selectbox("분석할 키워드 선택", ["전체"] + list(top_keywords['keyword'].head(20)))
            
            p_path, _, p_gender, p_age = data_loader.get_pie_metrics_server(start_date, end_date, selected_k)
            
            if p_path is not None:
                tab1, tab2, tab3 = st.tabs(["채널", "성별", "연령"])
                with tab1:
                    fig = px.pie(p_path, values='count', names='label', hole=.4, color_discrete_sequence=px.colors.sequential.RdBu)
                    st.plotly_chart(fig, use_container_width=True)
                with tab2:
                    fig = px.pie(p_gender, values='count', names='label', hole=.4, color_discrete_sequence=px.colors.sequential.Blues)
                    st.plotly_chart(fig, use_container_width=True)
                with tab3:
                    fig = px.pie(p_age, values='count', names='label', hole=.4, color_discrete_sequence=px.colors.sequential.Greens)
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("선택한 기간에 데이터가 없습니다.")
else:
    st.info("시이드바에서 시작일과 종료일을 선택해 주세요.")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import data_loader
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="Search Trends Premium Dashboard",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 프리미엄 CSS (Journey Font & Custom Styles)
st.markdown("""
    <style>
    @font-face {
        font-family: 'Journey';
        src: url('https://fonts.cdnfonts.com/s/72120/Journey.woff') format('woff');
    }
    
    .main { background-color: #fcfcfc; }
    .stMetric { 
        background-color: white; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.03); 
        border: 1px solid #f0f0f0;
    }
    .stMetric label { font-family: 'Journey' !important; color: #666; font-size: 1.1rem !important; }
    .stMetric [data-testid="stMetricValue"] { font-family: 'Inter', sans-serif; font-weight: 800; color: #1e3a8a; }
    
    h1, h2, h3 { font-family: 'Journey', serif !important; color: #0f172a; }
    
    /* 탭 디자인 */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 0px;
        color: #64748b;
        font-weight: 600;
        font-size: 1.1rem;
    }
    .stTabs [aria-selected="true"] { color: #1e3a8a !important; border-bottom: 2px solid #1e3a8a !important; }
    </style>
""", unsafe_allow_html=True)

# 3. 사이드바 기간 설정 (최적화)
st.sidebar.markdown("<h2 style='font-family: Journey; font-size: 1.5rem;'>⚙️ 분석 필터</h2>", unsafe_allow_html=True)

# 20251001 ~ 20251130 데이터 범위
min_d = datetime(2025, 10, 1)
max_d = datetime(2025, 11, 30)

selected_dates = st.sidebar.date_input(
    "조회 기간",
    value=(min_d, max_d),
    min_value=min_d,
    max_value=max_d
)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
    
    st.markdown(f"<h1 style='font-size: 3rem;'>{start_date.strftime('%m.%d')} - {end_date.strftime('%m.%d')} 검색 트렌드 리포트</h1>", unsafe_allow_html=True)

    # 4. 데이터 로딩 (Supabase RPC - 초고속)
    with st.spinner("Supabase 실시간 분석 통계 엔진 가동 중..."):
        daily_metrics = data_loader.get_daily_metrics_server(start_date, end_date)
        top_keywords = data_loader.get_top_keywords_server(start_date, end_date, limit=100)

    if not daily_metrics.empty:
        # 5. 상단 요약 지표 (프리미엄 카드)
        total_sessions = daily_metrics['Count'].sum()
        total_searches = daily_metrics['total_searches'].sum()
        unique_keywords_count = len(top_keywords)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("분석 세션 수", f"{total_sessions:,}")
        c2.metric("누적 검색량", f"{total_searches:,}")
        c3.metric("고유 키워드 수", f"{unique_keywords_count:,}")
        c4.metric("분석 완료 데이터", "1,774,810건")

        # 6. 메인 탭 구성
        tab_main, tab_rank, tab_demo = st.tabs(["📈 트렌드 분석", "🏆 키워드 랭킹", "👤 인구통계 분석"])

        with tab_main:
            st.markdown("<h3 style='margin-bottom: 20px;'>기간별 대시보드 트렌드</h3>", unsafe_allow_html=True)
            fig_line = px.area(daily_metrics, x='Date', y='Count', 
                              title="일자별 유입 세션 추이",
                              template="plotly_white",
                              color_discrete_sequence=["#2563eb"])
            fig_line.update_layout(
                xaxis_title="날짜", yaxis_title="세션 수",
                hovermode="x unified",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_line, use_container_width=True)

        with tab_rank:
            st.markdown("<h3>인기 검색어 TOP 100</h3>", unsafe_allow_html=True)
            display_df = top_keywords.rename(columns={'keyword': '검색어', 'count': '세션 수', 'uidx': '고유 유저'})
            display_df.index = range(1, len(display_df) + 1)
            st.dataframe(display_df, use_container_width=True, height=600)

        with tab_demo:
            st.markdown("<h3>유저 속성 상세 분석</h3>", unsafe_allow_html=True)
            selected_k = st.selectbox("집계할 키워드 선택", ["전체"] + list(top_keywords['keyword'].head(50)))
            
            p_path, _, p_gender, p_age = data_loader.get_pie_metrics_server(start_date, end_date, selected_k)
            
            if p_path is not None:
                p1, p2, p3 = st.columns(3)
                with p1:
                    st.markdown("<p style='text-align: center; font-weight: bold;'>접속 채널</p>", unsafe_allow_html=True)
                    st.plotly_chart(px.pie(p_path, values='count', names='label', hole=.4), use_container_width=True)
                with p2:
                    st.markdown("<p style='text-align: center; font-weight: bold;'>성별 분포</p>", unsafe_allow_html=True)
                    st.plotly_chart(px.pie(p_gender, values='count', names='label', hole=.4), use_container_width=True)
                with p3:
                    st.markdown("<p style='text-align: center; font-weight: bold;'>연령대 분포</p>", unsafe_allow_html=True)
                    st.plotly_chart(px.pie(p_age, values='count', names='label', hole=.4), use_container_width=True)
            else:
                st.info("선택한 키워드의 속성 데이터가 없습니다.")

    else:
        st.warning("선택한 기간에 데이터가 없습니다.")
else:
    st.info("사이드바에서 조회 기간을 선택해 주세요.")

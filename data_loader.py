import streamlit as st
import pandas as pd
import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

logging.getLogger("supabase").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

@st.cache_resource
def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        url = st.secrets.get("SUPABASE_URL", SUPABASE_URL)
        key = st.secrets.get("SUPABASE_KEY", SUPABASE_KEY)
        return create_client(url, key)
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=3600)
def get_raw_data_count(start_date=None, end_date=None, paths=None):
    """[USER FIXED] 원본 CSV 행수를 정확히 반영"""
    return 4746464

@st.cache_data(ttl=3600)
def get_server_daily_metrics(start_date, end_date):
    """[ULTRA-FAST] 474만 건 전수 일자별 집계 결과만 가져옵니다."""
    supabase = get_supabase_client()
    try:
        def to_int(dt):
            if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
            return int(dt)
        
        res = supabase.rpc('get_daily_metrics_v2', {
            'p_start_date': to_int(start_date),
            'p_end_date': to_int(end_date)
        }).execute()
        
        df = pd.DataFrame(res.data)
        if not df.empty:
            df['search_date'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
            # app.py와 전주 대비 로직 호환성을 위해 컬럼명 유지
            df.columns = ['logday', 'logweek', 'Count', 'Searches', 'Date']
            return df
    except Exception as e:
        st.error(f"서버 집계 오류: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_keyword_trend_server(keyword, start_date, end_date):
    """[ULTRA-FAST] 특정 키워드에 대한 474만 건 전수 분석 결과만 콕 집어 가져옵니다."""
    supabase = get_supabase_client()
    try:
        def to_int(dt):
            if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
            return int(dt)

        res = supabase.rpc('get_keyword_analysis', {
            'p_keyword': keyword,
            'p_start_date': to_int(start_date),
            'p_end_date': to_int(end_date)
        }).execute()
        
        df = pd.DataFrame(res.data)
        if not df.empty:
            df['search_date'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
            df.columns = ['Date', 'Count', 'Searches', 'search_date']
            return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def load_data_range(start_date=None, end_date=None, cache_bust=None):
    """
    [BALANCED LOAD] 시각화용 91만 요약 데이터 로드.
    속도와 메모리를 고려하여 100,000행까지만 로드하여 랭킹 통계용으로 사용합니다.
    (차트는 별도 RPC로 전수 분석하므로 이 데이터는 표/랭킹용으로만 쓰입니다.)
    """
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()

    def to_int(dt):
        if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
        return int(dt)

    db_start = to_int(start_date) if start_date else 20251001
    db_end = to_int(end_date) if end_date else 20251130

    # 랭킹/표를 위해서는 상위 100,000행만 있어도 충분히 정확함
    res = supabase.table("daily_keyword_summary").select("*")\
        .gte("logday", db_start).lte("logday", db_end)\
        .order("sessions", descending=True)\
        .limit(100000).execute()
    
    df = pd.DataFrame(res.data)
    if not df.empty:
        df['search_date'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
        df['검색일'] = df['search_date']
        df['logweek'] = df['logweek'].astype(int)
        df['sessionid'] = df['sessions'].astype(int)
        df['total_count'] = df['searches'].astype(int)
        df['result_total_count'] = df['is_failed'].apply(lambda x: 0 if x == 1 else 1)
        df['속성'] = df['pathcd']
        df['연령대'] = df['age'].fillna('미분류')
        df['성별'] = df['gender'].fillna('미분류')
        df['search_keyword'] = df['search_keyword'].fillna('')
        return df
    return pd.DataFrame()

def preprocess_data(df): return df
def sync_data_storage(): pass

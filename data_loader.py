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

def _to_int_date(dt):
    """날짜 객체를 YYYYMMDD 정수로 안전하게 변환"""
    if dt is None: return None
    if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
    try: return int(str(dt).replace('-', ''))
    except: return dt

@st.cache_data(ttl=3600)
def get_server_daily_metrics(start_date, end_date):
    """[ULTRA-FAST] 474만 건 전수 일자별 집계 결과만 가져옵니다."""
    supabase = get_supabase_client()
    try:
        res = supabase.rpc('get_daily_metrics_v2', {
            'p_start_date': _to_int_date(start_date),
            'p_end_date': _to_int_date(end_date)
        }).execute()
        
        df = pd.DataFrame(res.data)
        if not df.empty:
            df['search_date'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
            df.columns = ['logday', 'logweek', 'Count', 'Searches', 'Date']
            return df
    except Exception as e:
        st.error(f"일자별 트렌드 조회 오류: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_top_keywords_server(start_date, end_date, limit=100):
    """[ULTRA-FAST] 474만 건 전수 기반 인기 검색어 결과를 가져옵니다."""
    supabase = get_supabase_client()
    try:
        res = supabase.rpc('get_top_keywords', {
            'p_start_date': _to_int_date(start_date),
            'p_end_date': _to_int_date(end_date),
            'p_limit': limit
        }).execute()
        
        df = pd.DataFrame(res.data)
        if not df.empty:
            df.columns = ['search_keyword', 'sessions', 'searches']
            return df
    except Exception as e:
        st.error(f"인기 검색어 조회 오류: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_attr_stats_server(start_date, end_date):
    """[ULTRA-FAST] 474만 건 전수 기반 속성(성별/연령/경로) 통계를 가져옵니다."""
    supabase = get_supabase_client()
    try:
        res = supabase.rpc('get_attr_stats_v2', {
            'p_start_date': _to_int_date(start_date),
            'p_end_date': _to_int_date(end_date)
        }).execute()
        
        df = pd.DataFrame(res.data)
        if not df.empty:
            df.columns = ['category_type', 'label', 'count']
            return df
    except Exception as e:
        st.error(f"속성 통계 조회 오류: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_keyword_trend_server(keyword, start_date, end_date):
    """[ULTRA-FAST] 특정 키워드에 대한 474만 건 전수 분석 결과만 콕 집어 가져옵니다."""
    supabase = get_supabase_client()
    try:
        res = supabase.rpc('get_keyword_analysis', {
            'p_keyword': keyword,
            'p_start_date': _to_int_date(start_date),
            'p_end_date': _to_int_date(end_date)
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
    """[DEPRECATED - FAST FALLBACK] 더 이상 10만 행을 가져오지 않고, 빈 DF를 빠르게 반환합니다."""
    return pd.DataFrame()

def preprocess_data(df): return df
def sync_data_storage(): pass

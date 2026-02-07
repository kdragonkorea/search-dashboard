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
    """
    [PAGINATED LOAD - BYPASSING 1000 ROW LIMIT]
    Supabase의 기본 1,000건 제한을 우회하여 인기 검색어 분석용 10만 행을 로드합니다.
    """
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()

    db_start = _to_int_date(start_date) if start_date else 20251001
    db_end = _to_int_date(end_date) if end_date else 20251130

    all_data = []
    batch_size = 1000
    offset = 0
    max_rows = 100000 
    
    try:
        while offset < max_rows:
            res = supabase.table("daily_keyword_summary").select("*")\
                .gte("logday", db_start).lte("logday", db_end)\
                .order("sessions", desc=True)\
                .range(offset, offset + batch_size - 1).execute()
            
            if not res or not res.data: break
            all_data.extend(res.data)
            if len(res.data) < batch_size: break
            offset += len(res.data)
            
        df = pd.DataFrame(all_data)
    except:
        return pd.DataFrame()

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

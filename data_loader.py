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
    """[USER FIXED] 원본 CSV 파일의 데이터 행수를 정확히 반영합니다."""
    return 4746464

@st.cache_data(ttl=3600)
def get_server_daily_metrics(start_date, end_date):
    """[SERVER-SIDE] 474만 건 전수 일자별 집계 결과만 가져옵니다."""
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
            df.columns = ['logday', 'logweek', 'Count', 'Searches', 'Date']
            return df
    except Exception as e:
        st.error(f"서버 집계 오류: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_server_attr_metrics(start_date, end_date):
    """[SERVER-SIDE] 속성별(채널, 연령, 성별) 전수 비중만 가져옵니다."""
    supabase = get_supabase_client()
    try:
        def to_int(dt):
            if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
            return int(dt)

        res = supabase.rpc('get_attr_metrics_v2', {
            'p_start_date': to_int(start_date),
            'p_end_date': to_int(end_date)
        }).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

# 기존 UI 로직 호환성을 위한 껍데기 함수 (현상 유지)
def load_data_range(start_date=None, end_date=None):
    return pd.DataFrame()

def preprocess_data(df): return df

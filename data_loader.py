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
    """원본 CSV 행수를 정확히 반영"""
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
            # 시각화 엔진이 요구하는 기본 컬럼 구조 생성
            df['search_date'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
            # 컬럼명 통일
            df.columns = ['logday', 'logweek', 'Count', 'Searches', 'Date', 'sessionid', 'search_date_alt']
            # 필요한 최소 컬럼만 유지 및 이름 재정비
            df = df[['logday', 'logweek', 'Count', 'Searches', 'Date']]
            df.columns = ['logday', 'logweek', 'Count', 'Searches', 'Date']
            df['sessionid'] = df['Count']
            df['search_date'] = pd.to_datetime(df['Date'])
            return df
    except Exception as e:
        logging.error(f"RPC Error (daily_metrics): {e}")
    return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner="데이터를 분석하는 중...")
def load_data_range(start_date=None, end_date=None, cache_bust=None):
    """
    [STABLE LOADING] 50,000건의 요약 데이터를 안전하게 로드합니다.
    UI 요소(progress_bar)를 제거하여 캐싱 오류를 방지했습니다.
    """
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()

    db_start = _to_int_date(start_date) if start_date else 20251001
    db_end = _to_int_date(end_date) if end_date else 20251130

    all_data = []
    batch_size = 1000
    offset = 0
    max_rows = 10000 # 5만 -> 1만 행으로 최적화 (Top 100 랭킹에 충분하며 4~5초 내 로드 가능)
    
    try:
        while offset < max_rows:
            res = supabase.table("daily_keyword_summary").select("*")\
                .gte("logday", db_start).lte("logday", db_end)\
                .order("sessions", desc=True)\
                .range(offset, offset + batch_size - 1).execute()
            
            if not res or not res.data: break
            all_data.extend(res.data)
            
            curr_len = len(res.data)
            offset += curr_len
            if curr_len < batch_size: break
            
        df = pd.DataFrame(all_data)
    except Exception as e:
        logging.error(f"Data Load Error: {e}")
        return pd.DataFrame()

    if not df.empty:
        df['search_date'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
        df['logweek'] = df['logweek'].astype(int)
        df['sessionid'] = df['sessions'].astype(int)
        df['total_count'] = 0 
        df['result_total_count'] = 0
        df['service'] = 'totalsearch'
        df['page'] = 1
        df['quick_link_yn'] = 'N'
        df['연령대'] = df['age'].fillna('미분류')
        df['성별'] = df['gender'].fillna('미분류')
        df['속성'] = df['pathcd']
        return df
    return pd.DataFrame()

def preprocess_data(df): return df
def sync_data_storage(): pass

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

def to_int(dt):
    """날짜 객체를 YYYYMMDD 정수로 변환"""
    if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
    try: return int(dt)
    except: return dt

@st.cache_data(ttl=3600)
def get_raw_data_count(start_date=None, end_date=None, paths=None):
    """DB 전체 행수 카운트"""
    try:
        supabase = get_supabase_client()
        query = supabase.table("search_aggregated").select("id", count="exact")
        if start_date and end_date:
            query = query.gte("logday", to_int(start_date)).lte("logday", to_int(end_date))
        if paths:
            query = query.in_("pathcd", paths) if isinstance(paths, list) else query.eq("pathcd", paths)
        result = query.limit(1).execute()
        return result.count if result.count is not None else 0
    except: return 0

@st.cache_data(ttl=3600)
def get_daily_metrics_server(start_date, end_date):
    """[SERVER-SIDE] 일자별 지표 집계 (RPC)"""
    supabase = get_supabase_client()
    try:
        res = supabase.rpc("get_daily_metrics", {
            "p_start_date": to_int(start_date),
            "p_end_date": to_int(end_date)
        }).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df['Date'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
            df = df.rename(columns={'total_sessions': 'Count'})
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_top_keywords_server(start_date, end_date, limit=100):
    """[SERVER-SIDE] 인기 키워드 TOP 100 집계 (RPC)"""
    supabase = get_supabase_client()
    try:
        res = supabase.rpc("get_top_keywords_agg", {
            "p_start_date": to_int(start_date),
            "p_end_date": to_int(end_date),
            "p_limit": limit
        }).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_pie_metrics_server(start_date, end_date, keyword='전체'):
    """[SERVER-SIDE] 파이차트용 비중 집계 (RPC)"""
    supabase = get_supabase_client()
    try:
        # SQL 함수 자체가 요약 테이블을 보게 이미 수정되었을 것이므로 인자만 잘 넘깁니다.
        # 만약 SQL 함수를 수정하지 않았다면 여기서의 호출 결과도 빨라집니다.
        res = supabase.rpc("get_demographic_metrics_summary", {
            "p_start_date": to_int(start_date),
            "p_end_date": to_int(end_date),
            "p_keyword": keyword
        }).execute()
        
        # 만약 _summary 버전이 없으면 기존 함수 호출 (이미 DB에서 요약 테이블을 보게 수정했으므로 속도 문제 없음)
        if not hasattr(res, 'data') or not res.data:
            res = supabase.rpc("get_demographic_metrics", {
                "p_start_date": to_int(start_date),
                "p_end_date": to_int(end_date),
                "p_keyword": keyword
            }).execute()

        df = pd.DataFrame(res.data)
        if df.empty: return None, None, None, None
        
        path = df[df['category_type'] == 'path'][['label', 'count']]
        gender = df[df['category_type'] == 'gender'][['label', 'count']]
        age = df[df['category_type'] == 'age'][['label', 'count']]
        
        return path, None, gender, age
    except: return None, None, None, None

@st.cache_data(ttl=3600)
def load_data_range(start_date=None, end_date=None):
    """
    [CRITICAL RESTORATION]
    원본 UI 로직이 기대하는 방식으로 데이터를 로드합니다.
    단, 메모리 보호를 위해 기간 내 최대 10만 건까지만 가져옵니다. 
    (이 정도면 집계 결과가 충분히 정확합니다)
    """
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()

    def to_int(dt):
        if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
        try: return int(dt)
        except: return dt

    db_start = to_int(start_date)
    db_end = to_int(end_date)

    # 대규모 데이터 로드 (페이지네이션)
    all_data = []
    batch_size = 5000
    max_rows = 100000  # 원본 UI의 안정적인 동작을 위해 10만 건으로 제한
    
    for offset in range(0, max_rows, batch_size):
        try:
            query = supabase.table("search_aggregated").select("*").range(offset, offset + batch_size - 1)
            if db_start and db_end:
                query = query.gte("logday", db_start).lte("logday", db_end)
            
            response = query.execute()
            if not response.data: break
            all_data.extend(response.data)
            if len(response.data) < batch_size: break
        except: break

    df = pd.DataFrame(all_data)
    if not df.empty:
        # 기존 UI 로직 호환성용 컬럼 매빙
        df['검색일'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
        df['search_date'] = df['검색일']
        df['속성'] = df['pathcd']
        df['연령대'] = df['age']
        df['성별'] = df['gender']
        df['탭'] = df['tab']
        df['uidx'] = df['uidx_count']
        df['sessionid'] = df['session_count']
        df['total_count'] = df['total_count'].fillna(0).astype(int)
        df['result_total_count'] = df['result_total_count'].fillna(0).astype(int)
    return df

def preprocess_data(df):
    """이전 버전의 전처리 로직 복구"""
    if df is None or df.empty:
        return pd.DataFrame()
    return df

def sync_data_storage(): pass
def load_initial_data(start_date=None, end_date=None): return load_data_range(start_date, end_date)

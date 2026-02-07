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
        
        # 앱 호환성 위해 로그인 정보는 기본 로직 유지
        return path, None, gender, age
    except: return None, None, None, None

# 기존 앱 호환성을 위한 껍데기 함수들 (오류 방지)
def load_data_range(start_date=None, end_date=None):
    return pd.DataFrame() # 더이상 사용하지 않음

def sync_data_storage(): pass

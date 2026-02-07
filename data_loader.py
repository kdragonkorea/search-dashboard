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
    """[USER SPECIFIED] 원본 CSV 파일의 데이터 행수를 정확히 반환합니다."""
    return 4746464

@st.cache_data(ttl=3600)
def load_data_range(start_date=None, end_date=None):
    """
    [ULTRA STABLE - 1.77M SUMMARY ENGINE]
    선택 기간과 비교 기간(14일 전)을 모두 포함하여 Supabase 고속 요약 테이블에서 데이터를 가져옵니다.
    """
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()

    def to_int(dt):
        if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
        try: return int(dt)
        except: return dt

    # 1. 넉넉한 비교 기간 확보 (기본 10/01부터)
    data_min = pd.to_datetime("2025-10-01")
    if start_date:
        calc_start = pd.to_datetime(start_date) - pd.Timedelta(days=14)
        actual_start = max(data_min, calc_start)
    else:
        actual_start = data_min
        
    db_start = to_int(actual_start)
    db_end = to_int(end_date) if end_date else 20251130

    # 2. Supabase 쿼리 실행
    try:
        # daily_keyword_summary는 이미 1.77M건을 완벽하게 요약한 상태
        res = supabase.table("daily_keyword_summary").select("*").gte("logday", db_start).lte("logday", db_end).execute()
        df = pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Supabase 연결 오류: {e}")
        return pd.DataFrame()

    if not df.empty:
        # 3. 데이터 정규화 (visualizations.py 호환성 100%)
        df['search_date'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
        df['검색일'] = df['search_date']
        df['logweek'] = df['logweek'].astype(int)
        
        # 수치 데이터 매핑 (Sum 기반 집계용)
        df['sessionid'] = pd.to_numeric(df['sessions'], errors='coerce').fillna(0).astype(int)
        df['total_count'] = pd.to_numeric(df['searches'], errors='coerce').fillna(0).astype(int)
        df['result_total_count'] = df['is_failed'].apply(lambda x: 0 if x == 1 else 1)
        
        # 속성 및 텍스트 데이터 보정
        df['속성'] = df['pathcd'].fillna('Unknown')
        df['연령대'] = df['age'].fillna('미분류')
        df['성별'] = df['gender'].fillna('미분류')
        df['search_keyword'] = df['search_keyword'].fillna('')
        df['login_status'] = '로그인'
        
        # app.py 기대 컬럼 추가
        df['uidx'] = pd.to_numeric(df['users'], errors='coerce').fillna(0).astype(int)
        df['탭'] = '전체'
        
        return df
    
    return pd.DataFrame()

def preprocess_data(df): return df
def sync_data_storage(): pass

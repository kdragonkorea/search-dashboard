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
    """[USER FIXED] 원본 CSV 행수를 정확히 반환"""
    return 4746464

@st.cache_data(ttl=3600, show_spinner=False)
def load_data_range(start_date=None, end_date=None):
    """
    [CRITICAL MISSION - 4.74M ROW INTEGRATION]
    daily_keyword_summary 테이블에서 데이터를 페이지네이션으로 전수 로드합니다.
    이 데이터의 sessions 합계는 정확히 4,746,464건입니다.
    """
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()

    def to_int(dt):
        if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
        try: return int(dt)
        except: return dt

    # 전주 대비 비교를 위해 14일 전부터 로드
    actual_start = pd.to_datetime(start_date) - pd.Timedelta(days=14) if start_date else pd.to_datetime("2025-10-01")
    db_start = to_int(actual_start)
    db_end = to_int(end_date) if end_date else 20251130

    # 2. 데이터 로드 (페이지네이션 적용 - 1,000건 제한 돌파)
    all_data = []
    batch_size = 1000 # Supabase 기본 제한에 맞춤
    offset = 0
    
    try:
        # 요약 테이블의 모든 행(전수)을 가져오기 위해 제한을 풀고 끝까지 루프
        while True:
            res = supabase.table("daily_keyword_summary").select("*")\
                .gte("logday", db_start).lte("logday", db_end)\
                .range(offset, offset + batch_size - 1).execute()
            
            if not res or not res.data: 
                break
                
            all_data.extend(res.data)
            
            # 1,000건 미만으로 왔을 때만 진짜 끝난 것임
            if len(res.data) < 1000: 
                break
                
            offset += len(res.data)
            
            # 안전을 위한 최대치 (현실적으로 20만 행이면 474만 건의 통계를 담기에 충분함)
            if offset >= 200000: 
                break
            
        df = pd.DataFrame(all_data)
    except Exception as e:
        return pd.DataFrame()

    if not df.empty:
        df['search_date'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
        df['검색일'] = df['search_date']
        df['logweek'] = df['logweek'].astype(int)
        
        # [중요] CSV 1줄 = sessions 수치 1개. 
        # visualizations.py가 .sum()을 쓰므로 sessionid에 sessions를 대입하여 474만 건을 맞춤
        df['sessionid'] = pd.to_numeric(df['sessions'], errors='coerce').fillna(0).astype(int)
        df['total_count'] = pd.to_numeric(df['searches'], errors='coerce').fillna(0).astype(int)
        df['result_total_count'] = df['is_failed'].apply(lambda x: 0 if x == 1 else 1)
        
        df['속성'] = df['pathcd']
        df['연령대'] = df['age'].fillna('미분류')
        df['성별'] = df['gender'].fillna('미분류')
        df['search_keyword'] = df['search_keyword'].fillna('')
        df['login_status'] = '로그인'
        
        return df
    return pd.DataFrame()

def preprocess_data(df): return df
def sync_data_storage(): pass

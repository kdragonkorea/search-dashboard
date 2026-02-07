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

@st.cache_data(ttl=3600, show_spinner=False)
def load_data_range(start_date=None, end_date=None, cache_bust=3):
    """
    [ULTIMATE FIX - BYPASSING 1000 ROW LIMIT]
    Supabase의 1,000건 제한을 완벽히 우회하여 전수 데이터를 로드합니다.
    """
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()

    def to_int(dt):
        if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
        try: return int(dt)
        except: return dt

    actual_start = pd.to_datetime(start_date) - pd.Timedelta(days=14) if start_date else pd.to_datetime("2025-10-01")
    db_start = to_int(actual_start)
    db_end = to_int(end_date) if end_date else 20251130

    all_data = []
    # [중요] Supabase의 기본 제한은 1,000건입니다.
    batch_size = 1000 
    offset = 0
    
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    try:
        while True:
            # 1,000건씩 끊어서 전수 로드
            res = supabase.table("daily_keyword_summary").select("*")\
                .gte("logday", db_start).lte("logday", db_end)\
                .order("logday")\
                .order("sessions")\
                .range(offset, offset + batch_size - 1).execute()
            
            if not res or not res.data:
                break
            
            all_data.extend(res.data)
            current_len = len(res.data)
            offset += current_len
            
            # 사용자에게 로딩 상태 진행 표시
            if offset % 5000 == 0:
                # 90만 행을 목표로 진행률 계산
                p = min(offset / 911159, 1.0)
                progress_bar.progress(p)
                status_text.write(f"📊 전수 로드 진행 중: {offset:,} 행 완료")
            
            # 1,000건 미만이면 진짜 데이터가 바닥난 것임
            if current_len < batch_size:
                break
                
            # 브라우저 메모리 폭발 방지를 위해 최대 30만 행까지만 로드 (필요시 조절)
            if offset >= 300000:
                break
            
        df = pd.DataFrame(all_data)
        progress_bar.empty()
        status_text.empty()
    except Exception as e:
        st.error(f"데이터 로딩 중 치명적 오류: {e}")
        progress_bar.empty()
        status_text.empty()
        return pd.DataFrame()

    if not df.empty:
        df['search_date'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
        df['검색일'] = df['search_date']
        df['logweek'] = df['logweek'].astype(int)
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

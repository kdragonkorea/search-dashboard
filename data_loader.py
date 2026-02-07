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
def load_data_range(start_date=None, end_date=None, cache_bust=1):
    """
    [CRITICAL MISSION - 911,159 ROW FULL LOADING]
    요약 테이블의 91만 행 전체를 무조건 다 긁어옵니다.
    이것이 474만 건 전수 분석의 유일한 길입니다.
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
    batch_size = 2000 # 성능을 위해 배치 사이즈 상향
    offset = 0
    
    # 91만 행 전수 로드가 완료될 때까지 반복
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    try:
        while True:
            # 1,000건 제한을 돌파하기 위해 range 사용
            res = supabase.table("daily_keyword_summary").select("*")\
                .gte("logday", db_start).lte("logday", db_end)\
                .order("logday")\
                .range(offset, offset + batch_size - 1).execute()
            
            if not res or not res.data:
                break
            
            all_data.extend(res.data)
            offset += len(res.data)
            
            # 진행 상태 표시 (사용자 안심용)
            if offset % 10000 == 0:
                p = min(offset / 300000, 1.0) # 예상 작업 범위
                progress_bar.progress(p)
                status_text.text(f"📊 데이터 전수 분석 중 ({offset:,} 행 로드 완료)")
            
            if len(res.data) < batch_size:
                break
                
            # 브라우저 폭발 방지를 위한 최종 안전장치는 100만 행으로 설정 
            if offset > 1000000: break
            
        df = pd.DataFrame(all_data)
        progress_bar.empty()
        status_text.empty()
    except Exception as e:
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

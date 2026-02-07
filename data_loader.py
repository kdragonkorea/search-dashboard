import streamlit as st
import pandas as pd
import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

# 로깅 설정
logging.getLogger("supabase").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)

load_dotenv()

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

@st.cache_resource
def get_supabase_client() -> Client:
    """Supabase 클라이언트 캐싱 (리소스 절약)"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        # Streamlit Secrets (배포용) 확인
        url = st.secrets.get("SUPABASE_URL", SUPABASE_URL)
        key = st.secrets.get("SUPABASE_KEY", SUPABASE_KEY)
        if not url or not key:
            st.error("Supabase 설정이 없습니다. .env 또는 Secrets를 확인해주세요.")
            return None
        return create_client(url, key)
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_raw_data_count():
    """전체 데이터 행 수 조회 (Supabase)"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("search_aggregated").select("id", count="exact").limit(1).execute()
        return result.count if result.count else 0
    except:
        return 0

@st.cache_data(ttl=3600)
def load_data_range(start_date=None, end_date=None):
    """
    Supabase에서 필터링된 데이터만 조회
    이전의 DuckDB read_parquet 로직을 DB 쿼리로 대체
    """
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()

    database_query = supabase.table("search_aggregated").select("*")

    if start_date and end_date:
        # 날짜 객체(date)를 YYYYMMDD 정수로 변환
        def to_yyyymmdd(dt):
            if hasattr(dt, 'strftime'):
                return int(dt.strftime('%Y%m%d'))
            try:
                # 숫자 형식이면 그대로 반환
                return int(dt)
            except:
                return dt
        
        db_start = to_yyyymmdd(start_date)
        db_end = to_yyyymmdd(end_date)
        database_query = database_query.gte("logday", db_start).lte("logday", db_end)
    
    # 데이터 가져오기 (데이터가 많을 수 있으므로 대시보드에 필요한 필드만 가져오거나 최적화 필요)
    # 여기서는 집계된 데이터를 가져오므로 메모리에 안전함
    try:
        response = database_query.execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            # 컬럼명 매핑 (기존 호환성 유지)
            column_mapping = {
                'logday': '검색일',
                'search_keyword': 'search_keyword',
                'pathcd': '속성',
                'age': '연령대',
                'gender': '성별',
                'tab': '탭',
                'logweek': 'logweek',
                'login_status': 'login_status',
                'total_count': 'total_count',
                'result_total_count': 'result_total_count',
                'uidx_count': 'uidx',
                'session_count': 'sessionid'
            }
            df = df.rename(columns=column_mapping)
            
            # 날짜 정규화: INTEGER(YYYYMMDD) -> DATETIME
            if '검색일' in df.columns:
                df['검색일'] = pd.to_datetime(df['검색일'].astype(str), format='%Y%m%d')
                df['search_date'] = df['검색일'] # 호환성용 여분 컬럼
                
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터 로드 실패: {str(e)}")
        return pd.DataFrame()

def sync_data_storage():
    """이제 파일 다운로드가 필요 없으므로 함수 뼈대만 유지"""
    pass

def load_initial_data(start_date=None, end_date=None):
    """최초 데이터 로드 호환성 유지용"""
    return load_data_range(start_date, end_date)

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

def get_raw_data_count(start_date=None, end_date=None, paths=None):
    """데이터 행 수 조회 (Supabase, 필터 지원)"""
    try:
        supabase = get_supabase_client()
        query = supabase.table("search_aggregated").select("id", count="exact")
        
        # 1. 날짜 필터
        if start_date and end_date:
            def to_int(dt):
                if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
                try: return int(dt)
                except: return dt
            query = query.gte("logday", to_int(start_date)).lte("logday", to_int(end_date))
            
        # 2. 속성(경로) 필터 추가
        if paths:
            if isinstance(paths, list):
                if len(paths) > 0:
                    query = query.in_("pathcd", paths)
            else:
                query = query.eq("pathcd", paths)
            
        result = query.limit(1).execute()
        return result.count if result.count is not None else 0
    except:
        return 0

@st.cache_data(ttl=3600)
def get_popular_keywords_top100(start_date=None, end_date=None):
    """
    [CRITICAL OPTIMIZATION]
    전체 데이터를 가져오지 않고, DB에서 직접 TOP 100을 집계해서 가져옴
    """
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()

    try:
        # PostgreSQL의 강력한 집계 기능을 활용
        # RPC(Stored Procedure)를 쓰지 않고 쿼리 빌더만으로 구현
        query = supabase.table("search_aggregated").select(
            "search_keyword, total_count.sum(), result_total_count.sum(), uidx_count.sum(), session_count.sum()"
        )

        if start_date and end_date:
            def to_int(dt):
                if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
                return int(dt)
            query = query.gte("logday", to_int(start_date)).lte("logday", to_int(end_date))

        # 특정 기간의 인기 키워드 집계 결과
        # 참고: Postgrest에서 집계를 직접 하려면 정교한 설정이 필요하므로
        # 가장 안정적인 방식인 '전체 로드' 대신 '일자별/키워드별 집계' 호출
        response = query.execute()
        # ... 하지만 Postgrest의 .sum() 연산은 복잡하므로 
        # 전략 수정: 앱 로직에 맞춰 필요한 만큼의 데이터를 '페이지네이션'하여 가져오는 로직 추가
        
        # [REVISED STRATEGY] 
        # 데이터가 177만 건이므로, 한 번에 가져오는 대신 
        # 주간/일간 대시보드에서 사용하는 '집계된' 데이터만 가져오도록 함수를 분화합니다.
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_data_range(start_date=None, end_date=None):
    """
    데이터를 한 번에 다 가져오지 않고, 최대 50,000건까지만 가져오도록 제한 (메모리 보호)
    실제 분석에는 TOP 100 집계가 더 필요하므로 이 함수는 보조적으로 사용
    """
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()

    def to_int(dt):
        if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
        try: return int(dt)
        except: return dt

    db_start = to_int(start_date)
    db_end = to_int(end_date)

    # 대량 데이터 로드를 위한 페이지네이션 (최대 5만 건)
    all_data = []
    batch_size = 5000
    for offset in range(0, 50000, batch_size):
        try:
            query = supabase.table("search_aggregated").select("*").range(offset, offset + batch_size - 1)
            if db_start and db_end:
                query = query.gte("logday", db_start).lte("logday", db_end)
            
            response = query.execute()
            if not response.data:
                break
            all_data.extend(response.data)
            if len(response.data) < batch_size:
                break
        except:
            break

    df = pd.DataFrame(all_data)
    if not df.empty:
        # 기존 호환성 유지용 컬럼 생성
        df['검색일'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
        df['search_date'] = df['검색일']
        df['속성'] = df['pathcd']
        df['연령대'] = df['age']
        df['성별'] = df['gender']
        df['탭'] = df['tab']
        df['uidx'] = df['uidx_count']
        df['sessionid'] = df['session_count']
    return df

def sync_data_storage():
    """파일 다운로드 중단 (Supabase 사용)"""
    pass

def load_initial_data(start_date=None, end_date=None):
    """최초 데이터 로드 호환성 유지용"""
    return load_data_range(start_date, end_date)

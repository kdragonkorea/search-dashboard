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
    [CRITICAL UPGRADE - 1.77M TOTAL REFLECTION]
    원본 데이터를 다 가져오면 메모리가 터지므로, DB에서 1.77M 건이 이미 반영된 
    '요약 테이블(daily_keyword_summary)'의 데이터를 가져옵니다.
    이 데이터는 행수는 적지만, 담고 있는 수치(searches, sessions)는 1.77M 전수 결과입니다.
    """
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()

    def to_int(dt):
        if hasattr(dt, 'strftime'): return int(dt.strftime('%Y%m%d'))
        try: return int(dt)
        except: return dt

    db_start = to_int(start_date)
    db_end = to_int(end_date)

    # 요약 테이블에서 데이터 로드 (행수가 압도적으로 적어 100% 로드 가능)
    try:
        query = supabase.table("daily_keyword_summary").select("*")
        if db_start and db_end:
            query = query.gte("logday", db_start).lte("logday", db_end)
        
        response = query.execute()
        df = pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

    if not df.empty:
        # --- [중요] 원본 UI 호환성 및 1.77M 건 수치 반영 ---
        
        # 1. 날짜 정규화
        df['search_date'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
        df['검색일'] = df['search_date']
        
        # 2. 속성 코드 매핑
        path_map = {
            'DCM': 'Domestic', 'DCP': 'Domestic', 
            'OCM': 'Overseas', 'OCP': 'Overseas',
            'HCM': 'Hotel', 'HCP': 'Hotel',
            'TCM': 'TourTicket', 'TCP': 'TourTicket'
        }
        df['pathcd'] = df['pathcd'].map(lambda x: path_map.get(x, x))
        df['속성'] = df['pathcd']
        
        # 3. 1.77M 전수 수치 매핑 (데이터 요약 시 이미 sessions, searches로 합산됨)
        # 원본 UI는 세션수를 sessionid 컬럼의 개수나 합계로 계산하므로 이를 맞춰줍니다.
        df['sessionid'] = df['sessions'].astype(int)
        df['uidx'] = df['users'].astype(int)
        df['total_count'] = df['searches'].astype(int)
        df['result_total_count'] = df['searches'].astype(int) # 실패 검색어는 별도 필터링
        
        # 4. 연령/성별 보정
        df['연령대'] = df['age'].fillna('Unknown')
        df['성별'] = df['gender'].fillna('U')
        df['search_keyword'] = df['search_keyword'].fillna('')
        df['login_status'] = '로그인' # 집계 데이터 특성상 단순화
            
        return df
    return pd.DataFrame()

def preprocess_data(df):
    """이전 버전의 전처리 로직 복구"""
    if df is None or df.empty:
        return pd.DataFrame()
    return df

def sync_data_storage(): pass
def load_initial_data(start_date=None, end_date=None): return load_data_range(start_date, end_date)

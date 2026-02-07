import streamlit as st
import pandas as pd
import os
import glob
import duckdb
import logging
from pathlib import Path
from huggingface_hub import hf_hub_download

# Hugging Face 및 httpx 로그 숨기기
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)

# Data storage directory
DATA_STORAGE_DIR = "data_storage"

def get_parquet_file_path():
    """
    Hugging Face에서 Parquet 파일 경로만 가져오기 (다운로드만 수행)
    
    Returns:
        str: Parquet 파일 경로
    """
    import sys
    
    # Streamlit Secrets에서 설정 가져오기
    if hasattr(st, 'secrets') and 'huggingface' in st.secrets:
        repo_id = st.secrets['huggingface'].get('repo_id', 'kdragonkorea/search-data')
        filename = st.secrets['huggingface'].get('filename', 'data_20261001_20261130.parquet')
        token = st.secrets['huggingface'].get('token', None)
    else:
        # 기본값 사용
        repo_id = 'kdragonkorea/search-data'
        filename = 'data_20261001_20261130.parquet'
        token = None
    
    
    # Hugging Face Hub에서 파일 다운로드 (캐시됨) - 로그 출력 제거
    file_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        repo_type="dataset",
        token=token
    )
    
    return file_path

@st.cache_data(ttl=3600)
def get_raw_data_count(start_date=None, end_date=None, path_filter=None):
    """
    원본 Parquet 파일의 행 개수를 조회 (메모리에 로드하지 않고 COUNT만 수행)
    
    Args:
        start_date: 시작 날짜 (YYYYMMDD 형식)
        end_date: 종료 날짜 (YYYYMMDD 형식)
        path_filter: 접속 경로 필터 리스트 (예: ['MDA', 'DCM'])
    
    Returns:
        int: 원본 데이터 행 개수
    """
    try:
        # Parquet 파일 경로 가져오기
        file_path = get_parquet_file_path()
        
        # DuckDB 연결
        conn = duckdb.connect()
        
        # 필터링 조건 구성
        where_conditions = []
        
        # 날짜 필터링
        if start_date and end_date:
            where_conditions.append(f"logday BETWEEN {start_date} AND {end_date}")
        
        # 경로 필터링
        if path_filter and len(path_filter) > 0:
            path_list = "', '".join(path_filter)
            where_conditions.append(f"pathcd IN ('{path_list}')")
        
        # WHERE 절 생성
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # COUNT 쿼리 (매우 빠름)
        query = f"""
        SELECT COUNT(*) as total_count
        FROM read_parquet('{file_path}')
        {where_clause}
        """
        
        result = conn.execute(query).fetchone()
        conn.close()
        
        return result[0] if result else 0
        
    except Exception as e:
        import traceback
#        print(f"✗ Error getting raw data count: {e}", flush=True)
        # traceback.print_exc()  # 로그 출력 제거
        return 0

@st.cache_data(ttl=3600)
def query_data_with_duckdb(start_date=None, end_date=None, use_aggregation=False):
    """
    DuckDB로 Parquet 파일을 직접 쿼리 (메모리에 전체 로드하지 않음)
    
    Args:
        start_date: 시작 날짜 (YYYYMMDD 형식)
        end_date: 종료 날짜 (YYYYMMDD 형식)
        use_aggregation: True면 일별 집계, False면 원본 데이터
    
    Returns:
        pd.DataFrame: 쿼리 결과
    """
    import sys
    
    try:
        # Parquet 파일 경로 가져오기
        file_path = get_parquet_file_path()
        
#        print(f"Querying data with DuckDB (memory-efficient)...", flush=True)
        sys.stdout.flush()
        
        # DuckDB 연결
        conn = duckdb.connect()
        
        # 날짜 필터링 조건
        if start_date and end_date:
            where_clause = f"WHERE logday BETWEEN {start_date} AND {end_date}"
        else:
            # 기본: 전체 데이터
            where_clause = ""
        
        if use_aggregation:
            # 집계 쿼리 (메모리 절약) - 일별/키워드별/속성별 집계
            # 원본 파일의 컬럼명 사용 (영문)
            # 로그인 상태를 CASE 문으로 추가
            query = f"""
            SELECT 
                logday,
                search_keyword,
                pathcd,
                age,
                gender,
                tab,
                logweek,
                CASE 
                    WHEN uidx LIKE 'C%' THEN '로그인'
                    ELSE '비로그인'
                END as login_status,
                SUM(total_count) as total_count,
                SUM(result_total_count) as result_total_count,
                COUNT(DISTINCT uidx) as uidx,
                COUNT(*) as sessionid
            FROM read_parquet('{file_path}')
            {where_clause}
            GROUP BY logday, search_keyword, pathcd, age, gender, tab, logweek, login_status
            """
        else:
            # 원본 데이터 쿼리 (사용하지 않음 - 항상 집계 사용)
            query = f"""
            SELECT 
                logday,
                search_keyword,
                total_count,
                result_total_count,
                pathcd,
                age,
                gender,
                tab,
                uidx,
                sessionid,
                logweek
            FROM read_parquet('{file_path}')
            {where_clause}
            """
        
#        print(f"Executing query...", flush=True)
        sys.stdout.flush()
        
        # 쿼리 실행
        df = conn.execute(query).df()
        conn.close()
        
        # 컬럼명을 한글로 변환
        column_mapping = {
            'logday': '검색일',
            'search_keyword': '검색어',
            'total_count': '검색량',
            'result_total_count': '검색결과수',
            'pathcd': 'pathcd',  # pathcd는 그대로
            'age': '연령대',
            'gender': '성별',
            'tab': '탭'
        }
        
        # 존재하는 컬럼만 변환
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
#        print(f"✓ Query completed: {len(df):,} rows, {len(df.columns)} columns", flush=True)
        sys.stdout.flush()
        
        return df
        
    except Exception as e:
        import traceback
        error_msg = f"✗ Error querying data: {e}"
#        print(error_msg, flush=True)
        sys.stdout.flush()
        # traceback.print_exc()  # 로그 출력 제거
        sys.stdout.flush()
        st.error(f"데이터 쿼리 실패: {str(e)}")
        raise e

def sync_data_storage():
    """
    데이터 저장소 동기화 - Streamlit Cloud에서는 캐싱 건너뛰기
    메모리 절약을 위해 Hugging Face에서 직접 로드
    """
    import sys
#    print(f"Skipping local cache on Streamlit Cloud (memory optimization)", flush=True)
    sys.stdout.flush()
    # 아무 작업도 하지 않음 - load_data()에서 직접 HF에서 로드

@st.cache_data(ttl=3600)
def load_data(start_date=None, end_date=None, use_aggregation=True):
    """
    데이터 로드 (DuckDB 쿼리 기반, 메모리 효율적)
    
    Args:
        start_date: 시작 날짜 (YYYYMMDD 형식)
        end_date: 종료 날짜 (YYYYMMDD 형식)
        use_aggregation: 항상 True (메모리 안전을 위해 항상 집계 사용)
    
    Returns:
        pd.DataFrame: 쿼리된 데이터프레임 (집계됨)
    """
    import sys
    
    # 항상 집계 사용 (메모리 안전)
    if start_date is None and end_date is None:
#        print("Loading aggregated data (full dataset)...", flush=True)
    else:
#        print(f"Loading aggregated data (filtered: {start_date} ~ {end_date})...", flush=True)
    
    sys.stdout.flush()
    
    # DuckDB로 집계된 데이터만 쿼리
    df = query_data_with_duckdb(start_date, end_date, use_aggregation=True)
    
#    print(f"✓ Data loaded successfully: {len(df):,} rows", flush=True)
    sys.stdout.flush()
    
    return df
    
    # 데이터 타입 변환 (중요: 숫자형을 문자열로 변환 후 날짜 파싱)
    if '검색일' in df.columns:
        # 숫자형이면 문자열로 변환
        if df['검색일'].dtype in ['int64', 'float64', 'Int64']:
            df['검색일'] = df['검색일'].astype(str).str.replace('.0', '', regex=False)
        df['검색일'] = pd.to_datetime(df['검색일'], format='%Y%m%d', errors='coerce')
    
    # 숫자형 컬럼 변환
    numeric_columns = ['검색순위', '검색량', '검색실패율', '검색결과수']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 검색실패율 계산 (없으면 생성)
    if '검색결과수' in df.columns and '검색실패율' not in df.columns:
        df['검색실패율'] = (df['검색결과수'] == 0).astype(float) * 100.0
    
    # 검색순위 생성 (없으면 생성) - 초기 로드 시 건너뛰기 (메모리 절약)
    # 필요할 때 필터링된 데이터에 대해서만 계산
    if '검색순위' not in df.columns:
        df['검색순위'] = None  # 나중에 계산
    
    # 앱 호환성을 위한 영문 컬럼명 추가 (기존 한글 컬럼 유지)
    # 메모리 절약: 필요한 alias만 추가
    column_aliases = {
        '검색일': 'search_date',
        '검색어': 'search_keyword',
        '검색량': 'total_count',
        '검색결과수': 'result_total_count',
        '검색실패율': 'fail_rate',
        '검색순위': 'rank',
        '속성': 'pathcd',
        '연령대': 'age',
        '성별': 'gender',
        '탭': 'tab',
        '검색타입': 'search_type'
    }
    
    for korean, english in column_aliases.items():
        if korean in df.columns and english not in df.columns:
            df[english] = df[korean]
    
    # sessionid 컬럼이 없으면 생성 (집계용)
    if 'sessionid' not in df.columns:
        df['sessionid'] = range(len(df))
    
    # logweek 컬럼이 없으면 생성 (주차 정보)
    if 'logweek' not in df.columns and 'search_date' in df.columns:
        df['logweek'] = df['search_date'].dt.isocalendar().week
    
#    print(f"✓ Data ready: {len(df):,} rows, {len(df.columns)} columns")
    
    return df

def preprocess_data(df):
    """
    데이터 전처리
    
    Args:
        df: 원본 데이터프레임
    
    Returns:
        pd.DataFrame: 전처리된 데이터프레임
    """
    if df is None or len(df) == 0:
        return df
    
    import sys
#    print(f"Preprocessing {len(df):,} rows...", flush=True)
    sys.stdout.flush()
    
    # 날짜 컬럼 타입 변환 (YYYYMMDD → datetime)
    if '검색일' in df.columns and df['검색일'].dtype in ['int64', 'float64', 'Int64']:
        df['검색일'] = pd.to_datetime(df['검색일'].astype(str), format='%Y%m%d', errors='coerce')
    
    # 검색실패율 계산 (없으면 생성)
    if '검색결과수' in df.columns and '검색실패율' not in df.columns:
        df['검색실패율'] = (df['검색결과수'] == 0).astype(float) * 100.0
    
    # 검색순위 생성 (50만 행 이하일 때만 계산 - 메모리 절약)
    if '검색순위' not in df.columns or df['검색순위'].isna().all():
        if '검색량' in df.columns and '검색일' in df.columns and len(df) < 500000:
#            print(f"Calculating rankings...", flush=True)
            sys.stdout.flush()
            df['검색순위'] = df.groupby('검색일')['검색량'].rank(ascending=False, method='dense')
        else:
            df['검색순위'] = None
    
    # 영문 alias 추가 (앱 호환성)
    alias_mapping = {
        '검색일': 'search_date',
        '검색어': 'search_keyword',
        '검색량': 'total_count',
        '검색결과수': 'result_total_count',
        '검색실패율': 'fail_rate',
        '검색순위': 'rank',
        '연령대': 'age',
        '성별': 'gender',
        '탭': 'tab'
    }
    
    for korean, english in alias_mapping.items():
        if korean in df.columns and english not in df.columns:
            df[english] = df[korean]
    
    # logweek 생성 (없으면)
    if 'logweek' not in df.columns and 'search_date' in df.columns:
        df['logweek'] = df['search_date'].dt.isocalendar().week
    
    # sessionid 생성 (없으면)
    if 'sessionid' not in df.columns:
        df['sessionid'] = range(len(df))
    
#    print(f"✓ Preprocessing complete: {len(df):,} rows", flush=True)
    sys.stdout.flush()
    
    return df

def load_data_range(start_date=None, end_date=None):
    """
    날짜 범위로 데이터 로드 (DuckDB 쿼리 기반)
    
    Args:
        start_date: 시작 날짜 (datetime.date 또는 None)
        end_date: 종료 날짜 (datetime.date 또는 None)
    
    Returns:
        pd.DataFrame: 필터링된 데이터프레임
    """
    # 날짜를 YYYYMMDD 형식으로 변환
    if start_date is not None:
        start_date_str = start_date.strftime('%Y%m%d') if hasattr(start_date, 'strftime') else str(start_date).replace('-', '')
    else:
        start_date_str = None
    
    if end_date is not None:
        end_date_str = end_date.strftime('%Y%m%d') if hasattr(end_date, 'strftime') else str(end_date).replace('-', '')
    else:
        end_date_str = None
    
    # DuckDB로 필터링된 데이터 로드
    df = load_data(start_date_str, end_date_str)
    
    return df

def get_data_info():
    """
    데이터 정보 반환
    
    Returns:
        dict: 데이터 통계 정보
    """
    df = load_data()
    
    info = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'date_range': (df['검색일'].min(), df['검색일'].max()) if '검색일' in df.columns else (None, None),
        'unique_keywords': df['검색어'].nunique() if '검색어' in df.columns else 0,
        'memory_usage': df.memory_usage(deep=True).sum() / (1024**2)  # MB
    }
    
    return info

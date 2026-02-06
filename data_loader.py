import streamlit as st
import pandas as pd
import os
import glob
import duckdb
from pathlib import Path
from huggingface_hub import hf_hub_download

# Data storage directory
DATA_STORAGE_DIR = "data_storage"

@st.cache_data(ttl=3600)
def load_data_from_huggingface():
    """
    Hugging Face Hub에서 데이터 다운로드 및 로드
    
    Returns:
        pd.DataFrame: 로드된 데이터프레임
    """
    import sys
    try:
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
        
        print(f"Loading dataset from Hugging Face Hub...", flush=True)
        sys.stdout.flush()
        print(f"  Repository: {repo_id}", flush=True)
        sys.stdout.flush()
        print(f"  Filename: {filename}", flush=True)
        sys.stdout.flush()
        
        # Hugging Face Hub에서 파일 다운로드
        print(f"Downloading from Hugging Face...", flush=True)
        sys.stdout.flush()
        file_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="dataset",
            token=token
        )
        
        print(f"✓ Downloaded to: {file_path}", flush=True)
        sys.stdout.flush()
        
        # Parquet 파일 로드
        print(f"Reading parquet file...", flush=True)
        sys.stdout.flush()
        df = pd.read_parquet(file_path)
        print(f"✓ Successfully loaded {len(df):,} rows, {len(df.columns)} columns", flush=True)
        sys.stdout.flush()
        
        # 컬럼명 매핑 (원본 데이터 → 앱에서 사용하는 컬럼명)
        column_mapping = {
            'logday': '검색일',
            'search_keyword': '검색어',
            'total_count': '검색량',
            'result_total_count': '검색결과수',
            'pathcd': '속성',
            'age': '연령대',
            'gender': '성별',
            'tab': '탭',
            'search_type': '검색타입'
        }
        
        # 컬럼명 변경
        print(f"Applying column mapping...", flush=True)
        sys.stdout.flush()
        df = df.rename(columns=column_mapping)
        print(f"✓ Column mapping applied", flush=True)
        sys.stdout.flush()
        
        # 필요한 컬럼 선택 (매핑된 컬럼 + 추가 필요 컬럼)
        required_columns = list(column_mapping.values())
        additional_columns = ['uidx', 'sessionid', 'logweek', 'pathcd']  # 파이차트용 추가 컬럼
        
        # 존재하는 컬럼만 선택
        available_columns = [col for col in required_columns + additional_columns if col in df.columns]
        # 중복 제거
        available_columns = list(dict.fromkeys(available_columns))
        
        if available_columns:
            df = df[available_columns]
            print(f"✓ Selected {len(available_columns)} columns", flush=True)
            sys.stdout.flush()
        
        print(f"✓ load_data_from_huggingface() completed successfully", flush=True)
        sys.stdout.flush()
        return df
        
    except Exception as e:
        import sys
        import traceback
        error_msg = f"✗ Error loading from Hugging Face: {e}"
        print(error_msg, flush=True)
        sys.stdout.flush()
        traceback.print_exc()
        sys.stdout.flush()
        # Streamlit에 에러 표시
        st.error(f"데이터 로드 실패: {str(e)}")
        st.error("Hugging Face 데이터셋 접근 권한을 확인해주세요.")
        raise e  # 에러를 다시 발생시켜 Streamlit Cloud 로그에 표시

def sync_data_storage():
    """
    데이터 저장소 동기화
    - 로컬 parquet 파일이 없으면 Hugging Face에서 다운로드
    - 다운로드한 파일을 data_storage/에 캐싱
    """
    import sys
    os.makedirs(DATA_STORAGE_DIR, exist_ok=True)
    
    # Check for existing parquet files
    parquet_files = glob.glob(f"{DATA_STORAGE_DIR}/*.parquet")
    
    if parquet_files:
        print(f"Found {len(parquet_files)} existing parquet file(s) in {DATA_STORAGE_DIR}/", flush=True)
        sys.stdout.flush()
        return
    
    print(f"No parquet files found in {DATA_STORAGE_DIR}/", flush=True)
    sys.stdout.flush()
    print("Attempting to download from Hugging Face...", flush=True)
    sys.stdout.flush()
    
    try:
        # Hugging Face에서 데이터 로드
        print(f"Calling load_data_from_huggingface()...", flush=True)
        sys.stdout.flush()
        df = load_data_from_huggingface()
        print(f"✓ load_data_from_huggingface() returned successfully", flush=True)
        sys.stdout.flush()
        
        # 로컬에 캐싱
        output_file = f"{DATA_STORAGE_DIR}/data_huggingface.parquet"
        print(f"Caching to {output_file}...", flush=True)
        sys.stdout.flush()
        df.to_parquet(output_file, index=False)
        print(f"✓ Cached to {output_file}", flush=True)
        sys.stdout.flush()
        print(f"  Size: {os.path.getsize(output_file) / (1024*1024):.1f}MB", flush=True)
        sys.stdout.flush()
    except Exception as e:
        import traceback
        print(f"\n⚠ Failed to load data from Hugging Face: {e}", flush=True)
        sys.stdout.flush()
        traceback.print_exc()
        sys.stdout.flush()
        print("  Please check:", flush=True)
        print("  1. Repository ID is correct", flush=True)
        print("  2. Filename is correct", flush=True)
        print("  3. Token is valid (for private datasets)", flush=True)
        print("  4. Dataset exists and is accessible", flush=True)
        sys.stdout.flush()
        # 에러를 다시 발생시켜서 앱이 명확하게 실패하도록
        raise

@st.cache_data(ttl=3600)
def load_data():
    """
    데이터 로드 (캐싱 적용)
    
    우선순위:
    1. 로컬 data_storage/ 디렉토리의 parquet 파일
    2. Hugging Face Hub에서 직접 로드
    
    Returns:
        pd.DataFrame: 로드된 데이터프레임
    """
    # 로컬 파일 확인
    parquet_files = glob.glob(f"{DATA_STORAGE_DIR}/*.parquet")
    
    if parquet_files:
        # 로컬 파일 사용
        print(f"Loading data from {len(parquet_files)} local parquet file(s)...", flush=True)
        import sys
        sys.stdout.flush()
        
        # DuckDB로 빠르게 로드 - 메모리 절약을 위해 전체 로드
        conn = duckdb.connect()
        parquet_pattern = f"{DATA_STORAGE_DIR}/*.parquet"
        query = f"SELECT * FROM read_parquet('{parquet_pattern}')"
        df = conn.execute(query).df()
        conn.close()
        
        print(f"✓ Loaded {len(df):,} rows from local storage", flush=True)
        sys.stdout.flush()
    else:
        # Hugging Face에서 직접 로드
        print("No local files found. Loading from Hugging Face Hub...")
        df = load_data_from_huggingface()  # 에러 발생 시 여기서 raise됨
        
        # 로컬에 캐싱 (다음 실행 시 빠르게 로드)
        try:
            os.makedirs(DATA_STORAGE_DIR, exist_ok=True)
            output_file = f"{DATA_STORAGE_DIR}/data_huggingface.parquet"
            df.to_parquet(output_file, index=False)
            print(f"✓ Cached to {output_file} for faster loading next time")
        except Exception as e:
            print(f"Warning: Could not cache data locally: {e}")
    
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
    
    print(f"✓ Data ready: {len(df):,} rows, {len(df.columns)} columns")
    
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
    
    # 데이터 타입 변환
    if '검색일' in df.columns:
        # 숫자형이면 문자열로 변환 후 날짜 파싱
        if df['검색일'].dtype in ['int64', 'float64']:
            df['검색일'] = df['검색일'].astype(str).str.replace('.0', '', regex=False)
        df['검색일'] = pd.to_datetime(df['검색일'], format='%Y%m%d', errors='coerce')
    
    # 숫자형 컬럼 변환
    numeric_columns = ['검색순위', '검색량', '검색실패율', '검색결과수']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 검색실패율 계산 (검색결과수가 0이면 실패)
    if '검색결과수' in df.columns and '검색실패율' not in df.columns:
        df['검색실패율'] = (df['검색결과수'] == 0).astype(float) * 100.0
    
    # 검색순위 생성 (날짜별, 검색량 기준) - 필터링된 데이터에만 적용
    if '검색순위' not in df.columns or df['검색순위'].isna().all():
        if '검색량' in df.columns and '검색일' in df.columns and len(df) < 1000000:
            # 100만 행 이하일 때만 계산 (필터링 후)
            df['검색순위'] = df.groupby('검색일')['검색량'].rank(ascending=False, method='dense')
        else:
            df['검색순위'] = None
    
    # 결측값 처리 (컬럼이 존재하는 경우만)
    if '검색어' in df.columns:
        df = df.dropna(subset=['검색어'])
    
    # 앱 호환성을 위한 영문 컬럼명 추가 (기존 한글 컬럼 유지)
    
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
    
    print(f"✓ Preprocessing complete: {len(df):,} rows")
    
    return df

def load_data_range(start_date=None, end_date=None):
    """
    날짜 범위로 데이터 필터링
    
    Args:
        start_date: 시작 날짜 (None이면 전체)
        end_date: 종료 날짜 (None이면 전체)
    
    Returns:
        pd.DataFrame: 필터링된 데이터프레임
    """
    df = load_data()
    
    if start_date is None and end_date is None:
        return df
    
    if '검색일' not in df.columns:
        return df
    
    # 날짜 필터링
    if start_date is not None:
        df = df[df['검색일'] >= pd.to_datetime(start_date)]
    
    if end_date is not None:
        df = df[df['검색일'] <= pd.to_datetime(end_date)]
    
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

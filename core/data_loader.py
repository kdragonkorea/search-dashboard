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
        
        print(f"Loading dataset from Hugging Face Hub...")
        print(f"  Repository: {repo_id}")
        print(f"  Filename: {filename}")
        
        # Hugging Face Hub에서 파일 다운로드
        file_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="dataset",
            token=token
        )
        
        print(f"✓ Downloaded to: {file_path}")
        
        # Parquet 파일 로드
        df = pd.read_parquet(file_path)
        print(f"✓ Successfully loaded {len(df):,} rows, {len(df.columns)} columns")
        
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
        df = df.rename(columns=column_mapping)
        print(f"✓ Column mapping applied")
        
        # 필요한 컬럼만 선택 (존재하는 컬럼만)
        available_columns = [col for col in column_mapping.values() if col in df.columns]
        if available_columns:
            df = df[available_columns]
            print(f"✓ Selected {len(available_columns)} columns")
        
        return df
        
    except Exception as e:
        print(f"✗ Error loading from Hugging Face: {e}")
        import traceback
        traceback.print_exc()
        return None

def sync_data_storage():
    """
    데이터 저장소 동기화
    - 로컬 parquet 파일이 없으면 Hugging Face에서 다운로드
    - 다운로드한 파일을 data_storage/에 캐싱
    """
    os.makedirs(DATA_STORAGE_DIR, exist_ok=True)
    
    # Check for existing parquet files
    parquet_files = glob.glob(f"{DATA_STORAGE_DIR}/*.parquet")
    
    if parquet_files:
        print(f"Found {len(parquet_files)} existing parquet file(s) in {DATA_STORAGE_DIR}/")
        return
    
    print(f"No parquet files found in {DATA_STORAGE_DIR}/")
    print("Attempting to download from Hugging Face...")
    
    # Hugging Face에서 데이터 로드
    df = load_data_from_huggingface()
    
    if df is not None:
        # 로컬에 캐싱
        output_file = f"{DATA_STORAGE_DIR}/data_huggingface.parquet"
        df.to_parquet(output_file, index=False)
        print(f"✓ Cached to {output_file}")
        print(f"  Size: {os.path.getsize(output_file) / (1024*1024):.1f}MB")
    else:
        print("\n⚠ Failed to load data from Hugging Face")
        print("  Please check:")
        print("  1. Repository ID is correct")
        print("  2. Filename is correct")
        print("  3. Token is valid (for private datasets)")
        print("  4. Dataset exists and is accessible")

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
        print(f"Loading data from {len(parquet_files)} local parquet file(s)...")
        
        # DuckDB로 빠르게 로드
        conn = duckdb.connect()
        parquet_pattern = f"{DATA_STORAGE_DIR}/*.parquet"
        query = f"SELECT * FROM read_parquet('{parquet_pattern}')"
        df = conn.execute(query).df()
        conn.close()
        
        print(f"✓ Loaded {len(df):,} rows from local storage")
    else:
        # Hugging Face에서 직접 로드
        print("No local files found. Loading from Hugging Face Hub...")
        df = load_data_from_huggingface()
        
        if df is None:
            st.error("데이터를 불러올 수 없습니다. Hugging Face 설정을 확인해주세요.")
            st.stop()
        
        # 로컬에 캐싱 (다음 실행 시 빠르게 로드)
        try:
            os.makedirs(DATA_STORAGE_DIR, exist_ok=True)
            output_file = f"{DATA_STORAGE_DIR}/data_huggingface.parquet"
            df.to_parquet(output_file, index=False)
            print(f"✓ Cached to {output_file} for faster loading next time")
        except Exception as e:
            print(f"Warning: Could not cache data locally: {e}")
    
    # 데이터 타입 변환
    if '검색일' in df.columns:
        df['검색일'] = pd.to_datetime(df['검색일'])
    
    # 숫자형 컬럼 변환
    numeric_columns = ['검색순위', '검색량', '검색실패율']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
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
        df['검색일'] = pd.to_datetime(df['검색일'], format='%Y%m%d', errors='coerce')
    
    # 숫자형 컬럼 변환
    numeric_columns = ['검색순위', '검색량', '검색실패율', '검색결과수']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 검색실패율 계산 (검색결과수가 0이면 실패)
    if '검색결과수' in df.columns and '검색실패율' not in df.columns:
        df['검색실패율'] = (df['검색결과수'] == 0).astype(float) * 100.0
    
    # 검색순위 생성 (날짜별, 검색량 기준)
    if '검색순위' not in df.columns and '검색량' in df.columns and '검색일' in df.columns:
        df['검색순위'] = df.groupby('검색일')['검색량'].rank(ascending=False, method='dense')
    
    # 결측값 처리 (컬럼이 존재하는 경우만)
    if '검색어' in df.columns:
        df = df.dropna(subset=['검색어'])
    
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

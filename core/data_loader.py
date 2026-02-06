import streamlit as st
import pandas as pd
import os
import glob
import duckdb
from pathlib import Path

# Data storage directory
DATA_STORAGE_DIR = "data_storage"

def load_data_from_huggingface(dataset_name="kdragonkorea/search-trends-data", split="train"):
    """
    Hugging Face Datasets에서 데이터 로드
    
    Args:
        dataset_name: Hugging Face 데이터셋 이름 (username/dataset-name)
        split: 데이터셋 분할 (train, test, validation 등)
    
    Returns:
        pd.DataFrame: 로드된 데이터프레임
    """
    try:
        from datasets import load_dataset
        
        print(f"Loading dataset from Hugging Face: {dataset_name}")
        dataset = load_dataset(dataset_name, split=split)
        
        # Convert to pandas DataFrame
        df = dataset.to_pandas()
        print(f"✓ Successfully loaded {len(df):,} rows from Hugging Face")
        
        return df
        
    except ImportError:
        print("✗ Error: 'datasets' package not installed")
        print("  Install with: pip install datasets")
        return None
    except Exception as e:
        print(f"✗ Error loading from Hugging Face: {e}")
        return None

def sync_data_storage():
    """
    데이터 저장소 동기화
    - Hugging Face Datasets에서 데이터 로드
    - 로컬 parquet 파일로 캐싱
    """
    os.makedirs(DATA_STORAGE_DIR, exist_ok=True)
    
    # Check for existing parquet files
    parquet_files = glob.glob(f"{DATA_STORAGE_DIR}/*.parquet")
    
    if parquet_files:
        print(f"Found {len(parquet_files)} existing parquet file(s) in {DATA_STORAGE_DIR}/")
        return
    
    print(f"No parquet files found in {DATA_STORAGE_DIR}/")
    
    # Try to load Hugging Face dataset configuration from secrets
    hf_config = {}
    try:
        if hasattr(st, 'secrets') and 'huggingface' in st.secrets:
            print("Using Hugging Face config from Streamlit secrets")
            hf_config = {
                'dataset_name': st.secrets['huggingface'].get('dataset_name', 'kdragonkorea/search-trends-data'),
                'split': st.secrets['huggingface'].get('split', 'train'),
                'enabled': st.secrets['huggingface'].get('enabled', True)
            }
    except Exception as e:
        print(f"Warning: Could not load secrets ({e}). Using default config.")
        hf_config = {
            'dataset_name': 'kdragonkorea/search-trends-data',
            'split': 'train',
            'enabled': True
        }
    
    # Load from Hugging Face if enabled
    if hf_config.get('enabled', False):
        dataset_name = hf_config.get('dataset_name')
        split = hf_config.get('split', 'train')
        
        print(f"\nAttempting to load from Hugging Face...")
        print(f"  Dataset: {dataset_name}")
        print(f"  Split: {split}")
        
        df = load_data_from_huggingface(dataset_name, split)
        
        if df is not None:
            # Save to local parquet file
            output_file = f"{DATA_STORAGE_DIR}/data_huggingface.parquet"
            df.to_parquet(output_file, index=False)
            print(f"✓ Saved to {output_file}")
            print(f"  Size: {os.path.getsize(output_file) / (1024*1024):.1f}MB")
            return
    
    print("\n⚠ No data available. Please:")
    print("  1. Upload parquet files to data_storage/ directory, OR")
    print("  2. Configure Hugging Face dataset in .streamlit/secrets.toml")

@st.cache_data(ttl=3600)
def load_data():
    """
    데이터 로드 (캐싱 적용)
    
    Returns:
        pd.DataFrame: 로드된 데이터프레임
    """
    # Ensure data is synced
    sync_data_storage()
    
    # Find parquet files
    parquet_files = glob.glob(f"{DATA_STORAGE_DIR}/*.parquet")
    
    if not parquet_files:
        st.error("데이터를 불러올 수 없습니다. 데이터 파일을 확인해주세요.")
        st.stop()
    
    print(f"Loading data from {len(parquet_files)} parquet file(s)...")
    
    # Load all parquet files using DuckDB for better performance
    conn = duckdb.connect()
    
    # Create a query to read all parquet files
    parquet_pattern = f"{DATA_STORAGE_DIR}/*.parquet"
    query = f"""
        SELECT * FROM read_parquet('{parquet_pattern}')
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    print(f"✓ Loaded {len(df):,} rows, {len(df.columns)} columns")
    
    # Data type conversion
    if '검색일' in df.columns:
        df['검색일'] = pd.to_datetime(df['검색일'])
    
    # Ensure numeric columns
    numeric_columns = ['검색순위', '검색량', '검색실패율']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
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

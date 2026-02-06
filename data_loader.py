import streamlit as st
import pandas as pd
import os
import glob
import duckdb
import requests
from pathlib import Path

# Data storage directory
DATA_STORAGE_DIR = "data_storage"

# Google Drive 파일 설정 (Streamlit Secrets에서 관리)
# .streamlit/secrets.toml 파일에 설정하거나 여기에 직접 입력
GDRIVE_FILE_CONFIG = {
    "data_20261001_20261130.parquet": {
        "file_id": None,  # Google Drive 파일 ID (설정 필요)
        "enabled": False  # True로 변경하면 활성화
    }
}

def download_file_from_gdrive(file_id, output_path, file_name="data file"):
    """
    Google Drive에서 파일 다운로드
    
    Args:
        file_id: Google Drive 공유 링크의 파일 ID
        output_path: 저장할 파일 경로
        file_name: 로그 출력용 파일 이름
    
    Returns:
        bool: 다운로드 성공 여부
    """
    try:
        print(f"Downloading {file_name} from Google Drive (ID: {file_id[:10]}...)...")
        
        # 대용량 파일 처리를 위한 세션 사용
        session = requests.Session()
        
        # Method 1: Try usercontent.google.com (direct download, bypasses virus scan)
        print("Attempting direct download via usercontent.google.com...")
        usercontent_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
        
        response = session.get(usercontent_url, stream=True, allow_redirects=True)
        
        # Check if we got a valid file response
        content_type = response.headers.get('content-type', '')
        
        # If usercontent method failed, try traditional method
        if 'text/html' in content_type or response.status_code != 200:
            print("Direct download failed, trying traditional method...")
            
            # Method 2: Traditional drive.google.com with confirm token
            base_url = "https://drive.google.com/uc?export=download"
            response = session.get(base_url, params={'id': file_id}, stream=True)
            
            # Extract confirm token from HTML
            token = None
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    token = value
                    break
            
            if not token:
                content = response.content.decode('utf-8', errors='ignore')
                if 'confirm=' in content:
                    import re
                    match = re.search(r'name="confirm"\s+value="([^"]+)"', content)
                    if match:
                        token = match.group(1)
                        print(f"Found confirm token: {token[:10]}...")
            
            if token:
                print("Bypassing virus scan warning with confirm token...")
                params = {'id': file_id, 'confirm': token, 'export': 'download'}
                response = session.get(base_url, params=params, stream=True)
            
            # Final check
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                print(f"✗ Failed: Still receiving HTML. Check these:")
                print(f"   1. File must be shared as 'Anyone with the link'")
                print(f"   2. Link should end with '?usp=sharing' not '?usp=drive_link'")
                print(f"   3. File ID might be incorrect: {file_id}")
                return False
        
        # 파일 저장
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        if total_size > 0:
            print(f"Starting download... (Expected size: {total_size / (1024*1024):.1f}MB)")
        else:
            print(f"Starting download... (size unknown)")
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # 진행률 표시
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if downloaded % (block_size * 1000) == 0:  # 매 8MB마다 로그
                            print(f"Progress: {progress:.1f}% ({downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB)")
                    else:
                        # 크기를 모를 때는 다운로드된 크기만 표시
                        if downloaded % (block_size * 1000) == 0:
                            print(f"Downloaded: {downloaded / (1024*1024):.1f}MB")
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        
        # 파일 크기 검증 (너무 작으면 실패로 간주)
        if file_size < 0.1:  # 100KB 미만
            print(f"✗ Download failed: File too small ({file_size:.2f}MB)")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
        
        print(f"✓ Download complete: {file_name} ({file_size:.1f}MB)")
        return True
        
    except Exception as e:
        print(f"✗ Failed to download {file_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        # 실패 시 부분 다운로드 파일 삭제
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

def sync_data_storage():
    """
    Scan data_storage directory and handle data files.
    Priority:
    1. Use existing parquet files
    2. Download from Google Drive if configured
    3. Convert CSV files to parquet
    4. Generate sample data as fallback
    """
    if not os.path.exists(DATA_STORAGE_DIR):
        os.makedirs(DATA_STORAGE_DIR)
    
    # Check if any parquet files exist
    parquet_files = glob.glob(os.path.join(DATA_STORAGE_DIR, "*.parquet"))
    
    # If no data exists, try to download from Google Drive
    if not parquet_files:
        print("No parquet files found in data_storage/")
        
        # Try to get Google Drive config from Streamlit secrets first
        gdrive_config = GDRIVE_FILE_CONFIG.copy()
        
        # Override with Streamlit secrets if available
        try:
            if hasattr(st, 'secrets') and 'gdrive' in st.secrets:
                print("Using Google Drive config from Streamlit secrets")
                for file_name, config in st.secrets['gdrive'].items():
                    gdrive_config[file_name] = {
                        'file_id': config.get('file_id'),
                        'enabled': config.get('enabled', False)
                    }
        except Exception as e:
            print(f"Warning: Could not load secrets ({e}). Using default config.")
        
        # Try to download configured files
        downloaded_any = False
        for file_name, config in gdrive_config.items():
            if config.get('enabled') and config.get('file_id'):
                output_path = os.path.join(DATA_STORAGE_DIR, file_name)
                if download_file_from_gdrive(config['file_id'], output_path, file_name):
                    downloaded_any = True
                    print(f"✓ Successfully downloaded: {file_name}")
                else:
                    print(f"✗ Failed to download: {file_name}")
        
        # Re-check parquet files after download
        parquet_files = glob.glob(os.path.join(DATA_STORAGE_DIR, "*.parquet"))
        
        # If still no data, generate sample data
        if not parquet_files and not downloaded_any:
            print("No data downloaded. Generating sample data for demo...")
            generate_sample_data()
            return
    else:
        print(f"Found {len(parquet_files)} parquet file(s) in data_storage/")
    
    # Find all CSV files and convert to parquet
    csv_files = glob.glob(os.path.join(DATA_STORAGE_DIR, "*.csv"))
    
    for csv_file in csv_files:
        parquet_file = csv_file.replace('.csv', '.parquet')
        
        # Convert to parquet if not exists
        if not os.path.exists(parquet_file):
            try:
                print(f"Converting {csv_file} to parquet...")
                df = pd.read_csv(csv_file)
                df.to_parquet(parquet_file, index=False)
                print(f"✓ Converted {csv_file} to {parquet_file}")
            except Exception as e:
                print(f"✗ Error converting {csv_file}: {e}")

def generate_sample_data():
    """
    Generate sample data for demo purposes when no data files exist.
    Creates a parquet file in data_storage directory.
    """
    import random
    from datetime import datetime, timedelta
    
    print("Generating sample data...")
    
    # Sample data configuration
    num_days = 60  # 2 months of data
    records_per_day = 500
    
    # Sample keywords and attributes
    keywords = [
        "제주도", "부산", "서울", "강릉", "여수", "전주", "경주", "통영", "속초", "대구",
        "Tokyo", "Osaka", "Bangkok", "Danang", "Paris", "London", "New York", "Dubai"
    ]
    
    failed_keywords = ["asdf", "zzz", "nowhere", "unknown", "test123"]
    
    search_types = ["패키지", "항공", "숙박"]
    access_paths = ["메인", "검색", "이벤트", "추천"]
    
    # Generate data
    data = []
    start_date = datetime.now() - timedelta(days=num_days)
    
    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        logday = int(current_date.strftime('%Y%m%d'))
        
        for _ in range(records_per_day):
            # 10% failed searches
            is_failed = random.random() < 0.1
            
            if is_failed:
                keyword = random.choice(failed_keywords)
                result_count = 0
            else:
                keyword = random.choice(keywords)
                result_count = random.randint(1, 100)
            
            # Generate record
            record = {
                'logday': logday,
                'sessionid': f"session_{day_offset}_{_}",
                'search_keyword': keyword,
                'result_count': result_count,
                'user_age': random.choice([20, 30, 40, 50, 60]),
                'search_type': random.choice(search_types),
                'access_path': random.choice(access_paths)
            }
            
            data.append(record)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to parquet
    output_file = os.path.join(DATA_STORAGE_DIR, f"sample_data_{start_date.strftime('%Y%m%d')}_{datetime.now().strftime('%Y%m%d')}.parquet")
    df.to_parquet(output_file, index=False)
    
    print(f"Sample data created: {output_file}")
    print(f"Total records: {len(df):,}")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")

@st.cache_data(show_spinner="데이터를 조회 중입니다...")
def load_data_range(start_date=None, end_date=None):
    """
    Load data from parquet files within date range using DuckDB.
    If no dates provided, loads all data.
    """
    # Find all parquet files
    parquet_files = glob.glob(os.path.join(DATA_STORAGE_DIR, "*.parquet"))
    
    if not parquet_files:
        return pd.DataFrame()
    
    # Use DuckDB for efficient querying
    con = duckdb.connect(':memory:')
    
    # Create file pattern for DuckDB
    parquet_pattern = os.path.join(DATA_STORAGE_DIR, "*.parquet")
    
    try:
        if start_date and end_date:
            # Query with date filter (using logday column)
            query = f"""
                SELECT * FROM read_parquet('{parquet_pattern}')
                WHERE logday >= '{start_date.strftime('%Y%m%d')}' AND logday <= '{end_date.strftime('%Y%m%d')}'
            """
        else:
            # Query all data
            query = f"SELECT * FROM read_parquet('{parquet_pattern}')"
        
        df = con.execute(query).df()
        con.close()
        
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        con.close()
        return pd.DataFrame()

def preprocess_data(df):
    """
    Preprocess the loaded data:
    - Convert date columns
    - Add derived columns (search_date from logday, age groups)
    - Clean data types
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Convert logday to search_date (datetime)
    if 'logday' in df.columns:
        df['search_date'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d', errors='coerce')
    
    # logweek already exists in data, but ensure it's numeric
    if 'logweek' in df.columns:
        df['logweek'] = pd.to_numeric(df['logweek'], errors='coerce')
    
    # Age column already exists in data (e.g., '20대 이하', '30대', etc.)
    # No need to map from age_grp
    
    # Ensure string columns are proper strings
    string_cols = ['search_keyword', 'search_type', 'pathcd', 'uidx', 'sessionid']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)
    
    return df

@st.cache_data
def get_all_unique_keywords():
    """
    Get all unique keywords from the dataset.
    Used for keyword selection dropdown.
    """
    parquet_files = glob.glob(os.path.join(DATA_STORAGE_DIR, "*.parquet"))
    
    if not parquet_files:
        return []
    
    parquet_pattern = os.path.join(DATA_STORAGE_DIR, "*.parquet")
    
    try:
        con = duckdb.connect(':memory:')
        res = con.execute(f"SELECT DISTINCT search_keyword FROM read_parquet('{parquet_pattern}') ORDER BY search_keyword").fetchall()
        con.close()
        
        keywords = [row[0] for row in res if row[0]]
        return keywords
    except Exception as e:
        print(f"Error getting keywords: {e}")
        return []

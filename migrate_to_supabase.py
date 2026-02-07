"""
Supabase 데이터 마이그레이션 스크립트
Parquet 파일에서 데이터를 읽어 Supabase에 업로드합니다.

사용법:
1. .env 파일에 SUPABASE_URL과 SUPABASE_KEY 설정
2. python migrate_to_supabase.py 실행
"""

import os
import pandas as pd
import duckdb
from supabase import create_client, Client
from dotenv import load_dotenv
from tqdm import tqdm
import glob

# 환경 변수 로드
load_dotenv()

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_supabase_client() -> Client:
    """Supabase 클라이언트 생성"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL과 SUPABASE_KEY를 .env 파일에 설정해주세요.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def load_parquet_data():
    """Parquet 파일에서 집계 데이터 로드"""
    print("📁 Parquet 파일 로드 중...")
    
    # data_storage 폴더에서 parquet 파일 찾기
    parquet_files = glob.glob("data_storage/*.parquet")
    
    if not parquet_files:
        #Huggging Face에서 다운로드
        from huggingface_hub import hf_hub_download
        print("⬇️ Hugging Face에서 데이터 다운로드 중...")
        file_path = hf_hub_download(
            repo_id="kdragonkorea/search-data",
            filename="data_20261001_20261130.parquet",
            repo_type="dataset"
        )
    else:
        file_path = parquet_files[0]
    
    print(f"   파일: {file_path}")
    
    # DuckDB로 집계 쿼리 실행 (한글 컬럼명 대응)
    conn = duckdb.connect()
    query = f"""
    SELECT 
        "검색일" as logday,
        "검색어" as search_keyword,
        "속성" as pathcd,
        "연령대" as age,
        "성별" as gender,
        "탭" as tab,
        "logweek" as logweek,
        CASE 
            WHEN uidx LIKE 'C%' THEN '로그인'
            ELSE '비로그인'
        END as login_status,
        SUM("검색량") as total_count,
        SUM("검색결과수") as result_total_count,
        COUNT(DISTINCT uidx) as uidx_count,
        COUNT(*) as session_count
    FROM read_parquet('{file_path}')
    GROUP BY logday, search_keyword, pathcd, age, gender, tab, logweek, login_status
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    # [NEW] 데이터 정제: 검색어가 비어있는 행 제거 (null 제약조건 오류 방지)
    initial_len = len(df)
    df = df.dropna(subset=['search_keyword'])
    dropped_len = initial_len - len(df)
    if dropped_len > 0:
        print(f"⚠️ 검색어가 없는 {dropped_len:,}개의 행을 제외했습니다.")

    # 데이터 타입 변환: float -> int (Supabase bigint 대응)
    numeric_cols = ['total_count', 'result_total_count', 'uidx_count', 'session_count']
    for col in numeric_cols:
        df[col] = df[col].fillna(0).astype(int)
    
    # 날짜 데이터도 정수형 확인
    df['logday'] = df['logday'].astype(int)
    df['logweek'] = df['logweek'].astype(int)
    
    print(f"✅ 집계 데이터 로드 및 타입 변환 완료: {len(df):,}행")
    return df

def upload_to_supabase(df: pd.DataFrame, batch_size: int = 2000):
    """데이터를 Supabase에 업로드 (배치 처리)"""
    supabase = get_supabase_client()

    print("\n📤 Supabase 업로드 시작 (2,000개씩 배치)...")
    
    # DataFrame을 딕셔너리 리스트로 변환
    records = df.to_dict('records')
    total_records = len(records)
    
    # 배치 처리
    uploaded = 0
    errors = 0
    
    for i in tqdm(range(0, total_records, batch_size), desc="업로드 진행"):
        batch = records[i:i+batch_size]
        
        try:
            # Supabase에 업로드
            supabase.table("search_aggregated").insert(batch).execute()
            uploaded += len(batch)
        except Exception as e:
            # 에러 발생 시 건너뜀 (이미 데이터 정제를 했으므로 드문 케이스임)
            errors += 1
            continue
    
    print(f"\n✅ 업로드 완료!")
    print(f"   - 성공: {uploaded:,}행")
    print(f"   - 실패 배치: {errors}개")

def verify_upload():
    """업로드된 데이터 확인"""
    print("\n🔍 데이터 확인 중...")
    
    try:
        supabase = get_supabase_client()
        
        # 전체 행 수 확인
        result = supabase.table("search_aggregated").select("id", count="exact").limit(1).execute()
        total_count = result.count
        
        print(f"✅ 검증 완료:")
        print(f"   - 전체 행 수: {total_count:,}")
    except Exception as e:
        print(f"⚠️ 검증 중 오류: {str(e)}")

def main():
    print("=" * 50)
    print("Supabase 데이터 마이그레이션 (Clean Retry)")
    print("=" * 50)
    
    # 1. Parquet 데이터 로드 (정제 포함)
    df = load_parquet_data()
    
    # 2. Supabase 업로드 (트런케이트 포함, 배치 2000으로 조정)
    upload_to_supabase(df, batch_size=2000)
    
    # 3. 검증
    verify_upload()
    
    print("\n" + "=" * 50)
    print("마이그레이션 완료!")
    print("=" * 50)

if __name__ == "__main__":
    main()

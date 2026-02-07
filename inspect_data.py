import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def inspect_final_data_structure():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)

    print("=== [Data Inspection] ===")
    
    # 1. 원본 데이터 10건만 샘플링
    res = supabase.table("search_aggregated").select("*").limit(10).execute()
    df = pd.DataFrame(res.data)
    
    print("\n1. Raw Columns from DB:")
    print(df.columns.tolist())
    
    # 2. 전처리 후 앱에 전달될 데이터 시뮬레이션
    df['search_date'] = pd.to_datetime(df['logday'].astype(str), format='%Y%m%d')
    df['속성'] = df['pathcd']
    df['성별'] = df['gender']
    df['연령대'] = df['age']
    
    print("\n2. Rebuilt Columns for UI Compatibility:")
    print(df[['search_date', 'search_keyword', '속성', '성별', '연령대']].head(3))
    print("\n3. Data Types Check:")
    print(df.dtypes)

    # 4. 실패 검색어 추출 테스트 (가장 중요한 부분)
    failed_sample = supabase.table("search_aggregated").select("*").eq("result_total_count", 0).limit(5).execute()
    print(f"\n4. Failed Keywords Found in DB: {len(failed_sample.data)} rows")

if __name__ == "__main__":
    inspect_final_data_structure()

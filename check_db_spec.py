import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def check_data_spec():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)

    print("=== Supabase Data Specification Check ===")
    
    # 1. 전체 행 수
    res_count = supabase.table("search_aggregated").select("id", count="exact").limit(1).execute()
    total_count = res_count.count
    print(f"Total Rows: {total_count:,}")

    # 2. 날짜 범위
    res_dates = supabase.table("search_aggregated").select("logday").order("logday").limit(1).execute()
    min_date = res_dates.data[0]['logday'] if res_dates.data else "N/A"
    
    res_dates_max = supabase.table("search_aggregated").select("logday").order("logday", desc=True).limit(1).execute()
    max_date = res_dates_max.data[0]['logday'] if res_dates_max.data else "N/A"
    print(f"Date Range: {min_date} ~ {max_date}")

    # 3. 고유 키워드 수 (샘플링)
    res_keywords = supabase.rpc("get_unique_keyword_count").execute()
    # RPC가 없으면 수동 집계 (시간 걸릴 수 있음)
    if not hasattr(res_keywords, 'data'):
        print("Note: Unique keyword count check skipped (need RPC for performance)")

    # 4. 데이터 샘플 로드 테스트
    res_sample = supabase.table("search_aggregated").select("*").limit(5).execute()
    print("\nData Sample:")
    print(pd.DataFrame(res_sample.data))

if __name__ == "__main__":
    check_data_spec()

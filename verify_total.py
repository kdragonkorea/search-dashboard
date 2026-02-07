import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase = create_client(url, key)

def verify():
    # 1. 요약 테이블 전체 행 수 확인 (count="*" 사용)
    res = supabase.table('daily_keyword_summary').select('*', count='exact').limit(1).execute()
    total_rows = res.count
    
    print(f"--- DB 실시간 점검 결과 ---")
    print(f"daily_keyword_summary 테이블의 총 행수: {total_rows:,} 행")
    
    # 2. 첫 5줄 샘플 확인
    res_sample = supabase.table('daily_keyword_summary').select('*').limit(5).execute()
    print("\n--- 데이터 샘플 (첫 5줄) ---")
    for row in res_sample.data:
        print(row)

if __name__ == "__main__":
    verify()

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

try:
    supabase = create_client(url, key)
    # 간단한 쿼리 테스트 (테이블 존재 여부 및 권한 확인)
    response = supabase.table("search_aggregated").select("id").limit(1).execute()
    print("✅ Supabase 접속 및 테이블 확인 성공!")
except Exception as e:
    print(f"❌ 접속 실패: {str(e)}")
    print("\n[알림] 아래 원인 중 하나일 수 있습니다:")
    print("1. SQL Editor에서 테이블 생성 스크립트를 아직 실행하지 않음")
    print("2. API Key(sb_publishable_...)에 권한이 없음 (대시보드 anon 키 권장)")
    print(f"URL: {url}")

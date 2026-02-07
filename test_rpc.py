import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def test_rpc_calls():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)

    start_date = 20251001
    end_date = 20251130

    print("--- Testing get_daily_metrics ---")
    try:
        res = supabase.rpc("get_daily_metrics", {"p_start_date": start_date, "p_end_date": end_date}).execute()
        print(f"Daily Metrics Result Count: {len(res.data)}")
        if res.data: print(f"Sample: {res.data[0]}")
    except Exception as e:
        print(f"Error in daily: {e}")

    print("\n--- Testing get_top_keywords_agg ---")
    try:
        res = supabase.rpc("get_top_keywords_agg", {"p_start_date": start_date, "p_end_date": end_date}).execute()
        print(f"Top Keywords Result Count: {len(res.data)}")
        if res.data: print(f"Sample: {res.data[0]}")
    except Exception as e:
        print(f"Error in top keywords: {e}")

if __name__ == "__main__":
    test_rpc_calls()

"""
Hugging Face 데이터 다운로드 테스트 스크립트
"""
import pandas as pd
from huggingface_hub import hf_hub_download
import os

print("=" * 60)
print("Hugging Face 데이터 다운로드 테스트")
print("=" * 60)

# 설정
REPO_ID = "kdragonkorea/search-data"
FILENAME = "data_20261001_20261130.parquet"
# TOKEN은 .streamlit/secrets.toml에서 가져오거나 환경변수로 설정
import os
TOKEN = os.getenv("HF_TOKEN", None)  # 환경변수에서 가져오기

if not TOKEN:
    print("⚠️  Warning: HF_TOKEN not found in environment variables")
    print("   Set it with: export HF_TOKEN=your_token_here")
    print("   Or use .streamlit/secrets.toml")
    import sys
    sys.exit(1)

print(f"\n📦 다운로드 설정:")
print(f"  Repository: {REPO_ID}")
print(f"  Filename: {FILENAME}")
print(f"  Token: {TOKEN[:20]}...")

try:
    print(f"\n⏳ Hugging Face Hub에서 다운로드 중...")
    
    # 파일 다운로드
    file_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        repo_type="dataset",
        token=TOKEN
    )
    
    print(f"✓ 다운로드 완료!")
    print(f"  파일 경로: {file_path}")
    
    # 파일 크기 확인
    file_size = os.path.getsize(file_path) / (1024 * 1024)
    print(f"  파일 크기: {file_size:.2f} MB")
    
    # 데이터 로드 테스트
    print(f"\n⏳ 데이터 로딩 중...")
    df = pd.read_parquet(file_path)
    
    print(f"✓ 데이터 로드 완료!")
    print(f"\n📊 데이터 정보:")
    print(f"  총 행 수: {len(df):,}")
    print(f"  총 컬럼 수: {len(df.columns)}")
    print(f"\n📋 컬럼 목록:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    
    # 날짜 범위 확인
    if '검색일' in df.columns:
        df['검색일'] = pd.to_datetime(df['검색일'])
        print(f"\n📅 날짜 범위:")
        print(f"  시작일: {df['검색일'].min()}")
        print(f"  종료일: {df['검색일'].max()}")
    
    # 샘플 데이터 출력
    print(f"\n📄 샘플 데이터 (처음 5행):")
    print(df.head())
    
    print(f"\n" + "=" * 60)
    print("✅ 테스트 성공! Hugging Face 데이터를 정상적으로 가져왔습니다.")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    print(f"\n확인 사항:")
    print(f"  1. Repository ID가 정확한지 확인: {REPO_ID}")
    print(f"  2. 파일명이 정확한지 확인: {FILENAME}")
    print(f"  3. 토큰이 유효한지 확인")
    print(f"  4. 데이터셋이 존재하고 접근 가능한지 확인")
    print(f"     https://huggingface.co/datasets/{REPO_ID}")

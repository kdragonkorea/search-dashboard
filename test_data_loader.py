"""
data_loader 모듈 테스트 스크립트
"""
import sys
sys.path.insert(0, 'core')

import data_loader
import pandas as pd

print("=" * 60)
print("data_loader 모듈 테스트")
print("=" * 60)

try:
    print("\n1️⃣ Hugging Face에서 데이터 로드 중...")
    df_raw = data_loader.load_data_from_huggingface()
    
    if df_raw is None:
        print("❌ 데이터 로드 실패")
        sys.exit(1)
    
    print(f"✓ 원본 데이터 로드 완료: {len(df_raw):,} 행, {len(df_raw.columns)} 컬럼")
    print(f"\n📋 로드된 컬럼:")
    for i, col in enumerate(df_raw.columns, 1):
        print(f"  {i}. {col}")
    
    print(f"\n2️⃣ 데이터 전처리 중...")
    df_processed = data_loader.preprocess_data(df_raw.copy())
    
    print(f"✓ 전처리 완료: {len(df_processed):,} 행")
    
    print(f"\n📊 전처리 후 컬럼:")
    for i, col in enumerate(df_processed.columns, 1):
        dtype = df_processed[col].dtype
        print(f"  {i}. {col} ({dtype})")
    
    # 날짜 범위 확인
    if '검색일' in df_processed.columns:
        print(f"\n📅 날짜 범위:")
        print(f"  시작일: {df_processed['검색일'].min()}")
        print(f"  종료일: {df_processed['검색일'].max()}")
    
    # 검색어 통계
    if '검색어' in df_processed.columns:
        print(f"\n🔍 검색어 통계:")
        print(f"  고유 검색어 수: {df_processed['검색어'].nunique():,}")
        print(f"  총 검색 기록: {len(df_processed):,}")
    
    # 검색량 통계
    if '검색량' in df_processed.columns:
        print(f"\n📈 검색량 통계:")
        print(f"  평균: {df_processed['검색량'].mean():.2f}")
        print(f"  중앙값: {df_processed['검색량'].median():.2f}")
        print(f"  최대: {df_processed['검색량'].max():,.0f}")
    
    # 샘플 데이터
    print(f"\n📄 샘플 데이터 (처음 5행):")
    print(df_processed.head())
    
    print(f"\n3️⃣ load_data() 함수 테스트...")
    df_full = data_loader.load_data()
    print(f"✓ load_data() 완료: {len(df_full):,} 행")
    
    print(f"\n" + "=" * 60)
    print("✅ 모든 테스트 통과!")
    print("=" * 60)
    print(f"\n💡 다음 단계: Streamlit 앱 실행")
    print(f"   streamlit run app.py")
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

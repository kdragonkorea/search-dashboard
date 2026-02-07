-- Supabase 테이블 스키마 for Search Dashboard
-- 실행 순서: 1. 테이블 생성 → 2. 인덱스 생성

-- =====================================================
-- 1. 집계 데이터 테이블 (메인 테이블)
-- =====================================================
CREATE TABLE IF NOT EXISTS search_aggregated (
    id BIGSERIAL PRIMARY KEY,
    logday INTEGER NOT NULL,           -- 날짜 (YYYYMMDD 형식)
    logweek INTEGER NOT NULL,          -- 주차 (YYYYWW 형식)
    search_keyword TEXT NOT NULL,      -- 검색 키워드
    pathcd TEXT,                       -- 채널 코드 (PC, MW 등)
    age TEXT,                          -- 연령대
    gender TEXT,                       -- 성별
    tab TEXT,                          -- 탭 구분
    login_status TEXT,                 -- 로그인 상태 (로그인/비로그인)
    total_count BIGINT DEFAULT 0,      -- 검색 횟수
    result_total_count BIGINT DEFAULT 0, -- 결과 있는 검색 횟수
    uidx_count INTEGER DEFAULT 0,      -- 고유 사용자 수
    session_count INTEGER DEFAULT 0,   -- 세션 수
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 2. 인덱스 생성 (쿼리 성능 최적화)
-- =====================================================

-- 날짜 범위 검색용
CREATE INDEX IF NOT EXISTS idx_search_logday ON search_aggregated(logday);
CREATE INDEX IF NOT EXISTS idx_search_logweek ON search_aggregated(logweek);

-- 키워드 검색용
CREATE INDEX IF NOT EXISTS idx_search_keyword ON search_aggregated(search_keyword);

-- 복합 인덱스 (주간 키워드 분석용)
CREATE INDEX IF NOT EXISTS idx_search_week_keyword ON search_aggregated(logweek, search_keyword);

-- 날짜 + 키워드 복합 인덱스
CREATE INDEX IF NOT EXISTS idx_search_day_keyword ON search_aggregated(logday, search_keyword);

-- =====================================================
-- 3. Row Level Security (RLS) 설정
-- =====================================================

-- RLS 활성화
ALTER TABLE search_aggregated ENABLE ROW LEVEL SECURITY;

-- 모든 사용자에게 읽기 권한 부여 (공개 대시보드)
CREATE POLICY "Allow public read access" 
ON search_aggregated FOR SELECT 
USING (true);

-- =====================================================
-- 4. 주간 키워드 통계 뷰 (선택적)
-- =====================================================
CREATE OR REPLACE VIEW weekly_keyword_stats AS
SELECT 
    logweek,
    search_keyword,
    SUM(total_count) as total_search_count,
    SUM(result_total_count) as result_search_count,
    SUM(uidx_count) as unique_users,
    SUM(session_count) as total_sessions
FROM search_aggregated
GROUP BY logweek, search_keyword
ORDER BY logweek DESC, total_search_count DESC;

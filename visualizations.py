import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os

def plot_weekly_trend(df):
    """
    #1: Daily Traffic Comparison by Week (Grouped Bar)
    - X-axis: Day of Week (Mon-Sun)
    - Legend: Week Range (e.g., '2025/12/29 ~ 2026/01/04')
    - Color: #5E2BB8 with fading based on recency (Most recent = Full color)
    """
    if df is None or df.empty:
        return None

    # 1. Prepare Data
    if not pd.api.types.is_datetime64_any_dtype(df['search_date']):
        df['search_date'] = pd.to_datetime(df['search_date'])

    # Calculate Date Range per logweek (YY/MM/DD format - 2 digit year)
    week_ranges = df.groupby('logweek')['search_date'].agg(['min', 'max']).reset_index()
    week_ranges['Label'] = week_ranges.apply(
        lambda x: f"{x['min'].strftime('%y/%m/%d')} ~ {x['max'].strftime('%y/%m/%d')}", axis=1
    )
    week_label_map = dict(zip(week_ranges['logweek'], week_ranges['Label']))

    # Group by logweek and day of week, capture the specific date
    daily_counts = df.groupby(['logweek', df["search_date"].dt.dayofweek]).agg(
        session_count=('sessionid', 'sum'), # [UPDATED] 1.77M 건 반영을 위해 합계로 변경
        actual_date=('search_date', 'min')
    ).reset_index()
    daily_counts.columns = ['logweek', 'day_num', 'Session Count', 'actual_date']
    daily_counts['date_str'] = daily_counts['actual_date'].dt.strftime('%y/%m/%d')

    # Map Day Numbers to Korean Names
    days_ko = {0:'월', 1:'화', 2:'수', 3:'목', 4:'금', 5:'토', 6:'일'}
    daily_counts['Day'] = daily_counts['day_num'].map(days_ko)
    daily_counts['Week Label'] = daily_counts['logweek'].map(week_label_map)

    # Sort for plotting order
    daily_counts = daily_counts.sort_values(['logweek', 'day_num'])

    # 2. Define Colors based on Recency
    sorted_weeks = sorted(daily_counts['logweek'].unique())
    n_weeks = len(sorted_weeks)
    
    color_map = {}
    brand_color = "#5E2BB8" # Primary Brand Color
    base_r, base_g, base_b = 94, 43, 184
    
    for i, week in enumerate(sorted_weeks):
        # i=n-1 (Latest) -> Full Opacity (1.0), i=0 (Oldest) -> Faintest
        if n_weeks > 1:
            # Opacity ranges from 0.2 to 1.0
            opacity = 0.2 + (0.8 * (i / (n_weeks - 1)))
        else:
            opacity = 1.0
        
        label = week_label_map[week]
        color_map[label] = f"rgba({base_r}, {base_g}, {base_b}, {opacity:.2f})"

    # 3. Plot - Graph Objects로 직접 구현 (범례 위치 강제)
    fig = go.Figure()
    
    # 요일 순서
    days_order = ["월", "화", "수", "목", "금", "토", "일"]
    
    # 각 주차별로 Bar 추가 (주차 순서대로 정렬)
    sorted_week_labels = sorted(daily_counts['Week Label'].unique())
    for week_label in sorted_week_labels:
        week_data = daily_counts[daily_counts['Week Label'] == week_label]
        
        fig.add_trace(go.Bar(
            name=week_label,
            x=week_data['Day'],
            y=week_data['Session Count'],
            marker_color=color_map[week_label],
            customdata=week_data['date_str'],
            hovertemplate="date: %{customdata}<br>count: %{y:,.0f}<extra></extra>"
        ))
    
    # Layout 설정 (한 번에 모든 설정)
    fig.update_layout(
        font_family="Journey, sans-serif",
        title={
            'text': '요일별 검색량 추이',
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis={
            'title': "요일",
            'categoryorder': 'array',
            'categoryarray': days_order,
            'domain': [0, 1]  # 전체 폭 사용
        },
        yaxis={
            'title': "검색량",
            'domain': [0, 0.75]  # 상단 75%만 사용 (더 많은 범례 공간)
        },
        barmode='group',
        hovermode="closest",
        height=550,  # 높이 더 증가
        margin=dict(t=60, b=160, l=60, r=60),  # 하단 마진 160px
        showlegend=True,
        legend={
            'title': {'text': '조회 기간'},
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': -0.35,  # 더 아래로 이동
            'xanchor': 'center',
            'x': 0.5,
            'bgcolor': 'rgba(255, 255, 255, 0.9)',
            'bordercolor': 'rgba(0, 0, 0, 0.2)',
            'borderwidth': 1,
            'traceorder': 'normal'
        },
        template="plotly_white"
    )
    return fig

def calculate_popular_keywords_stats(df):
    """
    Generates the Top 20 stats table: Rank, Keyword(search_keyword), Volume, WoW Change, Rank Change.
    Focuses on the latest 2 weeks present in the data.
    """
    target_keyword_col = 'search_keyword'
    if target_keyword_col not in df.columns:
        return None

    if 'logweek' not in df.columns:
        return None
        
    weeks = sorted(df['logweek'].unique())
    if len(weeks) < 1:
        return None
        
    this_week = weeks[-1]
    prev_week = weeks[-2] if len(weeks) > 1 else None
    
    # Aggregation (합계 방식)
    weekly_stats = df.groupby(['logweek', target_keyword_col])['sessionid'].sum().reset_index()
    weekly_stats.columns = ['logweek', 'keyword', 'count']
    
    # Current Week Stats
    current_data = weekly_stats[weekly_stats['logweek'] == this_week].copy()
    # Rank: Descending count (High count = Rank 1), Tie-break: Alphabetical (Unique Rank)
    current_data = current_data.sort_values(by=['count', 'keyword'], ascending=[False, True])
    current_data['rank'] = range(1, len(current_data) + 1)
    
    # Previous Week Stats
    if prev_week is not None:
        prev_data = weekly_stats[weekly_stats['logweek'] == prev_week].copy()
        # Rank: Descending count, Tie-break: Alphabetical
        prev_data = prev_data.sort_values(by=['count', 'keyword'], ascending=[False, True])
        prev_data['prev_rank'] = range(1, len(prev_data) + 1)
        prev_data = prev_data[['keyword', 'count', 'prev_rank']]
        prev_data.columns = ['keyword', 'prev_count', 'prev_rank']
        
        # Merge
        merged = pd.merge(current_data, prev_data, on='keyword', how='left')
        merged['prev_count'] = merged['prev_count'].fillna(0)
        
        # Calculate Changes
        merged['count_change'] = merged['count'] - merged['prev_count']
        
        # Rank Change: Prev - Curr (Positive = Improved/Up)
        # Mark as "NEW" if not in previous Top 100
        merged['rank_change_val'] = merged.apply(
            lambda row: 0 if pd.isna(row['prev_rank']) or row['prev_rank'] > 100 else row['prev_rank'] - row['rank'],
            axis=1
        )
        merged['rank_change_display'] = merged.apply(
            lambda row: 'NEW' if pd.isna(row['prev_rank']) or row['prev_rank'] > 100 else row['prev_rank'] - row['rank'],
            axis=1
        )
    else:
        merged = current_data
        merged['count_change'] = 0
        merged['rank_change_val'] = 0
        merged['rank_change_display'] = 0
        
    # Filter Top 100 by Current Rank (Expanded from 20)
    top_20 = merged.sort_values('rank').head(100)
    
    # Select and Rename Columns for App
    # Return: rank, keyword, count, count_change, rank_change_val, rank_change_display
    return top_20[['rank', 'keyword', 'count', 'count_change', 'rank_change_val', 'rank_change_display']]

def plot_keyword_group_trend(df, keywords, title="Keyword Trend"):
    """
    Plots a grouped bar chart for specific keywords over the last 8 weeks.
    Keyword Source: search_keyword
    """
    target_keyword_col = 'search_keyword'
    
    # Filter data for keywords
    all_weeks = sorted(df['logweek'].unique())
    recent_weeks = all_weeks[-8:]
    
    mask = (df[target_keyword_col].isin(keywords)) & (df['logweek'].isin(recent_weeks))
    trend_data = df[mask].groupby(['logweek', target_keyword_col])['sessionid'].sum().reset_index()
    trend_data.columns = ['Week', 'Keyword', 'Count']
    
    # Add Date Range Labels for Weeks (YY/MM/DD format - 2 digit year)
    if pd.api.types.is_datetime64_any_dtype(df['search_date']):
        week_ranges = df.groupby('logweek')['search_date'].agg(['min', 'max']).reset_index()
        week_ranges['Label'] = week_ranges.apply(
            lambda x: f"{x['min'].strftime('%y/%m/%d')}~{x['max'].strftime('%y/%m/%d')}", axis=1
        )
        label_map = dict(zip(week_ranges['logweek'], week_ranges['Label']))
        trend_data['Week Label'] = trend_data['Week'].map(label_map)
    else:
        trend_data['Week Label'] = trend_data['Week'].astype(str)
        
    # Sort Weeks properly
    trend_data = trend_data.sort_values(['Week', 'Keyword'])
    
    # [NEW] Determine Keyword Order based on the latest week's count (Descending)
    latest_week = trend_data['Week'].max()
    latest_week_data = trend_data[trend_data['Week'] == latest_week]
    
    # Sort keywords by count descending. If keywords are missing in the latest week, they go to the end.
    ordered_keywords = latest_week_data.sort_values('Count', ascending=False)['Keyword'].tolist()
    # Add any keywords that might not have existed in the latest week but are in the requested list
    for kw in keywords:
        if kw not in ordered_keywords:
            ordered_keywords.append(kw)

    # Define Colors based on Recency
    week_map_df = trend_data[['Week', 'Week Label']].drop_duplicates().sort_values('Week')
    sorted_labels = week_map_df['Week Label'].tolist()
    
    n_weeks = len(sorted_labels)
    color_map = {}
    base_r, base_g, base_b = 94, 43, 184 # #5E2BB8
    
    for i, label in enumerate(sorted_labels):
        if n_weeks > 1:
            opacity = 0.3 + (0.7 * (i / (n_weeks - 1)))
        else:
            opacity = 1.0
        color_map[label] = f"rgba({base_r}, {base_g}, {base_b}, {opacity:.2f})"

    # Plot
    fig = px.bar(
        trend_data, 
        x='Keyword', 
        y='Count', 
        color='Week Label', 
        barmode='group',
        custom_data=['Week Label'], # Added for hover template
        category_orders={
            "Week Label": sorted_labels,
            "Keyword": ordered_keywords # Apply calculated order
        },
        color_discrete_map=color_map,
        template="plotly_white"
    )
    
    # Layout 설정 (범례 오른쪽 배치)
    fig.update_layout(
        font_family="Journey, sans-serif",
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'weight': 700}
        },
        xaxis={
            'title': {'text': "검색어", 'font': {'size': 14}},
            'tickfont': {'size': 12}
        },
        yaxis={
            'title': {'text': "검색량", 'font': {'size': 14}},
            'tickfont': {'size': 12}
        },
        legend={
            'title': {
                'text': '조회 기간', 
                'font': {'size': 13, 'weight': 600},
                'side': 'top'  # 제목을 상단에 배치
            },
            'orientation': 'v',  # 세로 방향
            'yanchor': 'middle',
            'y': 0.5,
            'xanchor': 'left',
            'x': 1.02,  # 차트 오른쪽 밖
            'font': {'size': 12},
            'itemsizing': 'constant',
            'tracegroupgap': 8,
            'bgcolor': 'rgba(255, 255, 255, 0.8)'  # 반투명 배경만 유지
        },
        hovermode="closest",
        height=420,
        margin=dict(t=70, b=80, l=60, r=180)  # 오른쪽 마진 180px, 하단 마진 증가
    )
    
    # Update hover template to show date and count
    fig.update_traces(
        hovertemplate="date: %{customdata[0]}<br>count: %{y:,.0f}<extra></extra>"
    )
    
    return fig

def plot_keywords_by_attribute(df, attribute='search_type'):
    """
    #3: Popular search terms by attribute
    attribute: column name to group by (e.g., 'search_type', 'pathCd', 'tab')
    """
    if attribute in df.columns:
        attr_counts = df[attribute].value_counts().reset_index()
        attr_counts.columns = ['Attribute', 'Count']
        
        # Translate attribute name for title if possible, or just keep english var
        fig = px.pie(attr_counts, values='Count', names='Attribute', title=f'{attribute}별 검색 분포')
        return fig
    else:
        st.warning(f"컬럼 '{attribute}'을(를) 찾을 수 없습니다.")
        return None

def plot_path_distribution(df):
    """
    pathcd (MDA, DCM, DCP) -> (앱, 모바일웹, PC) 변환 후 비율 시각화
    """
    # 컬럼명이 전처리 과정에서 소문자로 변경되었으므로 'pathcd' 사용
    target_col = 'pathcd' if 'pathcd' in df.columns else 'pathCd'
    
    if df is None or target_col not in df.columns:
        return None
        
    temp_df = df.copy()
    # Mappings
    path_map = {'MDA': '앱', 'DCM': '모바일웹', 'DCP': 'PC'}
    temp_df['Path_Label'] = temp_df[target_col].map(path_map)
    
    # Filter and count
    path_counts = temp_df.dropna(subset=['Path_Label'])['Path_Label'].value_counts().reset_index()
    path_counts.columns = ['Path', 'Count']
    
    fig = px.pie(
        path_counts, values='Count', names='Path',
        color_discrete_sequence=["#5E2BB8", "#8A63D2", "#B59CE6"],
        hole=0.4,
        template="plotly_white"
    )
    
    fig.update_layout(
        font_family="Journey, sans-serif",
        title_text="채널 비중",
        title_x=0.5,
        title_xanchor="center",
        margin=dict(t=50, b=20, l=10, r=10),
        height=320,
        showlegend=False,
        autosize=True
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def plot_login_status_distribution(df):
    """
    uidx 기반 로그인/비로그인 비중 시각화
    로그인(Light: #B59CE6), 비로그인(Dark: #5E2BB8)
    """
    if df is None or 'uidx' not in df.columns:
        return None
        
    temp_df = df.copy()
    status_counts = temp_df.groupby('login_status')['sessionid'].sum().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    # Sort to ensure '비로그인' is first (Dark Purple) and '로그인' is second (Light Purple)
    status_counts = status_counts.sort_values('Status', ascending=False) # '비로그인' > '로그인'
    
    fig = px.pie(
        status_counts, values='Count', names='Status',
        color_discrete_sequence=["#5E2BB8", "#B59CE6"],
        template="plotly_white"
    )
    
    fig.update_layout(
        font_family="Journey, sans-serif",
        title_text="로그인 비중",
        title_x=0.5,
        title_xanchor="center",
        margin=dict(t=50, b=20, l=10, r=10),
        height=320,
        showlegend=False,
        autosize=True
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def plot_gender_distribution(df):
    """
    성별(gender) 비중 시각화 (F: 여성, M: 남성)
    로그인 여부 비중과 동일한 컬러 체계 적용 (Dark/Light)
    """
    if df is None or 'gender' not in df.columns:
        return None
        
    temp_df = df.copy()
    gender_counts = temp_df.groupby('성별')['sessionid'].sum().reset_index()
    gender_counts.columns = ['Gender', 'Count']
    
    # 로그인 여부 비중과 동일한 색상 (#5E2BB8, #B59CE6) 적용
    fig = px.pie(
        gender_counts, values='Count', names='Gender',
        color_discrete_sequence=["#5E2BB8", "#B59CE6"],
        hole=0.4,
        template="plotly_white"
    )
    
    fig.update_layout(
        font_family="Journey, sans-serif",
        title_text="성별 비중",
        title_x=0.5,
        title_xanchor="center",
        margin=dict(t=50, b=20, l=10, r=10),
        height=320,
        showlegend=False,
        autosize=True
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def plot_age_distribution(df):
    """
    연령대(age) 비중 시각화
    - '미분류' 제외
    - 20대 이하: #B59CE6 (로그인 컬러와 통일)
    """
    if df is None or 'age' not in df.columns:
        return None
        
    temp_df = df[df['연령대'] != '미분류'].copy()
    age_counts = temp_df.groupby('연령대')['sessionid'].sum().reset_index()
    age_counts.columns = ['Age', 'Count']
    
    # Sort order
    age_order = ["20대 이하", "30대", "40대", "50대 이상"]
    age_counts['Age'] = pd.Categorical(age_counts['Age'], categories=age_order, ordered=True)
    age_counts = age_counts.sort_values('Age')
    
    purple_palette = ["#B59CE6", "#8A63D2", "#7445C7", "#5E2BB8"]
    
    fig = px.pie(
        age_counts, values='Count', names='Age',
        color_discrete_sequence=purple_palette,
        hole=0.4,
        template="plotly_white"
    )
    
    fig.update_layout(
        font_family="Journey, sans-serif",
        title_text="연령 비중",
        title_x=0.5,
        title_xanchor="center",
        margin=dict(t=50, b=20, l=10, r=10),
        height=320,
        showlegend=False,
        autosize=True
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig


def plot_keywords_by_age(df):
    """
    #4: Popular search terms by user age
    """
    # DATA MISSING in real file
    # Display placeholder msg
    st.info("현재 데이터셋에 연령 데이터가 없습니다 (사용자 테이블 매핑 필요).")
    return None

def preprocess_failed_keyword_data(df):
    """
    Apply IP exclusion and Regex filters as requested by user.
    """
    temp_df = df.copy()
    
    # IP Exclusion
    if 'userip' in temp_df.columns:
        blocked_ips = [
            '112.223.61.10','112.223.61.11','112.223.61.12','112.223.61.13','112.223.61.14',
            '112.223.61.16','112.223.61.17','112.223.61.18','112.223.61.39','112.223.61.40',
            '112.220.71.243','112.220.71.244'
        ]
        temp_df['userip'] = temp_df['userip'].astype(str).str.strip()
        temp_df = temp_df[~temp_df['userip'].isin(blocked_ips)]
        
    # Regex Filters on search_keyword
    if 'search_keyword' not in temp_df.columns:
        return temp_df
        
    temp_df = temp_df[temp_df['search_keyword'].notna()]
    temp_df['search_keyword'] = temp_df['search_keyword'].astype(str)
    
    kw = temp_df['search_keyword']
    
    # 1. Special Characters (Only allow Alphanumeric + Korean + Whitespace)
    mask_special = ~kw.str.contains(r'[^ㄱ-ㅎㅏ-ㅣ가-힣a-zA-Z0-9\s]', regex=True)
    
    # 2. H Code (H + 11 alnum)
    mask_h_code = ~kw.str.match(r'^[Hh][a-zA-Z0-9]{11}$')
    
    # 3. Numeric Only
    mask_numeric = ~kw.str.match(r'^[0-9]+$')
    
    # 4. Product Code (Alpha + 13+ alnum)
    mask_prod_code = ~kw.str.match(r'^[A-Za-z][A-Za-z0-9]{13,}$')
    
    # 5. DB/디비
    mask_db = ~kw.str.contains(r'[Dd][Bb]|디비', regex=True)
    
    # 6. Alpha3+Num (Space separated)
    # Updated regex to handle "Start or Space" correctly using python regex syntax
    mask_alpha_num = ~kw.str.contains(r'(?:^|\s)[A-Za-z]{3}[0-9]+(?:\s|$)', regex=True)
    
    # 7. Spam
    mask_spam = ~kw.str.contains(r'텔레|출장|마사지', regex=True)
    
    # 8. Kanji Only
    mask_kanji = ~kw.str.match(r'^[\u4E00-\u9FFF]+$')
    
    # 9. Alpha3+Num6+
    mask_complex = ~kw.str.contains(r'[A-Za-z]{3}[0-9]{6,}', regex=True)
    
    # 10. Empty
    mask_empty = kw != ''
    
    final_mask = (
        mask_special & mask_h_code & mask_numeric & mask_prod_code & 
        mask_db & mask_alpha_num & mask_spam & mask_kanji & 
        mask_complex & mask_empty
    )
    
    return temp_df[final_mask]

def get_failed_keywords(df):
    """
    #5: Weekly failed search terms with advanced filtering (Strict User Request)
    Conditions:
    - total_count = 0
    - result_total_count = 0
    - search_type = 'all'
    - quick_link_yn = 'N'
    - userip excluded
    - regex filters (kept for data quality)
    - distinct sessionid count
    """
    # 0. Copy to avoid SettingWithCopyWarning
    temp_df = df.copy()
    
    # 1. Normalize Column Names (Handle camelCase vs snake_case)
    col_map = {
        'totalCount': 'total_count',
        'resultTotalCount': 'result_total_count',
        'searchType': 'search_type',
        'quickLinkYn': 'quick_link_yn',
        'userIp': 'userip',
        'userId': 'sessionid', # Assuming matches
        'pathCd': 'pathCd' # Keep original case if needed
    }
    # Only rename columns that exist
    rename_dict = {k: v for k, v in col_map.items() if k in temp_df.columns}
    temp_df = temp_df.rename(columns=rename_dict)
    
    # Check for required columns for aggregation
    required_agg_cols = ['search_keyword']
    if not all(col in temp_df.columns for col in required_agg_cols):
        return pd.DataFrame()

    # 2. Base Filters
    # pathcd/pathCd IN ('DCM', 'MDA', 'DCP')
    path_col = 'pathcd' if 'pathcd' in temp_df.columns else ('pathCd' if 'pathCd' in temp_df.columns else None)
    if path_col:
        temp_df = temp_df[temp_df[path_col].astype(str).str.upper().isin(['DCM', 'MDA', 'DCP'])]
        
    # service = 'totalsearch'
    if 'service' in temp_df.columns:
        temp_df = temp_df[temp_df['service'].astype(str).str.lower() == 'totalsearch']
        
    # page = 1
    if 'page' in temp_df.columns:
        temp_df['page'] = pd.to_numeric(temp_df['page'], errors='coerce')
        temp_df = temp_df[temp_df['page'] == 1]
        
    # total_count == 0
    if 'total_count' in temp_df.columns:
         temp_df['total_count'] = pd.to_numeric(temp_df['total_count'], errors='coerce').fillna(-1)
         temp_df = temp_df[temp_df['total_count'] == 0]
    
    # result_total_count == 0
    if 'result_total_count' in temp_df.columns:
        temp_df['result_total_count'] = pd.to_numeric(temp_df['result_total_count'], errors='coerce').fillna(-1)
        temp_df = temp_df[temp_df['result_total_count'] == 0]
        
    # search_type == 'all'
    if 'search_type' in temp_df.columns:
        temp_df = temp_df[temp_df['search_type'].astype(str).str.lower() == 'all']
        
    # quick_link_yn != 'Y' (Treat NaN/Empty as 'N')
    if 'quick_link_yn' in temp_df.columns:
        temp_df = temp_df[temp_df['quick_link_yn'].fillna('N').astype(str).str.upper() != 'Y']

    # 3. Apply Preprocessing (IPs + Regex)
    temp_df = preprocess_failed_keyword_data(temp_df)
    
    # 5. Aggregation & Ranking
    # Logic: Count distinct (logweek, sessionid) pairs per keyword (User Request)
    if 'logweek' in temp_df.columns and 'sessionid' in temp_df.columns:
        # One failure count per session per week per keyword
        # (e.g., Session A fails on "Test" in W1 and W2 -> Count 2)
        unique_failures = temp_df.drop_duplicates(subset=['logweek', 'sessionid', 'search_keyword'])
        results = unique_failures.groupby('search_keyword').size().reset_index(name='cnt')
    elif 'sessionid' in temp_df.columns:
        # Fallback to global unique session if logweek missing
        results = temp_df.groupby('search_keyword')['sessionid'].nunique().reset_index()
        results.columns = ['search_keyword', 'cnt']
    else:
        # Fallback to raw count
        results = temp_df['search_keyword'].value_counts().reset_index()
        results.columns = ['search_keyword', 'cnt']
    
    # Sort by Count DESC, Keyword ASC
    results = results.sort_values(by=['cnt', 'search_keyword'], ascending=[False, True])
    
    # Add Rank
    results['rn'] = range(1, len(results) + 1)
    
    # 6. Limit 120
    results = results.head(120)
    
    # Rename for UI
    results = results[['rn', 'search_keyword', 'cnt']]
    results.columns = ['순위', '검색어', '실패 횟수']
    
    return results

def plot_failed_keywords_wordcloud(df):
    """
    Generates an interactive word cloud from failed keywords using Plotly.
    """
    failed_counts_df = get_failed_keywords(df)
    
    if failed_counts_df.empty:
        return None
        
    # Convert to dict for wordcloud {keyword: count}
    word_freq = dict(zip(failed_counts_df['검색어'], failed_counts_df['실패 횟수']))
    
    if not word_freq:
        return None
        
    # Generate WordCloud logic
    # Use custom font if available for Korean support
    use_default_font = False
    
    try:
        # Use absolute path relative to this file's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_file = os.path.join(current_dir, 'assets', 'JOURNEYITSELF-REGULAR 3.TTF')
        
        # Fallback to project root if not found
        if not os.path.exists(font_file):
            font_file = os.path.join(os.path.dirname(current_dir), 'assets', 'JOURNEYITSELF-REGULAR 3.TTF')

        wc = WordCloud(
            font_path=font_file if os.path.exists(font_file) else None,
            width=600, 
            height=1000,
            background_color='white',
            colormap='Purples', # Premium purple theme
            relative_scaling=0.4, # Balanced size difference
            min_font_size=20,
            max_font_size=100,
            prefer_horizontal=1.0,
            margin=5,
            random_state=42
        ).generate_from_frequencies(word_freq)
    except Exception as e:
        use_default_font = True
        
    if use_default_font:
        wc = WordCloud(
            font_path=None, 
            width=1000, 
            height=600, 
            background_color='white',
            colormap='Purples',
            relative_scaling=0.4,
            min_font_size=10,
            max_font_size=120,
            prefer_horizontal=1.0,
            margin=5,
            random_state=42
        ).generate_from_frequencies(word_freq)
    
    # Create Matplotlib Figure for high-quality rendering
    fig, ax = plt.subplots(figsize=(10, 15)) # Adjusted for user's width:600 height:1000 preference
    
    # Use bilinear interpolation for smoother edges as requested
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    plt.tight_layout(pad=0)
    
    return fig

def get_filtered_failed_keywords_df(df):
    """
    실패 검색어 필터링을 적용한 데이터프레임 반환
    (차트용으로 사용)
    """
    temp_df = df.copy()
    
    # 1. Normalize Column Names
    col_map = {
        'totalCount': 'total_count',
        'resultTotalCount': 'result_total_count',
        'searchType': 'search_type',
        'quickLinkYn': 'quick_link_yn',
        'userIp': 'userip',
        'userId': 'sessionid',
        'pathCd': 'pathCd'
    }
    rename_dict = {k: v for k, v in col_map.items() if k in temp_df.columns}
    temp_df = temp_df.rename(columns=rename_dict)
    
    # Check required
    if 'search_keyword' not in temp_df.columns:
        return pd.DataFrame()

    # 2. Base Filters
    # pathcd/pathCd IN ('DCM', 'MDA', 'DCP')
    path_col = 'pathcd' if 'pathcd' in temp_df.columns else ('pathCd' if 'pathCd' in temp_df.columns else None)
    if path_col:
        temp_df = temp_df[temp_df[path_col].astype(str).str.upper().isin(['DCM', 'MDA', 'DCP'])]
        
    # service = 'totalsearch'
    if 'service' in temp_df.columns:
        temp_df = temp_df[temp_df['service'].astype(str).str.lower() == 'totalsearch']
        
    # page = 1
    if 'page' in temp_df.columns:
        temp_df['page'] = pd.to_numeric(temp_df['page'], errors='coerce')
        temp_df = temp_df[temp_df['page'] == 1]
        
    # total_count == 0
    if 'total_count' in temp_df.columns:
         temp_df['total_count'] = pd.to_numeric(temp_df['total_count'], errors='coerce').fillna(-1)
         temp_df = temp_df[temp_df['total_count'] == 0]
    
    # result_total_count == 0
    if 'result_total_count' in temp_df.columns:
        temp_df['result_total_count'] = pd.to_numeric(temp_df['result_total_count'], errors='coerce').fillna(-1)
        temp_df = temp_df[temp_df['result_total_count'] == 0]
        
    # search_type == 'all'
    if 'search_type' in temp_df.columns:
        temp_df = temp_df[temp_df['search_type'].astype(str).str.lower() == 'all']
        
    # quick_link_yn != 'Y' (Treat NaN/Empty as 'N')
    if 'quick_link_yn' in temp_df.columns:
        temp_df = temp_df[temp_df['quick_link_yn'].fillna('N').astype(str).str.upper() != 'Y']

    # 3. Apply Preprocessing (IPs + Regex)
    temp_df = preprocess_failed_keyword_data(temp_df)
    
    return temp_df

def calculate_failed_keywords_stats(df):
    """
    Generates Failed Keywords Ranking with WoW comparison.
    Columns: Rank, Keyword, Count, Count Change, Rank Change
    """
    # 0. Copy and Preprocess (Apply all filters to the full range)
    temp_df = df.copy()
    
    # 1. Normalize Column Names
    col_map = {
        'totalCount': 'total_count',
        'resultTotalCount': 'result_total_count',
        'searchType': 'search_type',
        'quickLinkYn': 'quick_link_yn',
        'userIp': 'userip',
        'userId': 'sessionid',
        'pathCd': 'pathCd'
    }
    rename_dict = {k: v for k, v in col_map.items() if k in temp_df.columns}
    temp_df = temp_df.rename(columns=rename_dict)
    
    # Check required
    if 'search_keyword' not in temp_df.columns:
        return pd.DataFrame()

    # 2. Base Filters
    # pathcd/pathCd IN ('DCM', 'MDA', 'DCP')
    path_col = 'pathcd' if 'pathcd' in temp_df.columns else ('pathCd' if 'pathCd' in temp_df.columns else None)
    if path_col:
        temp_df = temp_df[temp_df[path_col].astype(str).str.upper().isin(['DCM', 'MDA', 'DCP'])]
        
    # service = 'totalsearch'
    if 'service' in temp_df.columns:
        temp_df = temp_df[temp_df['service'].astype(str).str.lower() == 'totalsearch']
        
    # page = 1
    if 'page' in temp_df.columns:
        temp_df['page'] = pd.to_numeric(temp_df['page'], errors='coerce')
        temp_df = temp_df[temp_df['page'] == 1]
        
    # total_count == 0
    if 'total_count' in temp_df.columns:
         temp_df['total_count'] = pd.to_numeric(temp_df['total_count'], errors='coerce').fillna(-1)
         temp_df = temp_df[temp_df['total_count'] == 0]
    
    # result_total_count == 0
    if 'result_total_count' in temp_df.columns:
        temp_df['result_total_count'] = pd.to_numeric(temp_df['result_total_count'], errors='coerce').fillna(-1)
        temp_df = temp_df[temp_df['result_total_count'] == 0]
        
    # search_type == 'all'
    if 'search_type' in temp_df.columns:
        temp_df = temp_df[temp_df['search_type'].astype(str).str.lower() == 'all']
        
    # quick_link_yn != 'Y' (Treat NaN/Empty as 'N')
    if 'quick_link_yn' in temp_df.columns:
        temp_df = temp_df[temp_df['quick_link_yn'].fillna('N').astype(str).str.upper() != 'Y']

    # 3. Apply Preprocessing (IPs + Regex)
    temp_df = preprocess_failed_keyword_data(temp_df)
    
    # 4. Identify Weeks
    if 'logweek' not in temp_df.columns:
        return pd.DataFrame()
        
    weeks = sorted(temp_df['logweek'].unique())
    if len(weeks) < 1:
        return pd.DataFrame()
        
    this_week = weeks[-1]
    prev_week = weeks[-2] if len(weeks) > 1 else None
    
    # 5. Define Aggregation Logic (Internal function to reuse)
    def aggregate_week_data(week_df):
        if week_df.empty:
            return pd.DataFrame(columns=['search_keyword', 'cnt'])
            
        if 'logweek' in week_df.columns and 'sessionid' in week_df.columns:
             unique_failures = week_df.drop_duplicates(subset=['logweek', 'sessionid', 'search_keyword'])
             res = unique_failures.groupby('search_keyword').size().reset_index(name='cnt')
        elif 'sessionid' in week_df.columns:
             res = week_df.groupby('search_keyword')['sessionid'].nunique().reset_index()
             res.columns = ['search_keyword', 'cnt']
        else:
             res = week_df['search_keyword'].value_counts().reset_index()
             res.columns = ['search_keyword', 'cnt']
        return res

    # 6. Current Week Stats
    current_data = aggregate_week_data(temp_df[temp_df['logweek'] == this_week])
    # Rank
    current_data = current_data.sort_values(by=['cnt', 'search_keyword'], ascending=[False, True])
    current_data['rank'] = range(1, len(current_data) + 1)
    
    # 7. Previous Week Stats
    if prev_week is not None:
        prev_data = aggregate_week_data(temp_df[temp_df['logweek'] == prev_week])
        prev_data = prev_data.sort_values(by=['cnt', 'search_keyword'], ascending=[False, True])
        prev_data['prev_rank'] = range(1, len(prev_data) + 1)
        
        prev_data = prev_data[['search_keyword', 'cnt', 'prev_rank']]
        prev_data.columns = ['search_keyword', 'prev_count', 'prev_rank']
        
        # Merge
        merged = pd.merge(current_data, prev_data, on='search_keyword', how='left')
        merged['prev_count'] = merged['prev_count'].fillna(0)
        
        # Calculate Changes
        merged['count_change'] = merged['cnt'] - merged['prev_count']
        
        # Rank Change: Prev - Curr (Positive = Improved/Up)
        # Mark as "NEW" if not in previous Top 100
        merged['rank_change_val'] = merged.apply(
            lambda row: 0 if pd.isna(row['prev_rank']) or row['prev_rank'] > 100 else row['prev_rank'] - row['rank'],
            axis=1
        )
        merged['rank_change_display'] = merged.apply(
            lambda row: 'NEW' if pd.isna(row['prev_rank']) or row['prev_rank'] > 100 else row['prev_rank'] - row['rank'],
            axis=1
        )
    else:
        merged = current_data
        merged['count_change'] = 0
        merged['rank_change_val'] = 0
        merged['rank_change_display'] = 0
        
    # 8. Limit 100 and Formatting
    top_120 = merged.head(100).copy()
    
    # Rename columns for internal consistency (will be renamed to Korean in app.py)
    # Output: rank, search_keyword, cnt, count_change, rank_change_val, rank_change_display
    return top_120[['rank', 'search_keyword', 'cnt', 'count_change', 'rank_change_val', 'rank_change_display']]

def plot_daily_line_trend(df):
    """
    일자별 검색량 추이 - 선형 차트
    선택된 키워드에 따라 일자별 검색량을 선형 그래프로 표시
    """
    if df is None or df.empty:
        return None

    # 날짜 변환
    if not pd.api.types.is_datetime64_any_dtype(df['search_date']):
        df['search_date'] = pd.to_datetime(df['search_date'])

    # 일자별 집계
    daily_counts = df.groupby('search_date')['sessionid'].count().reset_index()
    daily_counts.columns = ['Date', 'Count']
    daily_counts = daily_counts.sort_values('Date')

    # 선형 차트 생성
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_counts['Date'],
        y=daily_counts['Count'],
        mode='lines+markers',
        name='검색량',
        line=dict(color='#5E2BB8', width=3, shape='spline'),  # 곡선으로 변경
        marker=dict(size=8, color='#5E2BB8'),
        hovertemplate='날짜: %{x|%Y/%m/%d}<br>검색량: %{y:,.0f}<extra></extra>'
    ))

    fig.update_layout(
        font_family="Journey, sans-serif",
        title='일자별 검색량 추이',
        title_x=0.5,
        title_xanchor='center',
        xaxis_title="날짜",
        yaxis_title="검색량",
        yaxis=dict(rangemode='tozero'),  # Y축 0부터 시작
        template="plotly_white",
        hovermode="closest",
        showlegend=False
    )

    return fig

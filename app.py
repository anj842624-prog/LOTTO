import streamlit as st
import pandas as pd
from collections import Counter
from itertools import combinations
import os
import random
import statistics
import requests
from datetime import datetime

# 1. 웹 페이지 기본 레이아웃 및 고급 폰트 설정 (Poppins, Lato)
st.set_page_config(
    page_title="LOTTO AI PLATFORM v8.0", 
    page_icon="💎", 
    layout="centered"
)

# 고급 CSS 주입 (컨설팅 보고서 스타일 테마)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&family=Lato:wght@400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Lato', sans-serif; color: #1e293b; }
    h1, h2, h3 { font-family: 'Poppins', sans-serif; font-weight: 700; color: #001f3f; }
    
    .stButton>button {
        background: linear-gradient(90deg, #001f3f 0%, #0056b3 100%);
        color: white; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
    
    .premium-card {
        background-color: #f8fafc; border-radius: 16px; border-left: 8px solid #0056b3;
        padding: 30px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .data-label { font-size: 13px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 1px; }
    .data-value { font-size: 20px; font-weight: 700; color: #001f3f; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# [NEW] 로또 공 스타일 렌더링 엔진 (각 공 밑에 번호 텍스트 개별 정렬 버전)
def render_lotto_balls(numbers):
    ball_htmls = []
    for n in sorted(numbers):
        if n <= 10:
            bg = "linear-gradient(135deg, #fbc02d, #f9a825)" # 황금색
        elif n <= 20:
            bg = "linear-gradient(135deg, #1e88e5, #1565c0)" # 파란색
        elif n <= 30:
            bg = "linear-gradient(135deg, #e53935, #c62828)" # 빨간색
        elif n <= 40:
            bg = "linear-gradient(135deg, #78909c, #455a64)" # 회색
        else:
            bg = "linear-gradient(135deg, #43a047, #2e7d32)" # 초록색
            
        # 개별 공과 밑의 텍스트 숫자를 세트로 묶어서 정렬하는 세련된 Flexbox 컴포넌트
        ball_htmls.append(
            f'<div style="display: flex; flex-direction: column; align-items: center; margin-right: 15px;">'
            f'  <div style="width: 48px; height: 48px; line-height: 48px; background: {bg}; color: white; '
            f'              font-size: 19px; font-weight: bold; text-align: center; border-radius: 50%; '
            f'              box-shadow: 0 4px 6px rgba(0,0,0,0.15), inset -3px -3px 6px rgba(0,0,0,0.2);">'
            f'    {n:02d}'
            f'  </div>'
            f'  <div style="margin-top: 8px; font-family: \'Poppins\', sans-serif; font-size: 16px; font-weight: 700; color: #334155;">'
            f'    {n}'
            f'  </div>'
            f'</div>'
        )
        
    return f'<div style="display: flex; align-items: center; margin: 15px 0 25px 0;">{"".join(ball_htmls)}</div>'

# 동행복권 공식 API 연동 자동 최신화 엔진
def sync_lotto_dataset(filename="lotto_history.csv"):
    if not os.path.exists(filename):
        return None, "파일이 존재하지 않습니다."
        
    try:
        df_local = pd.read_csv(filename)
        if '회차' not in df_local.columns:
            return df_local, "CSV 파일에 '회차' 컬럼이 없습니다."
            
        df_local = df_local.sort_values(by='회차').reset_index(drop=True)
        last_drawn_idx = int(df_local['회차'].iloc[-1])
        
        base_date = datetime(2019, 4, 6)
        base_idx = 852
        now = datetime.now()
        
        weeks_diff = (now - base_date).days // 7
        expected_current_idx = base_idx + weeks_diff
        
        if now.weekday() == 5 and now.hour < 21:
            expected_current_idx -= 1
            
        updated_count = 0
        new_rows = []
        
        with st.spinner("🔄 동행복권 공식 API로부터 최신 당첨 데이터를 동기화 중입니다..."):
            for target_idx in range(last_drawn_idx + 1, expected_current_idx + 1):
                api_url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={target_idx}"
                response = requests.get(api_url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("returnValue") == "success":
                        new_rows.append({
                            "회차": target_idx, "추첨일": data.get("drwNoDate"),
                            "번호1": data.get("drwtNo1"), "번호2": data.get("drwtNo2"),
                            "번호3": data.get("drwtNo3"), "번호4": data.get("drwtNo4"),
                            "번호5": data.get("drwtNo5"), "번호6": data.get("drwtNo6"),
                            "보너스": data.get("bnusNo")
                        })
                        updated_count += 1
                    else:
                        break
                else:
                    break
                    
        if updated_count > 0:
            df_new = pd.DataFrame(new_rows)
            df_combined = pd.concat([df_local, df_new], ignore_index=True)
            df_combined.to_csv(filename, index=False)
            return df_combined, f"🚀 성공적으로 {updated_count}개의 최신 회차 데이터를 동기화했습니다! (최신: {df_combined['회차'].iloc[-1]}회)"
            
        return df_local, f"✅ 이미 최신 데이터 상태입니다. (현재: {last_drawn_idx}회)"
        
    except Exception as e:
        return pd.read_csv(filename) if os.path.exists(filename) else None, f"⚠️ 동기화 중 일시적 지연 발생: {str(e)}"

@st.cache_data
def bootstrap_data_engine(df_input):
    number_cols = ['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']
    all_matrix = df_input[number_cols].values
    counter = Counter(all_matrix.flatten())
    
    pair_list, triple_list = [], []
    for row in all_matrix:
        sorted_row = sorted(row)
        pair_list.extend(combinations(sorted_row, 2))
        triple_list.extend(combinations(sorted_row, 3))
        
    return counter, dict(Counter(pair_list)), dict(Counter(triple_list))

# CORE MATH & ENGINE CORES
def calculate_quality_score(nums):
    score = 0
    nums = sorted(nums)
    total_sum = sum(nums)
    if 110 <= total_sum <= 180: score += 25
    elif 90 <= total_sum <= 200: score += 12
    
    odd_cnt = len([x for x in nums if x % 2 == 1])
    if odd_cnt in [2, 3, 4]: score += 20
    elif odd_cnt in [1, 5]: score += 8
    
    gaps = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
    if min(gaps) > 1 and max(gaps) < 18: score += 20
    elif min(gaps) >= 1 and max(gaps) < 28: score += 10
    
    zones = [0]*5
    for n in nums:
        if n <= 10: zones[0]+=1
        elif n <= 20: zones[1]+=1
        elif n <= 30: zones[2]+=1
        elif n <= 40: zones[3]+=1
        else: zones[4]+=1
    if max(zones) <= 3: score += 15
    elif max(zones) == 4: score += 5
    
    consec = sum(1 for i in range(len(nums)-1) if nums[i+1] == nums[i] + 1)
    if consec == 1: score += 10
    elif consec == 0: score += 7
    
    ends = set(x % 10 for x in nums)
    if len(ends) >= 5: score += 10
    elif len(ends) >= 4: score += 5
    return min(score, 100)

def calculate_risk_matrix(nums, popular_numbers):
    risk = 0
    reason_flags = []
    nums = sorted(nums)
    
    bday_nums = len([x for x in nums if x <= 31])
    if bday_nums >= 5:
        risk += 30
        reason_flags.append("⚠️ 생일 패턴(1~31) 과밀 집중 사용")
    elif bday_nums == 4:
        risk += 15
        
    pop_cnt = len([x for x in nums if x in popular_numbers])
    if pop_cnt >= 4:
        risk += 30
        reason_flags.append("⚠️ 대중 선호 군집 인기수 다수 마킹")
    elif pop_cnt >= 2:
        risk += 15
        
    if len(nums) > 1:
        deviation = statistics.stdev(nums)
        if deviation < 8.5:
            risk += 20
            reason_flags.append("⚠️ 기하학적 번호 배치 조밀도 임계치 초과")
        elif deviation < 11.5:
            risk += 10
            
    max_consec = 1
    curr_consec = 1
    for i in range(len(nums)-1):
        if nums[i+1] == nums[i] + 1:
            curr_consec += 1
            max_consec = max(max_consec, curr_consec)
        else:
            curr_consec = 1
    if max_consec >= 3:
        risk += 20
        reason_flags.append("⚠️ 3개 연번 이상 마킹 위험 수준 감지")
    elif max_consec == 2:
        risk += 5
    return min(risk, 100), reason_flags if reason_flags else ["✅ 표준 안정 범위 스크리닝 통과"]

def convert_score_to_s_grade(score):
    if score >= 95: return "S+"
    elif score >= 90: return "S"
    elif score >= 80: return "A"
    elif score >= 70: return "B"
    elif score >= 60: return "C"
    else: return "D"

def compute_overdue_days(df_input):
    number_cols = ['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']
    latest = len(df_input)
    overdue = {num: latest for num in range(1, 46)}
    for idx in reversed(range(latest)):
        for num in df_input.iloc[idx][number_cols].tolist():
            if overdue[num] == latest:
                overdue[num] = latest - (idx + 1)
    return overdue

# 메인 헤더 구성
st.title("💎 LOTTO INTELLIGENCE PLATFORM v8.0")
st.markdown("##### Strategic Analysis & Premium Human Interface")

csv_filename = "lotto_history.csv"
df = None

if os.path.exists(csv_filename):
    df, sync_msg = sync_lotto_dataset(csv_filename)
    st.sidebar.info(sync_msg)
else:
    st.sidebar.warning(f"'{csv_filename}' 파일이 존재하지 않습니다.")
    uploaded_file = st.sidebar.file_uploader("최초 데이터 구축용 CSV 업로드", type=["csv"])
    if uploaded_file is not None:
        with open(csv_filename, "wb") as f:
            f.write(uploaded_file.getbuffer())
        df, sync_msg = sync_lotto_dataset(csv_filename)
        st.sidebar.info(sync_msg)

if df is not None:
    popular_numbers = {7, 10, 11, 17, 20, 21, 27, 30, 33, 40}
    counter, pair_dict, triple_dict = bootstrap_data_engine(df)
    
    if 'top5_combinations' not in st.session_state:
        st.session_state.top5_combinations = []
    if 'web_report' not in st.session_state:
        st.session_state.web_report = ""

    tab1, tab2, tab3, tab4 = st.tabs(["🏆 AI 추천 센터", "❤️ 번호 건강도", "⚠️ 위험도 & 독식 분석", "🧬 패턴 연구소"])

    # 탭 1: AI 추천 센터 (고급 카드 레이아웃 및 텍스트 하단 배치 적용)
    with tab1:
        st.subheader("🏆 AI 추천 센터 프리미엄")
        col1, col2 = st.columns([2, 1])
        with col1:
            trigger = st.button("⚡ 10,000개 조합 고속 필터 시뮬레이션 가동", use_container_width=True)
        with col2:
            if st.session_state.web_report:
                st.download_button(
                    label="💾 분석 결과 리포트 저장", data=st.session_state.web_report,
                    file_name="Lotto_AI_Recommend_Report.txt", mime="text/plain", use_container_width=True
                )
            else:
                st.button("💾 분석 결과 리포트 저장", disabled=True, use_container_width=True)

        if trigger:
            with st.spinner("🚀 고밀도 모의 세트 생성 및 프리미엄 인텔리전스 필터링 중..."):
                number_cols = ['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']
                recent_30 = df.tail(30)
                ex_counter = Counter()
                for _, r in recent_30.iterrows():
                    ex_counter.update(r[number_cols])
                excluded_set = set([x[0] for x in ex_counter.most_common(5)])
                
                pool = [x for x in range(1, 46) if x not in excluded_set]
                candidate_pool = []
                for _ in range(10000):
                    nums = sorted(random.sample(pool, 6))
                    candidate_pool.append(nums)
                    
                evaluated_pool = []
                for nums in candidate_pool:
                    q_score = calculate_quality_score(nums)
                    r_score, reasons = calculate_risk_matrix(nums, popular_numbers)
                    m_score = 100 - r_score
                    evaluated_pool.append({
                        "numbers": nums, "quality": q_score, "risk": r_score, "monopoly": m_score, "reasons": reasons
                    })
                    
                top_100 = sorted(evaluated_pool, key=lambda x: x["quality"], reverse=True)[:100]
                final_top5 = sorted(top_100, key=lambda x: (x["quality"], x["monopoly"]), reverse=True)[:5]
                st.session_state.top5_combinations = final_top5
                
                report_buffer = f"🏆 [AI 추천 센터 프리미엄 결과 리포트 - 기준 데이터: 총 {len(df)}회차]\n"
                report_buffer += "=========================================================\n"
                for idx, item in enumerate(final_top5, 1):
                    num_str = " ".join(f"{n:02d}" for n in item["numbers"])
                    grade = convert_score_to_s_grade(item["quality"])
                    stars = "★" * max(1, round(item["monopoly"] / 20))
                    report_buffer += f"   🥇 [최적 추천 조합 제 {idx}위]\n   👉  조합 번호 : [ {num_str} ]\n   -------------------------------------------------------\n"
                    report_buffer += f"   ▫️ 종합 평정 등급 : {grade:<5} | ▫️ 분석 품질 점수 : {item['quality']}점\n   ▫️ 구조적 위험도  : {item['risk']:<5} | ▫️ 독식 가능 지수 : {item['monopoly']}점 ({stars})\n   ▫️ 세부 리스크 프로파일 디텍션:\n"
                    for r in item["reasons"]: report_buffer += f"     - {r}\n"
                    report_buffer += "=========================================================\n"
                st.session_state.web_report = report_buffer
                st.rerun()

        if st.session_state.top5_combinations:
            st.markdown("### 🔮 AI 최적 추천 스루풋 (TOP 5)")
            for idx, item in enumerate(st.session_state.top5_combinations, 1):
                grade = convert_score_to_s_grade(item["quality"])
                stars = "★" * max(1, round(item["monopoly"] / 20))
                
                # 컨설팅 스타일의 세련된 프리미엄 카드 UI 출력
                st.markdown(f"""
                <div class="premium-card">
                    <div style="font-size: 22px; font-weight: 700; margin-bottom: 20px; color:#001f3f;">🥇 RANK #{idx} 추천 조합 (종합 평정 등급: {grade})</div>
                    {render_lotto_balls(item['numbers'])}
                    <div style="display: flex; gap: 50px; margin-top: 5px;">
                        <div><div class="data-label">분석 품질</div><div class="data-value">{item['quality']}점 / 100</div></div>
                        <div><div class="data-label">독식 가능성</div><div class="data-value">{item['monopoly']}점 ({stars})</div></div>
                        <div><div class="data-label">위험도 스코어</div><div class="data-value">{item['risk']}점</div></div>
                    </div>
                    <div style="margin-top: 15px; border-top: 1px solid #e2e8f0; padding-top: 15px;">
                        <div class="data-label">리스크 프로파일 디텍션</div>
                        <div style="font-size: 15px; font-weight: 600; color:#475569; margin-top:5px;">{" / ".join(item['reasons'])}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("📂 **텍스트 리포트 원본 백업**")
            st.code(st.session_state.web_report, language="text")
        else:
            st.info("시뮬레이션 가동 버튼을 누르면 정밀 분석 필터를 거친 고해상도 디자인 결과물이 활성화됩니다.")

    # 탭 2: 번호 건강도 시스템
    with tab2:
        st.subheader("❤️ 개별 번호 인텔리전스 건강도 리포트 - TOP 20")
        overdue = compute_overdue_days(df)
        max_f = max(counter.values()) if counter.values() else 1
        max_o = max(overdue.values()) if overdue.values() else 1
        
        p_strength = {i:0 for i in range(1,46)}
        for p, c in pair_dict.items():
            p_strength[p[0]]+=c; p_strength[p[1]]+=c
        t_strength = {i:0 for i in range(1,46)}
        for t, c in triple_dict.items():
            t_strength[t[0]]+=c; t_strength[t[1]]+=c; t_strength[t[2]]+=c
            
        max_p = max(p_strength.values()) if p_strength.values() else 1
        max_t = max(t_strength.values()) if t_strength.values() else 1
        
        health_registry = []
        for n in range(1, 46):
            f_part = (counter[n]/max_f)*25
            o_part = ((max_o - overdue[n])/max_o)*25
            p_part = (p_strength[n]/max_p)*25
            t_part = (t_strength[n]/max_t)*25
            total_h = min(100, int(f_part + o_part + p_part + t_part))
            
            def letter_grade(val, base=25):
                ratio = val / base
                if ratio >= 0.85: return "A+"
                elif ratio >= 0.70: return "A"
                elif ratio >= 0.55: return "B"
                elif ratio >= 0.40: return "C"
                else: return "D"
                
            health_registry.append({
                "번호": f"{n:02d}번", "건강도 점수": f"{total_h}점",
                "출현 빈도": letter_grade(f_part), "미출현 기간": letter_grade(o_part),
                "번호쌍 강도": letter_grade(p_part), "트리플 강도": letter_grade(t_part),
                "raw_h": total_h
            })
        top_20_health = sorted(health_registry, key=lambda x: x["raw_h"], reverse=True)[:20]
        st.table(pd.DataFrame(top_20_health).drop(columns=["raw_h"]))

    # 탭 3: 위험도 및 독식 분석 (수동 검증 창도 동일 디자인 적용)
    with tab3:
        st.subheader("🧪 수동 입력 조합 리스크 인스펙터")
        custom_input = st.text_input("검증 번호 입력 (공백 구분 6개):", value="4 11 19 28 37 44")
        try:
            raw_tokens = custom_input.split()
            if len(raw_tokens) == 6:
                nums = sorted([int(x) for x in raw_tokens])
                if any(x < 1 or x > 45 for x in nums) or len(set(nums)) != 6:
                    st.error("1~45 사이의 중복 없는 숫자 6개를 입력해주세요.")
                else:
                    r_score, reasons = calculate_risk_matrix(nums, popular_numbers)
                    m_score = 100 - r_score
                    q_score = calculate_quality_score(nums)
                    stars = "★" * max(1, round(m_score / 20))
                    
                    st.markdown("### 🎯 대상 검증 조합")
                    st.markdown(render_lotto_balls(nums), unsafe_allow_html=True)
                    
                    c_risk, c_mono, c_qual = st.columns(3)
                    c_risk.metric("🔴 최종 판정 위험도", f"{r_score} 점 / 100")
                    c_mono.metric("🟢 독식 가능성 점수", f"{m_score} 점", delta=stars, delta_color="off")
                    c_qual.metric("🔵 균형 품질 점수", f"{q_score} 점", delta=f"등급: {convert_score_to_s_grade(q_score)}", delta_color="off")
                    
                    st.write("📋 **리스크 상세 분석 결과:**")
                    for r in reasons: st.write(f"- {r}")
        except ValueError:
            st.error("올바른 숫자 형식이 아닙니다.")

    # 탭 4: 패턴 연구소 & 관계도
    with tab4:
        st.subheader("🧬 패턴 연구소 통계 허브")
        number_cols = ['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']
        total_draws = len(df)
        df_10 = df.tail(10)[number_cols].values.flatten()
        df_30 = df.tail(30)[number_cols].values.flatten()
        df_100 = df.tail(100)[number_cols].values.flatten()
        
        c_10, c_30, c_100 = Counter(df_10), Counter(df_30), Counter(df_100)
        window_data = []
        for n in range(1, 6):
            window_data.append({
                "번호": f"{n:02d}번", "최근 10회차 출현": f"{c_10[n]}회", "최근 30회차 출현": f"{c_30[n]}회", "최근 100회차 출현": f"{c_100[n]}회"
            })
        st.dataframe(pd.DataFrame(window_data), use_container_width=True)
        
        total_matrix = df[number_cols].values
        odd_all = sum(1 for row in total_matrix for x in row if x % 2 == 1)
        even_all = (total_draws * 6) - odd_all
        st.info(f"📈 **[누적 역대 데이터]** 총 홀수({odd_all}개) : 총 짝수({even_all}개)")

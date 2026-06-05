import streamlit as st
import pandas as pd
from collections import Counter
from itertools import combinations
import os
import random
import statistics

# 1. 웹 페이지 기본 레이아웃 셋업
st.set_page_config(
    page_title="로또 AI 인텔리전스 플랫폼 v6.0",
    page_icon="🧠",
    layout="centered"
)

# 2. 고속 성능을 위한 인메모리 데이터 캐싱 엔진
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
        
    pair_dict = dict(Counter(pair_list))
    triple_dict = dict(Counter(triple_list))
    
    return counter, pair_dict, triple_dict

# 3. CORE MATH & ENGINE CORES (기존 로직 100% 보존)
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
        reason_flags.append("⚠️ 대중 선호 군집인기수 다수 마킹")
    elif pop_cnt >= 2:
        risk += 15
        
    if len(nums) > 1:
        deviation = statistics.stdev(nums)
        if deviation < 8.5:
            risk += 20
            reason_flags.append("⚠️ 기하학적 번호 배치 조밀도(군집도) 임계치 초과")
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

# 4. 메인 플랫폼 헤더 구성
st.title("🧠 LOTTO INTELLIGENCE PLATFORM v6.0")
st.caption("데이터 기반 조합 품질 평가 및 다각적 독식 가능성 시뮬레이터 (Web Responsive)")

# 5. 데이터 동기화 파트 (로컬 CSV 검색 -> 없을 시 웹 업로드 유도)
csv_filename = "lotto_history.csv"
df = None

if os.path.exists(csv_filename):
    df = pd.read_csv(csv_filename)
else:
    st.sidebar.warning(f"'{csv_filename}'이 로컬에 없습니다.")
    uploaded_file = st.sidebar.file_uploader("로또 히스토리 CSV 파일을 업로드해주세요.", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

# 데이터가 로드되었을 때만 인텔리전스 엔진 가동
if df is not None:
    popular_numbers = {7, 10, 11, 17, 20, 21, 27, 30, 33, 40}
    counter, pair_dict, triple_dict = bootstrap_data_engine(df)
    
    # 세션 상태 초기화 (리포트 저장용 데이터 보존 아키텍처)
    if 'web_report' not in st.session_state:
        st.session_state.web_report = ""

    # 새롭게 규정된 4대 핵심 탭 레이아웃 셋업
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 AI 추천 센터", "❤️ 번호 건강도", "⚠️ 위험도 & 독식 분석", "🧬 패턴 연구소"])

    # ==========================================================
    # VIEWPORT 1: AI 추천 센터
    # ==========================================================
    with tab1:
        st.subheader("🏆 AI 추천 센터 프리미엄")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            trigger = st.button("⚡ 10,000개 조합 고속 필터 시뮬레이션 가동", use_container_width=True)
        with col2:
            # 리포트 다운로드 버튼 배치 (컨텐트가 있을 때만 활성화 유도)
            if st.session_state.web_report:
                st.download_button(
                    label="💾 분석 결과 리포트 저장",
                    data=st.session_state.web_report,
                    file_name="Lotto_AI_Recommend_Report.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.button("💾 분석 결과 리포트 저장", disabled=True, use_container_width=True)

        if trigger:
            with st.spinner("🚀 [AI 인텔리전스 가동] 10,000개 고밀도 모의 세트 생성 중..."):
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
                
                # 내부 세션 상태 텍스트 빌드업
                report_buffer = "🏆 [AI 추천 센터 프리미엄 품질 마스터 결과 리포트]\n"
                report_buffer += "=========================================================\n"
                for idx, item in enumerate(final_top5, 1):
                    num_str = " ".join(f"{n:02d}" for n in item["numbers"])
                    grade = convert_score_to_s_grade(item["quality"])
                    stars = "★" * max(1, round(item["monopoly"] / 20))
                    
                    report_buffer += f"   🥇 [최적 추천 조합 제 {idx}위]\n"
                    report_buffer += f"   👉  조합 번호 : [ {num_str} ]\n"
                    report_buffer += f"   -------------------------------------------------------\n"
                    report_buffer += f"   ▫️ 종합 평정 등급 : {grade:<5} | ▫️ 분석 품질 점수 : {item['quality']}점 / 100만점\n"
                    report_buffer += f"   ▫️ 구조적 위험도  : {item['risk']:<5} | ▫️ 독식 가능 지수 : {item['monopoly']}점 ({stars})\n"
                    report_buffer += f"   ▫️ 세부 리스크 프로파일 디텍션:\n"
                    for r in item["reasons"]:
                        report_buffer += f"     - {r}\n"
                    report_buffer += "=========================================================\n"
                
                st.session_state.web_report = report_buffer
                st.rerun() # 다운로드 버튼 활성화를 위한 리런 처리

        if st.session_state.web_report:
            st.code(st.session_state.web_report, language="text")
        else:
            st.info("상단의 시뮬레이션 버튼을 누르면 인텔리전스 분석결과 데이터가 이곳에 렌더링됩니다.")

    # ==========================================================
    # VIEWPORT 2: 번호 건강도 시스템
    # ==========================================================
    with tab2:
        st.subheader("❤️ 데이터 기반 개별 번호 인텔리전스 건강도 리포트 - TOP 20")
        st.caption("💡 반영 매개변수: 단일 빈도(25%) + 최신 활성도(25%) + 쌍 강도(25%) + 트리플 강도(25%)")
        
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
        health_df = pd.DataFrame(top_20_health).drop(columns=["raw_h"])
        st.table(health_df)

    # ==========================================================
    # VIEWPORT 3: 위험도 및 독식 분석 레이어
    # ==========================================================
    with tab3:
        st.subheader("🧪 수동 입력 조합 리스크 인스펙터")
        custom_input = st.text_input("검증 공백구분 6번호 입력:", value="4 11 19 28 37 44")
        
        try:
            raw_tokens = custom_input.split()
            if len(raw_tokens) == 6:
                nums = sorted([int(x) for x in raw_tokens])
                if any(x < 1 or x > 45 for x in nums) or len(set(nums)) != 6:
                    st.error("1~45 사이의 중복 없는 숫자 6개를 입력해 주십시오.")
                else:
                    r_score, reasons = calculate_risk_matrix(nums, popular_numbers)
                    m_score = 100 - r_score
                    q_score = calculate_quality_score(nums)
                    stars = "★" * max(1, round(m_score / 20))
                    
                    st.markdown(f"### 🎯 대상 검증 마킹 조합 : `{nums}`")
                    c_risk, c_mono, c_qual = st.columns(3)
                    c_risk.metric("🔴 최종 판정 위험도", f"{r_score} 점 / 100")
                    c_mono.metric("🟢 독식 가능성 점수", f"{m_score} 점", delta=stars, delta_color="off")
                    c_qual.metric("🔵 균형 품질 점수", f"{q_score} 점", delta=f"등급: {convert_score_to_s_grade(q_score)}", delta_color="off")
                    
                    st.write("📋 **리스크 심층 감지 요인 브레이크다운:**")
                    for r in reasons:
                        st.write(f"- {r}")
            else:
                st.warning("공백으로 구분된 6개의 숫자를 완벽하게 입력하면 자동 실시간 분석이 시작됩니다.")
        except ValueError:
            st.error("올바른 숫자 형식이 아닙니다.")

    # ==========================================================
    # VIEWPORT 4: 패턴 연구소 & 관계도
    # ==========================================================
    with tab4:
        st.subheader("🧬 패턴 연구소 통계 허브")
        
        number_cols = ['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']
        total_draws = len(df)
        df_10 = df.tail(10)[number_cols].values.flatten()
        df_30 = df.tail(30)[number_cols].values.flatten()
        df_100 = df.tail(100)[number_cols].values.flatten()
        
        c_10, c_30, c_100 = Counter(df_10), Counter(df_30), Counter(df_100)
        
        st.write("📊 **[시계열 윈도우 기준 번호 출현 성향 분석]** (상위 예시)")
        window_data = []
        for n in range(1, 6):
            window_data.append({
                "번호": f"{n:02d}번", "최근 10회차 출현": f"{c_10[n]}회", "최근 30회차 출현": f"{c_30[n]}회", "최근 100회차 출현": f"{c_100[n]}회"
            })
        st.dataframe(pd.DataFrame(window_data), use_container_width=True)
        
        total_matrix = df[number_cols].values
        odd_all = sum(1 for row in total_matrix for x in row if x % 2 == 1)
        even_all = (total_draws * 6) - odd_all
        st.info(f"📈 **[역대 누적 필터 분포 데이터]** 누적 총체적 홀짝 비율 — 홀수( {odd_all}개 ) : 짝수( {even_all}개 )")
        
        st.write("🕸️ **[AI 관계도 연구실: 핵심 연계망 구조 트리 분석 (Network Analysis)]**")
        top_3_single = [x[0] for x in counter.most_common(3)]
        
        network_text = ""
        for root_num in top_3_single:
            network_text += f"📍 {root_num}번 메인 루트 노드\n"
            sub_pairs = [k for k in pair_dict.keys() if root_num in k]
            sorted_sub_pairs = sorted(sub_pairs, key=lambda x: pair_dict[x], reverse=True)[:3]
            
            for p in sorted_sub_pairs:
                linked = p[1] if p[0] == root_num else p[0]
                network_text += f"   ├── [번호쌍 연계] ──> {linked}번 (동시출현: {pair_dict[p]}회)\n"
                
            sub_triples = [k for k in triple_dict.keys() if root_num in k]
            if sub_triples:
                best_t = sorted(sub_triples, key=lambda x: triple_dict[x], reverse=True)[0]
                t_links = [x for x in best_t if x != root_num]
                network_text += f"   └── [트리플 연쇄] ──> {t_links[0]}번, {t_links[1]}번 (공동 당첨: {triple_dict[best_t]}회)\n"
            network_text += "-------------------------------------------------------------------------\n"
        st.code(network_text, language="text")
else:
    st.info("💡 배포 및 구동을 위해 기저 데이터셋이 필요합니다. 왼쪽 사이드바에서 'lotto_history.csv' 파일을 업로드해 주세요.")
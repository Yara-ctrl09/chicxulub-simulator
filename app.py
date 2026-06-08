# -*- coding: utf-8 -*-
"""
🌍 K-Pg 대멸종 시뮬레이션 - 통합 웹 애플리케이션
HTML 웹사이트(운석 충돌 물리 시뮬레이션) + Python ABM(생태계 시뮬레이션) 통합

실행: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import math
from kpg_simulation import (
    Environment, Plant, Herbivore, Carnivore, Scavenger, World,
    TOTAL_STEPS, IMPACT_STEP
)

# ============================================================================
# Streamlit 페이지 설정
# ============================================================================
st.set_page_config(
    page_title="K-Pg 대멸종 시뮬레이션",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# 세션 상태 초기화 (페이지 네비게이션 관리)
# ============================================================================
"""
Streamlit의 session_state는 브라우저 세션 동안 상태를 유지합니다.
- page: 현재 페이지 ('home' / 'impact_sim' / 'abm_sim')
- asteroid_data: 운석 충돌 시뮬레이션의 입력값 저장
- world: Python ABM 시뮬레이션 결과 저장
"""
if 'page' not in st.session_state:
    st.session_state.page = 'home'

if 'asteroid_data' not in st.session_state:
    st.session_state.asteroid_data = None

if 'world' not in st.session_state:
    st.session_state.world = None

# ============================================================================
# 함수: 운석 충돌 에너지 계산
# ============================================================================
def calculate_impact_energy(diameter_km, velocity_kms):
    """
    공식: E = (1/2) × m × v²
    
    단계별:
    1. 소행성 부피 = (4/3) × π × r³ (구 공식)
    2. 질량 = 부피 × 밀도 (3000 kg/m³ 가정)
    3. 에너지 = 0.5 × 질량 × 속도²
    4. 단위 변환: J → TNT 메가톤 (1 Mt = 4.184×10¹⁵ J)
    """
    diameter_m = diameter_km * 1000
    radius_m = diameter_m / 2
    velocity_ms = velocity_kms * 1000
    density = 3000  # kg/m³
    
    # 구의 부피
    volume_m3 = (4/3) * math.pi * (radius_m ** 3)
    
    # 질량
    mass_kg = volume_m3 * density
    
    # 운동에너지
    energy_joules = 0.5 * mass_kg * (velocity_ms ** 2)
    
    # TNT 메가톤으로 변환
    energy_mt = energy_joules / (4.184e15)
    
    return energy_mt

# ============================================================================
# 함수: 크레이터 직경 계산
# ============================================================================
def calculate_crater_diameter(energy_mt, angle_degrees):
    """
    크레이터 = 에너지에 비례, 각도에 따라 조정
    - 90°(정면): 최대
    - 30°(측면): 최소 (에너지 분산)
    """
    angle_rad = math.radians(angle_degrees)
    angle_coeff = math.cos(angle_rad)
    
    base_size = 150
    reference_energy = 61
    crater = base_size * ((energy_mt / reference_energy) ** (1/3.4)) * angle_coeff
    
    return max(20, crater)

# ============================================================================
# 함수: 지진 규모 계산
# ============================================================================
def calculate_earthquake_magnitude(energy_mt):
    """
    리히터 규모: M = (2/3) × log₁₀(E) - 10.7
    E는 erg 단위 (1 Mt = 10²² erg)
    """
    energy_erg = energy_mt * 1e22
    magnitude = (2/3) * math.log10(energy_erg) - 10.7
    return magnitude

# ============================================================================
# 페이지 1: 홈 (메뉴)
# ============================================================================
def page_home():
    """메인 홈페이지 - 두 가지 시뮬레이션 선택"""
    st.markdown("""
    <style>
    .title-main {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(45deg, #00d4ff, #0099ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="title-main">🌍 칙술루브 충돌 시뮬레이터</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    # 약 6,600만 년 전, 유카탄 반도에 떨어진 운석
    
    지구 역사상 가장 극적인 사건을 **두 가지 방식**으로 시뮬레이션합니다:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🌐 방법 1: 물리 시뮬레이션
        
        **HTML 기반 운석 충돌 시뮬레이터**
        - 🎚️ 슬라이더로 직경, 속도, 각도 설정
        - ⚡ 물리 공식으로 에너지 계산
        - 📊 3년간의 기온 변화 그래프
        - 🦕 생물 종 생존율 추이
        - 🎬 충격파 애니메이션
        """)
        
        if st.button("🚀 물리 시뮬레이션 시작", use_container_width=True, key="impact"):
            st.session_state.page = 'impact_sim'
            st.rerun()
    
    with col2:
        st.markdown("""
        ### 🐍 방법 2: 에이전트 기반 모델링 (ABM)
        
        **생태계 붕괴 시뮬레이션**
        - 🎛️ 초기 개체수 조정
        - 🌡️ 환경 급변 시뮬레이션
        - 🔗 먹이사슬 연쇄 붕괴
        - 📈 시간별 생존율 추이
        - 💀 대멸종 메커니즘 분석
        """)
        
        if st.button("🔬 ABM 시뮬레이션 시작", use_container_width=True, key="abm"):
            st.session_state.page = 'abm_sim'
            st.rerun()
    
    st.markdown("---")
    
    st.info("""
    💡 **학습 목표**
    
    두 시뮬레이션은 상호 보완적입니다:
    - **물리 시뮬레이션**: 운석 충돌의 물리적 영향 (에너지, 기온 변화)
    - **ABM**: 생태계의 생물학적 반응 (개체수, 멸종)
    
    함께 보면 K-Pg 대멸종의 **전체 그림**을 이해할 수 있습니다! 🌍
    """)

# ============================================================================
# 페이지 2: 운석 충돌 물리 시뮬레이션 (입력)
# ============================================================================
def page_impact_input():
    """index.html과 동일한 기능 - 파라미터 입력"""
    
    col_nav, col_space = st.columns([1, 9])
    with col_nav:
        if st.button("← 메뉴로 돌아가기"):
            st.session_state.page = 'home'
            st.rerun()
    
    st.markdown("""
    <style>
    .title-sub {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #00d4ff;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="title-sub">⚙️ 충돌 조건 설정</div>', unsafe_allow_html=True)
    
    st.markdown("""
    아래 슬라이더를 조정하여 운석의 특성을 설정하세요.
    물리 공식(E = ½mv²)을 사용하여 자동으로 충돌 영향을 계산합니다.
    """)
    
    # 세 개 슬라이더
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🪨 소행성 직경")
        diameter = st.slider(
            "직경 (km)",
            min_value=1.0, max_value=30.0, value=10.0, step=0.5,
            label_visibility="collapsed"
        )
        st.caption(f"**{diameter:.1f} km** (실제 칙술루브: ~10 km)")
    
    with col2:
        st.markdown("### ⚡ 충돌 속도")
        velocity = st.slider(
            "속도 (km/s)",
            min_value=11.0, max_value=40.0, value=20.0, step=0.5,
            label_visibility="collapsed"
        )
        st.caption(f"**{velocity:.1f} km/s** (평균 우주 충돌: ~20 km/s)")
    
    with col3:
        st.markdown("### 📐 충돌 각도")
        angle = st.slider(
            "각도 (°)",
            min_value=30, max_value=90, value=60, step=1,
            label_visibility="collapsed"
        )
        st.caption(f"**{angle}°** (90°: 정면, 30°: 측면)")
    
    # 실시간 계산값 표시
    st.markdown("---")
    st.markdown("### 📊 즉시 계산값")
    
    energy = calculate_impact_energy(diameter, velocity)
    crater = calculate_crater_diameter(energy, angle)
    magnitude = calculate_earthquake_magnitude(energy)
    
    calc_col1, calc_col2, calc_col3 = st.columns(3)
    
    with calc_col1:
        st.metric("충돌 에너지", f"{energy:.1f} Mt TNT", 
                 delta=f"(실제 칙술루브: ~61 Mt)")
    
    with calc_col2:
        st.metric("크레이터 직경", f"{crater:.0f} km",
                 delta=f"(각도 {angle}° 적용)")
    
    with calc_col3:
        st.metric("지진 규모", f"{magnitude:.1f}",
                 delta="리히터 스케일")
    
    # 시뮬레이션 시작 버튼
    st.markdown("---")
    
    col_btn1, col_btn2 = st.columns([3, 1])
    
    with col_btn1:
        if st.button("🚀 충돌 시뮬레이션 시작", use_container_width=True, 
                    type="primary", key="launch_impact"):
            # 데이터를 session_state에 저장
            st.session_state.asteroid_data = {
                'diameter': diameter,
                'velocity': velocity,
                'angle': angle,
                'energy': energy,
                'crater': crater,
                'magnitude': magnitude
            }
            st.session_state.page = 'impact_results'
            st.rerun()
    
    with col_btn2:
        pass

# ============================================================================
# 페이지 3: 운석 충돌 결과 (분석)
# ============================================================================
def page_impact_results():
    """result.html과 동일한 기능 - 결과 분석 및 그래프"""
    
    if st.session_state.asteroid_data is None:
        st.error("❌ 입력 데이터가 없습니다. 이전 페이지로 돌아가주세요.")
        if st.button("← 뒤로가기"):
            st.session_state.page = 'impact_sim'
            st.rerun()
        return
    
    data = st.session_state.asteroid_data
    diameter = data['diameter']
    velocity = data['velocity']
    angle = data['angle']
    energy = data['energy']
    crater = data['crater']
    magnitude = data['magnitude']
    
    col_nav, col_space = st.columns([1, 9])
    with col_nav:
        if st.button("← 메뉴로"):
            st.session_state.page = 'home'
            st.rerun()
    
    st.markdown("""
    <style>
    .title-sub {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #ff6b35;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="title-sub">📊 충돌 분석 결과</div>', unsafe_allow_html=True)
    
    # 입력값 재확인
    st.subheader("📍 입력 파라미터")
    param_col1, param_col2, param_col3 = st.columns(3)
    
    with param_col1:
        st.metric("소행성 직경", f"{diameter:.1f} km")
    with param_col2:
        st.metric("충돌 속도", f"{velocity:.1f} km/s")
    with param_col3:
        st.metric("충돌 각도", f"{angle}°")
    
    # 계산 결과
    st.subheader("⚡ 계산 결과")
    result_col1, result_col2, result_col3 = st.columns(3)
    
    with result_col1:
        st.metric("충돌 에너지", f"{energy:.1f} Mt")
    with result_col2:
        st.metric("크레이터", f"{crater:.0f} km")
    with result_col3:
        st.metric("지진 규모", f"{magnitude:.1f}")
    
    # Canvas 애니메이션 (Python matplotlib 사용)
    st.subheader("🌏 충돌 시뮬레이션 애니메이션")
    
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='#1a1f3a')
    ax.set_facecolor('#1a1a2e')
    
    # 유카탄반도 표현
    center_x, center_y = 0.5, 0.5
    
    # 배경
    circle_bg = plt.Circle((center_x, center_y), 0.3, color='#2d5a3d', alpha=0.4)
    ax.add_patch(circle_bg)
    circle_border = plt.Circle((center_x, center_y), 0.3, fill=False, 
                               edgecolor='#64d4a0', linewidth=2, alpha=0.6)
    ax.add_patch(circle_border)
    
    # 충격파 표현 (여러 원)
    colors_shock = ['#ff9500', '#ff6b00', '#ff4500']
    for i, color in enumerate(colors_shock):
        r = 0.1 + i * 0.08
        circle_shock = plt.Circle((center_x, center_y), r, fill=False,
                                 edgecolor=color, linewidth=3, alpha=0.8)
        ax.add_patch(circle_shock)
    
    # 중심 운석
    circle_meteor = plt.Circle((center_x, center_y), 0.03, color='#ff6b00', alpha=0.9)
    ax.add_patch(circle_meteor)
    
    # 텍스트
    ax.text(center_x, 0.95, '☄️ 충돌 완료!', ha='center', fontsize=20, 
            color='#ffd700', fontweight='bold')
    ax.text(center_x, 0.15, f'직경: {diameter:.1f} km | 속도: {velocity:.1f} km/s | 각도: {angle}°',
            ha='center', fontsize=11, color='#e0e6ff')
    ax.text(center_x, 0.05, 'Yucatan Peninsula', ha='center', fontsize=10, 
            color='#a0adc7', style='italic')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.axis('off')
    
    st.pyplot(fig)
    
    # 기온 변화 그래프
    st.subheader("🌡️ 지구 평균 기온 변화 (Impact Winter)")
    
    months = np.arange(0, 37)
    temp_drop = min(50, 5 + energy / 2)
    recovery_time = min(36, 6 + energy / 10)
    
    temperatures = []
    for m in months:
        if m <= 6:
            temp = 15 - (temp_drop * (m / 6))
        elif m <= recovery_time:
            temp = 15 - temp_drop + (temp_drop * ((m - 6) / (recovery_time - 6)))
        else:
            temp = 15
        temperatures.append(temp)
    
    fig_temp, ax_temp = plt.subplots(figsize=(10, 5))
    ax_temp.fill_between(months, temperatures, alpha=0.3, color='#ff6b35')
    ax_temp.plot(months, temperatures, color='#ff6b35', linewidth=3, label='지구 평균 기온')
    ax_temp.axhline(15, color='gray', linestyle=':', alpha=0.5, label='정상 기온')
    ax_temp.set_xlabel('경과 시간 (개월)', fontsize=12)
    ax_temp.set_ylabel('기온 (°C)', fontsize=12)
    ax_temp.set_title('충돌 후 3년간 기온 변화', fontsize=14, fontweight='bold')
    ax_temp.grid(True, alpha=0.3)
    ax_temp.legend()
    
    st.pyplot(fig_temp)
    
    # 생물 생존율 그래프
    st.subheader("🦕 생물 종 생존율 변화")
    
    extinction_rate = min(0.95, (energy / 100) * 0.95)
    survival_rate = 1 - extinction_rate
    
    plant_survival = []
    herbivore_survival = []
    carnivore_survival = []
    
    for m in months:
        # 식물
        if m <= 12:
            plant = 100 * (survival_rate ** (m / 6))
        else:
            plant = 100 * survival_rate + (100 - 100 * survival_rate) * ((m - 12) / 24)
        plant_survival.append(max(0, plant))
        
        # 초식동물
        herbivore = 100 * survival_rate
        if m <= 24:
            herbivore = herbivore * max(0.1, 1 - (m / 24))
        else:
            herbivore = herbivore * max(0.1, 1 - (m / 24)) * (1 + (m - 24) / 12 * 0.5)
        herbivore_survival.append(max(0, herbivore))
        
        # 육식동물
        carnivore = 100 * survival_rate
        if m <= 36:
            carnivore = carnivore * max(0.05, 1 - (m / 20))
        carnivore_survival.append(max(0, carnivore))
    
    fig_surv, ax_surv = plt.subplots(figsize=(10, 5))
    ax_surv.plot(months, plant_survival, label='식물 (Plant)', color='#00d4ff', linewidth=2.5)
    ax_surv.plot(months, herbivore_survival, label='초식동물 (Herbivore)', 
                color='#ffd700', linewidth=2.5)
    ax_surv.plot(months, carnivore_survival, label='육식동물 (Carnivore)', 
                color='#ff6b35', linewidth=2.5)
    ax_surv.axhline(100, color='gray', linestyle=':', alpha=0.5)
    ax_surv.set_xlabel('경과 시간 (개월)', fontsize=12)
    ax_surv.set_ylabel('생존율 (%)', fontsize=12)
    ax_surv.set_title('충돌 후 먹이사슬 붕괴', fontsize=14, fontweight='bold')
    ax_surv.set_ylim(0, 110)
    ax_surv.grid(True, alpha=0.3)
    ax_surv.legend()
    
    st.pyplot(fig_surv)
    
    # 상세 리포트
    st.subheader("📋 상세 분석 리포트")
    
    report_col1, report_col2 = st.columns(2)
    
    with report_col1:
        st.info(f"""
        **지진 규모: {magnitude:.1f}**
        
        이는 역사상 가장 큰 지진(칠레 1960년 9.5규모)의 약 {(10 ** (magnitude - 9.5) * 100):.0f}배 규모입니다.
        """)
    
    with report_col2:
        atmosphere_temp = min(6000, 1500 + velocity * 150)
        st.warning(f"""
        **대기권 진입 온도: {atmosphere_temp:.0f} K**
        
        운석이 대기권에 진입할 때 마찰열로 극도의 열을 발생시킵니다.
        """)
    
    # 멸종 시나리오
    if energy > 30:
        st.error(f"""
        ### ⚠️ 대규모 멸종 발생!
        
        이 충돌 에너지({energy:.1f} Mt)는 지구 생태계에 치명적입니다.
        
        **충격 겨울(Impact Winter)** 메커니즘:
        1. 운석 충돌 → 엄청난 에너지 방출
        2. 먼지 + 화산재 + 황산염 에어로졸이 대기를 덮음
        3. 태양빛 차단 → 일조량 급감
        4. 지표면 기온 급락 (수십 도 하강)
        5. 광합성 중단 → 먹이사슬 붕괴
        6. 식물 → 초식동물 → 육식동물 순서로 멸종
        
        **결과**: 지구 생물의 75% 이상이 멸종 (실제 K-Pg 대멸종과 일치)
        """)
    elif energy > 10:
        st.warning(f"""
        ### ⚠️ 심각한 환경 재해 발생
        
        이 충돌 에너지({energy:.1f} Mt)로 지역 기반의 대규모 재해와 기후 변화가 발생합니다.
        생물 종 다양성이 크게 감소합니다.
        """)
    else:
        st.success(f"""
        ### ✓ 국지적 재해
        
        이 충돌 에너지({energy:.1f} Mt)는 충돌 지역과 인접 지역에 심각한 피해를 입히지만,
        전 지구적 멸종 규모로 발전하지는 않습니다.
        """)
    
    # 네비게이션
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    
    with nav_col1:
        if st.button("← 메뉴로 돌아가기", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
    
    with nav_col2:
        if st.button("🔄 다시 입력하기", use_container_width=True):
            st.session_state.page = 'impact_sim'
            st.rerun()
    
    with nav_col3:
        if st.button("🔬 ABM 시뮬레이션도 보기", use_container_width=True):
            st.session_state.page = 'abm_sim'
            st.rerun()

# ============================================================================
# 페이지 4: ABM 시뮬레이션 (생태계)
# ============================================================================
def page_abm_simulation():
    """생태계 시뮬레이션 (기존 dashboard.py 기능)"""
    
    col_nav, col_space = st.columns([1, 9])
    with col_nav:
        if st.button("← 메뉴로"):
            st.session_state.page = 'home'
            st.rerun()
    
    st.markdown("""
    <style>
    .title-sub {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #0099ff;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="title-sub">🔬 에이전트 기반 생태계 시뮬레이션 (ABM)</div>', 
                unsafe_allow_html=True)
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 시뮬레이션 설정")
        
        total_steps = st.slider(
            "총 시뮬레이션 길이 (step)",
            min_value=30, max_value=150, value=TOTAL_STEPS, step=10
        )
        
        impact_step = st.slider(
            "운석 충돌 시점 (step)",
            min_value=5, max_value=30, value=IMPACT_STEP, step=1
        )
        
        st.markdown("---")
        st.subheader("초기 개체수")
        
        fern_pop = st.number_input("🌿 양치식물", min_value=1000, value=10000, step=1000)
        triceratops_pop = st.number_input("🦖 트리케라톱스", min_value=100, value=1200, step=100)
        trex_pop = st.number_input("🦕 티라노사우루스", min_value=50, value=400, step=50)
        mammal_pop = st.number_input("🐭 쥐형 포유류", min_value=500, value=2500, step=500)
        crocodile_pop = st.number_input("🐊 악어", min_value=100, value=600, step=100)
    
    # 실행 버튼
    col1, col2 = st.columns(2)
    
    with col1:
        run_button = st.button("🚀 시뮬레이션 실행", use_container_width=True, type="primary")
    
    with col2:
        reset_button = st.button("🔄 초기화", use_container_width=True)
    
    # 시뮬레이션 함수
    def run_abm_simulation():
        """ABM 시뮬레이션 실행"""
        env = Environment(impact_step=impact_step)
        
        # 종 생성
        fern = Plant("양치식물", population=fern_pop, body_size=1,
                    habitat="surface", growth_rate=0.15, color="#2e7d32",
                    refuge=int(fern_pop * 0.03))
        
        triceratops = Herbivore("트리케라톱스", population=triceratops_pop, body_size=8,
                               habitat="surface", growth_rate=0.06, color="#ef6c00",
                               food_sources=[fern])
        
        trex = Carnivore("티라노사우루스", population=trex_pop, body_size=9,
                        habitat="surface", growth_rate=0.04, color="#c62828",
                        food_sources=[triceratops])
        
        mammal = Scavenger("쥐형 포유류", population=mammal_pop, body_size=1,
                          habitat="underground", growth_rate=0.10, color="#6a1b9a",
                          capacity=int(mammal_pop * 3))
        
        crocodile = Carnivore("악어", population=crocodile_pop, body_size=5,
                             habitat="aquatic", growth_rate=0.04, color="#1565c0",
                             food_sources=[mammal], capacity=int(crocodile_pop * 3))
        
        world = World(env, [fern, triceratops, trex, mammal, crocodile])
        
        # 진행 바
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for step in range(1, total_steps + 1):
            world.step()
            progress = step / total_steps
            progress_bar.progress(progress)
            status_text.text(f"진행 중... {step}/{total_steps} step")
        
        progress_bar.empty()
        status_text.empty()
        
        return world
    
    # 결과 표시 함수
    def display_abm_results(world):
        """ABM 시뮬레이션 결과 표시"""
        
        # 종별 생존 현황
        st.subheader("📊 종별 생존 현황")
        
        cols = st.columns(5)
        for idx, species in enumerate(world.species):
            with cols[idx]:
                if species.is_extinct:
                    status = "💀 멸종"
                    color = "#ff6b6b"
                else:
                    status = "✅ 생존"
                    color = "#51cf66"
                
                st.markdown(f"""
                <div style="background-color: {color}; padding: 15px; border-radius: 8px; text-align: center; color: white;">
                    <h4>{species.name}</h4>
                    <p style="font-size: 20px; font-weight: bold;">{species.population:,}</p>
                    <p>{status}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # 상세 결과 테이블
        st.subheader("📈 상세 결과")
        
        data = []
        for s in world.species:
            initial = s.history[0]
            final = s.population
            change = final - initial
            change_pct = (change / initial * 100) if initial > 0 else 0
            
            if s.is_extinct:
                status = f"💀 Time {s.extinction_step}"
            else:
                status = "✅ 생존"
            
            data.append({
                "종": s.name,
                "초기": f"{initial:,}",
                "최종": f"{final:,}",
                "변화": f"{change:+,} ({change_pct:+.1f}%)",
                "상태": status
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # 그래프
        st.subheader("🌡️ 환경 변화와 종별 생존율")
        
        steps = list(range(len(world.species[0].history)))
        
        fig, (ax_env, ax_pop) = plt.subplots(
            2, 1, figsize=(12, 8), sharex=True,
            gridspec_kw={"height_ratios": [1, 2]}
        )
        
        # 환경 변화
        ax_env.plot(steps, world.sunlight_history, color="#f9a825", linewidth=2.5, label="일조량")
        ax_env.set_ylabel("일조량 (%)", color="#f9a825", fontsize=11)
        ax_env.tick_params(axis="y", labelcolor="#f9a825")
        ax_env.set_title("환경 변화와 종별 생존율", fontsize=14, fontweight="bold")
        
        ax_temp = ax_env.twinx()
        ax_temp.plot(steps, world.temp_history, color="#0277bd", linewidth=2.5, label="기온")
        ax_temp.set_ylabel("기온 (°C)", color="#0277bd", fontsize=11)
        ax_temp.tick_params(axis="y", labelcolor="#0277bd")
        
        # 범례
        env_lines = ax_env.get_lines() + ax_temp.get_lines()
        ax_env.legend(env_lines, [ln.get_label() for ln in env_lines], loc="upper right")
        
        # 종별 생존율
        for s in world.species:
            survival = [h / s.history[0] * 100 for h in s.history]
            label = f"{s.name} ({s.population:,})"
            ax_pop.plot(steps, survival, label=label, color=s.color, linewidth=2.5)
        
        ax_pop.axhline(100, color="gray", linestyle=":", alpha=0.6)
        ax_pop.set_xlabel("시간 (Time-step)", fontsize=11)
        ax_pop.set_ylabel("초기 대비 개체수 (%)", fontsize=11)
        ax_pop.set_xlim(0, len(steps) - 1)
        ax_pop.legend(loc="upper left", fontsize=10)
        ax_pop.grid(True, alpha=0.3)
        
        # 운석 충돌 표시
        for ax in (ax_env, ax_pop):
            ax.axvline(world.env.impact_step, color="red", linestyle="--", linewidth=2, alpha=0.7)
        
        fig.tight_layout()
        st.pyplot(fig)
        
        # 통계
        st.subheader("📉 시뮬레이션 통계")
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        
        extinct_count = sum(1 for s in world.species if s.is_extinct)
        survive_count = len(world.species) - extinct_count
        
        with stat_col1:
            st.metric("생존한 종", f"{survive_count}/{len(world.species)}")
        
        with stat_col2:
            st.metric("멸종한 종", f"{extinct_count}/{len(world.species)}")
        
        with stat_col3:
            st.metric("최종 사체 풀", f"{int(world.carrion_pool):,}")
    
    # 버튼 이벤트
    if run_button:
        st.session_state.world = run_abm_simulation()
        st.success("✅ 시뮬레이션 완료!")
    
    if reset_button:
        st.session_state.world = None
        st.info("초기화되었습니다. 파라미터를 조정한 후 다시 실행해주세요.")
    
    # 결과 표시
    if st.session_state.world is not None:
        display_abm_results(st.session_state.world)
    else:
        st.info("⚠️ '시뮬레이션 실행' 버튼을 눌러 시작하세요.")

# ============================================================================
# 메인 라우터
# ============================================================================
if st.session_state.page == 'home':
    page_home()
elif st.session_state.page == 'impact_sim':
    page_impact_input()
elif st.session_state.page == 'impact_results':
    page_impact_results()
elif st.session_state.page == 'abm_sim':
    page_abm_simulation()

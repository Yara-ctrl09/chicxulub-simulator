# -*- coding: utf-8 -*-
"""
K-Pg 대멸종 시뮬레이션 대시보드
인터랙티브 웹 기반 대시보드로 시뮬레이션 결과를 실시간으로 확인합니다.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from kpg_simulation import (
    Environment, Plant, Herbivore, Carnivore, Scavenger, World,
    TOTAL_STEPS, IMPACT_STEP
)

# ============================================================================
# Streamlit 페이지 설정
# ============================================================================
st.set_page_config(
    page_title="K-Pg 대멸종 시뮬레이션",
    page_icon="☄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 제목 및 설명
# ============================================================================
st.title("☄️ K-Pg 대멸종 에이전트 기반 시뮬레이션")
st.markdown("""
유카탄 반도 운석 충돌(약 6,600만 년 전)로 인한 환경 급변을 
에이전트 기반 모델링(ABM)으로 시뮬레이션합니다.
""")

# ============================================================================
# 사이드바: 파라미터 조정
# ============================================================================
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
    st.subheader("초기 개체수 설정")
    
    fern_pop = st.number_input("양치식물", min_value=1000, value=10000, step=1000)
    triceratops_pop = st.number_input("트리케라톱스", min_value=100, value=1200, step=100)
    trex_pop = st.number_input("티라노사우루스", min_value=50, value=400, step=50)
    mammal_pop = st.number_input("쥐형 포유류", min_value=500, value=2500, step=500)
    crocodile_pop = st.number_input("악어", min_value=100, value=600, step=100)

# ============================================================================
# 시뮬레이션 실행 버튼
# ============================================================================
col1, col2 = st.columns(2)

with col1:
    run_button = st.button("🚀 시뮬레이션 실행", use_container_width=True)

with col2:
    reset_button = st.button("🔄 초기화", use_container_width=True)

# ============================================================================
# 시뮬레이션 함수
# ============================================================================
def run_simulation(total_steps, impact_step, 
                   fern_pop, triceratops_pop, trex_pop, mammal_pop, crocodile_pop):
    """주어진 파라미터로 시뮬레이션을 실행합니다."""
    env = Environment(impact_step=impact_step)
    
    # 생산자
    fern = Plant("양치식물", population=fern_pop, body_size=1,
                 habitat="surface", growth_rate=0.15, color="#2e7d32",
                 refuge=int(fern_pop * 0.03))
    
    # 1차 소비자
    triceratops = Herbivore("트리케라톱스", population=triceratops_pop, body_size=8,
                            habitat="surface", growth_rate=0.06, color="#ef6c00",
                            food_sources=[fern])
    
    # 2차 소비자 (최상위)
    trex = Carnivore("티라노사우루스", population=trex_pop, body_size=9,
                     habitat="surface", growth_rate=0.04, color="#c62828",
                     food_sources=[triceratops])
    
    # 부식성 종
    mammal = Scavenger("쥐형 포유류", population=mammal_pop, body_size=1,
                       habitat="underground", growth_rate=0.10, color="#6a1b9a",
                       capacity=int(mammal_pop * 3))
    
    # 중형 육식 — 수중 서식이라 한파 방어력이 높음
    crocodile = Carnivore("악어", population=crocodile_pop, body_size=5,
                          habitat="aquatic", growth_rate=0.04, color="#1565c0",
                          food_sources=[mammal], capacity=int(crocodile_pop * 3))
    
    world = World(env, [fern, triceratops, trex, mammal, crocodile])
    
    # 진행 바와 함께 시뮬레이션 실행
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

# ============================================================================
# 결과 출력 함수
# ============================================================================
def display_results(world):
    """시뮬레이션 결과를 대시보드에 표시합니다."""
    
    # 1. 종별 생존 현황
    st.header("📊 종별 생존 현황")
    
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
            <div style="background-color: {color}; padding: 15px; border-radius: 8px; text-align: center;">
                <h4>{species.name}</h4>
                <p style="font-size: 24px; font-weight: bold;">{species.population:,}</p>
                <p style="font-size: 12px;">{status}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # 2. 상세 결과 테이블
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
            "초기 개체수": f"{initial:,}",
            "최종 개체수": f"{final:,}",
            "변화": f"{change:+,} ({change_pct:+.1f}%)",
            "상태": status
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    
    # 3. 환경 변화 그래프
    st.subheader("🌡️ 환경 변화")
    
    steps = list(range(len(world.species[0].history)))
    
    fig, (ax_env, ax_pop) = plt.subplots(
        2, 1, figsize=(12, 8), sharex=True,
        gridspec_kw={"height_ratios": [1, 2]}
    )
    
    # 환경 변화
    ax_env.plot(steps, world.sunlight_history, color="#f9a825",
                linewidth=2, label="일조량")
    ax_env.set_ylabel("일조량 (%)", color="#f9a825")
    ax_env.tick_params(axis="y", labelcolor="#f9a825")
    ax_env.set_title("환경 변화와 종별 생존율", fontsize=14, fontweight="bold")
    
    ax_temp = ax_env.twinx()
    ax_temp.plot(steps, world.temp_history, color="#0277bd",
                 linewidth=2, label="기온")
    ax_temp.set_ylabel("기온 (°C)", color="#0277bd")
    ax_temp.tick_params(axis="y", labelcolor="#0277bd")
    
    # 범례 통합
    env_lines = ax_env.get_lines() + ax_temp.get_lines()
    ax_env.legend(env_lines, [ln.get_label() for ln in env_lines],
                  loc="center right")
    
    # 종별 생존율
    for s in world.species:
        survival = [h / s.history[0] * 100 for h in s.history]
        label = f"{s.name} (최종 {s.population:,})"
        ax_pop.plot(steps, survival, label=label, color=s.color, linewidth=2.2)
    
    ax_pop.axhline(100, color="gray", linestyle=":", alpha=0.6)
    ax_pop.set_xlabel("시간 (Time-step)")
    ax_pop.set_ylabel("초기 대비 개체수 (%)")
    ax_pop.set_xlim(0, len(steps) - 1)
    ax_pop.legend(loc="upper left", fontsize=9)
    ax_pop.grid(True, alpha=0.3)
    
    # 운석 충돌 표시
    for ax in (ax_env, ax_pop):
        ax.axvline(world.env.impact_step, color="red", linestyle="--", alpha=0.7)
    ax_pop.text(world.env.impact_step + 0.5, ax_pop.get_ylim()[1] * 0.5,
                "운석 충돌", color="red", fontweight="bold",
                rotation=90, va="center", fontsize=10)
    
    fig.tight_layout()
    st.pyplot(fig)
    
    # 4. 통계 정보
    st.subheader("📉 시뮬레이션 통계")
    
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    extinct_count = sum(1 for s in world.species if s.is_extinct)
    survive_count = len(world.species) - extinct_count
    
    with stat_col1:
        st.metric("생존한 종", f"{survive_count}/{len(world.species)}")
    
    with stat_col2:
        st.metric("멸종한 종", f"{extinct_count}/{len(world.species)}")
    
    with stat_col3:
        peak_carrion = max(world.carrion_pool for _ in range(1))  # 임시
        st.metric("최종 사체 풀", f"{int(world.carrion_pool):,}")

# ============================================================================
# 메인 로직
# ============================================================================
if run_button:
    st.session_state.simulation_run = True
    st.session_state.world = run_simulation(
        total_steps, impact_step,
        fern_pop, triceratops_pop, trex_pop, mammal_pop, crocodile_pop
    )
    st.success("✅ 시뮬레이션 완료!")

if reset_button:
    st.session_state.simulation_run = False
    st.info("초기화되었습니다. 파라미터를 조정한 후 다시 실행해주세요.")

# 결과 표시
if "simulation_run" in st.session_state and st.session_state.simulation_run:
    display_results(st.session_state.world)
else:
    st.info("⚠️ '시뮬레이션 실행' 버튼을 눌러 시작하세요.")

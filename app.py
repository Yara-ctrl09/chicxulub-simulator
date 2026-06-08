import streamlit as st
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

# =========================================================================
# 🐍 [BACKEND] K-Pg 대멸종 에이전트 기반 모델링 (ABM) 엔진 구조
# =========================================================================

class Species(ABC):
    def __init__(self, count, growth_rate, death_rate):
        self._count = count  
        self.growth_rate = growth_rate
        self.death_rate = death_rate
        self.next_count = count 

    @property
    def count(self):
        return max(0.0, self._count)

    @count.setter
    def count(self, value):
        self._count = max(0.0, value)

    @abstractmethod
    def update_next_phase(self, current_env, other_species):
        pass

    def apply_phase_update(self):
        self._count = self.next_count


class Plant(Species):
    def update_next_phase(self, current_env, other_species):
        sunlight_factor = max(0.05, (current_env['temp'] / 25.0) * (1.0 - current_env['soot_block']))
        acid_damage = max(0.1, (7.0 - current_env['acid_rain_ph']) * 0.2)
        
        carrying_capacity = max(100.0, 5000.0 * sunlight_factor * (1.0 - acid_damage))
        
        births = self.growth_rate * self.count * (1.0 - (self.count / carrying_capacity))
        deaths = self.death_rate * self.count * (1.0 + acid_damage)
        eaten = 0.06 * other_species['herbivores'].count
        
        self.next_count = self.count + births - deaths - eaten


class Herbivore(Species):
    def update_next_phase(self, current_env, other_species):
        plant_food = other_species['plants'].count
        starvation_factor = 1.0 if plant_food > self.count else (plant_food / (self.count + 1e-5))
        tsunami_damage = 0.2 if current_env['step'] == 1 and current_env['tsunami'] > 100 else 0.0
        
        births = self.growth_rate * self.count * starvation_factor
        deaths = self.death_rate * self.count * (1.5 - starvation_factor) + (self.count * tsunami_damage)
        predated = 0.08 * other_species['carnivores'].count
        
        self.next_count = self.count + births - deaths - predated


class Carnivore(Species):
    def update_next_phase(self, current_env, other_species):
        prey = other_species['herbivores'].count
        starvation_factor = 1.0 if prey > self.count else (prey / (self.count + 1e-5))
        
        births = self.growth_rate * self.count * starvation_factor
        deaths = self.death_rate * self.count * (2.2 - starvation_factor)
        
        self.next_count = self.count + births - deaths


class AdvancedEcosystemSimulation:
    def __init__(self, size, v, soot, sulfur, ph, tsunami, is_extinction_level):
        self.size = size
        self.v = v
        self.soot_input = soot
        self.sulfur_input = sulfur
        self.ph_input = ph
        self.tsunami_input = tsunami
        self.is_extinction_level = is_extinction_level # 임계점 돌파 여부
        
        self.species = {
            'plants': Plant(count=2500.0, growth_rate=0.45, death_rate=0.08),
            'herbivores': Herbivore(count=200.0, growth_rate=0.22, death_rate=0.09),
            'carnivores': Carnivore(count=60.0, growth_rate=0.12, death_rate=0.07)
        }
        self.env = {'temp': 25.0, 'soot_block': 0.0, 'acid_rain_ph': 7.0, 'tsunami': 0.0, 'step': 0}

    def run_simulation(self, steps=60):
        history = []
        for step in range(steps):
            self.env['step'] = step
            
            if step < 5:
                self.env['temp'] = 25.0
                self.env['soot_block'] = 0.0
                self.env['acid_rain_ph'] = 7.0
                self.env['tsunami'] = 0.0
            else:
                t = step - 5
                
                # 임계점 돌파 여부에 따른 기후 하강 폭의 수학적 스케일링 변조
                if self.is_extinction_level:
                    temp_drop = (15.0 * (self.size / 10.0) * (self.sulfur_input / 100.0)) + (5.0 * (self.soot_input / 100.0))
                    self.env['soot_block'] = (self.soot_input / 100.0) * np.exp(-t / 12)
                    self.env['acid_rain_ph'] = self.ph_input if t < 24 else 7.0 - (7.0 - self.ph_input) * np.exp(-(t-24)/10)
                else:
                    # 임계점 미달 시 성층권 돌파 실패 모델링 (피해 최소화)
                    temp_drop = 3.0 * (self.size / 3.0) 
                    self.env['soot_block'] = (self.soot_input / 100.0) * 0.1 * np.exp(-t / 3)
                    self.env['acid_rain_ph'] = max(5.6, self.ph_input) # 정상 범주의 빗물 산도 보존
                
                self.env['temp'] = 25.0 - (temp_drop * (t / (t + 2)) * np.exp(-t / 20))
                self.env['tsunami'] = self.tsunami_input if t == 0 else 0.0
            
            for sp in self.species.values():
                sp.update_next_phase(self.env, self.species)
            for sp in self.species.values():
                sp.apply_phase_update()
                
            history.append({
                "세대(Step)": step,
                "백악기 식물군": self.species['plants'].count,
                "초식 공룡": self.species['herbivores'].count,
                "육식 공룡": self.species['carnivores'].count,
                "지구 평균 기온(°C)": self.env['temp'],
                "대기 햇빛 차단율(%)": self.env['soot_block'] * 100
            })
        return history

# =========================================================================
# 🚀 [FRONTEND] Streamlit 대시보드 UI 및 시각화 파트
# =========================================================================

st.set_page_config(page_title="통합 K-Pg 대멸종 ABM 시뮬레이터", layout="wide")

st.title("☄️ K-Pg 대멸종 통합 시뮬레이션 시스템 (Advanced ABM)")
st.markdown("""
이 프로그램은 **소행성 충돌의 기초 물리 공식**과 지구생물의 75% 이상을 도멸시키는 **과학적 에너지 임계점(2,400,000 Mt)**을 연동한 시뮬레이터입니다.
""")
st.divider()

# 사이드바 매개변수
st.sidebar.header("🛸 1. 기본 소행성 제어")
d_val = st.sidebar.slider("소행성 직경 (km)", 1.0, 30.0, 10.0, step=0.5)
v_val = st.sidebar.slider("충돌 속도 (km/s)", 11.0, 40.0, 20.0, step=1.0)
a_val = st.sidebar.slider("충돌 각도 (도)", 30, 90, 60, step=5)

st.sidebar.markdown("---")

st.sidebar.header("🔬 2. 대멸종 환경 상세 변수 설정")
with st.sidebar.expander("🛠️ 세부 환경 변수 직접 튜닝", expanded=True):
    soot_val = st.slider("대기 그을음/미세먼지 방출량 (%)", 0, 100, 85)
    sulfur_val = st.slider("성층권 황산염 가스 주입량 (%)", 0, 100, 90)
    ph_val = st.slider("초기 산성비 산도 (pH)", 1.0, 7.0, 3.8, step=0.1)
    tsunami_val = st.slider("초기 메가 쓰나미 높이 (m)", 0, 500, 300, step=50)

st.sidebar.markdown("---")
run_engine = st.sidebar.button("💥 시뮬레이션 엔진 가동 (Run Engine)", type="primary", use_container_width=True)

# 📐 [물리 에너지 연산]
radius_meters = (d_val * 1000) / 2
v_meters_second = v_val * 1000
asteroid_mass = (4/3) * np.pi * (radius_meters ** 3) * 3000
energy_j = 0.5 * asteroid_mass * (v_meters_second ** 2)
energy_megaton = energy_j / (4.184 * (10**15))

crater_dia = 1.2 * (energy_megaton ** (1/3.4)) * np.cos(np.radians(90 - a_val))
earthquake_m = 0.67 * np.log10(energy_j) - 5.87

# 🚨 과학적 대멸종 에너지 임계점 정의 (TNT 2,400,000 메가톤)
EXTINCTION_THRESHOLD_MT = 2400000
is_extinction_level = energy_megaton >= EXTINCTION_THRESHOLD_MT

if run_engine:
    st.subheader("🌋 1단계 결과: 충돌 물리학 장비 계측 데이터")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("TNT 폭발 에너지", f"{energy_megaton:,.0f} Mt", f"히로시마 원폭 {int(energy_megaton/15):,}배")
    m2.metric("최종 크레이터 지름", f"{crater_dia:.1f} km")
    m3.metric("리히터 규모 지진", f"{earthquake_m:.1f} M")
    
    # 임계점 돌파 여부에 따른 경보 문구 레이아웃 변동
    if is_extinction_level:
        st.error(f"🚨 **[위험] 에너지 임계점 돌파:** 충돌 에너지가 대멸종 하한선({EXTINCTION_THRESHOLD_MT:,.0f} Mt)을 초과했습니다. 성층권 변조 공정이 시작됩니다.")
    else:
        st.success(f"✅ **[안전] 에너지 임계점 미달:** 충돌 에너지가 대멸종 하한선({EXTINCTION_THRESHOLD_MT:,.0f} Mt)보다 낮습니다. 분출물이 성층권에 도달하지 못합니다.")
        
    st.divider()
    
    # ABM 가동
    sim_instance = AdvancedEcosystemSimulation(d_val, v_val, soot_val, sulfur_val, ph_val, tsunami_val, is_extinction_level)
    simulation_data = sim_instance.run_simulation(steps=60)
    df_result = pd.DataFrame(simulation_data)
    
    st.subheader("📉 2단계 결과: 생태계 에이전트 상호작용 및 기후 그래프")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("##### 🦖 먹이사슬 에이전트 개체수 변동 추이")
        st.line_chart(df_result.set_index("세대(Step)")[["백악기 식물군", "초식 공룡", "육식 공룡"]])
    with g2:
        st.markdown("##### ❄️ 지구 환경 변수 변화 트렌드")
        st.line_chart(df_result.set_index("세대(Step)")[["지구 평균 기온(°C)", "대기 햇빛 차단율(%)"]])
        
    st.divider()
    
    # 📝 3단계 결과: 데이터 기반 자동 그래프 해석 리포트
    st.subheader("📝 3단계 결과: 데이터 기반 자동 그래프 해석 리포트")
    
    min_temp = df_result["지구 평균 기온(°C)"].min()
    max_soot = df_result["대기 햇빛 차단율(%)"].max()
    
    herb_extinct_step = df_result[df_result["초식 공룡"] <= 5.0]["세대(Step)"]
    carn_extinct_step = df_result[df_result["육식 공룡"] <= 5.0]["세대(Step)"]
    
    herb_extinct_time = f"약 {herb_extinct_step.iloc[0]}세대" if not herb_extinct_step.empty else "안정세 유지"
    carn_extinct_time = f"약 {carn_extinct_step.iloc[0]}세대" if not carn_extinct_step.empty else "안정세 유지"

    if is_extinction_level:
        st.error("### 🔴 데이터 해석 결과: 전 지구적 대멸종 확정 (75% 이상 절멸)")
    else:
        st.success("### 🟢 데이터 해석 결과: 국지적 피해 및 백악기 생태계 보존")

    tab1, tab2, tab3 = st.tabs(["❄️ 기온 및 햇빛 차트 해석", "🦖 먹이사슬 도미노 해석", "🔬 지구과학 탐구 결론"])
    
    with tab1:
        if is_extinction_level:
            st.markdown(f"""
            ##### 📈 '지구 평균 기온'과 '햇빛 차단율' 그래프를 읽어봅시다!
            - **성층권 오염 및 암흑기 도달 ({max_soot:.1f}%):** 충돌 에너지가 임계점({EXTINCTION_THRESHOLD_MT:,.0f} Mt)을 넘으면서 무수한 파편이 성층권까지 도달했습니다. 햇빛 차단율이 최고 **{max_soot:.1f}%**까지 치솟아 전 지구가 밤처럼 어두워졌습니다.
            - **충격 겨울의 절정 (최저 기온 {min_temp:.1f}°C):** 햇빛이 반사되면서 백악기 평균 기온(25°C)이 무려 **{min_temp:.1f}°C**까지 곤두박질쳤습니다. 교과서에 나오는 **'충격 겨울(Impact Winter)'** 현상이 완벽하게 시각화되었습니다.
            """)
        else:
            st.markdown(f"""
            ##### 📈 '지구 평균 기온'과 '햇빛 차단율' 그래프를 읽어봅시다!
            - **대류권 내 먼지 침강 ({max_soot:.1f}% 미미한 차단):** 충돌 에너지가 대멸종 하한선에 미치지 못해, 먼지와 가스가 성층권을 뚫지 못하고 대류권 내에서 비에 씻겨 빠르게 내려앉았습니다. 햇빛 차단율은 잠시 상승했다가 곧바로 안정화됩니다.
            - **안정적인 기온 유지 (최저 기온 {min_temp:.1f}°C):** 기온이 일시적으로 소폭 하강했으나 가혹한 한랭화로 이어지지 않아, 백악기 본래의 따뜻한 아열대 기후 환경을 안전하게 유지하고 있습니다.
            """)
        
    with tab2:
        if is_extinction_level:
            st.markdown(f"""
            ##### 📉 '식물 ➡️ 초식 ➡️ 육식' 개체수 곡선의 시간차(도미노) 현상 해석
            - **식물의 급락과 연쇄 멸종:** 햇빛 가림막 때문에 식물 그래프가 수직 하강했으며, 이를 먹는 초식 공룡의 멸종 시점이 **{herb_extinct_time}** 부근에서 검출되었습니다.
            - **최상위 포식자의 붕괴:** 연쇄 멸종 메커니즘에 의해 육식 공룡 역시 **{carn_extinct_time}** 시점에 절멸 위험군에 도달했습니다. 생태계의 기초(생산자)가 무너지면 생물종의 75% 이상이 파멸한다는 사실이 증명됩니다.
            """)
        else:
            st.markdown(f"""
            ##### 📉 '식물 ➡️ 초식 ➡️ 육식' 개체수 곡선의 시간차(도미노) 현상 해석
            - **포식-피식 관계의 항상성 유지:** 초기 쓰나미({tsunami_val}m) 타격으로 인해 일시적인 개체수 동요가 그래프에 기록되었습니다.
            - **생태계 복원력:** 하지만 먹이(식물)가 풍부하게 유지되므로 초식 공룡과 육식 공룡 모두 멸종 위험 시점({herb_extinct_time} / {carn_extinct_time})을 겪지 않고, 자연스러운 생태계 평형 상태(항상성)로 되돌아가는 양상이 뚜렷하게 관찰됩니다.
            """)
        
    with tab3:
        st.markdown(f"""
        ##### 🎓 이 시뮬레이션이 주는 최종 과학적 메시지
        - 지구 생물종의 75% 이상이 절멸하기 위해서는 단순히 충돌 지점 근처가 파괴되는 것을 넘어, **지구 전체 기후 순환계를 변조시키는 최소 에너지 임계점($10^{21}\sim10^{22} \text{{ J}}$)**을 넘어야 함을 본 데이터 분석을 통해 알 수 있습니다.
        - **탐구 팁:** 직경 슬라이더를 **4.5km ~ 5.5km** 사이로 세밀하게 조절해 보세요. 에너지가 240만 메가톤 경계선을 넘나들며 그래프 추세선이 **'대멸종(Red)'**과 **'보존(Green)'**으로 다이내믹하게 바뀌는 임계점 분기 현상을 직접 포트폴리오에 인용할 수 있습니다.
        """)
else:
    st.info("👈 왼쪽 사이드바에서 소행성 스펙을 조절하여 충돌 에너지가 240만 메가톤(대멸종 임계점)을 넘는지 확인해 보며 엔진을 가동해 보세요!")

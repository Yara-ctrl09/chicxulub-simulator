# -*- coding: utf-8 -*-
"""
K-Pg 대멸종 에이전트 기반 시뮬레이션 (Agent-Based Modeling, ABM)
================================================================

이 모듈은 무엇을 하는가:
    유카탄 반도 운석 충돌(약 6,600만 년 전)로 인한 환경 급변을, 각 생물 종을
    '객체(Agent)'로 모델링하여 시간에 따른 개체수 변화를 시뮬레이션한다.
    환경(Environment) · 생물(Species 계층) · 진행 엔진(World)을 분리해
    객체 지향(OOP)의 상속·다형성·캡슐화를 보여준다.

이 모듈은 무엇을 하지 않는가:
    실제 고생물학 데이터를 적합(fitting)하지 않는다. 파라미터는 K-Pg 멸종의
    '정성적 패턴'(대형 종 멸종, 소형 부식성 종 생존, 양치식물 회복)을
    재현하도록 교육 목적으로 조정한 값이다.

작성 의도: 컴퓨터 공학과 진학을 위한 학생부 세특용 프로젝트.
"""

from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Windows 기본 콘솔(cp949)은 이모지(☄️ 💀 등)를 출력하지 못해 오류를 낸다.
# 표준 출력을 UTF-8로 전환해 어느 환경에서도 안전하게 실행되도록 한다.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================================
#  시뮬레이션 전역 설정
# ============================================================================
TOTAL_STEPS = 80     # 총 시뮬레이션 길이 (Time-step)
IMPACT_STEP = 15     # 운석이 충돌하는 시점 (이 전까지는 안정 상태)


# ============================================================================
#  1. Environment — 지구의 '환경 상태'만 책임지는 클래스
# ============================================================================
class Environment:
    """시간 흐름에 따른 일조량·기온과 운석 충돌 이벤트를 관리한다.

    이 클래스는 '환경'만 다룬다. 생물의 생사 판정은 Species의 책임이다.
    (책임 분리 = 단일 책임 원칙, SRP)
    """

    def __init__(self, impact_step: int = IMPACT_STEP):
        self.time_step = 0
        self.sunlight = 100.0       # 일조량 (%) — 광합성의 원천
        self.temperature = 25.0     # 전 지구 평균 기온 (°C)
        self.impact_step = impact_step
        self.impacted = False       # 충돌이 이미 발생했는가

    def update(self) -> None:
        """매 Time-step마다 호출되어 환경을 한 단계 갱신한다."""
        self.time_step += 1

        if self.time_step == self.impact_step:
            # ── 운석 충돌: 먼지 구름이 햇빛을 차단 → '충돌 겨울'(Impact Winter)
            self.sunlight = 5.0
            self.temperature = -10.0
            self.impacted = True
            print(f"\n  [Time {self.time_step}] "
                  f"☄️  운석 충돌! 먼지 구름이 하늘을 뒤덮습니다.\n")

        elif self.impacted:
            # ── 충돌 이후: 먼지가 가라앉으며 환경이 '서서히' 회복
            #    (급락은 한순간, 회복은 수십 step에 걸쳐 점진적으로)
            self.sunlight = min(100.0, self.sunlight + 2.8)
            self.temperature = min(25.0, self.temperature + 1.0)


# ============================================================================
#  2. Species — 모든 생물의 '부모 클래스' (추상 클래스)
# ============================================================================
class Species(ABC):
    """모든 생물 종이 공유하는 속성과 공통 생존 로직을 담은 부모 클래스.

    ABC(추상 클래스)로 선언했으므로 Species 자체로는 객체를 만들 수 없고,
    반드시 Plant/Herbivore/Carnivore/Scavenger 중 하나로 만들어야 한다.
    → '식성 없는 생물'이라는 말이 안 되는 객체 생성을 코드 차원에서 차단.
    """

    def __init__(self, name: str, population: int, body_size: int,
                 habitat: str, growth_rate: float, color: str,
                 capacity: int | None = None, refuge: int = 0):
        self.name = name
        self.initial_population = population
        self.population = population
        self.body_size = body_size          # 1(소형) ~ 10(거대)
        self.habitat = habitat              # 'surface' | 'underground' | 'aquatic'
        self.growth_rate = growth_rate      # 환경이 양호할 때의 번식률
        self.color = color                  # 그래프에서 쓸 고유 색상
        self.capacity = capacity if capacity is not None else population
        self.refuge = refuge                # 최소 생존 개체수(피난처/씨앗은행)
        self.is_extinct = False
        self.extinction_step: int | None = None
        self.history: list[int] = [population]   # step별 개체수 기록
        self._pending = population               # '다음 개체수' 임시 저장칸

    # ------------------------------------------------------------------
    #  공통 로직 ① — 서식지에 따른 기온 페널티 (모든 종이 동일하게 사용)
    # ------------------------------------------------------------------
    def _climate_penalty(self, env: Environment) -> float:
        """추위로 인한 생존율 감소분을 반환한다.

        지하/수중 서식 종은 외부 온도 변화가 훨씬 덜 전달되므로 페널티를
        크게 감쇄(shield)받는다 — 실제로 K-Pg 때 굴을 파거나 물속에 사는
        동물의 생존율이 높았던 이유.
        """
        shield = 0.12 if self.habitat in ("underground", "aquatic") else 1.0

        if env.temperature < 0:
            return 0.20 * shield        # 영하: 치명적인 한파
        elif env.temperature < 12:
            return 0.08 * shield        # 저온: 만성적 스트레스
        return 0.0                      # 온화: 페널티 없음

    # ------------------------------------------------------------------
    #  공통 로직 ② — 몸집에 따른 아사(餓死) 페널티
    # ------------------------------------------------------------------
    def _body_size_penalty(self, scarcity: float) -> float:
        """식량이 부족(scarcity 0~1)할수록, 몸집이 클수록 커지는 페널티.

        대형 동물은 유지 대사량이 커서 같은 기근에도 먼저 굶어 죽는다.
        → 티라노사우루스·트리케라톱스 같은 거대 공룡이 멸종한 핵심 원인.
        """
        if scarcity <= 0:
            return 0.0
        # 몸집 4 이하의 소형 종은 페널티 면제, 그 이상은 선형 증가
        return max(0, self.body_size - 4) * 0.03 * scarcity

    # ------------------------------------------------------------------
    #  공통 로직 ③ — 먹이 가용량 → 굶주림 곡선 (Herbivore/Carnivore 공용)
    # ------------------------------------------------------------------
    def _trophic_response(self, available: int, baseline: int) -> tuple[float, float]:
        """먹이의 현재 총량(available)을 평소 총량(baseline)과 비교해
        (식량부족도 scarcity, 직접 생존 페널티)를 반환한다.
        """
        ratio = available / baseline if baseline > 0 else 0.0
        scarcity = min(1.0, max(0.0, 1.0 - ratio / 0.6))

        if ratio < 0.15:
            penalty = 0.22      # 먹이 거의 소멸
        elif ratio < 0.40:
            penalty = 0.12      # 심각한 부족
        elif ratio < 0.70:
            penalty = 0.04      # 가벼운 부족
        else:
            penalty = 0.0       # 충분
        return scarcity, penalty

    # ------------------------------------------------------------------
    #  추상 메서드(다형성 훅) — 자식 클래스가 '반드시' 다르게 구현해야 함
    # ------------------------------------------------------------------
    @abstractmethod
    def _diet_factor(self, env: Environment, world: "World") -> tuple[float, float]:
        """식성별 생존 로직. (식량부족도 scarcity, 식성 페널티)를 반환한다.

        식물은 일조량, 초식동물은 식물 개체수, 육식동물은 피식자 개체수,
        부식성 종은 사체 풀(carrion_pool)을 본다 — 같은 이름의 메서드지만
        종마다 완전히 다르게 동작한다. 이것이 '다형성(Polymorphism)'.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    #  템플릿 메서드 — 갱신 절차의 '뼈대'. 자식은 이 흐름을 바꾸지 않는다.
    # ------------------------------------------------------------------
    def compute(self, env: Environment, world: "World") -> None:
        """[Phase 1] 다음 개체수를 '계산만' 한다 (아직 반영하지 않음).

        모든 종이 서로의 '현재' 개체수를 보고 동시에 계산하므로,
        업데이트 순서에 따라 결과가 달라지는 버그가 원천 차단된다.
        """
        if self.is_extinct:
            self._pending = 0
            return

        # 식성별 로직은 자식에게 위임 (다형성)
        scarcity, diet_penalty = self._diet_factor(env, world)

        # 공통 로직으로 최종 생존·번식률 조립
        rate = 1.0 + self.growth_rate                 # 평상시 번식
        rate -= self._climate_penalty(env)            # 추위
        rate -= diet_penalty                          # 굶주림
        rate -= self._body_size_penalty(scarcity)     # 큰 몸집의 아사
        rate = max(0.0, rate)

        next_pop = int(self.population * rate)
        self._pending = min(next_pop, self.capacity)  # 환경 수용력 상한

    def commit(self, env: Environment) -> int:
        """[Phase 2] 계산해 둔 값을 실제로 반영하고 멸종을 판정한다.

        반환값: 이번 step에 죽은 개체 수 (부식성 종의 먹이가 됨).
        """
        if self.is_extinct:
            self.history.append(0)
            return 0

        # 피난처(refuge) 아래로는 떨어지지 않는다.
        # 양치식물의 '포자(spore) 은행'이 대표적 — 지상 개체가 전멸해도
        # 포자가 살아남아 재난 후 가장 먼저 번성한다(화석 기록의 'fern spike').
        new_pop = max(self._pending, self.refuge)
        deaths = max(0, self.population - new_pop)
        self.population = new_pop

        if self.population <= 0:
            self.is_extinct = True
            self.extinction_step = env.time_step
            print(f"  [Time {env.time_step:>2}] 💀 {self.name} 멸종")

        self.history.append(self.population)
        return deaths


# ============================================================================
#  2-1 ~ 2-4. 자식 클래스들 — 식성별로 _diet_factor 를 다르게 오버라이딩
# ============================================================================
class Plant(Species):
    """식물(생산자). 광합성을 하므로 오직 '일조량'에만 의존한다."""

    def _diet_factor(self, env: Environment, world: "World") -> tuple[float, float]:
        # 식물은 먹이를 '먹지' 않으므로 몸집 아사 페널티 없음 → scarcity = 0
        if env.sunlight < 25:
            return 0.0, 0.55        # 광합성 거의 불가
        elif env.sunlight < 55:
            return 0.0, 0.22
        elif env.sunlight < 80:
            return 0.0, 0.06
        return 0.0, 0.0


class Herbivore(Species):
    """초식동물(1차 소비자). '식물 객체'를 직접 참조해 굶주림을 판정한다."""

    def __init__(self, *args, food_sources: list[Species], **kwargs):
        super().__init__(*args, **kwargs)
        self.food_sources = food_sources    # 먹이가 되는 Plant 객체 리스트

    def _diet_factor(self, env: Environment, world: "World") -> tuple[float, float]:
        available = sum(f.population for f in self.food_sources)
        baseline = sum(f.initial_population for f in self.food_sources)
        return self._trophic_response(available, baseline)


class Carnivore(Species):
    """육식동물(2차 소비자). '피식자 객체'를 참조한다 → 먹이사슬의 핵심 연결."""

    def __init__(self, *args, food_sources: list[Species], **kwargs):
        super().__init__(*args, **kwargs)
        self.food_sources = food_sources    # 먹이가 되는 동물 객체 리스트

    def _diet_factor(self, env: Environment, world: "World") -> tuple[float, float]:
        available = sum(f.population for f in self.food_sources)
        baseline = sum(f.initial_population for f in self.food_sources)
        scarcity, penalty = self._trophic_response(available, baseline)

        # 포식자 특화 로직: 혹한기에는 사냥 성공률이 떨어진다.
        # → 초식동물과 '같은 _trophic_response'를 쓰면서도 거동이 다르다.
        if env.temperature < 0:
            penalty += 0.05
        return scarcity, penalty


class Scavenger(Species):
    """부식성 종(분해자). 살아있는 먹이가 아닌 '사체·죽은 유기물'을 먹는다.

    그래서 대멸종 '직후' 사체가 폭증할 때 오히려 번성한다 — 실제로 작은
    포유류·곤충 등 부식성 생물이 K-Pg 직후 살아남아 번성한 메커니즘.
    """

    def _diet_factor(self, env: Environment, world: "World") -> tuple[float, float]:
        carrion = world.carrion_pool        # 환경에 쌓인 사체·유기물의 양

        if carrion > 4000:
            return 0.0, -0.12       # 사체 폭증 → 음수 페널티 = 오히려 번성
        elif carrion > 1000:
            return 0.0, -0.04
        elif carrion > 200:
            return 0.0, 0.05
        # 사체가 고갈되면 잡식으로 근근이 버틴다 (소형 = 몸집 페널티 거의 0)
        return 0.20, 0.10


# ============================================================================
#  3. World — 환경과 생물들을 묶어 시뮬레이션을 '진행'시키는 엔진
# ============================================================================
class World:
    """Environment 1개 + Species 여러 개를 담아 매 step을 진행하는 컨테이너.

    이 클래스는 '진행'만 책임진다. 환경 규칙은 Environment가, 생존 규칙은
    각 Species가 안다 → World는 그들을 '조율'만 한다.
    """

    def __init__(self, environment: Environment, species: list[Species]):
        self.env = environment
        self.species = species
        self.carrion_pool = 0.0     # 환경에 쌓인 사체·죽은 유기물 (부식성 종의 먹이)
        self.sunlight_history = [environment.sunlight]
        self.temp_history = [environment.temperature]

    def step(self) -> None:
        """한 Time-step을 진행한다: 환경 갱신 → 동시 계산 → 일괄 반영."""
        self.env.update()

        # Phase 1: 모든 종이 '서로의 현재 개체수'를 보고 다음 값을 계산
        for s in self.species:
            s.compute(self.env, self)

        # Phase 2: 계산된 값을 일괄 반영하고, 이번 step의 총 사망 수를 집계
        deaths = 0
        for s in self.species:
            deaths += s.commit(self.env)

        # 사체 풀: 새 사망분이 유입되고, 매 step 35%가 부패해 사라진다
        self.carrion_pool = self.carrion_pool * 0.65 + deaths

        self.sunlight_history.append(self.env.sunlight)
        self.temp_history.append(self.env.temperature)


# ============================================================================
#  4. 시뮬레이션 구성 — 5개 대표 종을 에이전트로 등록
# ============================================================================
def build_simulation() -> World:
    """K-Pg 시뮬레이션에 등장할 환경과 5종을 생성해 World로 묶어 반환한다.

    먹이사슬: 양치식물 → 트리케라톱스 → 티라노사우루스
              쥐형 포유류 → 악어
    """
    env = Environment(impact_step=IMPACT_STEP)

    # 생산자 — 포자 은행(refuge) 덕에 전멸하지 않고 재난 후 회복
    fern = Plant("양치식물", population=10_000, body_size=1,
                 habitat="surface", growth_rate=0.15, color="#2e7d32",
                 refuge=300)

    # 1차 소비자(대형 초식) — 식물에 의존, 거대한 몸집이 약점
    triceratops = Herbivore("트리케라톱스", population=1_200, body_size=8,
                            habitat="surface", growth_rate=0.06, color="#ef6c00",
                            food_sources=[fern])

    # 2차 소비자(대형 육식) — 트리케라톱스에 의존, 최상위 포식자
    trex = Carnivore("티라노사우루스", population=400, body_size=9,
                     habitat="surface", growth_rate=0.04, color="#c62828",
                     food_sources=[triceratops])

    # 부식성 소형 종 — 지하 서식 + 사체를 먹어 대멸종 직후 번성 (capacity 큼)
    mammal = Scavenger("쥐형 포유류", population=2_500, body_size=1,
                       habitat="underground", growth_rate=0.10, color="#6a1b9a",
                       capacity=7_500)

    # 중형 육식 — 수중 서식이라 한파 방어력이 높음 (실제로 악어류는 K-Pg 생존)
    crocodile = Carnivore("악어", population=600, body_size=5,
                          habitat="aquatic", growth_rate=0.04, color="#1565c0",
                          food_sources=[mammal], capacity=2000)

    return World(env, [fern, triceratops, trex, mammal, crocodile])


# ============================================================================
#  5. 결과 출력 — 콘솔 요약과 matplotlib 그래프
# ============================================================================
def print_summary(world: World) -> None:
    """시뮬레이션 종료 후 종별 최종 결과를 표로 출력한다."""
    print("\n" + "=" * 60)
    print("  시뮬레이션 종료 — 종별 결과 요약")
    print("=" * 60)
    for s in world.species:
        if s.is_extinct:
            status = f"💀 멸종 (Time {s.extinction_step})"
        else:
            status = "✅ 생존"
        print(f"  {s.name:<10} {s.history[0]:>7,} 마리 → "
              f"{s.population:>7,} 마리   {status}")
    print("=" * 60)


def _set_korean_font() -> None:
    """matplotlib 그래프에 한글이 깨지지 않도록 한글 폰트를 설정한다."""
    for candidate in ("Malgun Gothic", "AppleGothic", "NanumGothic"):
        if any(f.name == candidate for f in fm.fontManager.ttflist):
            plt.rcParams["font.family"] = candidate
            break
    plt.rcParams["axes.unicode_minus"] = False   # 음수 기호(−) 깨짐 방지


def plot_results(world: World) -> None:
    """환경 변화(위)와 종별 생존율(아래)을 2단 그래프로 시각화한다.

    [설계 메모] 식물 10,000마리와 티라노사우루스 400마리를 같은 절대 눈금에
    그리면 작은 종이 바닥에 깔려 안 보인다. 그래서 아래 그래프는 '초기
    개체수 대비 비율(%)'로 정규화해 5종을 공정하게 비교하고, 각 선 끝에
    최종 절대 개체수를 함께 표기한다.
    """
    _set_korean_font()
    steps = list(range(len(world.species[0].history)))

    fig, (ax_env, ax_pop) = plt.subplots(
        2, 1, figsize=(12, 9), sharex=True,
        gridspec_kw={"height_ratios": [1, 2]})

    # ── 상단: 환경 변화 (일조량 + 기온, y축 2개) ──────────────────────
    ax_env.plot(steps, world.sunlight_history, color="#f9a825",
                linewidth=2, label="일조량")
    ax_env.set_ylabel("일조량 (%)", color="#f9a825")
    ax_env.tick_params(axis="y", labelcolor="#f9a825")
    ax_env.set_title("K-Pg 대멸종 시뮬레이션 — 환경 변화와 종별 생존율",
                     fontsize=14, fontweight="bold")

    ax_temp = ax_env.twinx()
    ax_temp.plot(steps, world.temp_history, color="#0277bd",
                 linewidth=2, label="기온")
    ax_temp.set_ylabel("기온 (°C)", color="#0277bd")
    ax_temp.tick_params(axis="y", labelcolor="#0277bd")

    # y축이 2개이므로 두 축의 선을 하나의 범례로 합쳐 표시
    env_lines = ax_env.get_lines() + ax_temp.get_lines()
    ax_env.legend(env_lines, [ln.get_label() for ln in env_lines],
                  loc="center right")

    # ── 하단: 종별 생존율 (초기 대비 %) ───────────────────────────────
    # 최종 절대 개체수는 범례에 함께 표기한다 (선 끝 라벨은 서로 겹치므로).
    for s in world.species:
        survival = [h / s.history[0] * 100 for h in s.history]
        label = f"{s.name}  (최종 {s.population:,}마리)"
        ax_pop.plot(steps, survival, label=label, color=s.color, linewidth=2.2)

    ax_pop.axhline(100, color="gray", linestyle=":", alpha=0.6)   # 초기 수준 기준선
    ax_pop.set_xlabel("시간 (Time-step)")
    ax_pop.set_ylabel("초기 대비 개체수 (%)")
    ax_pop.set_xlim(0, TOTAL_STEPS)
    ax_pop.legend(loc="upper left")
    ax_pop.grid(True, alpha=0.3)

    # ── 두 그래프 모두에 운석 충돌 시점 표시 ──────────────────────────
    for ax in (ax_env, ax_pop):
        ax.axvline(world.env.impact_step, color="red", linestyle="--", alpha=0.7)
    ax_pop.text(world.env.impact_step + 0.8, ax_pop.get_ylim()[1] * 0.5,
                "운석 충돌", color="red", fontweight="bold",
                rotation=90, va="center")

    fig.tight_layout()

    # 스크립트와 같은 폴더에 PNG로 저장 (실행 위치와 무관하게 동작)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "kpg_simulation_result.png")
    fig.savefig(out_path, dpi=120)
    print(f"\n  📊 그래프를 저장했습니다: {out_path}")
    plt.show()


# ============================================================================
#  6. 메인 실행부
# ============================================================================
def main() -> None:
    print("=" * 60)
    print("  ☄️  K-Pg 대멸종 에이전트 기반 시뮬레이션 (ABM)")
    print("=" * 60)

    world = build_simulation()
    print(f"  등록된 종    : " + ", ".join(s.name for s in world.species))
    print(f"  시뮬레이션   : 0 ~ {TOTAL_STEPS} step "
          f"(운석 충돌 = step {IMPACT_STEP})")

    for step in range(1, TOTAL_STEPS + 1):
        world.step()
        # 10 step마다 환경·개체수 스냅샷 출력
        if step % 10 == 0:
            snap = "  ".join(f"{s.name[:4]} {s.population:,}"
                             for s in world.species)
            print(f"  [Time {step:>2}] 🌞{world.env.sunlight:5.1f}% "
                  f"🌡{world.env.temperature:6.1f}°C | {snap}")

    print_summary(world)
    plot_results(world)


if __name__ == "__main__":
    main()


# ============================================================================
#  💡 면접·세특 대비 — 이 코드로 설명하는 객체 지향(OOP)의 장점
# ============================================================================
#
#  [1] 확장성 (Extensibility) — "종을 추가하기 쉽다"
#      새 생물을 넣고 싶다면 Species를 상속한 클래스 '하나'만 추가하면 된다.
#      예: 곤충을 먹는 Insectivore, 잡식성 Omnivore.
#      Environment·World·시뮬레이션 루프 코드는 단 한 줄도 안 고쳐도 된다.
#      → '확장에는 열려 있고 수정에는 닫혀 있다' (개방-폐쇄 원칙, OCP).
#
#  [2] 유지보수성 (Maintainability) — "고칠 곳이 한 군데다"
#      기온 방어 규칙은 Species._climate_penalty 한 메서드에만 있다.
#      한파 로직을 바꾸려면 그 메서드 하나만 고치면 5종 전체에 반영된다.
#      모든 종을 거대한 if-elif 한 함수로 처리했다면, 수정할 때마다
#      그 분기문을 헤집어야 하고 한 종을 고치다 다른 종을 망가뜨리기 쉽다.
#      → 중복 제거(DRY).
#
#  [3] 다형성 (Polymorphism) — "호출하는 쪽이 단순해진다"
#      World.step()은 그냥 `for s in species: s.compute(...)`를 돌 뿐,
#      그 객체가 식물인지 육식동물인지 '알지도, 신경 쓰지도' 않는다.
#      각 객체가 자기 식성에 맞는 _diet_factor()를 알아서 실행한다.
#      종류가 10개로 늘어도 World의 코드는 그대로다.
#
#  [4] 캡슐화·책임 분리 (Encapsulation & SRP) — "버그를 빨리 찾는다"
#      Environment=환경, Species=생물의 생사, World=진행. 역할이 나뉘어
#      있어 문제가 생기면 어느 클래스를 봐야 할지 바로 안다.
#
#  [면접 한 줄 요약]
#  "if-else로 짰다면 종이 늘 때마다 분기문이 폭발하지만, 상속·다형성으로
#   짜면 클래스 파일 하나만 늘면 됩니다. 그것이 객체 지향이 복잡한
#   시스템을 감당하는 방식입니다."
# ============================================================================

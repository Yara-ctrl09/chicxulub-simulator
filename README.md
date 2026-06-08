# 🌍 K-Pg 대멸종 시뮬레이션 프로젝트

**유카탄 반도 운석 충돌(약 6,600만 년 전)로 인한 K-Pg 대멸종을 재현하는 멀티 플랫폼 프로젝트입니다.**

- 🌐 **웹사이트** (HTML + JavaScript): 인터랙티브 충돌 시뮬레이터
- 🐍 **Python ABM**: 객체 지향 에이전트 기반 모델링 (생태계 시뮬레이션)
- 📊 **웹 대시보드** (Streamlit): 실시간 시뮬레이션 제어 및 분석

> **대상**: 고등학교 2학년 탐구 활동 / 컴퓨터 공학과 진학용 세특 프로젝트

---

## 📁 프로젝트 구조

```
창의융합/
├── 🌐 웹사이트 (HTML/CSS/JavaScript)
│   ├── index.html              ← 메인 입력 페이지 (슬라이더로 파라미터 설정)
│   └── result.html             ← 결과 분석 페이지 (그래프 + 애니메이션)
│
├── 🐍 Python 시뮬레이션
│   ├── kpg_simulation.py       ← 핵심 ABM 엔진 (OOP 설계)
│   ├── dashboard.py            ← Streamlit 웹 대시보드
│   ├── requirements.txt         ← 의존성 패키지
│   └── kpg_simulation_result.png ← 시뮬레이션 결과 그래프
│
└── 📄 문서
    └── README.md               ← 이 파일
```

---

## 🚀 빠른 시작

### 1️⃣ 웹사이트 (HTML 기반) - 즉시 실행 가능

운석 충돌의 물리 시뮬레이션을 웹에서 직관적으로 체험합니다.

**실행 방법:**
- `index.html`을 브라우저에서 열기
- 슬라이더로 소행성 직경, 속도, 각도 설정
- "시뮬레이션 시작" 클릭 → `result.html`로 자동 이동
- 애니메이션, 그래프, 상세 분석 보기

**특징:**
- 📊 Chart.js로 3년간의 기온 변화 그래프
- 📈 생물 종 생존율 추이 (식물 → 초식동물 → 육식동물)
- 🎬 Canvas 애니메이션 (충격파 확산 효과)
- 📐 물리 공식 적용 (E = ½mv², 크레이터 계산 등)

### 2️⃣ Python ABM (에이전트 기반 모델링)

실제 생태계 붕괴를 객체 지향으로 시뮬레이션합니다.

**설치 및 실행:**
```bash
# 의존성 설치
pip install -r requirements.txt

# 콘솔 기반 시뮬레이션 실행
python kpg_simulation.py

# 또는 웹 대시보드 실행
python -m streamlit run dashboard.py
# → http://localhost:8501에서 접속
```

**시뮬레이션 종류:**
- **5개 생물 종**: 양치식물, 트리케라톱스, 티라노사우루스, 쥐형 포유류, 악어
- **환경 변화**: 일조량 급감, 기온 급락 (Impact Winter)
- **먹이사슬**: 식물 → 초식동물 → 육식동물로 연쇄 붕괴
- **부식성 공급처**: 운석 충돌 직후 사체 폭증으로 부식성 종 번성

---

## 🔧 코드 설계 (Python ABM)

### 핵심 클래스 구조

| 클래스 | 책임 | 상속 관계 |
|---|---|---|
| `Environment` | 시간별 환경 변수 (일조량, 기온) | - |
| `Species` | 모든 생물의 공통 속성·생존 로직 | 추상 클래스 |
| `Plant` | 식물 (일조량에만 의존) | ← Species |
| `Herbivore` | 초식동물 (식물 섭취) | ← Species |
| `Carnivore` | 육식동물 (다른 동물 포식) | ← Species |
| `Scavenger` | 부식성 종 (사체 섭취) | ← Species |
| `World` | 시뮬레이션 엔진 (환경 + 모든 종 조율) | - |

### 객체 지향 핵심 개념

#### 1️⃣ 상속 (Inheritance)
```python
class Species(ABC):
    def __init__(self, name, population, metabolism):
        self.name = name
        self.population = population
        self.metabolism = metabolism
    
    @abstractmethod
    def _diet_factor(self, env, world):
        """각 종이 식성별로 다르게 구현"""
        pass

# 자식 클래스들
class Plant(Species):
    def _diet_factor(self, env, world):
        # 식물: 일조량에만 의존
        return 0, penalty_based_on_sunlight

class Herbivore(Species):
    def _diet_factor(self, env, world):
        # 초식동물: 식물 개체수에 의존
        return scarcity, penalty_based_on_food_plants
```

#### 2️⃣ 다형성 (Polymorphism)
```python
# 같은 메서드명이지만 종마다 다른 동작
for species in all_species:
    scarcity, penalty = species._diet_factor(env, world)
    # ↑ Plant는 일조량 보고, Herbivore는 식물 개체수 보고, ...
```

#### 3️⃣ 동시 갱신 (2-Phase Update)
```python
# Phase 1: 모든 종이 '다음 개체수'를 계산만 함 (현재값 기준)
for species in all_species:
    species.compute(env, world)  # _pending에만 저장

# Phase 2: 계산 결과를 일괄 반영
for species in all_species:
    deaths = species.commit(env)  # 실제 개체수 업데이트
    carrion_pool += deaths        # 사망자가 부식성 종의 먹이
```
→ 순환 참조/업데이트 순서 버그 방지

#### 4️⃣ 먹이사슬 (Food Chain Reference)
```python
# 초식동물이 식물 객체를 직접 참조
self.prey = herbivore_population
self.food_source = plants  # Plant 객체 참조

# 한 종의 개체수 변화가 다음 단계로 자동 전파
if plants.population < threshold:
    herbivore_survival_rate -= penalty  # 연쇄 붕괴
```

---

## 📊 시뮬레이션 결과 예시

### 초기 개체수
| 종 | 개체수 | 특징 |
|---|---|---|
| 양치식물 | 10,000 | 에너지 기반 |
| 트리케라톱스 | 1,200 | 대형 초식공룡 |
| 티라노사우루스 | 400 | 최상위 포식자 |
| 쥐형 포유류 | 2,500 | 소형 부식성 포유류 |
| 악어 | 600 | 수중 서식 |

### 최종 결과 (Time 80, 약 2년)

| 종 | 최종 개체수 | 상태 | 멸종 시점 | 원인 |
|---|---|---|---|---|
| 양치식물 | 10,000 | ✅ 생존 | - | 포자 저장소 덕에 회복 |
| 트리케라톱스 | 0 | 💀 멸종 | Time 27 | 먹이(식물) 부족 + 한파 |
| 티라노사우루스 | 0 | 💀 멸종 | Time 24 | 피식자(초식공룡) 멸종 |
| 쥐형 포유류 | 7,008 | ✅ 번성 | - | 지하 서식 + 부식물 풍부 |
| 악어 | 600+ | ✅ 생존 | - | 수중 환경의 한파 완충 |

### 시뮬레이션이 재현하는 실제 K-Pg 패턴

✅ **대형 공룡 멸종**
- 티라노사우루스 · 트리케라톱스 등 대형 공룡 완전 멸종
- 이유: 한파 + 먹이사슬 붕괴 + 높은 신진대사

✅ **소형 포유류 번성**
- 쥐형 포유류 개체수 증가 (초기 2,500 → 최종 7,000+)
- 이유: 지하 서식(한파 방어) + 부식물 풍부

✅ **악어류 생존**
- 악어는 개체수 유지
- 이유: 수중 환경이 한파를 완충, 변온동물의 대사 저하 이점

✅ **양치식물 회복**
- 화석 기록의 'fern spike' 재현
- 이유: 포자 은행에서 천천히 재발아

---

## 💡 학습 목표 & 세특용 내용

### 1️⃣ 객체 지향 프로그래밍 (OOP)
- ✅ 클래스 설계 (속성 + 메서드)
- ✅ 상속 (Inheritance): Species → 자식 클래스들
- ✅ 다형성 (Polymorphism): 같은 메서드명, 다른 구현
- ✅ 캡슐화 (Encapsulation): 각 클래스의 책임 분리
- ✅ 추상 클래스 (Abstract Class): 틀을 정의하고 자식이 구현

### 2️⃣ 에이전트 기반 모델링 (ABM)
- ✅ 개별 에이전트(Agent) 모델링: 각 생물을 독립적 객체로 표현
- ✅ 국소적 규칙 → 전역적 현상: 개별 생존 규칙 → 생태계 붕괴
- ✅ 창발 (Emergence): 미리 설계하지 않은 양치식물 번성 현상
- ✅ 시스템 동역학: 피드백 루프 (먹이 감소 → 개체수 감소 → 다음 단계 영향)

### 3️⃣ 자료 구조 & 알고리즘
- ✅ 딕셔너리 (Dictionary): 종별 통계 저장
- ✅ 리스트 (List): 시간 시계열 데이터 기록
- ✅ 객체 참조 (Reference): 먹이사슬을 객체 참조로 표현
- ✅ 2-Phase 갱신 알고리즘: 동시성 문제 해결

### 4️⃣ 시각화 & 데이터 분석
- ✅ matplotlib: 다중 라인 그래프로 종별 개체수 추이 표시
- ✅ Streamlit: 파라미터 조정 UI 및 실시간 대시보드
- ✅ 데이터 해석: 실제 고생물학·진화생물학과 비교

### 5️⃣ 웹 개발 (Full Stack 체험)
- ✅ HTML + CSS: 반응형 UI 디자인
- ✅ JavaScript: 물리 계산 + 로컬 스토리지 활용
- ✅ Canvas API: 2D 애니메이션 렌더링
- ✅ 페이지 간 데이터 전달: localStorage 활용

---

## 📖 사용 방법

### 웹사이트 (HTML)
```bash
# 방법 1: 브라우저에서 직접 열기
index.html을 우클릭 → "브라우저로 열기"

# 방법 2: VS Code Live Server 사용
# (Live Server 확장 설치 후)
index.html에서 우클릭 → "Open with Live Server"
```

### Python 시뮬레이션
```bash
# 1. 의존성 설치 (첫 실행 시만)
pip install -r requirements.txt

# 2. 콘솔 기반 시뮬레이션 (그래프 저장)
python kpg_simulation.py

# 3. 웹 대시보드 (파라미터 조정 가능)
python -m streamlit run dashboard.py
# → 브라우저가 자동으로 http://localhost:8501 에서 열림
```

---

## 📚 참고 자료

### 교과서 연계 개념
- **고등학교 생명과학 II**: 진화의 증거, 멸종, 먹이사슬
- **컴퓨터공학 기초**: OOP, 알고리즘, 자료 구조
- **수학 (확률과 통계)**: 시간 시계열 데이터 분석

### K-Pg 대멸종의 실제 패턴
- 6,600만 년 전 유카탄반도 칙술루브(Chicxulub) 충돌
- 지구 생물 75% 이상 멸종 (대형 동물 거의 전멸, 소형 동물 생존)
- Impact Winter: 충돌로 인한 먼지 + 황산염 에어로졸 → 일조량 급감 → 광합성 중단
- Fern Spike: 공룡 멸종 후 양치식물이 번성하는 화석 증거

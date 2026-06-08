# 📋 프로젝트 구조 및 파일 설명

## 🎯 프로젝트 개요

**K-Pg 대멸종 시뮬레이션** - 고등학교 2학년 창의융합 탐구 활동

- 목표: 6,600만 년 전 유카탄 반도 운석 충돌로 인한 대멸종을 재현
- 플랫폼: 웹사이트(HTML/JS) + Python(ABM) 듀얼 구성
- 교육 목표: OOP, 에이전트 기반 모델링, 데이터 시각화 학습

---

## 📁 전체 파일 구조

```
창의융합/
│
├─ 🌐 웹사이트 (브라우저 기반 물리 시뮬레이션)
│  ├─ index.html                 [메인 페이지 - 파라미터 입력]
│  └─ result.html                [결과 페이지 - 분석 및 그래프]
│
├─ 🐍 Python ABM (생태계 시뮬레이션)
│  ├─ kpg_simulation.py          [시뮬레이션 엔진]
│  ├─ dashboard.py               [Streamlit 웹 대시보드]
│  ├─ requirements.txt           [의존성 패키지]
│  └─ kpg_simulation_result.png  [시뮬레이션 결과 그래프]
│
├─ 📄 문서
│  ├─ README.md                  [프로젝트 전체 설명]
│  └─ PROJECT_STRUCTURE.md       [이 파일]
│
└─ 🔧 시스템 파일
   └─ __pycache__/              [Python 컴파일 캐시 (무시)]
```

---

## 📄 각 파일 상세 설명

### 🌐 웹사이트 파일

#### `index.html` (메인 입력 페이지)
**역할**: 사용자가 운석 충돌 파라미터를 입력하는 첫 번째 화면

**주요 구성 요소:**
- 우주 배경 + 별 애니메이션 (CSS)
- 3개 슬라이더:
  - 소행성 직경: 1 ~ 30 km (기본값: 10)
  - 충돌 속도: 11 ~ 40 km/s (기본값: 20)
  - 충돌 각도: 30° ~ 90° (기본값: 60°)
- "🚀 시뮬레이션 시작" 버튼

**기술 스택:**
- HTML5: 구조
- CSS3: 다크 모드 그라데이션 디자인
- JavaScript (Vanilla): 슬라이더 이벤트 + localStorage 저장

**핵심 기능:**
```javascript
function launchSimulation() {
    // 1. 슬라이더 값 읽기
    const diameter = parseFloat(document.getElementById('diameterSlider').value);
    const velocity = parseFloat(document.getElementById('velocitySlider').value);
    const angle = parseFloat(document.getElementById('angleSlider').value);
    
    // 2. localStorage에 저장 (페이지 간 데이터 전달)
    localStorage.setItem('asteroidData', JSON.stringify({
        diameter: diameter,
        velocity: velocity,
        angle: angle
    }));
    
    // 3. result.html로 이동
    window.location.href = 'result.html';
}
```

---

#### `result.html` (결과 분석 페이지)
**역할**: index.html에서 받은 파라미터를 기반으로 물리 계산 및 결과 시각화

**주요 구성 요소:**

1. **입력 파라미터 표시 (좌측)**
   - 소행성 직경, 속도, 각도 재확인

2. **계산 결과 표시**
   - 충돌 에너지 (TNT 메가톤)
   - 크레이터 직경 (km)
   - 지진 규모 (리히터 스케일)

3. **Canvas 애니메이션 (상단)**
   - 유카탄반도 표현 (원형)
   - 충격파 확산 애니메이션 (60프레임)

4. **Chart.js 그래프 (중단)**
   - 지구 기온 변화 (3년간 시뮬레이션)
   - 생물 종 생존율 (식물/초식동물/육식동물)

5. **상세 리포트 (하단)**
   - 지진 규모 설명
   - 대기 진입 온도
   - 대멸종 시나리오

**기술 스택:**
- Chart.js CDN: 데이터 시각화
- Canvas API: 2D 애니메이션
- JavaScript: 물리 공식 계산

**핵심 계산 공식:**

```javascript
// 1️⃣ 충돌 에너지 (E = ½mv²)
E = 0.5 * mass * velocity²
mass = (4/3) * π * radius³ * density  // 구의 부피 × 밀도
// 결과를 TNT 메가톤(Mt) 단위로 변환: 1Mt = 4.184×10¹⁵ J

// 2️⃣ 크레이터 직경
crater = baseSize × (E/E_ref)^(1/3.4) × cos(angle)
// 에너지 비례, 충돌 각도에 따라 조정

// 3️⃣ 지진 규모
magnitude = (2/3) × log₁₀(E) - 10.7
// 리히터 규모 공식
```

---

### 🐍 Python 시뮬레이션 파일

#### `kpg_simulation.py` (핵심 ABM 엔진)
**역할**: 객체 지향으로 설계된 생태계 시뮬레이션 엔진

**클래스 계층 구조:**

```
Species (추상 클래스)
│
├─ Plant (식물)
├─ Herbivore (초식동물)
├─ Carnivore (육식동물)
└─ Scavenger (부식성 종)

Environment (환경 변수 관리)
World (시뮬레이션 엔진 - 모든 종 조율)
```

**주요 클래스:**

| 클래스 | 설명 | 메서드 |
|---|---|---|
| `Environment` | 시간에 따른 환경 조건 | `get_sunlight()`, `get_temperature()`, `trigger_asteroid()` |
| `Species` (추상) | 모든 생물의 틀 | `compute()`, `commit()`, `_diet_factor()` |
| `Plant` | 양치식물 | 일조량에 따라 생장 |
| `Herbivore` | 초식동물 | 식물 개체수에 의존 |
| `Carnivore` | 육식동물 | 피식자 개체수에 의존 |
| `Scavenger` | 부식성 동물 | 사체(carrion pool)에 의존 |
| `World` | 시뮬레이션 엔진 | `step()`, `run()`, 통계 기록 |

**핵심 알고리즘: 2-Phase Update**

```python
class World:
    def step(self):
        # Phase 1: 모든 종이 '다음 개체수'를 계산만 함
        for species in all_species:
            species.compute(self.env, self)  # _pending에 저장
        
        # Phase 2: 계산 결과를 일괄 반영
        for species in all_species:
            deaths = species.commit(self.env)  # 실제 반영
            self.carrion_pool += deaths        # 사체를 부식성 먹이로
```

**동시성 예방:**
- 업데이트 순서가 결과에 영향을 주지 않음
- 모든 종이 공평하게 "현재 상태"를 기반으로 계산

**시뮬레이션 파라미터:**
- 시간 스텝: 기본 80 (약 2년)
- 운석 충돌 시점: 기본 Time 20
- 초기 개체수: 각 종별로 설정 가능

**출력:**
- 콘솔: 시간별 진행 로그
- 그래프 (matplotlib):
  - 상단: 환경 변수 (일조량, 기온)
  - 하단: 종별 개체수 추이
- 파일: `kpg_simulation_result.png` 저장

---

#### `dashboard.py` (Streamlit 웹 대시보드)
**역할**: 파라미터를 실시간으로 조정하고 시뮬레이션 결과를 시각화

**화면 구성:**

1. **사이드바 (좌측)**
   - 총 시뮬레이션 스텝 수 (슬라이더)
   - 운석 충돌 시점 (슬라이더)
   - 각 종별 초기 개체수 (숫자 입력)
   - "🚀 시뮬레이션 실행" 버튼

2. **메인 영역**
   - 진행 바 (실시간)
   - 종별 카드 (최종 개체수, 생존/멸종 여부)
   - 상세 결과 테이블 (초기 → 최종, 변화율)
   - matplotlib 그래프 (환경 + 개체수)
   - 통계 요약 (생존/멸종 종 개수)

**실행 방법:**
```bash
python -m streamlit run dashboard.py
# → http://localhost:8501 자동 열기
```

**기술 스택:**
- Streamlit: 대시보드 UI
- matplotlib: 그래프 렌더링
- pandas: 데이터 테이블

---

#### `requirements.txt` (의존성 패키지)
**역할**: Python 프로젝트에 필요한 라이브러리 목록

**내용:**
```
matplotlib>=3.5    # 그래프 그리기
streamlit          # 웹 대시보드
pandas             # 데이터 처리 (테이블)
```

**설치:**
```bash
pip install -r requirements.txt
```

---

#### `kpg_simulation_result.png` (결과 그래프)
**역할**: Python 시뮬레이션의 최종 결과 시각화

**구성:**
- 상단: 환경 변수 그래프
  - 일조량 (% of normal)
  - 기온 (°C)
- 하단: 생물 개체수 그래프
  - 각 종별 개체수 시간 추이
  - 색상 구분 (Plant, Herbivore, Carnivore, Scavenger)

---

### 📄 문서 파일

#### `README.md`
**역할**: 프로젝트 전체 개요 및 학습 목표

**주요 내용:**
- 프로젝트 소개
- 빠른 시작 가이드
- 코드 설계 원리 (OOP, ABM)
- 시뮬레이션 결과 설명
- 학습 목표
- K-Pg 대멸종의 실제 역사

---

#### `PROJECT_STRUCTURE.md` (이 파일)
**역할**: 파일별 상세 설명 및 기술 스택

---

## 🔄 데이터 흐름

### 웹사이트 (HTML ↔ result.html)

```
┌─────────────────┐
│  index.html     │
│ (입력 페이지)   │
└────────┬────────┘
         │ 슬라이더 설정
         │ + 버튼 클릭
         ↓
   localStorage에 저장
      (JSON 형식)
         ↓
┌─────────────────┐
│  result.html    │
│ (결과 페이지)   │
│ - localStorage  │
│   에서 데이터   │
│   읽기          │
│ - 물리 공식     │
│   계산          │
│ - Chart.js      │
│   그래프 그리기 │
└─────────────────┘
```

### Python 시뮬레이션

```
┌──────────────────┐
│ kpg_simulation.py│
│ (메인 엔진)      │
└────────┬─────────┘
         │
         ├─→ World 객체 생성
         │
         ├─→ 5개 Species 생성
         │   (Plant, Herbivore, ...)
         │
         └─→ Time step 반복:
             1. Environment 업데이트
             2. 모든 Species compute()
             3. 모든 Species commit()
             4. 통계 기록
             ↓
      ┌──────────────────┐
      │ kpg_simulation_  │
      │ result.png       │
      │ (결과 그래프)    │
      └──────────────────┘
             또는
      ┌──────────────────┐
      │ dashboard.py     │
      │ (웹 대시보드)    │
      │ - 실시간 제어    │
      │ - 파라미터 조정  │
      └──────────────────┘
```

---

## 🎓 학습 활용 포인트

### OOP 학습
- **파일**: `kpg_simulation.py`의 클래스 정의 부분
- **개념**: 상속, 다형성, 캡슐화, 추상 클래스
- **예시**: `Species` → `Plant`, `Herbivore` 상속 구조

### 데이터 구조 학습
- **파일**: `World` 클래스의 데이터 저장 방식
- **개념**: 딕셔너리, 리스트, 객체 참조
- **예시**: `self.all_species = [...]`, `self.history = {}`

### 알고리즘 학습
- **파일**: `step()` 메서드의 2-Phase Update
- **개념**: 순환 참조 해결, 동시 갱신
- **예시**: `compute()` → `commit()` 분리

### 시각화 학습
- **파일**: `dashboard.py`의 Streamlit 코드
- **개념**: matplotlib, Chart.js, Canvas API
- **예시**: 다중 라인 그래프, 애니메이션

### 물리학 적용
- **파일**: `result.html`의 계산 공식
- **개념**: 운동에너지, 지진 규모, 열 이동
- **예시**: E = ½mv², 리히터 규모 = (2/3)log(E) - 10.7

---

## 🔧 개선 가능성

1. **Python ABM 확장**
   - 더 많은 생물 종 추가
   - 개체 이동(migration) 모델링
   - 지리적 위치 기반 상호작용

2. **웹사이트 고도화**
   - Three.js로 3D 지구 시각화
   - 실시간 계산 결과 업데이트
   - 과거 시뮬레이션 비교 기능

3. **대시보드 개선**
   - 파라미터 프리셋 (사진, 애니메이션GIF)
   - 엑셀 내보내기
   - 고급 통계 (표준편차, 신뢰도)

4. **문서화**
   - 화석 기록 데이터 비교
   - 과학 논문 링크
   - 인터랙티브 튜토리얼

---

## 📝 체크리스트

- [x] HTML 웹사이트 구현 (index.html, result.html)
- [x] Python ABM 엔진 구현 (kpg_simulation.py)
- [x] Streamlit 대시보드 구현 (dashboard.py)
- [x] 의존성 파일 작성 (requirements.txt)
- [x] 프로젝트 문서 작성 (README.md)
- [x] 구조 설명 문서 작성 (PROJECT_STRUCTURE.md)
- [ ] 추가 물리 계산 공식 검증
- [ ] 화석 데이터와 비교 분석
- [ ] 사용자 테스트 및 피드백
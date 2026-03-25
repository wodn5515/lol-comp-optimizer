# LoL Comp Optimizer — 프로젝트 기획서

## 한줄 요약

2~5명의 소환사명을 입력하면 Riot API로 전적·챔피언풀을 분석해서 **최적 라인 배정 + 챔피언 조합 추천**을 해주는 웹앱.

> 📎 이 기획서와 함께 `lol-dev-process.md` (개발 프로세스·테스트 전략·스펙 드리븐 가이드)를 참고할 것.

---

## 1. 아키텍처

### 1-1. 백엔드 — 포트앤어댑터 (헥사고날)

핵심 원칙: **domain/ 안에는 외부 라이브러리(FastAPI, SQLModel, httpx) import 금지. 순수 Python만.**

```
backend/
├── main.py                           # FastAPI 부트스트랩, DI 조립
├── config.py                         # 환경 설정
│
├── domain/                           # 🔵 핵심 도메인 (외부 의존 없음)
│   ├── models/                       # 엔티티, 값 객체
│   │   ├── player.py                 # Player, LaneStats, ChampionStats
│   │   ├── champion.py               # Champion, ChampionAttributes
│   │   ├── composition.py            # Composition, Assignment, TeamAnalysis
│   │   └── match.py                  # MatchSummary
│   ├── services/                     # 비즈니스 로직 (유스케이스)
│   │   ├── player_analysis_service.py   # 플레이어 데이터 분석 (라인별 승률, 챔피언풀)
│   │   ├── lane_optimizer_service.py    # 라인 배정 최적화 (전수 탐색)
│   │   ├── comp_optimizer_service.py    # 챔피언 조합 최적화 (점수 산정)
│   │   └── champion_data_service.py     # 챔피언 속성 조회 + 기본값 부여
│   └── ports/                        # 🔌 포트 (인터페이스 = ABC)
│       ├── repositories/
│       │   └── champion_repo.py      # ChampionRepository(ABC) — 챔피언 속성 DB
│       └── external/
│           ├── riot_api_port.py       # RiotApiPort(ABC) — Riot API 추상화
│           └── ddragon_port.py        # DataDragonPort(ABC) — 정적 데이터 추상화
│
├── adapters/                         # 🔴 어댑터 (포트 구현체)
│   ├── inbound/                      # 외부 → 도메인
│   │   └── api/
│   │       ├── optimize_router.py    # POST /api/optimize
│   │       └── champion_router.py    # GET /api/champions (속성 조회)
│   └── outbound/                     # 도메인 → 외부
│       ├── persistence/
│       │   ├── database.py           # SQLite 연결
│       │   ├── orm_models.py         # SQLModel ORM
│       │   └── champion_repo_impl.py # 챔피언 속성 DB 구현
│       └── external/
│           ├── riot_api_client.py     # Riot API HTTP 클라이언트 (rate limiter 포함)
│           └── ddragon_client.py      # Data Dragon 클라이언트
│
└── requirements.txt
```

**포트/어댑터 예시:**

```python
# domain/ports/external/riot_api_port.py (포트)
class RiotApiPort(ABC):
    @abstractmethod
    async def get_account_by_riot_id(self, game_name: str, tag_line: str) -> Account | None: ...
    @abstractmethod
    async def get_match_ids(self, puuid: str, count: int, queue: int) -> list[str]: ...
    @abstractmethod
    async def get_match_detail(self, match_id: str) -> MatchDetail | None: ...
    @abstractmethod
    async def get_champion_masteries(self, puuid: str, top: int) -> list[Mastery]: ...

# adapters/outbound/external/riot_api_client.py (어댑터)
class RiotApiClient(RiotApiPort):
    def __init__(self, rate_limiter: RateLimiter):
        self.client = httpx.AsyncClient(timeout=15.0)
        self.rate_limiter = rate_limiter

    async def get_account_by_riot_id(self, game_name, tag_line):
        await self.rate_limiter.wait_if_needed()
        resp = await self.client.get(f"{ACCOUNT_BASE}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}",
                                      headers={"X-Riot-Token": self.api_key})
        ...

# domain/services/lane_optimizer_service.py (서비스 — 포트에만 의존)
class LaneOptimizerService:
    def optimize(self, players: list[Player], lane_count: int = 5) -> list[LaneAssignment]:
        # 순수 비즈니스 로직, 외부 의존 없음
        ...
```

### 1-2. 프론트엔드 — Feature-Sliced Design (FSD)

핵심 규칙: **상위 → 하위 방향으로만 의존 가능.**

```
app → pages → widgets → features → entities → shared
```

```
frontend/src/
│
├── app/                              # Layer 1: 앱 전역
│   ├── App.jsx
│   ├── providers/
│   │   └── QueryProvider.jsx         # React Query 프로바이더
│   ├── styles/index.css
│   └── router.jsx
│
├── pages/                            # Layer 2: 페이지
│   ├── home/ui/HomePage.jsx          # 입력 화면
│   └── result/ui/ResultPage.jsx      # 결과 화면
│
├── widgets/                          # Layer 3: 위젯 (독립 UI 블록)
│   ├── player-input-form/
│   │   ├── ui/PlayerInputForm.jsx    # 소환사명 2~5명 입력 폼
│   │   └── model/usePlayerForm.js
│   ├── result-board/
│   │   ├── ui/ResultBoard.jsx        # 추천 조합 카드 리스트
│   │   └── model/useResultData.js
│   ├── player-summary/
│   │   ├── ui/PlayerSummary.jsx      # 플레이어 개인 카드 그리드
│   │   └── model/usePlayerSummary.js
│   └── loading-progress/
│       ├── ui/LoadingProgress.jsx    # 단계별 프로그레스
│       └── model/useLoadingState.js
│
├── features/                         # Layer 4: 피처 (유저 액션)
│   ├── analyze-comp/
│   │   ├── ui/AnalyzeButton.jsx      # "조합 분석하기" 버튼
│   │   ├── model/useAnalyze.js
│   │   └── api/analyzeComp.js        # POST /api/optimize 호출
│   ├── setup-api-key/
│   │   ├── ui/ApiKeyInput.jsx
│   │   └── model/useApiKey.js
│   └── add-player/
│       ├── ui/AddPlayerButton.jsx    # 플레이어 추가/제거
│       └── model/usePlayerList.js
│
├── entities/                         # Layer 5: 엔티티 (비즈니스 모델)
│   ├── player/
│   │   ├── ui/PlayerCard.jsx         # 개인 정보 카드 (티어, 모스트, 라인)
│   │   ├── ui/LanePreference.jsx     # 라인 선호도 차트
│   │   ├── model/types.js
│   │   └── model/playerStore.js
│   ├── champion/
│   │   ├── ui/ChampionIcon.jsx       # 챔피언 아이콘 (Data Dragon CDN)
│   │   ├── ui/ChampionBadge.jsx      # 챔피언 + 승률/KDA 뱃지
│   │   └── model/types.js
│   └── composition/
│       ├── ui/TeamCompCard.jsx       # 추천 조합 카드
│       ├── ui/TeamAnalysisChart.jsx  # AD/AP 비율 차트
│       └── model/types.js
│
└── shared/                           # Layer 6: 공유
    ├── api/
    │   └── client.js                 # axios/fetch 기본
    ├── ui/
    │   ├── Button.jsx
    │   ├── Card.jsx
    │   ├── Chart.jsx                 # recharts 래퍼
    │   ├── Input.jsx
    │   └── ProgressBar.jsx
    ├── lib/
    │   ├── formatWinRate.js
    │   ├── tierToScore.js            # 티어 → 점수 변환
    │   └── cn.js
    └── config/
        └── constants.js              # API URL, Data Dragon 버전
```

### 1-3. 기획서 → 코드 매핑 (스펙 드리븐)

| 기획서 섹션 | 백엔드 domain/ | 백엔드 adapters/ | 프론트 FSD |
|------------|---------------|-----------------|-----------|
| 2. 라인 배정 최적화 | models/player, services/lane_optimizer_service | api/optimize_router | features/analyze-comp, widgets/result-board |
| 3. 챔피언 조합 최적화 | models/composition, services/comp_optimizer_service | api/optimize_router | entities/composition, widgets/result-board |
| 4. 챔피언 속성 데이터 | models/champion, services/champion_data_service | persistence/champion_repo_impl | entities/champion |
| 5. 플레이어 데이터 수집 | models/player, services/player_analysis_service | external/riot_api_client, ddragon_client | entities/player, widgets/player-summary |
| API 키 입력 | - | api/optimize_router (헤더) | features/setup-api-key |
| 소환사명 입력 | - | api/optimize_router (요청 바디) | features/add-player, widgets/player-input-form |

---

## 2. 핵심 기능

### 2-1. 유저 플로우

```
1. API 키 입력 (프론트 로컬스토리지 저장)
2. 2~5명의 Riot ID (gameName#tagLine) 입력
3. "분석 시작" 클릭
4. 로딩 (플레이어 정보 조회 → 전적 분석)
5. 밴픽 화면:
   - 플레이어 요약 카드 (챔피언풀, 라인 선호도)
   - 밴 챔피언 입력 (밴된 챔피언은 추천에서 제외)
   - 적 팀 챔피언 입력 (적 픽은 아군 풀에서 제외)
   - 아군 챔피언 고정 (특정 플레이어의 챔피언을 잠금)
   - 변경할 때마다 실시간 추천 조합 업데이트
6. 결과: 추천 조합 카드 (상위 3~5개) + 조합 유형 + 운영 가이드
```

### 2-1-1. 2단계 API 구조

```
1단계: POST /api/analyze-players (느림, Riot API 호출)
  → 플레이어 데이터 수집 (라인별 승률, 챔피언풀, 티어 등)
  → 결과를 프론트 메모리에 보관

2단계: POST /api/optimize-comp (빠름, 순수 계산)
  → 이미 수집된 플레이어 데이터 + 밴 목록 + 적 픽 + 아군 고정 픽 + 포지션 고정
  → 밴/픽/포지션 변경할 때마다 반복 호출 가능
  → locked_positions: {"gameName#tagLine": "TOP"} — 플레이어를 특정 라인에 고정
  → 전수 탐색: 모든 라인 배정(최대 120) × 모든 챔피언 조합을 전부 탐색
  → 순수 조합 점수로만 순위 결정 (라인 배정 보너스 없음)
  → 밴/적픽으로 풀 부족 시 메타 챔피언(S>A>B 순)으로 자동 보충
  → 추천 다양성: 동일 챔피언 세트 중복 제거
  → 재분석 시 이전 밴/픽/포지션 필터 자동 초기화
```

### 2-2. 라인 배정 최적화

각 플레이어의 최근 N판에서 라인별 플레이 횟수 + 승률 추출.
5개 포지션(TOP, JG, MID, ADC, SUP)에 배치.

```
알고리즘: 전수 탐색
- 5명: 5! = 120가지
- 4명: 5P4 = 120가지
- 3명: 5P3 = 60가지
- 2명: 5P2 = 20가지

배치 점수 = Σ (해당 라인 승률 × 해당 라인 게임 수 가중치)

가중치:
  게임 수 10+: ×1.0
  게임 수 5~9: ×0.8
  게임 수 1~4: ×0.5
  게임 수 0: ×0.1 (경험 없는 라인 페널티)

상위 N개 라인 배정 후보를 챔피언 추천 단계로 전달.
```

### 2-3. 챔피언 조합 최적화

각 라인 배정 후보에 대해, 플레이어별 챔피언풀에서 팀 조합 점수가 최대인 픽 추천.

#### 조합 점수 산정

| 항목 | 가중치 | 설명 |
|------|--------|------|
| 개인 숙련도 | 25% | (챔피언 승률 × 게임수 가중치) + mastery_points 보너스 |
| 메타 적합도 | 10% | 챔피언의 해당 라인 메타 티어 (S~D). S=100, A=80, B=60, C=40, D=20 |
| AD/AP 밸런스 | 15% | 이상: AD 2~3, AP 2~3. 풀AD/풀AP 페널티 |
| 프론트라인 | 15% | 조합 유형별 조건부 적용 (포킹/픽/폭딜은 불필요) |
| 딜 구성 | 15% | 팀 전체 DPS 충분한지 |
| 웨이브클리어 | 10% | waveclear 속성 합산 |
| 스플릿푸시 | 10% | splitpush 속성 합산 |

#### 페널티 (감점)

```
풀 AD (AP 딜러 0명): -30점
풀 AP (AD 딜러 0명): -30점
웨이브클리어 총합 < 10: -10점
이니시 부족 (engage < 2*n): -10점
필링 부족 (peel < 1.5*n): -8점
팀파이트 부족 (teamfight < 3*n): -8점
오프라인 배정 (primary_lanes 밖): 챔피언당 -25점
```

#### 프론트라인 등급제 점수

기존 "프론트라인 0명: -25점" 페널티를 **삭제**하고, 조합 유형별 단계적 점수로 교체.
WEIGHT_FRONTLINE(15%)에 아래 점수를 적용:

```
[프론트라인 필수 조합] — 이니시, 프론트투백 한타, 프로텍트
  0명: 0점, 1명: 60점, 2명: 100점, 3명+: 80점

[프론트라인 불필요 조합] — 포킹, 픽, 폭딜/어쌔신
  0명: 80점, 1명: 100점, 2명+: 70점

[프론트라인 유연 조합] — 나머지
  0명: 50점, 1명: 85점, 2명: 100점, 3명+: 75점
```

#### 적 조합 카운터 점수

적 픽 **3개 이상** 입력 시 활성화. 적 조합 유형 추정 후 상성표 참조:

```
유리 상성: +8점, 불리 상성: -5점, 중립: 0점
total_score에 직접 가산 (가중치 미적용)
상성 관계: 섹션 3-2 "조합 상성 (카운터 관계)" 참조
복수 유형: 각 유형별 계산 후 평균
```

#### 챔피언 선택 알고리즘

```
전수 탐색:
  1. 모든 라인 배정 생성 (5명: 5!=120, 4명: 120, 3명: 60, 2명: 20)
  2. 각 라인 배정에 대해:
     a. 각 플레이어의 전체 챔피언풀 추출 (인위적 제한 없음)
     b. primary_lanes 필터: 해당 라인에 맞는 챔피언만 사용
     c. 모든 챔피언 조합 생성 및 점수 산정 (analyze()는 호출하지 않음)
  3. 전체 결과를 순수 조합 점수로 정렬
  4. 다양성 필터 적용 후 상위 5개 반환
  5. 최종 5개에 대해서만 analyze() 호출 (운영 가이드 등 상세 분석)

다양성 필터:
  - min_diff = max(1, n - 2)  (n=2→1, n=3→1, n=4→2, n=5→3)
  - 기존 결과와 min_diff개 이상 챔피언이 달라야 포함
  - 상위 5개 중 2가지 이상의 조합 유형(archetype) 포함 시도

밴/적픽으로 풀이 부족하면 메타 챔피언(S>A>B 순)으로 자동 보충.
메타 보충 시 플레이어 주 라인 기반 + 다른 플레이어와 중복 방지.
```

#### 점수 분해 (Score Breakdown)

각 추천 조합에 항목별 점수를 반환하여 추천 근거를 설명:

```json
"score_breakdown": {
  "personal_mastery": { "score": 78.5, "weighted": 19.6, "weight": 0.25 },
  "meta_tier":        { "score": 72.0, "weighted": 7.2,  "weight": 0.10 },
  "ad_ap_balance":    { "score": 90.0, "weighted": 13.5, "weight": 0.15 },
  "frontline":        { "score": 60.0, "weighted": 9.0,  "weight": 0.15 },
  "deal_composition": { "score": 85.0, "weighted": 12.8, "weight": 0.15 },
  "waveclear":        { "score": 70.0, "weighted": 7.0,  "weight": 0.10 },
  "splitpush":        { "score": 55.0, "weighted": 5.5,  "weight": 0.10 },
  "penalties":        { "details": ["-30: 풀 AD"], "total": -30.0 }
}
```

---

## 3. 챔피언 속성 데이터

### 3-1. 속성 스키마

```python
{
  "Aatrox": {
    "damage_type": "AD",        # "AD" | "AP" | "HYBRID"
    "role_tags": ["BRUISER"],    # TANK, BRUISER, ASSASSIN, MAGE, MARKSMAN, SUPPORT, ENCHANTER
    "waveclear": 4,              # 1~5
    "splitpush": 3,              # 1~5
    "teamfight": 4,              # 1~5
    "engage": 3,                 # 1~5
    "peel": 1,                   # 1~5
    "poke": 1,                   # 1~5 (원거리 견제 능력)
    "pick": 2,                   # 1~5 (고립된 적 잡는 능력)
    "burst": 3,                   # 1~5 (순간 폭딜 능력)
    "primary_lanes": ["TOP"],      # 챔피언이 본래 가는 라인 (TOP/JG/MID/ADC/SUP)
    "meta_tier": {"TOP": "S"},    # 라인별 메타 티어 (S/A/B/C/D). 현재 패치 기준
    "play_tips": "1~2레벨 강력한 올인. Q 3히트 후 E로 이니시, 궁 타이밍에 적극 교전."
  }
}
```

#### 메타 티어

- 라인별로 S/A/B/C/D 등급 부여 (현재 패치 기준)
- 점수 변환: S=100, A=80, B=60, C=40, D=20
- 예: 베인 {"ADC": "A", "TOP": "C"} → 원딜로 추천 시 80점, 탑으로 추천 시 40점
- 패치마다 JSON 업데이트 필요 (u.gg, op.gg 참고)

#### 챔피언 운영 팁 (play_tips)

- 챔피언별 핵심 운영법/콤보/파워 스파이크를 1~2문장으로 요약
- 조합 운영 가이드에 활용: 각 챔피언의 역할을 조합 맥락에서 설명

#### 조합 운영 가이드 생성 규칙

추천 조합의 운영 가이드는 **조합 유형 전략 + 챔피언별 역할**을 결합하여 생성:

```
예시: 스플릿 + 이니시 조합 (피오라 탑, 자르반 정글, 오리아나 미드, 징크스 원딜, 레오나 서폿)

[조합 전략]
스플릿 + 이니시 시너지: 피오라가 사이드를 밀면서...

[챔피언별 역할]
- 피오라 (탑): 사이드 라인 스플릿. 1v1은 자신 있게 받되 2명 오면 TP로 합류.
- 자르반 (정글): 이니시 담당. R로 적 캐리를 가두고 팀이 따라오면 승리.
- 오리아나 (미드): 자르반에게 공을 붙여 R 콤보. 한타에서 충격파 타이밍이 핵심.
- 징크스 (원딜): 프론트 뒤에서 안전하게 딜링. 킬 나면 패시브로 정리.
- 레오나 (서폿): 자르반 이니시 후 E-Q로 추가 CC. 원딜 보호도 겸임.
```

### 3-2. 조합 유형 분류 (12가지)

팀 전체 점수 합산으로 조합 유형(archetype) 판별 → 운영 가이드 제공.
복수 유형 해당 가능 (예: "스플릿 + 글로벌 조합"). 시너지 조합은 전용 운영 가이드.

#### 기본 유형

| 유형 | 판별 조건 | 프론트라인 | 승리 조건 | 파워 스파이크 |
|------|----------|----------|----------|------------|
| 이니시 | engage ≥ 15 | **필수** (이니시에이터=프론트) | 오브젝트 앞 5v5 강제, CC 체인으로 타겟 폭파 | 미드(6렙 궁) |
| 디스인게이지 | peel ≥ 14, engage < 10 | 불필요 (필링 챔프면 충분) | 상대 이니시 무력화 → 쿨 빠진 틈에 역습 | 후반 |
| 포킹/시즈 | poke ≥ 14 | **불필요** (디스인게이지 필요) | 포킹으로 적 체력 50% 이하 → 시즈 or 오브젝트 | 미드 |
| 픽/캐치 | pick ≥ 14 | 불필요 (캐치 도구가 핵심) | 시야 장악 → 혼자 있는 적 캐치 → 4v5 오브젝트 | 미드 |
| 스플릿 | splitpush ≥ 14, 스플릿러(splitpush≥4) 1명+ | 유연 (스플릿러=브루저, 4인=디스인게이지) | 1-3-1 또는 1-4 사이드 압박, 상대 딜레마 유도 | 미드~후반 |
| 프론트투백 한타 | teamfight ≥ 18, TANK/BRUISER 1명+ | **필수** (조합의 핵심) | 정면 5v5, 탱커가 쿨흡수 + 원딜 안전 딜링 | 후반 |
| 프로텍트 | peel ≥ 12, MARKSMAN 1명+ | **필수** (필링용, 돌진X) | 하이퍼캐리 3코어 이후 그룹 → 원딜 중심 한타 | 후반 |
| 다이브 | engage ≥ 12, burst ≥ 12, peel < 8 | 돌진형 탱커/다이버 | 백라인 직행 → 적 원딜/미드 2초 내 삭제 | 미드 |
| 스커미시/초반 | 초반형 챔프(ASSASSIN/BRUISER) 3명+ | 브루저=pseudo 프론트 | 25분 안에 끝내기, 모든 초반 싸움 승리 → 스노우볼 | **초반** |
| 궁합(Wombo) | engage ≥ 12, teamfight ≥ 15, AoE 궁 2명+ | 이니시에이터만 (2~3초 버틸 정도) | 3명 이상에게 AoE 풀콤보 → 즉시 올킬 | 미드(6렙+1코어) |
| 글로벌 | 글로벌/반글로벌 궁 2명+ | 유연 | 맵 어디서든 숫자 우위 (봇 3v2 등) | 미드 |
| 폭딜/어쌔신 | burst ≥ 16, ASSASSIN 2명+ | **불필요** (죽이는 게 방어) | 적 캐리 원샷 → 4v5 | 미드(1~2코어) |

#### 프론트라인 페널티 조건부 적용

```
프론트라인 0명 페널티(-25점)를 적용하는 조합: 이니시, 프론트투백 한타, 프로텍트
프론트라인 0명이어도 감점 없는 조합: 포킹, 픽, 폭딜/어쌔신, 다이브(돌진형이면 OK)
나머지: 프론트라인 있으면 +보너스, 없어도 감점 없음
```

#### 시너지 조합 (복합 유형 운영 가이드)

| 시너지 | 운영법 |
|--------|--------|
| 스플릿 + 글로벌 | 스플릿러가 사이드 압박 + 글로벌 궁으로 즉시 합류. 쉔 스플릿 → 봇 싸움 나면 쉔 R로 순간 5v4 |
| 포킹 + 디스인게이지 | 포킹으로 깎다가 적이 들어오면 잔나 R 등으로 끊고 다시 포킹. 반복하여 적 소모 |
| 이니시 + 궁합 | 이니시 타이밍에 AoE 궁 연쇄. 말파 R → 오리아나 R → 미포 R. 좁은 지형 필수 |
| 이니시 + 한타 | 탱커가 이니시 + 프론트라인 겸임. 정면 5v5에서 CC 체인 후 원딜 안전 딜링 |
| 픽 + 다이브 | 시야로 적 위치 파악 → 녹턴 R 등으로 고립된 적 다이브. 잡고 오브젝트 전환 |
| 스플릿 + 픽 | 스플릿으로 적 분산 유도 → 이동 중인 적을 캐치. 소규모 교전에서 숫자 우위 |
| 프로텍트 + 디스인게이지 | 원딜 보호에 올인. 적 돌진 전부 끊고 원딜 안전 딜링 극대화 |
| 다이브 + 폭딜 | 전원 백라인 직행. 다이버가 CC → 어쌔신이 원샷. 교전 2~3초 내 종결 |

#### 조합 상성 (카운터 관계)

```
이니시   → 포킹, 스플릿을 이김  |  디스인게이지, 픽에 약함
디스인게이지 → 이니시, 다이브를 이김  |  스플릿, 포킹에 약함
포킹     → 디스인게이지, 스케일링을 이김  |  이니시, 서스테인에 약함
픽       → 포킹, 스플릿을 이김  |  디스인게이지, 뭉치는 팀에 약함
스플릿    → 포킹, 디스인게이지를 이김  |  이니시, 픽에 약함
한타     → 이니시(스케일 충분 시)를 이김  |  다이브, 스플릿에 약함
프로텍트   → 한타, 포킹(후반)을 이김  |  다이브, 어쌔신, 초반 어그로에 약함
다이브    → 프로텍트, 한타를 이김  |  디스인게이지, 필링에 약함
폭딜     → 물몸 조합, 포킹을 이김  |  탱커, 존야/GA, 필링에 약함
```

### 3-3. 챔피언 데이터

#### 한글 이름

- 모든 챔피언은 한글 이름(`champion_name_ko`)을 가짐
- Data Dragon ko_KR 데이터에서 자동 매핑
- UI에서는 한글 이름으로 표시, 정렬은 한글 가나다순

### 3-4. 데이터 구축 전략

```
1순위: 주요 챔피언 80~100개 수동 속성 입력 (JSON)
2순위: 나머지는 Data Dragon 태그 기반 자동 기본값:
  tags: ["Tank"]     → damage_type 추정, waveclear=3, teamfight=3
  tags: ["Assassin"] → splitpush=3, teamfight=2
  tags: ["Mage"]     → damage_type="AP", waveclear=4
  tags: ["Marksman"] → damage_type="AD", teamfight=3
  tags: ["Support"]  → peel=4, engage=3
3순위: 추후 프로 경기 데이터 기반 보정
```

---

## 4. Riot API

### 4-1. 엔드포인트

API 키는 유저가 직접 발급. 프론트에서 입력, 백엔드 요청 시 헤더 전달.

**리전 설정:**
- Account-v1, Match-v5 → `https://asia.api.riotgames.com` (아시아)
- Summoner-v4, League-v4, Mastery-v4 → `https://kr.api.riotgames.com` (한국)

| API | 엔드포인트 | 용도 |
|-----|-----------|------|
| Account-v1 | `GET /riot/account/v1/accounts/by-riot-id/{name}/{tag}` | Riot ID → puuid |
| Summoner-v4 | `GET /lol/summoner/v4/summoners/by-puuid/{puuid}` | 소환사 기본 정보 |
| League-v4 | `GET /lol/league/v4/entries/by-summoner/{id}` | 랭크/티어 |
| Match-v5 | `GET /lol/match/v5/matches/by-puuid/{puuid}/ids?count=N&queue={queueId}` | 매치 ID 목록 (큐별 조회) |
| Match-v5 | `GET /lol/match/v5/matches/{matchId}` | 매치 상세 |
| Mastery-v4 | `GET /lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count=30` | 챔피언 숙련도 |
| Data Dragon | `GET /cdn/{ver}/data/ko_KR/champion.json` | 챔피언 정적 데이터 |

**Rate Limit (Development Key):** 20 req/초, 100 req/2분

### 4-2. API 키 발급 가이드

```
1. https://developer.riotgames.com/ 접속
2. 라이엇 계정 로그인
3. 대시보드에서 Development API Key 확인
4. ⚠️ Dev Key는 24시간마다 만료 → 매일 갱신 필요
5. 장기 사용: 앱 등록 → Personal Key 신청 (승인 1~2주)
```

### 4-3. Rate Limiter

```python
# 슬라이딩 윈도우 방식
# 1초 윈도우: 최대 18회 (20 중 여유 마진)
# 2분 윈도우: 최대 95회 (100 중 여유 마진)
# 429 응답 시 Retry-After만큼 대기 후 재시도
```

### 4-4. Rate Limit 주의

```
5명 × 20매치 상세 = 최대 100+ 요청 → 2분 이상 소요 가능
→ 매치 수 조절 가능하게 (기본 15, 옵션으로 변경)
→ 프론트에서 프로그레스바로 대기 체감 줄이기
```

### 4-5. 챔피언 아이콘

```
Data Dragon CDN:
https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{championName}.png
```

---

## 5. 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python 3.11+, **FastAPI** |
| HTTP Client | httpx (async) |
| DB | **SQLite** (챔피언 속성 저장, 추후 PostgreSQL) |
| ORM | SQLModel |
| Frontend | **React 18** + Vite |
| 스타일링 | Tailwind CSS |
| 차트 | recharts (AD/AP 비율, 라인 선호도) |
| 상태관리 | zustand |
| API | Riot Games API, Data Dragon |

---

## 6. 백엔드 설계

### 6-1. DB 스키마

```python
# 챔피언 속성 (앱 시작 시 seed, 패치마다 업데이트)
class ChampionAttribute:
    id: int (PK)
    champion_id: int              # Riot champion ID (ex: 266 = Aatrox)
    champion_name: str            # "Aatrox"
    damage_type: str              # "AD" | "AP" | "HYBRID"
    role_tags: str                # JSON '["BRUISER"]'
    waveclear: int                # 1~5
    splitpush: int                # 1~5
    teamfight: int                # 1~5
    engage: int                   # 1~5
    peel: int                     # 1~5
    source: str                   # "MANUAL" | "AUTO" (Data Dragon 기반 자동)
    updated_at: datetime
```

나머지 데이터(플레이어 전적, 매치 결과 등)는 DB에 저장하지 않고
Riot API에서 실시간 조회 → 메모리에서 분석 → 결과 반환.
(캐싱은 2차 고도화에서 Redis 등 검토)

### 6-2. API 엔드포인트

```
POST /api/optimize
```

**Request:**
```json
{
  "api_key": "RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "players": [
    { "game_name": "Hide on bush", "tag_line": "KR1" },
    { "game_name": "Faker", "tag_line": "1234" }
  ],
  "match_count": 15,
  "queues": [420, 440]
}
```

**Response:**
```json
{
  "players": [
    {
      "game_name": "Hide on bush",
      "tag_line": "KR1",
      "tier": "CHALLENGER",
      "rank": "I",
      "lp": 1200,
      "profile_icon_id": 4567,
      "lane_stats": {
        "MID": { "games": 15, "wins": 10, "win_rate": 0.667 },
        "TOP": { "games": 3, "wins": 1, "win_rate": 0.333 }
      },
      "top_champions": [
        {
          "champion_id": 238,
          "champion_name": "Zed",
          "games": 8,
          "wins": 6,
          "win_rate": 0.75,
          "kda": 3.2,
          "mastery_points": 500000
        }
      ]
    }
  ],
  "recommendations": [
    {
      "rank": 1,
      "total_score": 87.5,
      "assignments": [
        {
          "player": "Hide on bush#KR1",
          "lane": "MID",
          "champion": "Zed",
          "champion_id": 238,
          "personal_win_rate": 0.75,
          "personal_kda": 3.2
        }
      ],
      "team_analysis": {
        "ad_ratio": 0.6,
        "ap_ratio": 0.4,
        "has_frontline": true,
        "waveclear_score": 16,
        "splitpush_score": 12,
        "teamfight_score": 18,
        "strengths": ["균형 잡힌 AD/AP 비율", "강력한 스플릿 옵션"],
        "weaknesses": ["이니시에이트 부족"]
      }
    }
  ]
}
```

**추가 엔드포인트:**

```
GET /api/champions                    # 전체 챔피언 속성 목록
GET /api/champions/{champion_id}      # 챔피언 속성 상세
GET /api/health                       # 서버 상태 체크
```

---

## 7. 프론트엔드 설계

### 7-1. 주요 화면 (3개)

**화면 1: 입력**
- 상단: API 키 입력 (로컬스토리지 저장, 마스킹)
- 중앙: 소환사명 입력 필드 2~5개 (동적 추가/제거)
  - 이름#태그 형식
- 하단: 매치 수 선택 (10/15/20), "분석 시작" 버튼

**화면 2: 로딩**
- 단계별 프로그레스:
  - "1/5 플레이어 정보 조회 중..."
  - "3/5 전적 분석 중..."
- 각 플레이어 수집 완료 시 개별 표시 (이름 + 티어 아이콘)

**화면 3: 밴픽**
- 상단: 플레이어 요약 카드 (챔피언풀, 라인 선호도)
- 좌측: 밴/픽 패널
  - 밴 챔피언 입력 (최대 10개, 추천에서 제외)
  - 적 팀 챔피언 입력 (5슬롯, 아군 풀에서 제외)
  - 아군 챔피언 고정 (특정 플레이어의 챔피언 잠금)
- 우측: 추천 조합 (밴/픽 변경 시 실시간 업데이트)
  - 조합 유형 (이니시, 포킹, 픽, 스플릿, 한타, 프로텍트, 폭딜)
  - 운영 가이드
  - 강점/약점, AD/AP 비율 차트

**화면 4: 결과 상세**
- 추천 조합 카드 (크게, 랭킹 순)
  - 라인별 플레이어+챔피언 배치도
  - 종합 점수, 팀 능력치 차트, 운영 가이드

---

## 8. 고려사항

### Rate Limit
- Dev Key: 20 req/초, 100 req/2분
- 5명 × (계정+소환사+랭크+마스터리+매치ID+매치상세×15) ≈ 90~100 요청
- 2분 윈도우에 걸릴 수 있음 → Rate Limiter 필수 + 프로그레스 UX

### 매치 데이터 수집
- 소환사 협곡 5v5만: 솔랭(420), 자랭(440), 일반 드래프트(400), 일반 블라인드(430)
- 칼바람(450), URF 등 특수모드 제외 (큐별 API 호출로 원천 차단)
- 큐별로 N개씩 조회 → 최신순 정렬 → 상위 N개 사용
- 정글 판별: teamPosition 대신 강타(Smite, spell ID 11) 보유 여부로 판단
- 라인 배정: 매치에서의 실제 라인이 아닌 챔피언의 `primary_lanes` 기준 추천
- 챔피언 풀 보강: 최근 매치 데이터가 부족하면 Mastery-v4 숙련도 데이터(모스트)로 보충
  - 매치 기반 챔피언이 5개 미만일 경우, 숙련도 상위 챔피언 추가
  - 숙련도 전용 챔피언은 승률/KDA 없이 mastery_points 기반으로 추천
- 최근 3개월 이내 매치만 조회 (startTime 파라미터). 3개월 이상 된 데이터는 무시
- 소환사 협곡 매치가 없으면 숙련도(모스트) 데이터만으로 추천

### 챔피언 속성 유지보수
- 패치마다 리워크/신챔 시 JSON 업데이트 필요
- v1: 수동 (champion_attributes.json)
- v2: 프로 매치 데이터 기반 자동 추정

### API 키 보안
- 서버 DB에 저장 안 함
- 프론트 로컬스토리지에만 보관
- 요청 시 헤더로 전달 → 백엔드 메모리에만 보유, 요청 종료 후 폐기

---

## 9. 개선 로드맵

### 구현 대상 (P0~P2)

| 우선순위 | 항목 | 유형 | 상태 |
|---------|------|------|------|
| P0 | analyze() 최적화 — 최종 top-N에 대해서만 호출 | 성능 | 미구현 |
| P0 | Session persistence — sessionStorage로 새로고침 시 상태 유지 | UX | 미구현 |
| P1 | 다양성 필터 강화 — min_diff=max(1,n-2) + archetype 다양성 | 알고리즘 | 미구현 |
| P1 | 점수 분해 / "Why This Comp" — 항목별 점수 시각화 | UX | 미구현 |
| P1 | 단계적 프론트라인 점수 — 이진→등급제 | 알고리즘 | 미구현 |
| P1 | 클립보드 복사 — 로비 채팅용 텍스트 복사 | UX | 미구현 |
| P2 | 적 조합 카운터 점수 — 상성 기반 보너스/패널티 | 알고리즘 | 미구현 |
| P2 | 접이식 조합 카드 — 1위 펼침, 나머지 접힘 | UX | 미구현 |
| P2 | 플렉스 픽 감지 — 2+ 라인 챔피언 표시 | 알고리즘 | 미구현 |

### v2 이관 (설계만 기록)

| 항목 | 설명 |
|------|------|
| SSE 로딩 진행률 | analyze-players 전용 실시간 프로그레스 |
| 밴 추천 | 아군 조합 약점 기반 밴 챔피언 자동 추천 |
| 드래프트 페이즈 통합 | 실제 드래프트 순서대로 단계별 추천 |
| 파워 스파이크 일관성 | early/mid/late 일치 여부 점수 반영 |

### 거부된 항목

| 항목 | 거부 사유 |
|------|----------|
| 티어 기반 라인 점수 | 캐주얼 그룹(실버~골드)에서 불공정. 게임수 가중치로 충분 |
| CC 속성 별도 추가 | (engage+peel)/2 프록시로 충분. 171개 수동 입력 비용 과다 |
| 라인 매치업 인식 | 패치마다 변동, 유지보수 비용 과다 |

### 구현 순서

```
Phase 5a (P0, 백엔드 우선):
  [ ] analyze() 최적화 — optimize() 내 analyze() top-N 지연 호출
  [ ] Session persistence — zustand + sessionStorage

Phase 5b (P1, 백엔드 + 프론트):
  [ ] 단계적 프론트라인 점수 — 기존 -25 페널티 삭제, 등급제 교체
  [ ] 점수 분해 — ScoreBreakdown 모델 + calculate_score 리팩토링
  [ ] 다양성 필터 강화 — diversity_filter 교체
  [ ] 클립보드 복사 — 프론트 전용

Phase 5c (P2):
  [ ] 적 조합 카운터 점수 — _calculate_counter_score() 추가
  [ ] 접이식 조합 카드 — TeamCompCard 접힘/펼침
  [ ] 플렉스 픽 감지 — is_flex, flex_lanes 필드 추가
```

---

## 10. 확장 아이디어

- **내전 밸런스**: 10명 입력 → 5v5 팀 분배 + 각 팀 조합 추천
- **공유 링크**: 추천 결과 URL 생성
- **메타 연동**: 프로 경기 데이터 기반 메타 조합 DB
- **캐싱**: Redis로 최근 조회 결과 캐싱 (동일 멤버 재조회 시 빠르게)
- **다른 서버**: KR 외 다른 리전 지원

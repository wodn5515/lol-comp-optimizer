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
  → 이미 수집된 플레이어 데이터 + 밴 목록 + 적 픽 + 아군 고정 픽
  → 밴/픽 변경할 때마다 반복 호출 가능
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
| 개인 숙련도 | 30% | (챔피언 승률 × 게임수 가중치) + mastery_points 보너스. 숙련도 10만+: +0.3, 5만+: +0.2, 1만+: +0.1 |
| AD/AP 밸런스 | 20% | 이상: AD 2~3, AP 2~3. 풀AD/풀AP 페널티 |
| 프론트라인 | 15% | 탱커/브루저 최소 1명 필수 |
| 딜 구성 | 15% | 팀 전체 DPS 충분한지 |
| 웨이브클리어 | 10% | waveclear 속성 합산 |
| 스플릿푸시 | 10% | splitpush 속성 합산 |

#### 페널티 (감점)

```
풀 AD (AP 딜러 0명): -30점
풀 AP (AD 딜러 0명): -30점
프론트라인 0명: -25점
웨이브클리어 총합 < 10: -10점
```

#### 챔피언 선택 알고리즘

```
각 라인 배정에 대해:
  1. 각 플레이어의 해당 라인 챔피언풀 추출 (숙련도 상위 5개)
  2. 5명의 챔피언풀 조합 (최대 5^5 = 3,125가지)
     → 챔피언풀이 작으면 훨씬 적음
  3. 각 조합에 대해 점수 산정
  4. 상위 3~5개 조합 반환

최종 결과: 라인 배정 × 챔피언 조합의 종합 점수 기준 상위 3~5개
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
    "primary_lanes": ["TOP"]      # 챔피언이 본래 가는 라인 (TOP/JG/MID/ADC/SUP)
  }
}
```

### 3-2. 조합 유형 분류

팀 전체 점수 합산으로 조합 유형(archetype) 판별 → 운영 가이드 제공.

| 유형 | 판별 조건 | 운영 방법 |
|------|----------|----------|
| 이니시 조합 | engage ≥ 15 | 한타 유도, 이니시 타이밍에 오브젝트 싸움 |
| 포킹 조합 | poke ≥ 14 | 오브젝트 앞 포킹으로 체력 깎기, 정면 한타 피하기 |
| 픽 조합 | pick ≥ 14 | 시야 장악 후 고립된 적 캐치, 소규모 교전 유도 |
| 스플릿 조합 | splitpush ≥ 14, 스플릿러 1명+ | 1-3-1 또는 1-4 운영, 사이드 압박 |
| 한타 조합 | teamfight ≥ 18 | 5:5 정면 한타, 좁은 지형 활용 |
| 프로텍트 조합 | peel ≥ 12, MARKSMAN 1명+ | 원딜 중심 포지셔닝, 원딜 보호 우선 |
| 폭딜 조합 | burst ≥ 16 | 핵심 타겟 순삭, 빠른 교전 종결 |

복수 유형 해당 가능 (예: "이니시 + 한타 조합").

### 3-2. 데이터 구축 전략

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
- 최근 시즌만 유의미

### 챔피언 속성 유지보수
- 패치마다 리워크/신챔 시 JSON 업데이트 필요
- v1: 수동 (champion_attributes.json)
- v2: 프로 매치 데이터 기반 자동 추정

### API 키 보안
- 서버 DB에 저장 안 함
- 프론트 로컬스토리지에만 보관
- 요청 시 헤더로 전달 → 백엔드 메모리에만 보유, 요청 종료 후 폐기

---

## 9. 확장 아이디어

- **상대 팀 입력**: 상대 챔피언 입력 시 카운터 픽 추천
- **밴 반영**: 밴 리스트 입력 → 밴된 챔피언 제외 후 추천
- **내전 밸런스**: 10명 입력 → 5v5 팀 분배 + 각 팀 조합 추천
- **공유 링크**: 추천 결과 URL 생성
- **메타 연동**: 프로 경기 데이터 기반 메타 조합 DB
- **캐싱**: Redis로 최근 조회 결과 캐싱 (동일 멤버 재조회 시 빠르게)
- **다른 서버**: KR 외 다른 리전 지원

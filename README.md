# LoL Comp Optimizer

2~5명의 소환사명을 입력하면 Riot API로 전적과 챔피언풀을 분석하여 **최적 라인 배정 + 챔피언 조합**을 추천하는 웹앱입니다.

## 주요 기능

- **플레이어 분석**: 최근 전적(솔랭/자랭/일반) + 챔피언 숙련도(모스트) 기반 챔피언풀 파악
- **라인 배정 최적화**: 전수 탐색으로 최적의 라인 배정 계산
- **챔피언 조합 추천**: AD/AP 밸런스, 프론트라인, 팀파이트, 포킹 등 다양한 지표 기반 점수 산정
- **조합 유형 판별**: 이니시/포킹/픽/스플릿/한타/프로텍트/폭딜 조합 자동 분류 + 운영 가이드
- **실시간 밴픽**: 챔피언 밴, 적 팀 픽, 아군 고정 픽을 반영하여 실시간 추천 업데이트
- **멀티서치**: 롤 로비 채팅 복붙으로 소환사 자동 입력
- **챔피언 본래 라인 기반 추천**: primary_lanes 데이터로 뽀삐 원딜 같은 비정상 추천 방지

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python 3.12, FastAPI, httpx (async), SQLModel, SQLite |
| Frontend | React 19, Vite, Tailwind CSS v4, zustand, recharts |
| Infra | Docker Compose (backend + nginx) |
| API | Riot Games API, Data Dragon |
| Architecture | Backend: 헥사고날 (포트앤어댑터) / Frontend: Feature-Sliced Design |

## 빠른 시작 (Docker)

```bash
git clone git@github.com:wodn5515/lol-comp-optimizer.git
cd lol-comp-optimizer
docker compose up -d --build
```

브라우저에서 **http://localhost:3000** 접속

## 로컬 개발

```bash
# 백엔드
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 프론트엔드 (별도 터미널)
cd frontend
npm install
npm run dev
```

- 프론트엔드: http://localhost:5173
- 백엔드 API 문서: http://localhost:8000/docs

## 사용법

### 1. API 키 발급

1. [Riot Developer Portal](https://developer.riotgames.com/) 접속
2. 라이엇 계정으로 로그인
3. 대시보드에서 **Development API Key** 복사
4. Dev Key는 24시간마다 만료되므로 매일 갱신 필요

### 2. 소환사 입력

API 키를 입력한 후, 2~5명의 소환사를 입력합니다.

**직접 입력:**
```
소환사이름#태그
```

**멀티서치 (롤 로비 채팅 복붙):**

`멀티서치` 버튼을 클릭하고 롤 로비 채팅을 그대로 붙여넣으세요:

```
미 키 #0313 님이 로비에 참가하셨습니다.
dlwldms #iuiu 님이 로비에 참가하셨습니다.
hle pyeonsik #HLE 님이 로비에 참가하셨습니다.
```

또는 쉼표로 구분:
```
미 키 #0313,dlwldms #iuiu,hle pyeonsik #HLE
```

### 3. 분석 시작

`분석 시작` 버튼을 클릭하면 Riot API를 통해 플레이어 데이터를 수집합니다.

- 소환사 협곡 5v5만 분석 (솔랭, 자랭, 일반)
- 칼바람, URF 등 특수 모드는 제외
- 최근 매치가 적은 경우 숙련도(모스트) 데이터로 보충

### 4. 밴픽

분석이 완료되면 밴픽 화면으로 이동합니다.

- **밴**: 밴할 챔피언을 입력하면 추천에서 제외
- **적 팀 픽**: 상대방이 선택한 챔피언 입력 (아군 풀에서도 제외)
- **아군 고정 픽**: 특정 플레이어의 챔피언을 고정
- 변경할 때마다 **실시간으로 추천 조합이 업데이트**됩니다

### 5. 추천 결과 확인

각 추천 조합 카드에서 확인할 수 있는 정보:

- **종합 점수** (100점 만점)
- **라인별 배정**: 5개 포지션(탑/정글/미드/원딜/서포터)에 플레이어 + 챔피언
- **조합 유형**: 이니시, 포킹, 픽, 스플릿, 한타, 프로텍트, 폭딜 조합
- **운영 가이드**: 조합 유형에 맞는 플레이 전략
- **팀 분석**: AD/AP 비율, 팀파이트/이니시/포킹/캐치/폭딜/클리어/스플릿/필링 점수
- **강점/약점**: 조합의 장단점

## 점수 산정 기준

| 항목 | 가중치 | 설명 |
|------|--------|------|
| 개인 숙련도 | 30% | 승률 × 게임수 + 숙련도(모스트) 보너스 |
| AD/AP 밸런스 | 20% | 풀 AD/AP 시 -30점 페널티 |
| 프론트라인 | 15% | 탱커/브루저 0명 시 -25점 페널티 |
| 딜 구성 | 15% | 팀파이트 능력치 합산 |
| 웨이브클리어 | 10% | 합산 < 10 시 -10점 페널티 |
| 스플릿푸시 | 10% | 스플릿 능력치 합산 |

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/analyze-players` | 플레이어 데이터 수집 (Riot API 호출) |
| POST | `/api/optimize-comp` | 조합 최적화 (밴/픽 반영, 순수 계산) |
| POST | `/api/optimize` | 원샷 분석+최적화 (레거시) |
| GET | `/api/champions` | 챔피언 속성 목록 |
| GET | `/api/health` | 서버 상태 |

## 프로젝트 구조

```
lol-comp-optimizer/
├── backend/                     # FastAPI 백엔드 (헥사고날 아키텍처)
│   ├── domain/                  # 핵심 도메인 (외부 의존 없음)
│   │   ├── models/              # Player, Champion, Composition, Match
│   │   ├── services/            # 비즈니스 로직 (최적화 알고리즘)
│   │   └── ports/               # ABC 인터페이스
│   ├── adapters/                # 어댑터 (포트 구현체)
│   │   ├── inbound/api/         # FastAPI 라우터
│   │   └── outbound/            # Riot API, DB, Data Dragon
│   ├── champion_attributes.json # 145개 챔피언 속성 데이터
│   └── tests/                   # 85개 테스트 (unit + integration + e2e)
├── frontend/                    # React 프론트엔드 (FSD 아키텍처)
│   └── src/
│       ├── app/                 # 라우터, 프로바이더
│       ├── pages/               # 홈, 밴픽, 결과
│       ├── widgets/             # 입력폼, 밴픽패널, 결과보드
│       ├── features/            # API키, 분석, 플레이어 추가
│       ├── entities/            # 플레이어, 챔피언, 조합
│       └── shared/              # 공통 UI, API 클라이언트
├── docker-compose.yml
└── docs/                        # 기획서, 개발 프로세스
```

## 테스트

```bash
cd backend
python -m pytest tests/ -v --cov=domain
```

- Unit 테스트 59개: 도메인 서비스 (라인 최적화, 조합 점수, 챔피언 데이터)
- Integration 테스트 18개: API 엔드포인트 전체 플로우
- E2E 테스트 8개: 밴/픽 포함 전체 시나리오

## 챔피언 데이터

145개 챔피언에 대해 다음 속성을 수동 설정:

- `damage_type`: AD / AP / HYBRID
- `role_tags`: TANK, BRUISER, ASSASSIN, MAGE, MARKSMAN, SUPPORT
- `primary_lanes`: 본래 라인 (TOP, JG, MID, ADC, SUP)
- 능력치: waveclear, splitpush, teamfight, engage, peel, poke, pick, burst (각 1~5)

## Rate Limit

Riot API Development Key 기준:
- 1초: 최대 18회 (20 중 마진)
- 2분: 최대 95회 (100 중 마진)
- 429 응답 시 Retry-After 대기 후 자동 재시도

5명 분석 시 약 90~100회 API 호출 → 2분 내외 소요

## 라이선스

MIT

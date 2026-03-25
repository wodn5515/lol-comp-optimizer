# LoL Comp Optimizer

2~5명의 소환사명을 입력하면 Riot API로 전적과 챔피언풀을 분석하여 **최적 라인 배정 + 챔피언 조합**을 추천하는 웹앱입니다.

## 주요 기능

- **전수 탐색**: 모든 라인 배정(최대 120) × 모든 챔피언 조합을 전부 탐색하여 최적 조합 도출
- **플레이어 분석**: 최근 3개월 전적(솔랭/자랭/일반) + 챔피언 숙련도(모스트) 기반 챔피언풀 파악
- **메타 티어 반영**: 패치 26.6 기준 챔피언별 라인 티어(S~D) 점수 반영 (10%)
- **12가지 조합 유형 판별**: 이니시, 디스인게이지, 포킹, 픽, 스플릿, 한타, 프로텍트, 다이브, 스커미시, 궁합, 폭딜 + 시너지 조합
- **조합별 운영 가이드**: 조합 전략 + 챔피언별 역할 설명 (콤보, 파워 스파이크 포함)
- **약점 감점 반영**: 이니시 부족(-10), 필링 부족(-8), 팀파이트 부족(-8) 등 약점이 실제 점수에 반영
- **조건부 프론트라인 평가**: 포킹/픽/폭딜 조합은 프론트라인 없어도 감점 없음
- **실시간 밴픽**: 챔피언 밴, 적 팀 픽, 아군 고정 픽, **포지션 고정** 반영 → 실시간 추천 업데이트
- **메타 챔피언 자동 보충**: 밴/적픽으로 풀 부족 시 S>A>B 티어 순으로 메타 챔피언 추가
- **멀티서치**: 롤 로비 채팅 복붙으로 소환사 자동 입력
- **챔피언 한글 표시**: 145개 챔피언 한글 이름, 가나다순 정렬, 한글+영문 검색
- **챔피언 운영 팁**: 145개 챔피언별 콤보/파워 스파이크/핵심 플레이 한글 가이드

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
- 최근 3개월 이내 매치만 분석
- 매치가 적은 경우 숙련도(모스트) 데이터로 보충

### 4. 밴픽

분석이 완료되면 밴픽 화면으로 이동합니다.

- **밴**: 밴할 챔피언을 입력하면 추천에서 제외 (풀 부족 시 메타 챔피언 자동 보충)
- **적 팀 픽**: 상대방이 선택한 챔피언 입력 (아군 풀에서도 제외)
- **포지션 고정**: 특정 플레이어를 특정 라인에 고정 (탑/정글/미드/원딜/서폿)
- **아군 고정 픽**: 특정 플레이어의 챔피언을 고정 (해당 챔피언 라인으로 배정)
- 변경할 때마다 **실시간으로 추천 조합이 업데이트**됩니다
- 재분석 시 이전 밴/픽/포지션 설정은 자동 초기화

### 5. 추천 결과 확인

각 추천 조합 카드에서 확인할 수 있는 정보:

- **종합 점수** (100점 만점)
- **라인별 배정**: 5개 포지션에 플레이어 + 챔피언 (한글 이름)
- **조합 유형**: 12가지 유형 자동 판별 + 시너지 조합
- **운영 가이드**: 조합 전략 + 챔피언별 역할 (콤보, 파워 스파이크)
- **팀 분석**: AD/AP 비율, 8개 능력치 차트 (한타/이니시/포킹/캐치/폭딜/클리어/스플릿/필링)
- **강점/약점**: 조합의 장단점

## 조합 유형 (12가지)

| 유형 | 프론트라인 | 설명 |
|------|----------|------|
| 이니시 | 필수 | CC 체인으로 한타 강제 |
| 디스인게이지 | 불필요 | 적 이니시 무력화 후 역습 |
| 포킹/시즈 | **불필요** | 원거리 스킬로 체력 소모 후 시즈 |
| 픽/캐치 | **불필요** | 시야 장악 → 고립된 적 캐치 |
| 스플릿 | 유연 | 1-3-1 또는 1-4 사이드 압박 |
| 프론트투백 한타 | 필수 | 탱커 앞, 원딜 뒤에서 정면 5v5 |
| 프로텍트 | 필수(필링) | 하이퍼캐리 보호 중심 |
| 다이브 | 돌진형 | 백라인 직행 → 캐리 순삭 |
| 스커미시 | 유연 | 초반 소규모 교전 → 스노우볼 |
| 궁합(Wombo) | 이니시만 | AoE 궁 연쇄 → 올킬 |
| 폭딜/어쌔신 | **불필요** | 핵심 타겟 원샷 |

시너지 조합: 스플릿+글로벌, 포킹+디스인게이지, 이니시+궁합, 픽+다이브 등 8가지 전용 전략

## 점수 산정 기준

| 항목 | 가중치 | 설명 |
|------|--------|------|
| 개인 숙련도 | 25% | 승률 × 게임수 + 숙련도(모스트) 보너스 |
| 메타 적합도 | 10% | 챔피언의 해당 라인 메타 티어 (S=100, D=20) |
| AD/AP 밸런스 | 15% | 풀 AD/AP 시 -30점 페널티 |
| 프론트라인 | 15% | 조합 유형별 조건부 적용 |
| 딜 구성 | 15% | 팀파이트 능력치 합산 |
| 웨이브클리어 | 10% | 합산 < 10 시 -10점 페널티 |
| 스플릿푸시 | 10% | 스플릿 능력치 합산 |

**추가 감점:**
- 풀 AD/AP: -30점 / 프론트라인 0명(조건부): -25점 / 웨이브클리어 부족: -10점
- 이니시 부족: -10점 / 필링 부족: -8점 / 팀파이트 부족: -8점
- 오프라인 배정: 챔피언당 -25점

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
│   ├── champion_attributes.json # 145개 챔피언 데이터 (속성, 한글 이름, 메타 티어, 운영 팁)
│   └── tests/                   # 98개 테스트 (unit + integration + e2e)
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

## 챔피언 데이터

145개 챔피언에 대해 다음 데이터를 관리:

- `champion_name_ko`: 한글 이름 (아트록스, 징크스 등)
- `damage_type`: AD / AP / HYBRID
- `role_tags`: TANK, BRUISER, ASSASSIN, MAGE, MARKSMAN, SUPPORT
- `primary_lanes`: 본래 라인 (TOP, JG, MID, ADC, SUP)
- `meta_tier`: 라인별 메타 티어 (S/A/B/C/D, 패치 26.6 기준)
- `play_tips`: 한글 운영 팁 (콤보, 파워 스파이크)
- 능력치: waveclear, splitpush, teamfight, engage, peel, poke, pick, burst (각 1~5)

### 메타 티어 업데이트

패치마다 `champion_attributes.json`의 `meta_tier` 필드를 업데이트하세요.
[lolalytics.com](https://lolalytics.com/lol/tierlist/) 또는 [op.gg](https://op.gg/lol/champions)에서 최신 티어를 확인할 수 있습니다.

## 테스트

```bash
cd backend
python -m pytest tests/ -v --cov=domain
```

- Unit 테스트: 도메인 서비스 (라인 최적화, 조합 점수, 메타 티어, 챔피언 역할 가이드)
- Integration 테스트: API 엔드포인트 전체 플로우
- E2E 테스트: 밴/픽 포함 전체 시나리오

## Rate Limit

Riot API Development Key 기준:
- 1초: 최대 18회 (20 중 마진)
- 2분: 최대 95회 (100 중 마진)
- 429 응답 시 Retry-After 대기 후 자동 재시도

5명 분석 시 약 90~100회 API 호출 → 2분 내외 소요

## 라이선스

MIT

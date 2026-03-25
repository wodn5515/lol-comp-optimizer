# CLAUDE.md

## 프로젝트

**LoL Comp Optimizer** — 2~5명의 소환사명을 입력하면 Riot API로 전적·챔피언풀을 분석해서 최적 라인 배정 + 챔피언 조합을 추천하는 웹앱.

## 문서

- 기획서: `docs/lol-comp-optimizer-spec.md` — 기능 스펙, 아키텍처, API, DB 스키마
- 개발 프로세스: `docs/lol-dev-process.md` — 개발 순서, 테스트 전략, 코딩 규칙

**코드 작성 전에 반드시 위 두 문서를 읽을 것.**
기획서에 없는 기능은 만들지 않는다.
기획서의 숫자/규칙과 코드의 값이 반드시 일치해야 한다.

## 아키텍처 규칙 (절대 위반 금지)

### 백엔드: 포트앤어댑터 (헥사고날)

```
backend/
├── domain/          # 핵심 도메인 (외부 의존 없음)
│   ├── models/      # 엔티티, 값 객체
│   ├── services/    # 비즈니스 로직
│   └── ports/       # 포트 (ABC 인터페이스)
└── adapters/        # 어댑터 (포트 구현체)
    ├── inbound/     # 외부→도메인 (FastAPI 라우터)
    └── outbound/    # 도메인→외부 (DB, Riot API)
```

**절대 규칙:**
- `domain/` 안에 FastAPI, SQLModel, httpx 등 외부 라이브러리 import 금지
- `domain/` 안에서는 순수 Python + 표준 라이브러리 + typing + abc만 사용
- 서비스는 포트(ABC) 타입에만 의존 (생성자 주입)
- 어댑터에서 포트를 구현, `main.py`에서 DI 조립

```python
# ✅ 올바른 예시 (domain/services/)
from domain.ports.external.riot_api_port import RiotApiPort

class LaneOptimizerService:
    def __init__(self, riot_api: RiotApiPort):  # 포트 타입
        self.riot_api = riot_api

# ❌ 잘못된 예시 (domain/ 안에서)
from fastapi import HTTPException    # 금지
from sqlmodel import Session         # 금지
import httpx                         # 금지
```

### 프론트엔드: Feature-Sliced Design (FSD)

```
frontend/src/
├── app/         # Layer 1: 앱 전역 (라우팅, 프로바이더)
├── pages/       # Layer 2: 페이지 (라우트 단위)
├── widgets/     # Layer 3: 위젯 (독립 UI 블록)
├── features/    # Layer 4: 피처 (유저 액션)
├── entities/    # Layer 5: 엔티티 (비즈니스 모델)
└── shared/      # Layer 6: 공유 (유틸, 기본 UI)
```

**절대 규칙:**
- 의존성 방향: 상위 → 하위만 가능
  - `app → pages → widgets → features → entities → shared`
  - ✅ `features/buy-stock → entities/team` (가능)
  - ❌ `entities/team → features/buy-stock` (불가)
- 각 slice의 public API는 `index.js`로 노출
- 외부에서는 slice 내부 파일 직접 import 금지 (반드시 index 경유)

## AI 개발 프로세스 (자동 준수)

아래 프로세스는 모든 작업에 자동으로 적용된다. 유저가 별도 지시하지 않아도 반드시 따를 것.

### 기획서 수정 시

```
1. 신규 문서 생성 금지 — 기존 spec.md에 직접 반영 (싱글 소스)
2. 변경 시 3곳 동기화: spec.md ↔ CLAUDE.md ↔ dev-process.md
3. 숫자 변경 시 기존 코드/테스트와 충돌 여부 확인
4. 미구현 항목은 섹션 9 "개선 로드맵"에 상태 표기 ([ ] / [x])
5. 구현 완료된 항목은 본문 섹션으로 승격, 로드맵에서 [x] 체크
```

### 구현 전

```
1. 기획서(spec.md) 해당 섹션 읽기
2. 기존 코드 읽기 (수정 대상 + 연관 파일)
3. dev-process.md 섹션 4 매핑 참고하여 테스트 케이스 먼저 작성
```

### 구현 중

```
4. 테스트 통과하는 코드 작성
5. 전체 테스트 실행 (pytest tests/ -v)
6. 실패 시 코드 수정, 재실행 — 전부 통과할 때까지
7. 같은 버그를 2번 이상 고치는 상황 → 멈추고 근본 원인부터 파악
```

### 구현 후

```
8. 3곳 문서 동기화 (spec.md ↔ CLAUDE.md ↔ dev-process.md)
9. "현재 진행 상황" 체크리스트 업데이트
10. 커밋 (1기능 = 1커밋)
```

### 금지 사항

```
- docker compose up/build, 배포 관련 명령 실행 금지 (유저가 직접 배포)
- git push는 유저가 요청할 때만
- 테스트 없이 커밋 금지
- 기획서에 없는 기능 추가 금지
- 기획서 신규 파일 생성 금지 (v1.5-spec.md 같은 분리 문서 만들지 않기)
```

## 기획서 핵심 숫자 (테스트에서 검증할 값)

```
라인 배정:
  - 게임 수 10+: 가중치 ×1.0
  - 게임 수 5~9: ×0.8
  - 게임 수 1~4: ×0.5
  - 게임 수 0: ×0.1

조합 점수 가중치:
  - 개인 숙련도: 25%
  - 메타 티어: 10%
  - AD/AP 밸런스: 15%
  - 프론트라인: 15%
  - 딜 구성: 15%
  - 웨이브클리어: 10%
  - 스플릿푸시: 10%

페널티:
  - 풀 AD (AP 0명): -30점
  - 풀 AP (AD 0명): -30점
  - 프론트라인: 등급제 (기획서 섹션 2-3 참조, 기존 -25 페널티 삭제)
  - 웨이브클리어 총합 < 10: -10점
  - 이니시 부족 (engage < 2*n): -10점
  - 필링 부족 (peel < 1.5*n): -8점
  - 팀파이트 부족 (teamfight < 3*n): -8점
  - 오프라인 배정: 챔피언당 -25점

Riot API Rate Limit:
  - 1초 윈도우: 최대 18회 (20 중 여유)
  - 2분 윈도우: 최대 95회 (100 중 여유)
```

## 기술 스택

```
백엔드: Python 3.11+, FastAPI, httpx (async), SQLModel, SQLite
프론트: React 18, Vite, Tailwind CSS, zustand, recharts
API: Riot Games API (Account-v1, Summoner-v4, League-v4, Match-v5, Mastery-v4)
데이터: Data Dragon (챔피언 정적 데이터)
테스트: pytest, pytest-asyncio (백), Vitest + RTL (프론트)
```

## 실행 명령어

```bash
# 백엔드
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
pytest tests/ -v --cov=domain

# 프론트엔드
cd frontend
npm install
npm run dev
npm run test
```

## 현재 진행 상황

```
[x] Phase 0: 스캐폴딩
    [x] 백엔드 프로젝트 셋업 (FastAPI + SQLite + SQLModel)
    [x] 프론트엔드 프로젝트 셋업 (React + Vite + Tailwind + zustand)
    [x] FSD 디렉토리 구조 생성
    [x] 포트앤어댑터 디렉토리 구조 생성
    [x] CORS 설정
    [x] Docker Compose 구성 (backend + frontend/nginx)

[x] Phase 1: 도메인 모델 + 챔피언 데이터
    [x] domain/models/ 전체 정의 (poke, pick, burst, primary_lanes 포함)
    [x] domain/ports/ 전체 정의 (ABC)
    [x] 챔피언 속성 JSON 작성 — 145개 (11개 속성 + primary_lanes)
    [x] champion_data_service
    [x] champion_repo_impl
    [x] DB seed 스크립트

[x] Phase 2: Riot API 연동
    [x] riot_api_client (rate limiter 포함)
    [x] ddragon_client
    [x] player_analysis_service
    [x] 소환사 협곡 큐별 조회 (420/440/400/430, 칼바람·URF 제외)
    [x] Smite 감지로 정글 판별
    [x] 서버 로깅 (단계별 진행 상황, 에러 추적)
    [x] 프론트: shared/, entities/player, entities/champion
    [x] 프론트: features/setup-api-key

[x] Phase 3: 최적화 알고리즘
    [x] lane_optimizer_service (전수 탐색)
    [x] comp_optimizer_service (조합 점수 + 유형 판별 + 운영 가이드)
    [x] primary_lanes 기반 라인 필터링 (뽀삐 원딜 방지)
    [x] 2단계 API: POST /api/analyze-players + POST /api/optimize-comp
    [x] 밴/픽 지원 (banned_champions, enemy_picks, locked_picks)
    [x] 프론트: features/analyze-comp, add-player
    [x] 프론트: widgets/player-input-form

[x] Phase 4: 결과 화면 + 밴픽
    [x] 프론트: entities/composition (조합 유형 배지, 운영 가이드)
    [x] 프론트: widgets/result-board, player-summary, loading-progress
    [x] 프론트: widgets/ban-pick-panel (밴/적픽/고정픽, 실시간 업데이트)
    [x] 프론트: pages/home, pages/banpick, pages/result
    [x] E2E 테스트 (8개: 전체 플로우, 밴/픽, 레거시 호환, 에러)
    [x] 전체 플로우 검증 (85개 테스트 통과, 엔드포인트 6개, 챔피언 145개 무결성)
```

## 세션 종료 시 해야 할 것

```
1. 이 파일의 "현재 진행 상황" 체크리스트 업데이트
2. 구현 완료된 항목 [x] 표시
3. 다음 세션에서 이어서 할 작업 메모 (아래)
```

### 다음 세션 메모

Phase 4 완료, 98개 테스트 통과. GitHub Pages + Render 배포 완료.
다음: Phase 5a (P0 개선) → 기획서 섹션 9 참조.
  - analyze() 최적화 (top-N 지연 호출)
  - Session persistence (sessionStorage)

# LoL Comp Optimizer — 개발 프로세스 & 테스트 전략

> 📎 이 문서는 `lol-comp-optimizer-spec.md` (기획서)와 함께 사용.

---

## 1. 스펙 드리븐 개발 (SDD) 원칙

```
기획서가 Single Source of Truth.
코드는 스펙의 구현체. 스펙에 없는 기능은 만들지 않는다.
```

### AI 프롬프트 템플릿

```
기획서 `lol-comp-optimizer-spec.md` 섹션 {N}을 구현해줘.

아키텍처:
- 백엔드: 포트앤어댑터. domain/에는 외부 라이브러리 import 금지.
- 프론트: FSD. 상위→하위 방향 의존만 허용.

기획서의 매핑 테이블(섹션 1-3)을 참고해서
백엔드와 프론트 각각 어디에 파일을 만들지 확인한 후 구현해줘.

테스트: lol-dev-process.md의 테스트 전략(섹션 3)을 따라
단위 테스트를 먼저 작성하고 구현해줘.
```

---

## 2. 개발 순서

### Phase 0: 스캐폴딩 ✅

```
[x] 백엔드 셋업 (FastAPI + SQLite + SQLModel)
[x] 프론트엔드 셋업 (React + Vite + Tailwind + zustand)
[x] FSD 디렉토리 구조 생성
[x] 포트앤어댑터 디렉토리 구조 생성
[x] CORS 설정
[x] CLAUDE.md 작성
```

### Phase 1: 도메인 모델 + 챔피언 데이터 ✅

```
[x] domain/models/ 전체 정의 (Player, Champion, Composition, Match)
[x] domain/ports/ 전체 정의 (ABC)
[x] 챔피언 속성 JSON 작성 (171개, 메타 티어·한글 이름·운영 팁 포함)
[x] champion_data_service (Data Dragon 태그 기반 기본값 부여)
[x] adapters/outbound/persistence/champion_repo_impl
[x] DB seed 스크립트 (챔피언 속성 초기화)
```

### Phase 2: Riot API 연동 ✅

```
[x] adapters/outbound/external/riot_api_client (rate limiter 포함)
[x] adapters/outbound/external/ddragon_client
[x] domain/services/player_analysis_service (전적 데이터 → 라인별 승률, 챔피언풀)
[x] 프론트: shared/ (API client, 공통 UI)
[x] 프론트: entities/player, entities/champion
[x] 프론트: features/setup-api-key
```

### Phase 3: 최적화 알고리즘 ✅

```
[x] domain/services/lane_optimizer_service (라인 배정 전수 탐색 + 챔피언풀 추론)
[x] domain/services/comp_optimizer_service (챔피언 조합 점수 산정 + 12가지 archetype)
[x] adapters/inbound/api/optimize_router (POST /api/optimize, /analyze-players, /optimize-comp)
[x] 프론트: features/analyze-comp
[x] 프론트: features/add-player
[x] 프론트: widgets/player-input-form (멀티서치 포함)
```

### Phase 4: 결과 화면 + 밴픽 ✅

```
[x] 프론트: entities/composition (TeamCompCard, TeamAnalysisChart, 챔피언 기여도 툴팁)
[x] 프론트: widgets/result-board, widgets/player-summary
[x] 프론트: widgets/loading-progress
[x] 프론트: widgets/ban-pick-panel (밴/적픽/고정픽/포지션 고정)
[x] 프론트: pages/home, pages/banpick, pages/result
[x] 98개 테스트 통과 (unit + integration)
[x] 전체 플로우 검증 + GitHub Pages/Render 배포
```

### Phase 5a: P0 개선 (성능 + 안정성) ✅

```
[x] analyze() 최적화 — optimize() 내 top-N 지연 호출
[x] Session persistence — zustand + sessionStorage (30분 만료)
```

### Phase 5b: P1 개선 (알고리즘 + UX) ✅

```
[x] 단계적 프론트라인 점수 — 기존 -25 페널티 삭제, 등급제 교체
[x] 점수 분해 / "Why This Comp" — ScoreBreakdown 모델 + UI
[x] 다양성 필터 강화 — min_diff=max(1,n-2) + archetype 다양성
[x] 클립보드 복사 — 로비 채팅용 텍스트 복사
```

### Phase 5c: P2 개선 (추가 기능) ✅

```
[x] 적 조합 카운터 점수 — 상성 기반 보너스/패널티 (+8/-5)
[x] 접이식 조합 카드 — 1위 펼침, 나머지 접힘
[x] 플렉스 픽 감지 — primary_lanes 2개+ 자동 표시
```

---

## 3. 테스트 전략

### 3-1. 테스트 피라미드

```
          ╱  E2E  ╲           — 핵심 1~2개
         ╱─────────╲
        ╱ Integration╲        — API 라우터 + Riot API Mock
       ╱───────────────╲
      ╱   Unit (Domain)  ╲    — 핵심: 최적화 알고리즘
     ╱─────────────────────╲
```

### 3-2. 단위 테스트

**대상**: domain/services/
**도구**: pytest + pytest-asyncio
**원칙**: 외부 의존 없이 순수 로직만. 포트는 Mock.

```
tests/
├── unit/
│   ├── test_lane_optimizer_service.py
│   ├── test_comp_optimizer_service.py
│   ├── test_player_analysis_service.py
│   └── test_champion_data_service.py
```

**예시 테스트 케이스:**

```python
# test_lane_optimizer_service.py
# 기획서 섹션 2-2: 라인 배정 최적화

class TestLaneOptimizer:

    def test_5_players_returns_top_assignments(self):
        """5명 입력 시 120가지 중 상위 N개 반환"""
        players = [
            make_player("A", lane_stats={"MID": (10, 0.7), "TOP": (3, 0.3)}),
            make_player("B", lane_stats={"ADC": (12, 0.65), "SUP": (5, 0.4)}),
            make_player("C", lane_stats={"JG": (15, 0.6), "MID": (5, 0.5)}),
            make_player("D", lane_stats={"TOP": (8, 0.55), "JG": (4, 0.4)}),
            make_player("E", lane_stats={"SUP": (10, 0.7), "ADC": (3, 0.45)}),
        ]
        results = lane_optimizer.optimize(players, top_n=3)
        assert len(results) == 3
        assert results[0].score >= results[1].score  # 점수 내림차순

    def test_2_players_assigns_2_lanes(self):
        """2명 입력 시 5P2=20가지 탐색, 2개 라인만 배정"""
        players = [
            make_player("A", lane_stats={"MID": (10, 0.7)}),
            make_player("B", lane_stats={"ADC": (8, 0.6)}),
        ]
        results = lane_optimizer.optimize(players, top_n=3)
        for r in results:
            assert len(r.assignments) == 2
            lanes = [a.lane for a in r.assignments]
            assert len(set(lanes)) == 2  # 중복 라인 없음

    def test_no_experience_lane_gets_penalty(self):
        """경험 없는 라인은 가중치 0.1 (페널티)"""
        player = make_player("A", lane_stats={"MID": (10, 0.7)})
        # TOP 경험 없음
        score_mid = lane_optimizer._lane_score(player, "MID")
        score_top = lane_optimizer._lane_score(player, "TOP")
        assert score_mid > score_top * 5  # 0.7*1.0 vs 0*0.1

    def test_game_count_weight(self):
        """게임 수에 따른 가중치: 10+→1.0, 5~9→0.8, 1~4→0.5"""
        p1 = make_player("A", lane_stats={"MID": (15, 0.6)})  # 15게임 → ×1.0
        p2 = make_player("B", lane_stats={"MID": (3, 0.6)})   # 3게임 → ×0.5
        s1 = lane_optimizer._lane_score(p1, "MID")
        s2 = lane_optimizer._lane_score(p2, "MID")
        assert s1 == pytest.approx(s2 * 2, rel=0.01)  # 0.6*1.0 vs 0.6*0.5


# test_comp_optimizer_service.py
# 기획서 섹션 2-3: 챔피언 조합 최적화

class TestCompOptimizer:

    def test_full_ad_penalty(self):
        """풀 AD 조합: -30점 페널티"""
        comp = make_composition(champions=[
            make_champ("Zed", damage_type="AD"),
            make_champ("LeeSin", damage_type="AD"),
            make_champ("Jayce", damage_type="AD"),
            make_champ("Jinx", damage_type="AD"),
            make_champ("Thresh", damage_type="AD"),
        ])
        score = comp_optimizer.calculate_score(comp)
        comp_with_ap = make_composition(champions=[
            make_champ("Zed", damage_type="AD"),
            make_champ("LeeSin", damage_type="AD"),
            make_champ("Viktor", damage_type="AP"),  # AP 추가
            make_champ("Jinx", damage_type="AD"),
            make_champ("Thresh", damage_type="AD"),
        ])
        score_with_ap = comp_optimizer.calculate_score(comp_with_ap)
        assert score_with_ap > score + 20  # 페널티 30점 차이

    def test_no_frontline_penalty(self):
        """프론트라인 0명: -25점"""
        comp = make_composition(champions=[
            make_champ("Zed", role_tags=["ASSASSIN"]),
            make_champ("Nidalee", role_tags=["MAGE"]),
            make_champ("LeBlanc", role_tags=["ASSASSIN"]),
            make_champ("Ezreal", role_tags=["MARKSMAN"]),
            make_champ("Lux", role_tags=["MAGE"]),
        ])
        score = comp_optimizer.calculate_score(comp)
        comp_with_tank = make_composition(champions=[
            make_champ("Ornn", role_tags=["TANK"]),  # 탱커 추가
            make_champ("Nidalee", role_tags=["MAGE"]),
            make_champ("LeBlanc", role_tags=["ASSASSIN"]),
            make_champ("Ezreal", role_tags=["MARKSMAN"]),
            make_champ("Lux", role_tags=["MAGE"]),
        ])
        score_with_tank = comp_optimizer.calculate_score(comp_with_tank)
        assert score_with_tank > score + 15

    def test_waveclear_low_penalty(self):
        """웨이브클리어 총합 < 10: -10점"""
        comp = make_composition(champions=[
            make_champ("A", waveclear=1),
            make_champ("B", waveclear=2),
            make_champ("C", waveclear=2),
            make_champ("D", waveclear=2),
            make_champ("E", waveclear=2),  # 총합 9
        ])
        analysis = comp_optimizer.analyze(comp)
        assert analysis.waveclear_score == 9
        assert analysis.penalties["low_waveclear"] == -10

    def test_balanced_comp_high_score(self):
        """균형 잡힌 조합: 페널티 없음 + 높은 점수"""
        comp = make_composition(champions=[
            make_champ("Ornn", damage_type="AP", role_tags=["TANK"],
                       waveclear=4, teamfight=5, engage=5),
            make_champ("LeeSin", damage_type="AD", role_tags=["BRUISER"],
                       waveclear=3, teamfight=3, engage=4),
            make_champ("Viktor", damage_type="AP", role_tags=["MAGE"],
                       waveclear=5, teamfight=4),
            make_champ("Jinx", damage_type="AD", role_tags=["MARKSMAN"],
                       waveclear=3, teamfight=4),
            make_champ("Thresh", damage_type="AP", role_tags=["SUPPORT"],
                       engage=4, peel=4),
        ])
        analysis = comp_optimizer.analyze(comp)
        assert analysis.ad_ratio == pytest.approx(0.4, abs=0.1)
        assert analysis.has_frontline == True
        assert analysis.waveclear_score >= 10
        assert len(analysis.penalties) == 0

    def test_personal_mastery_weight_30pct(self):
        """개인 숙련도 가중치 30%"""
        # 동일 조합인데 플레이어 숙련도만 다름
        comp_high = make_composition_with_mastery(avg_mastery=0.9)
        comp_low = make_composition_with_mastery(avg_mastery=0.3)
        diff = comp_optimizer.calculate_score(comp_high) - comp_optimizer.calculate_score(comp_low)
        total_range = 100  # 만점 기준
        assert diff == pytest.approx(total_range * 0.3 * 0.6, abs=5)


# test_player_analysis_service.py
# 기획서 섹션 5: 플레이어 데이터 수집

class TestPlayerAnalysis:

    def test_lane_stats_from_matches(self):
        """매치 히스토리에서 라인별 승률 추출"""
        matches = [
            make_match_summary(lane="MID", win=True),
            make_match_summary(lane="MID", win=True),
            make_match_summary(lane="MID", win=False),
            make_match_summary(lane="TOP", win=True),
        ]
        stats = player_analysis.calculate_lane_stats(matches)
        assert stats["MID"].games == 3
        assert stats["MID"].win_rate == pytest.approx(0.667, abs=0.01)
        assert stats["TOP"].games == 1

    def test_top_champions_extraction(self):
        """매치에서 챔피언별 승률/KDA 추출"""
        matches = [
            make_match_summary(champion="Zed", win=True, kills=10, deaths=2, assists=5),
            make_match_summary(champion="Zed", win=True, kills=8, deaths=3, assists=4),
            make_match_summary(champion="Ahri", win=False, kills=3, deaths=5, assists=7),
        ]
        champs = player_analysis.calculate_champion_stats(matches)
        zed = next(c for c in champs if c.champion_name == "Zed")
        assert zed.games == 2
        assert zed.win_rate == 1.0
        assert zed.kda == pytest.approx((18 + 9) / 5, abs=0.1)  # (K+A)/D


# test_champion_data_service.py
# 기획서 섹션 3: 챔피언 속성

class TestChampionData:

    def test_manual_champion_returns_attributes(self):
        """수동 입력된 챔피언은 정확한 속성 반환"""
        attrs = champion_data.get_attributes("Aatrox")
        assert attrs.damage_type == "AD"
        assert "BRUISER" in attrs.role_tags
        assert attrs.waveclear == 4

    def test_unknown_champion_gets_defaults_from_tags(self):
        """수동 입력 없는 챔피언은 Data Dragon 태그 기반 기본값"""
        # Data Dragon에서 tags: ["Mage", "Support"]인 신챔
        attrs = champion_data.get_attributes_with_fallback(
            champion_name="NewChamp", ddragon_tags=["Mage", "Support"])
        assert attrs.damage_type == "AP"
        assert attrs.source == "AUTO"

    def test_tank_tag_defaults(self):
        """Tank 태그 → waveclear=3, teamfight=3"""
        attrs = champion_data.get_attributes_with_fallback(
            champion_name="Unknown", ddragon_tags=["Tank"])
        assert attrs.waveclear == 3
        assert attrs.teamfight == 3
```

### 3-3. 통합 테스트

**대상**: API 라우터 전체 플로우
**도구**: pytest + httpx TestClient + Riot API Mock

```
tests/
├── integration/
│   ├── test_optimize_api.py          # POST /api/optimize 전체 플로우
│   ├── test_champion_api.py          # GET /api/champions
│   └── conftest.py                   # Riot API Mock fixture
```

```python
# test_optimize_api.py

async def test_optimize_full_flow(client, mock_riot_api):
    """전체 최적화 플로우: 입력 → Riot API 조회 → 분석 → 추천"""
    resp = await client.post("/api/optimize", json={
        "api_key": "test-key",
        "players": [
            {"game_name": "PlayerA", "tag_line": "KR1"},
            {"game_name": "PlayerB", "tag_line": "KR2"},
        ],
        "match_count": 5
    })
    assert resp.status_code == 200
    data = resp.json()

    # 플레이어 정보 반환
    assert len(data["players"]) == 2
    assert data["players"][0]["tier"] is not None

    # 추천 조합 반환
    assert len(data["recommendations"]) >= 1
    rec = data["recommendations"][0]
    assert rec["total_score"] > 0
    assert len(rec["assignments"]) == 2
    assert rec["team_analysis"]["ad_ratio"] + rec["team_analysis"]["ap_ratio"] == pytest.approx(1.0)

async def test_optimize_invalid_summoner(client, mock_riot_api):
    """존재하지 않는 소환사: 에러 응답"""
    mock_riot_api.set_not_found("Unknown", "0000")
    resp = await client.post("/api/optimize", json={
        "api_key": "test-key",
        "players": [{"game_name": "Unknown", "tag_line": "0000"}],
        "match_count": 5
    })
    assert resp.status_code == 404
    assert "소환사를 찾을 수 없습니다" in resp.json()["detail"]
```

### 3-4. E2E 테스트

```
tests/
├── e2e/
│   └── test_full_flow.py
```

```
시나리오 1: 가입 → 분석 → 결과
  1. API 키 입력
  2. 소환사명 2명 입력
  3. "조합 분석하기" 클릭
  4. 로딩 프로그레스 표시
  5. 결과: 플레이어 카드 2개 + 추천 조합 카드 표시
  6. 추천 조합에 AD/AP 비율 차트 표시
```

### 3-5. 프론트엔드 테스트

```
tests/
├── frontend/
│   ├── entities/
│   │   └── champion/ChampionIcon.test.jsx
│   ├── features/
│   │   └── analyze-comp/useAnalyze.test.js
│   └── widgets/
│       ├── player-input-form/PlayerInputForm.test.jsx
│       └── result-board/ResultBoard.test.jsx
```

---

## 4. 스펙 → 테스트 매핑

### 라인 배정

| 기획서 규칙 | 테스트 파일 | 테스트 케이스 |
|------------|-----------|-------------|
| 5명: 5!=120 전수 탐색 | test_lane_optimizer | test_5_players_returns_top |
| 2명: 5P2=20 탐색 | test_lane_optimizer | test_2_players_assigns_2_lanes |
| 게임 수 10+: ×1.0 | test_lane_optimizer | test_game_count_weight |
| 게임 수 0: ×0.1 | test_lane_optimizer | test_no_experience_penalty |

### 조합 최적화

| 기획서 규칙 | 테스트 파일 | 테스트 케이스 |
|------------|-----------|-------------|
| 풀 AD: -30점 | test_comp_optimizer | test_full_ad_penalty |
| 프론트라인 등급제 (필수 조합 0/1/2/3명) | test_comp_optimizer | test_graduated_frontline_required |
| 프론트라인 등급제 (불필요 조합) | test_comp_optimizer | test_graduated_frontline_unnecessary |
| 웨이브클리어 <10: -10점 | test_comp_optimizer | test_waveclear_low_penalty |
| 개인 숙련도 25% | test_comp_optimizer | test_personal_mastery_weight |
| 가중치 합계 = 1.0 | test_comp_optimizer | test_weights_sum_to_one |
| 다양성 필터 (5명: min_diff=3) | test_comp_optimizer | test_diversity_filter_5players |
| 다양성 필터 (2명: min_diff=1) | test_comp_optimizer | test_diversity_filter_2players |
| 점수 분해 합 = total_score | test_comp_optimizer | test_score_breakdown_sum |
| 카운터 점수 (적 3명+ 유리상성) | test_comp_optimizer | test_counter_score_favorable |
| 카운터 점수 (적 2명 미적용) | test_comp_optimizer | test_counter_score_inactive |

### 챔피언 데이터

| 기획서 규칙 | 테스트 파일 | 테스트 케이스 |
|------------|-----------|-------------|
| 수동 입력 챔피언 속성 | test_champion_data | test_manual_champion |
| Data Dragon 기반 기본값 | test_champion_data | test_unknown_champion_defaults |
| Tank 태그 → 기본값 | test_champion_data | test_tank_tag_defaults |

### 플레이어 분석

| 기획서 규칙 | 테스트 파일 | 테스트 케이스 |
|------------|-----------|-------------|
| 라인별 승률 추출 | test_player_analysis | test_lane_stats_from_matches |
| 챔피언별 승률/KDA | test_player_analysis | test_top_champions_extraction |

---

## 5. 코딩 규칙

### 백엔드

```
- Python 3.11+, type hints 필수
- domain/ 내 외부 라이브러리 import 금지
- 포트(ABC) 먼저 정의 → 어댑터에서 구현
- 서비스는 포트 타입만 의존 (생성자 주입)
- async/await 일관 사용
- snake_case (파일, 변수), PascalCase (클래스)
```

### 프론트엔드

```
- React 18 + hooks
- FSD 의존성 방향: 상위 → 하위만
- 각 slice의 public API는 index.js로 노출
- zustand (entities에 store)
- Tailwind 유틸리티 클래스
- PascalCase (컴포넌트), camelCase (변수/훅), kebab-case (디렉토리)
```

### Git

```
main ← develop ← feature/phase-N-xxx
커밋: feat: / test: / fix: / refactor: / docs:
```

---

## 6. 실행 명령어

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

# E2E
npx playwright test tests/e2e/
```

---

## 7. 환경 변수

```env
# backend/.env
DATABASE_URL=sqlite:///./lol_comp.db
CORS_ORIGINS=http://localhost:5173

# frontend/.env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_DDRAGON_VERSION=14.10.1
```

---

## 8. 코드 리뷰 체크리스트

### 아키텍처

```
[ ] domain/ 안에 외부 라이브러리 import 없는가?
[ ] 서비스가 포트(ABC)에만 의존하는가?
[ ] FSD 의존성 방향 지키는가?
[ ] 각 slice public API가 index.js로 노출?
```

### 스펙 일치

```
[ ] 기획서 숫자/규칙과 코드 값 일치?
    (가중치 25/10/15/15/15/10/10, 페널티 -30/-10/-8, 게임 수 ×0.1/0.5/0.8/1.0)
[ ] 프론트라인: 등급제 점수 사용 (기존 -25 페널티 아님)
[ ] 다양성 필터: min_diff = max(1, n-2)
[ ] 기획서에 없는 기능이 추가되지 않았는가?
[ ] 단위 테스트가 기획서 규칙을 검증하는가?
```

### 코드 품질

```
[ ] type hints?
[ ] 에러 처리 (소환사 못 찾음, Rate Limit 초과 등)?
[ ] 엣지 케이스 (2명 입력, 챔피언풀 1개뿐인 플레이어)?
```

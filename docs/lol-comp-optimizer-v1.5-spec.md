# LoL Comp Optimizer v1.5 — 개선 기획서

## 한줄 요약

v1.0 대비 **성능 최적화, 점수 체계 정비, 다양성 강화, UX 개선**을 목표로 하는 개선 스펙.
5차 리뷰를 거쳐 확정된 13개 항목을 P0~P3 우선순위로 구현한다.

> 이 문서는 `lol-comp-optimizer-spec.md` (v1.0 기획서)의 확장이다.
> v1.0 스펙에서 변경되지 않는 부분은 기존 문서를 따른다.
> 충돌 시 이 문서(v1.5)가 우선한다.

---

## 변경 요약

| # | 항목 | 우선순위 | 유형 |
|---|------|---------|------|
| 1 | analyze() 최적화 (top-N 지연 호출) | P0 | 성능 |
| 2 | Session persistence (sessionStorage) | P0 | UX |
| 3 | 점수 가중치 정규화 (canonical weights) | P0 | 데이터 정합성 |
| 4 | 다양성 필터 강화 (scaled threshold) | P1 | 알고리즘 |
| 5 | 점수 분해 / "Why This Comp" | P1 | UX |
| 6 | 단계적 프론트라인 점수 (graduated scoring) | P1 | 알고리즘 |
| 7 | 클립보드 복사 | P1 | UX |
| 8 | 적 조합 카운터 점수 | P2 | 알고리즘 |
| 9 | 접이식 조합 카드 (collapsible cards) | P2 | UX |
| 10 | 플렉스 픽 감지 | P2 | 알고리즘 |
| 11 | SSE 로딩 진행률 (analyze-players 전용) | P3 (v2 이관) | 인프라 |
| 12 | 밴 추천 | P3 (v2 이관) | 기능 |
| 13 | 드래프트 페이즈 통합 | P3 (v2 이관) | 기능 |
| 14 | 파워 스파이크 일관성 | P3 (v2 이관) | 알고리즘 |

**거부된 항목** (구현하지 않음):
- 티어 기반 라인 점수 — 기존 게임수 가중치로 충분
- CC 속성 별도 추가 — engage/peel로 프록시 가능
- 라인 매치업 인식 — 데이터 의존성 과다, ROI 낮음

---

## 1. analyze() 최적화 (P0)

### 문제

현재 코드는 모든 조합 후보에 대해 `analyze()`를 호출한다.
`analyze()`는 조합 유형 판별, 시너지 분석, 운영 가이드 생성 등 무거운 로직을 포함하며,
수천~수만 개 조합마다 실행되어 불필요한 CPU 소비가 발생한다.

### 변경 내용

`analyze()`를 **최종 top-N 조합에 대해서만** 호출하도록 변경한다.

### 알고리즘

```
변경 전:
  for each combination:
    score = calculate_score(...)
    analysis = analyze(...)           # 매 조합마다 호출
    all_compositions.append(Composition(score, analysis))
  sort → diversity filter → top-N

변경 후:
  for each combination:
    score = calculate_score(...)
    all_compositions.append((score, assignments, attrs_list))  # analyze 안 함
  sort → diversity filter → top-N 선별
  for each selected in top-N:
    analysis = analyze(...)           # 최종 N개만 호출
    result.append(Composition(score, analysis))
```

### 백엔드 변경

| 파일 | 변경 |
|------|------|
| `domain/services/comp_optimizer_service.py` | `optimize()` 메서드 내 루프에서 `analyze()` 호출 제거. diversity filter 후 최종 결과에 대해서만 `analyze()` 호출 |

### 프론트엔드 변경

없음. API 응답 형태 동일.

### 성공 기준

- 5명 × 챔피언풀 5개 기준, `optimize-comp` 응답 시간 **50% 이상 단축**
- 기존 테스트 전부 통과 (결과 동일)
- `analyze()` 호출 횟수 = top_n (기본 5)

---

## 2. Session Persistence (P0)

### 문제

브라우저 새로고침/뒤로가기 시 analyze-players 결과(플레이어 데이터)가 사라진다.
Riot API를 다시 호출해야 하며, 2분 이상 대기가 반복된다.

### 변경 내용

analyze-players 응답 데이터를 `sessionStorage`에 저장한다.
탭을 닫으면 자동 소멸 (보안: API 키는 저장하지 않음).

### 규칙

```
저장 키: "lol-comp-optimizer:session"
저장 값: {
  players: PlayerAnalysis[],        // analyze-players 응답 전체
  banned_champions: string[],       // 밴 목록
  enemy_picks: string[],            // 적 픽
  locked_picks: Record<string, string>,  // 고정 픽 (playerKey → champion)
  locked_positions: Record<string, string>,  // 고정 라인
  timestamp: number                 // 저장 시각 (ms)
}
만료: 30분 (timestamp 기준, 초과 시 무시)
크기 제한: 5MB 이내 (sessionStorage 기본 한도)
```

### 프론트엔드 변경

| 파일 | 변경 |
|------|------|
| `shared/lib/sessionPersistence.js` | 신규. `save(data)`, `load()`, `clear()` 유틸 |
| `features/analyze-comp/model/useAnalyze.js` | analyze-players 성공 시 `save()` 호출 |
| `pages/banpick/ui/BanPickPage.jsx` | 마운트 시 `load()` → 데이터 있으면 API 생략, 없으면 홈으로 redirect |
| `pages/result/ui/ResultPage.jsx` | 마운트 시 `load()` → 데이터 있으면 복원 |
| `widgets/ban-pick-panel/model/useBanPick.js` | 밴/픽 변경 시 `save()` 업데이트 |

### 백엔드 변경

없음.

### 성공 기준

- 밴픽 화면에서 새로고침 후 데이터 유지 (Riot API 재호출 없음)
- 탭 닫으면 데이터 소멸
- 30분 경과 시 자동 만료 → 홈으로 redirect
- API 키는 sessionStorage에 저장하지 않음 (기존 localStorage 유지)

---

## 3. 점수 가중치 정규화 (P0)

### 문제

CLAUDE.md에는 "개인 숙련도 30%"로 명시되어 있으나,
실제 코드는 "개인 숙련도 25% + 메타 적합도 10%"로 구현되어 있다.
기획서(v1.0)와 CLAUDE.md, 코드 간 불일치가 존재한다.

### 변경 내용

**정규 가중치 (canonical weights)** 를 아래와 같이 확정한다.
개인 숙련도 25%와 메타 적합도 10%를 합쳐 "개인 능력 35%"로 통합하고,
나머지 조합 점수 65%는 기존 비율을 유지한다.

### 정규 가중치 (v1.5 확정)

| 항목 | 가중치 | 코드 상수명 | 설명 |
|------|--------|-----------|------|
| 개인 숙련도 | 25% | `WEIGHT_PERSONAL_MASTERY` | 챔피언 승률 × 게임수 가중치 + mastery 보너스 |
| 메타 적합도 | 10% | `WEIGHT_META_TIER` | 해당 라인 메타 티어 (S=100 ~ D=20) |
| AD/AP 밸런스 | 15% | `WEIGHT_AD_AP_BALANCE` | AD 2~3, AP 2~3 이상적 |
| 프론트라인 | 15% | `WEIGHT_FRONTLINE` | 단계적 점수 (항목 6 참조) |
| 딜 구성 | 15% | `WEIGHT_DEAL_COMPOSITION` | 팀 DPS 충분성 |
| 웨이브클리어 | 10% | `WEIGHT_WAVECLEAR` | waveclear 합산 |
| 스플릿푸시 | 10% | `WEIGHT_SPLITPUSH` | splitpush 합산 |
| **합계** | **100%** | | |

### 정합성 규칙

```
1. 이 테이블이 유일한 정규 소스 (Single Source of Truth)
2. CLAUDE.md의 "개인 숙련도 30%"는 "개인 숙련도 25% + 메타 적합도 10% 중 5%"를
   반올림한 근사값이었음. v1.5부터 CLAUDE.md도 이 테이블로 갱신
3. 코드의 상수는 이 테이블과 반드시 일치
4. 테스트에서 가중치 합계 = 1.0 검증
```

### 변경 파일

| 파일 | 변경 |
|------|------|
| `domain/services/comp_optimizer_service.py` | 가중치 상수 유지 (현재 코드가 이미 정규값) |
| `CLAUDE.md` | "개인 숙련도 30%" → 위 테이블로 교체 |
| `tests/unit/test_comp_optimizer.py` | 가중치 합계 = 1.0 검증 테스트 추가 |

### 성공 기준

- CLAUDE.md, v1.0 기획서 참조 시 v1.5 정규 테이블이 우선
- `sum(all_weights) == 1.0` 테스트 통과
- 기존 점수 결과 변동 없음 (코드 상수는 동일)

---

## 4. 다양성 필터 강화 (P1)

### 문제

현재 다양성 필터는 "완전 동일 챔피언 세트 중복 제거"만 수행한다.
결과적으로 상위 5개 조합이 4개 챔피언 동일 + 1개만 다른 경우가 빈번하다.
또한 고정 임계값은 2명/3명 파티에서 지나치게 엄격하거나 느슨하다.

### 변경 내용

#### 4-1. 챔피언 차이 임계값 (플레이어 수에 따라 스케일링)

```
min_diff = max(1, n - 2)

  n=2: max(1, 0) = 1 → 최소 1개 챔피언 차이
  n=3: max(1, 1) = 1 → 최소 1개 챔피언 차이
  n=4: max(1, 2) = 2 → 최소 2개 챔피언 차이
  n=5: max(1, 3) = 3 → 최소 3개 챔피언 차이
```

#### 4-2. 조합 유형(archetype) 다양성

상위 5개 조합 중 최소 2개 이상의 서로 다른 조합 유형이 포함되도록 한다.

### 알고리즘

```python
def diversity_filter(sorted_compositions, top_n, player_count):
    min_diff = max(1, player_count - 2)
    result = []
    seen_archetypes = set()

    for comp in sorted_compositions:
        if len(result) >= top_n:
            break

        comp_champs = frozenset(a.champion_name for a in comp.assignments)

        # 기존 결과와 최소 min_diff개 챔피언이 달라야 함
        too_similar = False
        for existing in result:
            existing_champs = frozenset(a.champion_name for a in existing.assignments)
            diff_count = len(comp_champs.symmetric_difference(existing_champs)) // 2
            if diff_count < min_diff:
                too_similar = True
                break

        if too_similar:
            continue

        result.append(comp)
        seen_archetypes.update(comp.team_analysis.archetypes)

    # 조합 유형 다양성 보완: 유형이 1가지뿐이면 다른 유형 조합을 추가 탐색
    if len(seen_archetypes) < 2 and len(result) < top_n:
        for comp in sorted_compositions:
            if comp in result:
                continue
            comp_archetypes = set(comp.team_analysis.archetypes)
            if comp_archetypes - seen_archetypes:  # 새로운 유형이 있으면
                result.append(comp)
                seen_archetypes.update(comp_archetypes)
                if len(result) >= top_n:
                    break

    return result
```

### 변경 파일

| 파일 | 변경 |
|------|------|
| `domain/services/comp_optimizer_service.py` | `optimize()` 내 diversity filter 로직 교체 |
| `tests/unit/test_comp_optimizer.py` | 2/3/4/5명 각각에 대한 다양성 테스트 추가 |

### 성공 기준

- 5명 기준: 상위 5개 조합 간 최소 3개 챔피언 차이
- 3명 기준: 상위 5개 조합 간 최소 1개 챔피언 차이
- 상위 5개 조합 중 2가지 이상의 조합 유형 포함 (가능한 경우)
- 점수 상위 조합이 다양성 필터에 의해 제외될 수 있음 (의도된 동작)

---

## 5. 점수 분해 / "Why This Comp" (P1)

### 문제

사용자가 "왜 이 조합이 추천되었는지" 이해할 수 없다.
total_score만 표시되며, 어떤 요소가 높고 어떤 요소가 낮은지 모른다.

### 변경 내용

각 추천 조합에 점수 분해(score breakdown)를 포함한다.

### API 응답 변경

`team_analysis` 내에 `score_breakdown` 필드 추가:

```json
{
  "team_analysis": {
    "score_breakdown": {
      "personal_mastery": { "score": 78.5, "weighted": 19.6, "weight": 0.25 },
      "meta_tier":       { "score": 72.0, "weighted": 7.2,  "weight": 0.10 },
      "ad_ap_balance":   { "score": 90.0, "weighted": 13.5, "weight": 0.15 },
      "frontline":       { "score": 60.0, "weighted": 9.0,  "weight": 0.15 },
      "deal_composition":{ "score": 85.0, "weighted": 12.8, "weight": 0.15 },
      "waveclear":       { "score": 70.0, "weighted": 7.0,  "weight": 0.10 },
      "splitpush":       { "score": 55.0, "weighted": 5.5,  "weight": 0.10 },
      "penalties":       { "details": ["-30: 풀 AD"], "total": -30.0 }
    },
    "why_this_comp": "개인 숙련도가 높고 AD/AP 밸런스가 우수합니다. 프론트라인이 다소 부족하지만 딜 구성이 탄탄합니다.",
    ...기존 필드
  }
}
```

### why_this_comp 생성 규칙

```
1. 상위 3개 항목(weighted 기준)을 강점으로 언급
2. 하위 2개 항목을 약점으로 언급
3. 페널티가 있으면 명시
4. 한국어 1~2문장

예시 템플릿:
  강점: "{항목1}이(가) 뛰어나고 {항목2}도 우수합니다."
  약점: "{항목3}이(가) 다소 부족합니다."
  페널티: "주의: {페널티_내용}."
```

### 변경 파일

| 파일 | 변경 |
|------|------|
| `domain/models/composition.py` | `ScoreBreakdown`, `ScoreItem` 모델 추가 |
| `domain/services/comp_optimizer_service.py` | `calculate_score()` → 분해 점수 반환, `_generate_why_this_comp()` 메서드 추가 |
| `adapters/inbound/api/optimize_router.py` | 응답에 `score_breakdown`, `why_this_comp` 포함 |
| `entities/composition/ui/TeamCompCard.jsx` | 점수 분해 바 차트 표시 |
| `entities/composition/ui/ScoreBreakdown.jsx` | 신규. 항목별 가로 바 차트 컴포넌트 |
| `entities/composition/ui/WhyThisComp.jsx` | 신규. "왜 이 조합?" 텍스트 컴포넌트 |

### 성공 기준

- 모든 추천 조합에 `score_breakdown` 포함
- 7개 항목의 `weighted` 합 + `penalties.total` = `total_score` (오차 ±0.1)
- UI에서 각 항목별 비율 바 차트 표시
- `why_this_comp` 한국어 문장 포함

---

## 6. 단계적 프론트라인 점수 (P1)

### 문제

현재 프론트라인 점수는 이진(binary)이다:
- 있으면 감점 없음, 없으면 -25점
- 탱커 1명과 탱커 3명의 차이가 없음

### 변경 내용

기존 `-25점 페널티`를 **제거**하고, 단계적 점수로 **교체**한다.
(중복 적용 아님 — 기존 페널티는 완전히 삭제)

### 점수 규칙

프론트라인 챔피언 = role_tags에 TANK 또는 BRUISER 포함.

```
프론트라인 수별 기본 점수 (100점 만점):

  프론트라인 점수 계산:
    frontline_count = TANK + BRUISER 수

    조합 유형별 분기:

    [프론트라인 필수 조합] — 이니시, 프론트투백 한타, 프로텍트
      0명: 0점   (구 -25 페널티를 흡수)
      1명: 60점
      2명: 100점 (이상적)
      3명+: 80점 (과다 — 딜 부족 우려)

    [프론트라인 불필요 조합] — 포킹, 픽, 폭딜/어쌔신
      0명: 80점  (정상)
      1명: 100점 (유연성 보너스)
      2명+: 70점 (조합 취지에 맞지 않음)

    [프론트라인 유연 조합] — 나머지 (스플릿, 디스인게이지, 다이브, 스커미시, 궁합, 글로벌)
      0명: 50점
      1명: 85점
      2명: 100점
      3명+: 75점
```

### 페널티 테이블 변경

```
v1.0 페널티:
  프론트라인 0명: -25점 (조합 유형별 조건부)   ← 삭제

v1.5 페널티 (교체):
  프론트라인: 단계적 점수 (위 테이블) × WEIGHT_FRONTLINE(15%)로 반영

나머지 페널티는 유지:
  풀 AD (AP 0명): -30점
  풀 AP (AD 0명): -30점
  웨이브클리어 총합 < 10: -10점
  이니시 부족: -10점
  필링 부족: -8점
  팀파이트 부족: -8점
  오프라인 배정: 챔피언당 -25점
```

### 변경 파일

| 파일 | 변경 |
|------|------|
| `domain/services/comp_optimizer_service.py` | `_calculate_frontline_score()` 메서드 신규. 기존 `PENALTY_NO_FRONTLINE` 상수 및 관련 로직 삭제 |
| `tests/unit/test_comp_optimizer.py` | 프론트라인 0/1/2/3명 × 조합유형 3가지 조합 테스트 |

### 성공 기준

- 기존 `PENALTY_NO_FRONTLINE = -25` 상수 및 적용 코드 완전 제거
- 프론트라인 필수 조합에서 0명 → 0점 × 15% = 0점 기여 (실질적 감점 효과)
- 프론트라인 2명 이니시 조합 → 100점 × 15% = 15점 기여
- 탱커 3명 조합은 과다 페널티로 100점 미만

---

## 7. 클립보드 복사 (P1)

### 문제

추천 결과를 팀원에게 공유하려면 스크린샷을 찍어야 한다.

### 변경 내용

각 추천 조합 카드에 "복사" 버튼을 추가한다.
클릭 시 텍스트 형태로 클립보드에 복사.

### 복사 포맷

```
[LoL 조합 추천 #1] 점수: 87.5
유형: 이니시 + 한타

TOP: Hide on bush → 말파이트 (승률 68%)
JG:  Faker → 자르반 4세 (승률 72%)
MID: Dopa → 오리아나 (승률 65%)
ADC: Gumayusi → 징크스 (승률 70%)
SUP: Keria → 레오나 (승률 75%)

강점: 균형 잡힌 AD/AP, 강력한 이니시
약점: 초반 약함

— LoL Comp Optimizer
```

### 프론트엔드 변경

| 파일 | 변경 |
|------|------|
| `entities/composition/ui/TeamCompCard.jsx` | "복사" 버튼 추가 |
| `shared/lib/copyToClipboard.js` | 신규. `navigator.clipboard.writeText()` 래퍼 + fallback |
| `shared/lib/formatCompText.js` | 신규. Composition → 텍스트 포맷 변환 |

### 백엔드 변경

없음.

### 성공 기준

- 복사 버튼 클릭 → 클립보드에 텍스트 복사
- 복사 성공 시 버튼 텍스트 "복사됨" (2초 후 원복)
- HTTPS 또는 localhost에서 동작 (clipboard API 요구사항)
- 챔피언 한글 이름 사용

---

## 8. 적 조합 카운터 점수 (P2)

### 문제

현재 적 챔피언을 입력하면 아군 풀에서 제외만 하고,
상대 조합 유형에 대한 카운터 점수는 반영하지 않는다.

### 변경 내용

적 픽이 **3개 이상**일 때, 적 조합 유형을 추정하고 아군 조합에 카운터 보너스/페널티를 적용한다.
3개 미만이면 적 조합 유형 추정이 불안정하므로 카운터 점수를 적용하지 않는다.

### 알고리즘

```
1. 적 챔피언 3~5개의 속성 합산 → 적 조합 유형 추정 (기존 archetype 판별 로직 재사용)
   - 5명 기준 임계값을 (적 챔피언 수 / 5)로 스케일링
   - 예: 적 3명이면 engage ≥ 15 × (3/5) = engage ≥ 9 이면 "이니시"로 추정

2. 아군 조합 유형과 적 조합 유형의 상성표 참조:

   카운터 점수표:
   | 관계 | 점수 |
   |------|------|
   | 아군이 적을 이김 (유리 상성) | +8점 |
   | 보통 (상성 관계 없음) | 0점 |
   | 아군이 적에게 약함 (불리 상성) | -5점 |

   상성 관계는 v1.0 기획서 섹션 3-2의 "조합 상성 (카운터 관계)"를 따름.

3. 복수 유형인 경우:
   - 아군 유형별로 각각 계산 후 평균
   - 예: 아군 "스플릿+이니시" vs 적 "포킹"
     → 스플릿 vs 포킹 = +8 (이김)
     → 이니시 vs 포킹 = +8 (이김)
     → 평균 = +8

4. 카운터 점수는 total_score에 직접 가산 (가중치 미적용, 절대값)
```

### API 변경

`POST /api/optimize-comp` 요청은 기존과 동일 (enemy_picks 필드 이미 존재).

응답 `team_analysis`에 필드 추가:

```json
{
  "team_analysis": {
    "counter_analysis": {
      "enemy_archetypes": ["이니시", "한타"],
      "counter_score": 8.0,
      "details": "아군 디스인게이지 조합이 적 이니시에 유리합니다 (+8)"
    },
    ...기존 필드
  }
}
```

### 변경 파일

| 파일 | 변경 |
|------|------|
| `domain/models/composition.py` | `CounterAnalysis` 모델 추가 |
| `domain/services/comp_optimizer_service.py` | `_calculate_counter_score()` 메서드 추가. 적 3명+ 조건 분기 |
| `adapters/inbound/api/optimize_router.py` | 응답에 `counter_analysis` 포함 |
| `entities/composition/ui/TeamCompCard.jsx` | 카운터 분석 결과 표시 (유리/불리 아이콘) |
| `tests/unit/test_comp_optimizer.py` | 카운터 점수 테스트: 적 2명(적용 안 됨), 적 3명(적용됨), 상성 검증 |

### 성공 기준

- 적 2명 이하: 카운터 점수 = 0 (미적용)
- 적 3명 이상: 카운터 점수 -5 ~ +8 범위
- 유리 상성: +8점, 불리 상성: -5점, 중립: 0점
- 복수 유형 평균 계산 정확성 검증

---

## 9. 접이식 조합 카드 (P2)

### 문제

추천 조합이 5개 표시되면 스크롤이 길어진다.
1위 조합 외에는 상세 정보가 즉시 필요하지 않다.

### 변경 내용

- 1위 조합: 기본 펼침 (expanded)
- 2~5위 조합: 기본 접힘 (collapsed) — 클릭으로 펼침

### 접힌 상태 표시 내용

```
[#2] 점수 82.3 | 이니시 + 한타 | 말파 · 리신 · 오리아나 · 진 · 나미
                                   [펼치기 ▼]
```

### 프론트엔드 변경

| 파일 | 변경 |
|------|------|
| `entities/composition/ui/TeamCompCard.jsx` | `isExpanded` prop 추가. collapsed 뷰 구현 |
| `widgets/result-board/ui/ResultBoard.jsx` | 1위=expanded, 나머지=collapsed. 토글 상태 관리 |

### 백엔드 변경

없음.

### 성공 기준

- 1위 카드: 자동 펼침, 전체 정보 표시
- 2~5위 카드: 접힌 상태. 점수, 유형, 챔피언 이름만 한 줄 표시
- 클릭 시 펼침/접힘 토글
- 애니메이션: `max-height` transition (200ms)

---

## 10. 플렉스 픽 감지 (P2)

### 문제

같은 챔피언이 여러 라인에서 유효할 때 (예: 바이퍼의 아우렐리온 솔 탑/미드),
이 정보가 사용자에게 전달되지 않는다.

### 변경 내용

2개 이상의 라인에서 유의미한 성과가 있는 챔피언을 "플렉스 픽"으로 표시한다.

### 판별 규칙

```
플렉스 픽 조건:
  - primary_lanes가 2개 이상인 챔피언
  - 해당 플레이어의 매치 데이터에서 2개 이상 라인에서 플레이한 기록
  - 각 라인에서 최소 2게임 이상

표시:
  - 플레이어 요약 카드에 "FLEX" 배지
  - 추천 조합에서 해당 챔피언 옆에 "(탑/미드)" 라인 표시
```

### API 응답 변경

`players[].top_champions[]`에 필드 추가:

```json
{
  "champion_name": "AurelionSol",
  "is_flex": true,
  "flex_lanes": ["TOP", "MID"],
  ...기존 필드
}
```

### 변경 파일

| 파일 | 변경 |
|------|------|
| `domain/services/player_analysis_service.py` | 챔피언별 라인 교차 분석, `is_flex`, `flex_lanes` 산출 |
| `domain/models/player.py` | `ChampionStats`에 `is_flex: bool`, `flex_lanes: list[str]` 추가 |
| `adapters/inbound/api/optimize_router.py` | 응답에 flex 정보 포함 |
| `entities/champion/ui/ChampionBadge.jsx` | "FLEX" 배지 렌더링 |
| `entities/player/ui/PlayerCard.jsx` | 플렉스 챔피언 하이라이트 |

### 성공 기준

- primary_lanes 2개 이상 + 매치 데이터 2라인 이상 = 플렉스 표시
- 플렉스 챔피언은 추천 시 여러 라인 배정 후보에 포함
- UI에서 "FLEX" 배지 명확히 구분 가능

---

## 11~14. P3 (v2 이관) — 요약만 기록

아래 항목은 v1.5에서 설계만 하고 구현은 v2로 이관한다.

### 11. SSE 로딩 진행률

- `POST /api/analyze-players` 전용 (optimize-comp에는 적용 안 함)
- FastAPI `StreamingResponse` + `text/event-stream`
- 이벤트: `player_start`, `player_complete`, `error`, `done`
- 프론트: `EventSource` API로 실시간 프로그레스 수신
- 현재 폴링 방식을 대체

### 12. 밴 추천

- 적 팀 정보 없이도, 아군 조합의 약점을 보완하는 밴 추천
- 아군 조합 유형의 카운터 챔피언 중 메타 S/A 티어를 밴 추천
- UI: 밴 슬롯 옆에 "추천 밴" 버튼

### 13. 드래프트 페이즈 통합

- 밴/픽을 실제 드래프트 순서(블루/레드 번갈아)로 진행
- 각 단계마다 최적 픽/밴 추천 갱신
- WebSocket 기반 실시간 동기화

### 14. 파워 스파이크 일관성

- 조합 내 챔피언들의 파워 스파이크가 일치하는지 검증
- 초반 조합에 후반 챔피언이 섞이면 감점
- `power_spike` 속성 추가 필요: "early" | "mid" | "late"

---

## 구현 단계

### Phase 1: P0 (예상 1~2일)

```
순서:
1. 점수 가중치 정규화 (#3)
   - CLAUDE.md 갱신
   - 가중치 합계 테스트 추가
   → 코드 변경 최소, 문서 정합성 확보

2. analyze() 최적화 (#1)
   - comp_optimizer_service.py 수정
   - 기존 테스트 전부 통과 확인
   → 성능 개선, API 응답 동일

3. Session persistence (#2)
   - sessionPersistence.js 작성
   - BanPickPage, ResultPage 마운트 로직 수정
   → UX 개선, 백엔드 무변경
```

### Phase 2: P1 (예상 3~4일)

```
순서:
4. 단계적 프론트라인 점수 (#6)
   - 기존 페널티 삭제 + 신규 메서드
   → 점수 분해(#5)의 전제 조건

5. 점수 분해 / Why This Comp (#5)
   - 모델 추가 + calculate_score 리팩토링
   - ScoreBreakdown, WhyThisComp 컴포넌트
   → 프론트라인 점수가 확정된 후 작업

6. 다양성 필터 강화 (#4)
   - diversity_filter 교체
   → 독립적이나 점수 체계 확정 후가 안전

7. 클립보드 복사 (#7)
   - 프론트 전용, 독립적
   → 언제든 가능
```

### Phase 3: P2 (예상 2~3일)

```
순서:
8. 적 조합 카운터 점수 (#8)
   - 카운터 로직 + 테스트
   → archetype 판별 로직 재사용

9. 접이식 조합 카드 (#9)
   - 프론트 전용
   → 독립적

10. 플렉스 픽 감지 (#10)
    - 백엔드 분석 + 프론트 표시
    → 독립적
```

### Phase 4: P3 (v2 이관)

```
11~14: 설계 문서만 유지, v2에서 구현
```

---

## 기획서 → 코드 매핑 (v1.5 추가분)

| 기획서 항목 | 백엔드 domain/ | 백엔드 adapters/ | 프론트 FSD |
|------------|---------------|-----------------|-----------|
| #1 analyze() 최적화 | services/comp_optimizer_service | — | — |
| #2 Session persistence | — | — | shared/lib/sessionPersistence, pages/banpick, pages/result |
| #3 점수 가중치 정규화 | services/comp_optimizer_service | — | — |
| #4 다양성 필터 강화 | services/comp_optimizer_service | — | — |
| #5 점수 분해 | models/composition, services/comp_optimizer_service | api/optimize_router | entities/composition/ui/ScoreBreakdown, WhyThisComp |
| #6 단계적 프론트라인 | services/comp_optimizer_service | — | — |
| #7 클립보드 복사 | — | — | shared/lib/copyToClipboard, formatCompText, entities/composition |
| #8 카운터 점수 | models/composition, services/comp_optimizer_service | api/optimize_router | entities/composition |
| #9 접이식 카드 | — | — | entities/composition, widgets/result-board |
| #10 플렉스 픽 | models/player, services/player_analysis_service | api/optimize_router | entities/champion, entities/player |

---

## 테스트 체크리스트

### 백엔드 (pytest)

```
P0:
[ ] test_weights_sum_to_one — 가중치 합계 = 1.0
[ ] test_analyze_called_only_for_top_n — analyze() 호출 횟수 = top_n
[ ] test_optimize_performance — 5명 × 5챔피언, 응답 시간 < 기존 50%

P1:
[ ] test_graduated_frontline_required_archetype — 이니시 조합, 프론트라인 0/1/2/3명 점수
[ ] test_graduated_frontline_unnecessary_archetype — 포킹 조합, 프론트라인 0/1/2명 점수
[ ] test_graduated_frontline_flexible_archetype — 스플릿 조합, 프론트라인 0/1/2명 점수
[ ] test_old_frontline_penalty_removed — PENALTY_NO_FRONTLINE 상수 없음
[ ] test_score_breakdown_sum — 분해 점수 합 = total_score (±0.1)
[ ] test_score_breakdown_all_fields — 7개 항목 + penalties 필드 존재
[ ] test_why_this_comp_not_empty — why_this_comp 비어있지 않음
[ ] test_diversity_filter_2players — 2명: min_diff=1
[ ] test_diversity_filter_3players — 3명: min_diff=1
[ ] test_diversity_filter_5players — 5명: min_diff=3
[ ] test_diversity_archetype_variety — 상위 5개 중 2가지+ 유형

P2:
[ ] test_counter_score_enemy_2 — 적 2명: 카운터 미적용
[ ] test_counter_score_enemy_3_favorable — 적 3명, 유리 상성: +8
[ ] test_counter_score_enemy_3_unfavorable — 적 3명, 불리 상성: -5
[ ] test_counter_score_multi_archetype — 복수 유형 평균
[ ] test_flex_pick_detection — 2라인 이상 = flex
[ ] test_flex_pick_single_lane — 1라인만 = flex 아님
```

### 프론트엔드 (Vitest + RTL)

```
P0:
[ ] test_session_save_load — sessionStorage 저장/복원
[ ] test_session_expiry — 30분 초과 시 만료
[ ] test_session_no_api_key — API 키 미포함 확인

P1:
[ ] test_score_breakdown_render — 점수 분해 바 차트 렌더링
[ ] test_why_this_comp_render — 텍스트 표시
[ ] test_copy_to_clipboard — 복사 동작 + 버튼 텍스트 변경

P2:
[ ] test_collapsible_card_default — 1위 펼침, 나머지 접힘
[ ] test_collapsible_card_toggle — 클릭 시 토글
[ ] test_flex_badge_render — FLEX 배지 표시
[ ] test_counter_analysis_render — 카운터 분석 UI 표시
```

---

## 숫자 요약 (테스트에서 검증할 값)

```
가중치 (v1.5 정규):
  개인 숙련도: 25% (0.25)
  메타 적합도: 10% (0.10)
  AD/AP 밸런스: 15% (0.15)
  프론트라인: 15% (0.15)
  딜 구성: 15% (0.15)
  웨이브클리어: 10% (0.10)
  스플릿푸시: 10% (0.10)
  합계: 100% (1.00)

다양성 임계값:
  min_diff = max(1, n - 2)
  n=2 → 1, n=3 → 1, n=4 → 2, n=5 → 3

카운터 점수:
  적 최소 인원: 3명
  유리 상성: +8점
  불리 상성: -5점
  중립: 0점

단계적 프론트라인 (필수 조합):
  0명: 0점, 1명: 60점, 2명: 100점, 3명+: 80점

단계적 프론트라인 (불필요 조합):
  0명: 80점, 1명: 100점, 2명+: 70점

단계적 프론트라인 (유연 조합):
  0명: 50점, 1명: 85점, 2명: 100점, 3명+: 75점

세션 만료: 30분

페널티 (v1.5):
  풀 AD: -30점
  풀 AP: -30점
  프론트라인 0명: 삭제 (단계적 점수로 교체)
  웨이브클리어 < 10: -10점
  이니시 부족: -10점
  필링 부족: -8점
  팀파이트 부족: -8점
  오프라인 배정: 챔피언당 -25점
```

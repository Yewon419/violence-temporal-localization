# Drama frames v2 — 우선순위 3·4 vision 샘플 검수 보고서

**검수 일자**: 2026-05-30
**방식**: 핸드오프 전략대로 **전수가 아닌 층화 샘플링** (object 라벨은 FP 낮음·unknown은 패턴 가이드용). 박스별 단독 하이라이트 이미지(`scripts/vision_review_prep.py`)를 score·raw_label 층화로 추출해 vision Read.

---

## 우선순위 4 — `bottle`·`cup`·`cigarette` (전체 373 bbox)

전체 분포: bottle 186 / cup 168 / cigarette 19. score 분포:
| 라벨 | ≥0.5 | 0.4–0.5 | 0.3–0.4 | <0.3 |
|---|---:|---:|---:|---:|
| bottle | 50 | 44 | 90 | 2 |
| cup | 40 | 53 | 72 | 3 |
| cigarette | 3 | 7 | 9 | 0 |

### 샘플 35장 결과 (층화: 라벨×score band)

| 판정 | 수 | 비율 |
|---|---:|---:|
| **clear KEEP** (실제 병/컵/담배) | 26 | 74% |
| borderline (식기 세부클래스·작은/부분 객체) | 7 | 20% |
| questionable (담배 불명확) | 2 | 6% |
| **hard FP** (엉뚱한 객체) | **0** | **0%** |

- **결론: object 라벨은 신뢰도 높음.** violence 라벨(P1 FP 98%)과 정반대. 샘플 35장 중 violence처럼 꽃·차·포스터로 튄 hard FP는 **0건**.
- 본 **score ≥0.5 샘플은 전부 진짜** → 핸드오프의 "≥0.5 자동 keep" 전략 검증됨.
- borderline 7건은 전부 "실제 식기/객체이긴 한데 세부 클래스가 헐거움" (예: 검은 반찬 접시·다기 주전자·장례식 장식 유리통을 cup/bottle로) 또는 너무 작아 애매. **틀린 게 아니라 느슨함.**
- questionable 2건: 차 안·식사 중 담배 여부 화질상 불명확.
- borderline 예시: #000(검은 반찬 접시), #007(다기 주전자), #111(연회 작은 물체), #186(벽 장식), #236(트럭 내 작은 물체), #299(장례식 장식 유리통), #309(작은 물체)

### 권고
- **bottle/cup/cigarette는 일괄 유지(keep) 권고.** 특히 score ≥0.4는 거의 전량 진짜.
- 정밀도가 필요하면 score <0.3(bottle 2·cup 3) + 세부클래스 혼동(bowl/teapot/glass→cup/bottle)만 별도 점검. 비용 대비 효과는 낮음.

---

## 우선순위 3 — `unknown` (전체 373 bbox)

### 정체 (재추적 결과)
CVAT "unknown" = triage **uncertain/low_score(거의 전부 <0.3)** 박스들의 잡탕. raw_label은 전 라벨에 걸침:
`cup 93·explosion 71·bottle 69·car 31·riot 24·abuse 14·bottle cup 13·blood 12·cigarette 12·gun 10·knife 9·car accident 7 …`
score 분포: **<0.3 357 / 0.3–0.4 14 / 0.4–0.5 2** (초저신뢰).

raw_label 기준 분류:
- **OBJ-raw** (cup/bottle/cigarette/bottle cup/drinking) = **169**
- **VIO-raw** (explosion/car/riot/abuse/blood/gun/knife/...) = **204**

### 샘플 20장 결과 (OBJ 10 + VIO 10)

| 분류 | clean KEEP | borderline (저품질·실객체) | FP |
|---|---:|---:|---:|
| OBJ-raw (10) | 0 | 6 | 4 |
| VIO-raw (10) | 0 | 1 | 9 |

- **clean high-quality keep: 0건.**
- VIO-raw는 P1과 동일하게 ~전량 FP (텍스트·반찬·렌즈플레어·포스터·조각상·어두운 인물).
- OBJ-raw는 "실제 식기/병이긴 한데 <0.3이라 너무 작거나 부분 가림" 저품질 + 전화기·문틀·선반 잡동 FP 혼재.
- FP 예시: #117(전화기 수화기→bottle), #256(문틀), #207(선반 잡동), #000(채널 텍스트), #024(반찬), #042(렌즈플레어), #125(문어 조각상), #238(베를린 포스터)

### 권고
- **unknown(373)은 일괄 삭제 권고.** <0.3 잡탕이라 VIO-raw(204)는 거의 FP, OBJ-raw(169)도 학습 가치 있는 깨끗한 박스가 거의 없음.
- 굳이 건진다면 OBJ-raw 중 **육안으로 또렷한 병/컵만** 선별 가능하나, 169장 중 비율이 낮아 비용 대비 효과 미미.

---

## 산출물

- 박스별 이미지: `data/processed/vision_review/p3_unknown/*.jpg`, `.../p4_objects/*.jpg`
- manifest: `data/processed/vision_review/p3_unknown_manifest.json`, `p4_objects_manifest.json`
- 생성 스크립트: `scripts/vision_review_prep.py` (`p3_unknown`/`p4_objects` 그룹)

## 4개 우선순위 종합

| 순위 | 라벨군 | bbox | 방식 | 결론 |
|---|---|---:|---|---|
| 1 | explosion·car_accident·blood·abuse | 119 | 전수 | FP 98.3%, KEEP 2 → **라벨 일괄 제거 검토** |
| 2 | weapon_knife·riot·weapon_gun | 50 | 전수 | KEEP 18(거의 마약왕 벽 장총 1장면)·RELABEL 3(검→knife)·DELETE 29 |
| 3 | unknown | 373 | 샘플 20 | clean keep 0 → **일괄 삭제 권고** |
| 4 | bottle·cup·cigarette | 373 | 샘플 35 | hard FP 0, ~74% 진짜 → **일괄 유지 권고** |

**핵심**: GD 확장 prompt에서 **violence 이벤트·행위 라벨(explosion/car_accident/blood/abuse/riot)은 거의 노이즈**, **object 라벨(bottle/cup/cigarette/gun)은 신뢰 가능**. unknown은 저신뢰 잡탕. 검수자(대표님) 액션은 사실상 ①·③ 라벨 일괄 제거 + ② 마약왕 장총·AK47 keep·검 relabel + ④ object 유지로 수렴.

# dataset_Ver2 — 데이터셋 집계 리포트

> **아카이브 문서입니다.**
> 폐기된 객체검출 트랙의 작업 기록으로, 당시 상태를 그대로 보존한 것입니다.
> 현재 파이프라인은 [저장소 README](../../README.md)를 참고하세요.
> 이 트랙을 왜 접었는지는 README의 「전환 1」 절에 정리했습니다.

> 작성: 2026-06-01 · 대상: [DEteam4/dataset_Ver2](https://huggingface.co/datasets/DEteam4/dataset_Ver2)
> Ultralytics YOLO Detection 1.0 포맷 · `images/{split}/...` + `labels/{split}/...` 미러 구조

---

## 1. 전체 규모

**총 13,928 프레임 · 12,678 박스**

| split | 프레임 | 라벨 txt |
|---|---|---|
| train | 12,334 | 10,751 (빈 txt 4,699) |
| val | 133 | 84 |
| test | 1,461 | 1,461 (빈 815) |

> 빈/누락 txt = 배경(negative) 프레임. YOLO에서 객체 없는 이미지로 학습됨.

**train 서브셋별 프레임**

| 서브셋 | 프레임 |
|---|---|
| train1 | 1,142 |
| train2 | 2,437 |
| train3 | 332 |
| train4 | 4,526 |
| train5 | 200 |
| train6 | 2,443 |
| train7 | 1,254 |

---

## 2. 라벨 분포 (box 기준, 전체)

| 라벨 (id) | 박스 | 비중 |
|---|---|---|
| bottle (1) | 3,337 | 26.3% |
| weapon_blunt (10) | 1,650 | 13.0% |
| smoking_act (5) | 1,459 | 11.5% |
| weapon_gun (9) | 1,186 | 9.4% |
| weapon_knife (8) | 1,131 | 8.9% |
| cup (2) | 1,100 | 8.7% |
| alcohol (4) | 800 | 6.3% |
| cigarette (0) | 490 | 3.9% |
| blood (11) | 399 | 3.1% |
| drinking_act (6) | 339 | 2.7% |
| wine_glass (3) | 229 | 1.8% |
| unknown (7) | 167 | 1.3% |
| riot (14) | 122 | 1.0% |
| shooting (13) | 84 | 0.7% |
| explosion (16) | 65 | 0.5% |
| car_accident (17) | 48 | 0.4% |
| abuse (15) | 37 | 0.3% |
| fighting (12) | 35 | 0.3% |

> id↔name은 CVAT 프로젝트 스킴(0~17) 기준. 클래스 18종.

---

## 3. ⚠ 주의 — id 스킴 불일치 (집계 해석)

데이터셋에 통합 `data.yaml`이 없고, **train2가 다른 ad-hoc id 스킴**을 써서 일부 라벨 집계가 오염됨.

- **weapon_blunt(id10) = 1,650**은 비현실적으로 높음 → train2 `Car Accident` 폴더(1,054프레임)가
  car_accident를 **id10**으로 단 것으로 추정. 대부분 실제 둔기가 아니라 **차량사고**일 가능성.
- id 2·3·7·9 일부도 train2에서 다른 의미로 섞였을 수 있음.

**신뢰 가능 여부**

| 구분 | 라벨 | 상태 |
|---|---|---|
| 객체 클래스 | bottle, cup, cigarette, wine_glass, alcohol, smoking_act, drinking_act, weapon_gun, weapon_knife, blood | ✅ train1·3·5·6·7 정합, 숫자 신뢰 가능 |
| event 계열 | weapon_blunt, car_accident, explosion, fighting, shooting, abuse, riot, unknown | ⚠ train2 스킴 오염 — name↔id 재확인 필요 |

**To-do (팀):** 통합 `data.yaml` 제정 → train2 라벨 id를 정본 스킴으로 remap 후 재집계.

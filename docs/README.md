# 문서

## 현재 파이프라인

| 문서 | 내용 |
|---|---|
| [demo_violence_localization.md](demo_violence_localization.md) | **데모 전체 사양.** 전처리 상수, 모델 구조, 후처리, UI, 정규화 편향 분석까지. 이 프로젝트에서 가장 상세한 문서입니다 |
| [annotation_guide.md](annotation_guide.md) | 폭력 구간을 무엇으로 보고 어디서 끊을지에 대한 판단 기준 |
| [../violence_annotator/README.md](../violence_annotator/README.md) | 자작 어노테이션 도구 사용법 |
| [../labels/README.md](../labels/README.md) | 라벨과 검수 판정 기록의 구성 |

## 아카이브: 폐기된 객체검출 트랙

담배·술잔·흉기 같은 객체를 프레임 단위로 검출하던 초기 트랙의 기록입니다.
심의라는 문제를 풀지 못한다는 판단으로 접었고, 그 경위는 [저장소 README](../README.md)의 「전환 1」에 있습니다.
당시 상태를 그대로 보존했으므로 현재 코드와 맞지 않는 서술이 있습니다.

**설계와 의사결정**

| 문서 | 내용 |
|---|---|
| [decisions.md](_archive_object_detection/decisions.md) | 설계 결정 로그. 각 결정의 이유를 시간순으로 누적 |
| [datasets.md](_archive_object_detection/datasets.md) | 데이터셋별 출처, 라이선스, 다운로드 절차, 클래스 매핑 |
| [README_dataset_pipeline.md](_archive_object_detection/README_dataset_pipeline.md) | 데이터셋 빌드 파이프라인 사용법 |
| [cvat_workflow.md](_archive_object_detection/cvat_workflow.md) | CVAT 셋업과 팀 검수 운영 |

**자동 라벨 검수 기록**

Grounding DINO가 생성한 bbox를 전수 또는 층화 샘플로 검수한 결과입니다.
"자동 라벨은 못 쓴다"는 결론의 근거가 되는 문서들입니다.

| 문서 | 내용 |
|---|---|
| [vision_review_p1_report.md](_archive_object_detection/vision_review_p1_report.md) | explosion·car_accident·blood·abuse 119 bbox 전수. **FP 98.3%** |
| [vision_review_p1_violence_event_report.md](_archive_object_detection/vision_review_p1_violence_event_report.md) | 위 검수의 상세판 |
| [vision_review_p2_weapon_riot_report.md](_archive_object_detection/vision_review_p2_weapon_riot_report.md) | riot·weapon_knife·weapon_gun 50 bbox 전수 |
| [vision_review_p3p4_sample_report.md](_archive_object_detection/vision_review_p3p4_sample_report.md) | bottle·cup·cigarette 층화 샘플. 사물 라벨은 신뢰 가능 |

**작업 기록**

| 문서 | 내용 |
|---|---|
| [drama_frames_process_log.md](_archive_object_detection/drama_frames_process_log.md) | 영화 8편 프레임 수집부터 CVAT 반영까지 전 과정 |
| [handoff_2026-05-30.md](_archive_object_detection/handoff_2026-05-30.md) | 검수 완료 시점의 인수인계 문서 |
| [violence_report.md](_archive_object_detection/violence_report.md) | 폭력 카테고리 데이터셋 구축 보고 |
| [smoking_drinking_report.md](_archive_object_detection/smoking_drinking_report.md) | 흡연·음주 카테고리 구축 보고 |
| [dataset_ver2_report.md](_archive_object_detection/dataset_ver2_report.md) | YOLO 학습 데이터셋 업로드 보고 |

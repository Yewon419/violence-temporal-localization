# labels

라벨과 검수 판정 기록입니다. 원본 이미지·영상은 저작권 문제로 제외했고, **좌표와 판정만** 남겼습니다.
파일 수가 1만 5천 개지만 전부 텍스트라 합쳐서 13MB입니다.

원래는 `data/` 아래에서 이미지와 섞여 있던 것을 공개용으로 분리했습니다.
경로 구조는 그대로라 스크립트가 참조하는 상대 경로와 대응됩니다.

## 폭력 구간 어노테이션

이 프로젝트의 최종 산출물인 구간 라벨은 여기가 아니라
[`../violence_annotator/output/`](../violence_annotator/output/)에 있습니다.

```
[신세계, 0, 0, 253, neg_easy]
[신세계, 1, 254, 256, neg_hard]
[신세계, 2, 257, 379, neg_easy]
```

`[movie_id, scene_num, start_frame, end_frame, label]` 형식이고 **frame index는 2fps 기준**입니다.
즉 프레임 k는 k/2초입니다. 5초 = 10프레임.

## 이 폴더의 구성

| 경로 | 내용 |
|---|---|
| `processed/vision_review/` | Grounding DINO 자동 라벨을 전수 검수한 판정 기록. KEEP/DELETE/RELABEL |
| `processed/cvat_backup_2026-05-30/` | CVAT 일괄 정리 **직전** 백업 (적용 전 916 shapes 전량) |
| `processed/zombie01_yolo/` | 좀비 영화 트랙 YOLO 라벨 (검수 후 확정분) |
| `processed/gd_zombie_full/`, `gd_zombie_filtered/` | GD 원본 추론 결과와 필터 통과분. 필터 전후 비교용 |
| `processed/hf_train7/`, `hf_train8/` | Hugging Face 업로드 배치의 라벨 |
| `processed/smoking/`, `drinking/` | 객체검출 트랙의 bbox 라벨 |
| `processed/gd_demo*`, `gd_triage*` | 초기 파일럿과 트리아지 산출물 |
| `annotated/xdv_test_annotations.txt` | XD-Violence test split 원본 annotation |
| `logs/` | 유튜브 수집 로그 |

## 검수 기록을 왜 남겼는가

`processed/vision_review/`의 판정은 "자동 라벨이 실패했다"는 주장의 **근거**입니다.
explosion·car_accident·blood·abuse 119개를 전수로 본 결과 117개가 False Positive였고,
그 판정 하나하나가 여기에 남아 있습니다. 결론만 적고 근거를 버리면 검증할 수 없습니다.

판정 결과를 사람이 읽을 수 있게 정리한 보고서는
[`../docs/_archive_object_detection/`](../docs/_archive_object_detection/)의
`vision_review_p1_report.md`, `vision_review_p2_weapon_riot_report.md`,
`vision_review_p3p4_sample_report.md`에 있습니다.

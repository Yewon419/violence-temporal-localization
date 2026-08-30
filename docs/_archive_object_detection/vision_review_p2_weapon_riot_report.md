# Drama frames v2 — 우선순위 2 — weapon_knife·riot·weapon_gun vision 전수 검수 보고서

> **아카이브 문서입니다.**
> 폐기된 객체검출 트랙의 작업 기록으로, 당시 상태를 그대로 보존한 것입니다.
> 현재 파이프라인은 [저장소 README](../../README.md)를 참고하세요.
> 이 트랙을 왜 접었는지는 README의 「전환 1」 절에 정리했습니다.

**대상**: CVAT v2 import 중 `weapon_knife`·`riot`·`weapon_gun` 라벨 50 bbox 전수
**방법**: 박스별 단독 하이라이트 이미지 생성 후 vision Read 전수 판정
**검수 일자**: 2026-05-30

## 요약

- 전체: **50** bbox
- KEEP(유지): **18**
- RELABEL(라벨 교체): **3**
- DELETE(삭제): **29**
- **삭제 비율(FP): 58.0%** (29/50)

| 라벨 | 전체 | keep | relabel | delete |
|---|---:|---:|---:|---:|
| weapon_gun | 23 | 18 | 3 | 2 |
| riot | 16 | 0 | 0 | 16 |
| weapon_knife | 11 | 0 | 0 | 11 |

## KEEP 목록 (유지/확인 대상)

| idx | 영상 | frame | 라벨 | score | 이미지 | 관찰 |
|---:|---|---|---|---:|---|---|
| 11 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00019.jpg | weapon_gun | 0.46 | `011_LkSY-EuTb1E_00019_weapon_gun.jpg` | 마약왕 저택 벽 장식 장총(라이플) — 근접 명확 |
| 12 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00019.jpg | weapon_gun | 0.42 | `012_LkSY-EuTb1E_00019_weapon_gun.jpg` | 마약왕 저택 벽 장식 장총 — 근접 명확 |
| 13 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00019.jpg | weapon_gun | 0.31 | `013_LkSY-EuTb1E_00019_weapon_gun.jpg` | 마약왕 저택 벽 장식 장총 — 근접 명확 |
| 14 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00019.jpg | weapon_gun | 0.39 | `014_LkSY-EuTb1E_00019_weapon_gun.jpg` | 마약왕 저택 벽 장식 장총 — 근접 명확 |
| 15 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00019.jpg | weapon_gun | 0.36 | `015_LkSY-EuTb1E_00019_weapon_gun.jpg` | 마약왕 저택 벽 장식 장총 — 근접 명확 |
| 16 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00023.jpg | weapon_gun | 0.38 | `016_LkSY-EuTb1E_00023_weapon_gun.jpg` | 마약왕 저택 벽 장총(와이드샷, 원거리·작음·저품질) |
| 17 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00023.jpg | weapon_gun | 0.33 | `017_LkSY-EuTb1E_00023_weapon_gun.jpg` | 마약왕 저택 벽 장총(와이드샷, 원거리·저품질) |
| 18 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00023.jpg | weapon_gun | 0.32 | `018_LkSY-EuTb1E_00023_weapon_gun.jpg` | 마약왕 저택 벽 장총(와이드샷, 원거리·저품질) |
| 19 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00023.jpg | weapon_gun | 0.33 | `019_LkSY-EuTb1E_00023_weapon_gun.jpg` | 마약왕 저택 벽 장총(와이드샷, 원거리·저품질) |
| 21 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00322.jpg | weapon_gun | 0.49 | `021_LkSY-EuTb1E_00322_weapon_gun.jpg` | 마약왕 저택 벽 쌍열 산탄총 — 명확 |
| 22 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00322.jpg | weapon_gun | 0.44 | `022_LkSY-EuTb1E_00322_weapon_gun.jpg` | 마약왕 저택 벽 장총(박스 약간 위로 헐거움) |
| 23 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00322.jpg | weapon_gun | 0.49 | `023_LkSY-EuTb1E_00322_weapon_gun.jpg` | 마약왕 저택 벽 산탄총 — 명확 |
| 24 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00322.jpg | weapon_gun | 0.42 | `024_LkSY-EuTb1E_00322_weapon_gun.jpg` | 마약왕 저택 벽 장총(박스 약간 위로 헐거움) |
| 25 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00326.jpg | weapon_gun | 0.48 | `025_LkSY-EuTb1E_00326_weapon_gun.jpg` | 마약왕 저택 벽 쌍열 산탄총 — 명확 |
| 26 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00326.jpg | weapon_gun | 0.47 | `026_LkSY-EuTb1E_00326_weapon_gun.jpg` | 마약왕 저택 벽 장총 — 명확 |
| 27 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00326.jpg | weapon_gun | 0.38 | `027_LkSY-EuTb1E_00326_weapon_gun.jpg` | 마약왕 저택 벽 장총(박스 약간 위로 헐거움) |
| 28 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00326.jpg | weapon_gun | 0.37 | `028_LkSY-EuTb1E_00326_weapon_gun.jpg` | 마약왕 저택 벽 장총(박스 약간 위로 헐거움) |
| 32 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_01425.jpg | weapon_gun | 0.57 | `032_Rqlf3zNPqgQ_01425_weapon_gun.jpg` | ★ AK-47 소총 명확 (달콤한 인생) |

## RELABEL 목록 (라벨 교체 권고)

| idx | 영상 | frame | 현재 라벨 | score | 이미지 | 권고 |
|---:|---|---|---|---:|---|---|
| 0 | 3auH8hGUezI | 3auH8hGUezI_frame_00264.jpg | weapon_gun | 0.34 | `000_3auH8hGUezI_00264_weapon_gun.jpg` | →weapon_knife: 내부자들 칼(검) 뽑는 장면 (총 아님, borderline) |
| 1 | 3auH8hGUezI | 3auH8hGUezI_frame_00264.jpg | weapon_gun | 0.34 | `001_3auH8hGUezI_00264_weapon_gun.jpg` | →weapon_knife: 위와 동일 frame 중복 박스 (검) |
| 2 | 3auH8hGUezI | 3auH8hGUezI_frame_00295.jpg | weapon_gun | 0.54 | `002_3auH8hGUezI_00295_weapon_gun.jpg` | →weapon_knife: 빗속 장검 명확 (총 아님) |

## DELETE 목록 (삭제 권고 — 전체)

| idx | 영상 | frame | 라벨 | score | 관찰(실제 내용) |
|---:|---|---|---|---:|---|
| 3 | 3auH8hGUezI | 3auH8hGUezI_frame_00477.jpg | riot | 0.34 | 롤렉스 시계(상자 안) |
| 4 | 3auH8hGUezI | 3auH8hGUezI_frame_00518.jpg | riot | 0.39 | 롤렉스 시계(서랍 안) |
| 5 | 3auH8hGUezI | 3auH8hGUezI_frame_00812.jpg | weapon_knife | 0.31 | 식탁 상추/음식 |
| 6 | 3auH8hGUezI | 3auH8hGUezI_frame_00822.jpg | weapon_knife | 0.31 | 식탁 그릇 |
| 7 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_00705.jpg | weapon_knife | 0.32 | 식탁 반찬 |
| 8 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01233.jpg | weapon_knife | 0.38 | 식탁 소주병/젓가락 |
| 9 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01445.jpg | weapon_knife | 0.32 | 연회 식탁 |
| 10 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00010.jpg | riot | 0.33 | 채널 인트로 영화관 의자 일러스트 |
| 20 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00143.jpg | weapon_knife | 0.44 | 마약왕 폐허신 — 박스는 잔해 벽(칼 안 보임) |
| 29 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00349.jpg | riot | 0.32 | 어선 |
| 30 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00441.jpg | riot | 0.31 | '남산의 부장들' 포스터 |
| 31 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00446.jpg | riot | 0.30 | 불티 날리는 배 |
| 33 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_01456.jpg | riot | 0.30 | 폴더폰(흑백) |
| 34 | vyXEi00PVrw | vyXEi00PVrw_frame_00404.jpg | riot | 0.35 | 아시아나 비행기 |
| 35 | vyXEi00PVrw | vyXEi00PVrw_frame_00413.jpg | weapon_knife | 0.30 | 식탁 커틀러리(식사용 나이프, 무기 아님) |
| 36 | vyXEi00PVrw | vyXEi00PVrw_frame_00646.jpg | weapon_gun | 0.41 | 문서 속 흑백 사진(총 확인 불가, 저해상) |
| 37 | vyXEi00PVrw | vyXEi00PVrw_frame_00681.jpg | riot | 0.41 | 인화 사진들 |
| 38 | vyXEi00PVrw | vyXEi00PVrw_frame_00807.jpg | riot | 0.30 | 장례식 영정 |
| 39 | vyXEi00PVrw | vyXEi00PVrw_frame_00834.jpg | riot | 0.34 | 건설 철탑/크레인 |
| 40 | wBr3f72w-fg | wBr3f72w-fg_frame_00001.jpg | weapon_knife | 0.31 | 타이틀 글자 'f' |
| 41 | wBr3f72w-fg | wBr3f72w-fg_frame_00568.jpg | weapon_knife | 0.34 | 식탁 그릇/숟가락 |
| 42 | wBr3f72w-fg | wBr3f72w-fg_frame_00792.jpg | riot | 0.31 | 서류 |
| 43 | x2PjLCMrfTk | x2PjLCMrfTk_frame_00252.jpg | weapon_knife | 0.37 | 식당 숟가락 |
| 44 | x2PjLCMrfTk | x2PjLCMrfTk_frame_00252.jpg | weapon_knife | 0.36 | 식당 숟가락 |
| 45 | x2PjLCMrfTk | x2PjLCMrfTk_frame_00754.jpg | riot | 0.36 | 공중전화 키패드 |
| 46 | x2PjLCMrfTk | x2PjLCMrfTk_frame_00862.jpg | weapon_gun | 0.32 | 눈밭 나뭇가지/막대기(총 아님) |
| 47 | x2PjLCMrfTk | x2PjLCMrfTk_frame_01274.jpg | riot | 0.32 | 빗속 주행 차 |
| 48 | x2PjLCMrfTk | x2PjLCMrfTk_frame_01633.jpg | riot | 0.32 | 자막 텍스트 오버레이 |
| 49 | x2PjLCMrfTk | x2PjLCMrfTk_frame_01741.jpg | riot | 0.46 | 야간 어선 |

## 산출물

- 박스별 검수 이미지: `data/processed/vision_review/p2_weapon_riot/*.jpg`
- 판정 머신리더블: `data/processed/vision_review/p2_weapon_riot_verdicts.json`
- 생성 스크립트: `scripts/vision_review_prep.py`, `scripts/vision_review_merge.py`

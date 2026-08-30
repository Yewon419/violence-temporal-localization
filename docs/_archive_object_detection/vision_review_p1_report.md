# Drama frames v2 — 우선순위 1 vision 전수 검수 보고서

**대상**: CVAT v2 import 중 `explosion`·`car_accident`·`blood`·`abuse` 라벨 119 bbox 전수
**방법**: 박스별 단독 하이라이트 이미지 생성 후 vision Read 전수 판정
**검수 일자**: 2026-05-30

## 요약

- 전체: **119** bbox
- KEEP(유지): **2**
- DELETE(삭제): **117**
- **False Positive 비율: 98.3%** (117/119)

라벨별 분포:

| 라벨 | 전체 | keep | delete |
|---|---:|---:|---:|
| explosion | 57 | 0 | 57 |
| car_accident | 49 | 2 | 47 |
| blood | 10 | 0 | 10 |
| abuse | 3 | 0 | 3 |

## 핵심 결론

- 우선순위 1 (violence event 라벨)은 **거의 전량 FP**. GD 확장 prompt가 일상 사물·풍경·UI 요소를 violence 이벤트로 오검출.
- 주요 FP 패턴:
  - `explosion` → 빨간 네온/등, 꽃·화환, 채널 로고·인트로 일러스트, 포스터 텍스처, 백열등·보케, 액자 그림
  - `car_accident` → **정상 주차·주행 중인 멀쩡한 차량**(대부분), 어선, 포스터, 폴더폰 화면
  - `blood` → 립스틱, 꽃다발·화환, 반찬, 장미밭
  - `abuse` → **자막/채널 텍스트 오버레이**
- 권고: 이 4개 라벨은 CVAT에서 일괄 제거 검토. 실제 유지 대상은 아래 KEEP 목록뿐.

## KEEP 목록 (유지/확인 대상)

| idx | 영상 | frame | 라벨 | score | 이미지 | 관찰 |
|---:|---|---|---|---:|---|---|
| 114 | x2PjLCMrfTk | x2PjLCMrfTk_frame_01238.jpg | car_accident | 0.31 | `114_x2PjLCMrfTk_01238_car_accident.jpg` | ★ 진짜 car_accident — 트럭이 다수 차량과 충돌, 차량 박살·파편 비산 (황해 엔딩 추돌) |
| 117 | x2PjLCMrfTk | x2PjLCMrfTk_frame_01651.jpg | car_accident | 0.31 | `117_x2PjLCMrfTk_01651_car_accident.jpg` | 앞범퍼 파손 차량(사고 후 차량 가능성, borderline — 대표님 최종 확인 권장) |

## DELETE 목록 (삭제 권고 — 전체)

| idx | 영상 | frame | 라벨 | score | 관찰(실제 내용) |
|---:|---|---|---|---:|---|
| 0 | 3auH8hGUezI | 3auH8hGUezI_frame_00001.jpg | explosion | 0.44 | '리뷰쇼' 인트로 주황 원 로고 |
| 1 | 3auH8hGUezI | 3auH8hGUezI_frame_00487.jpg | blood | 0.35 | 여성 입술(립스틱) |
| 2 | 3auH8hGUezI | 3auH8hGUezI_frame_00812.jpg | explosion | 0.44 | 벽에 걸린 마늘 두름 |
| 3 | 3auH8hGUezI | 3auH8hGUezI_frame_00822.jpg | blood | 0.30 | 배경 선반의 붉은 음식(고추 등) |
| 4 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_00071.jpg | explosion | 0.25 | 렌즈 플레어/핑크 빛번짐 |
| 5 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_00124.jpg | explosion | 0.39 | 흰 커튼/창 |
| 6 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_00265.jpg | car_accident | 0.36 | 어선 |
| 7 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_00282.jpg | car_accident | 0.25 | 멀리 떠 있는 배 |
| 8 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_00388.jpg | explosion | 0.40 | 룸살롱 벽지 무늬 |
| 9 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_00423.jpg | car_accident | 0.38 | 거리 싸움 배경 주차 차량 |
| 10 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_00617.jpg | explosion | 0.52 | 경찰서 꽃 엠블럼 |
| 11 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_00705.jpg | blood | 0.33 | 반찬 접시 |
| 12 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01075.jpg | explosion | 0.41 | 술집 빨간 네온사인 |
| 13 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01092.jpg | explosion | 0.38 | 술집 빨간 네온사인 |
| 14 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01110.jpg | explosion | 0.32 | 빨간 등 |
| 15 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01216.jpg | car_accident | 0.42 | 정상 주차 세단(야간) |
| 16 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01216.jpg | explosion | 0.33 | 주황 종이등 |
| 17 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01233.jpg | explosion | 0.36 | 벽 장식 접시 |
| 18 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01251.jpg | car_accident | 0.32 | 배경 주차 차량 |
| 19 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01339.jpg | explosion | 0.33 | 모란 그림 액자 |
| 20 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01356.jpg | blood | 0.38 | 꽃꽂이 붉은 열매 |
| 21 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01356.jpg | explosion | 0.34 | 산수화 액자 |
| 22 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01374.jpg | car_accident | 0.40 | 경광등 단 차(검찰 체포신, 충돌 없음) |
| 23 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01656.jpg | car_accident | 0.36 | 몸싸움 중 멀쩡한 차(사고 아님) |
| 24 | 69RJZ7TwDrQ | 69RJZ7TwDrQ_frame_01744.jpg | explosion | 0.33 | 돌잔치 꽃 장식 |
| 25 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00010.jpg | car_accident | 0.45 | 채널 인트로 영화관 의자 일러스트 |
| 26 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00010.jpg | explosion | 0.35 | 채널 인트로 의자 일러스트 |
| 27 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00014.jpg | blood | 0.35 | 팝콘통 일러스트 |
| 28 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00014.jpg | explosion | 0.33 | 채널 인트로 의자 일러스트 |
| 29 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00014.jpg | blood | 0.31 | 팝콘 일러스트 |
| 30 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00037.jpg | explosion | 0.46 | 마약왕 포스터 거친 한자 텍스처 |
| 31 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00088.jpg | explosion | 0.31 | 초록 선풍기 |
| 32 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00124.jpg | car_accident | 0.43 | 저택 앞 정상 주차 차량 |
| 33 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00129.jpg | blood | 0.42 | 장미밭 |
| 34 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00134.jpg | explosion | 0.32 | 밀짚 장식 램프 |
| 35 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00138.jpg | explosion | 0.32 | 밀짚 장식 램프 |
| 36 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00152.jpg | car_accident | 0.44 | 정상 주차 세단 |
| 37 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00157.jpg | explosion | 0.55 | 검찰 무궁화 엠블럼 |
| 38 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00212.jpg | car_accident | 0.35 | 신문 흑백사진 속 차량 |
| 39 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00216.jpg | blood | 0.35 | 꽃다발 |
| 40 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00221.jpg | car_accident | 0.42 | 부산 일몰 항공 뷰 |
| 41 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00244.jpg | explosion | 0.30 | 어두운 빈 영역 |
| 42 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00262.jpg | car_accident | 0.43 | 정상 주차 클래식카 |
| 43 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00285.jpg | explosion | 0.32 | 붉은 조명 신(폭발 아님) |
| 44 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00290.jpg | explosion | 0.36 | 백열 전구 |
| 45 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00313.jpg | explosion | 0.32 | 배경 꽃 그림 |
| 46 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00345.jpg | explosion | 0.33 | 창문 흐릿한 영역 |
| 47 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00349.jpg | car_accident | 0.32 | 어선 |
| 48 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00368.jpg | car_accident | 0.44 | 거리 주차 차량 |
| 49 | LkSY-EuTb1E | LkSY-EuTb1E_frame_00446.jpg | car_accident | 0.39 | 불티 날리는 배(차 아님) |
| 50 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00092.jpg | explosion | 0.39 | 화분/꽃꽂이 |
| 51 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00108.jpg | explosion | 0.33 | 화분/꽃꽂이 |
| 52 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00246.jpg | car_accident | 0.33 | 정상 주차 빨간 차 |
| 53 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00460.jpg | car_accident | 0.39 | 야간 도로 주행 차량 |
| 54 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00475.jpg | car_accident | 0.45 | 정상 주차 SUV |
| 55 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00491.jpg | car_accident | 0.35 | 헤드라이트 글레어 차량 |
| 56 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00506.jpg | explosion | 0.34 | 빛 보케 |
| 57 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00521.jpg | explosion | 0.33 | 담쟁이 흰꽃 |
| 58 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00537.jpg | explosion | 0.36 | 빛나는 램프갓 |
| 59 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00644.jpg | car_accident | 0.42 | 다리 위 정상 주차 차 |
| 60 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00659.jpg | car_accident | 0.38 | 흰 차 위 폭행 장면(폭력이나 car_accident 라벨 오류, 박스는 차) |
| 61 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00675.jpg | car_accident | 0.34 | 다리 위 정상 차(옆 도로 쓰러진 사람은 박스 밖) |
| 62 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00690.jpg | car_accident | 0.44 | 주차장 멀쩡한 차 |
| 63 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00843.jpg | explosion | 0.40 | 어두운 손/주먹 |
| 64 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_00920.jpg | explosion | 0.35 | 보케 조명 |
| 65 | Rqlf3zNPqgQ | Rqlf3zNPqgQ_frame_01119.jpg | explosion | 0.32 | 금발 머리카락 |
| 66 | sMpzdgHrINs | sMpzdgHrINs_frame_00058.jpg | explosion | 0.46 | 원형 마스크 포스터 텍스트 |
| 67 | sMpzdgHrINs | sMpzdgHrINs_frame_00081.jpg | car_accident | 0.36 | 정비소 멀쩡한 차(절도 장면) |
| 68 | sMpzdgHrINs | sMpzdgHrINs_frame_00653.jpg | car_accident | 0.36 | 야간 주행 머스탱 |
| 69 | sMpzdgHrINs | sMpzdgHrINs_frame_00745.jpg | explosion | 0.41 | 검찰 수사관증 엠블럼 |
| 70 | sMpzdgHrINs | sMpzdgHrINs_frame_00768.jpg | blood | 0.31 | 꽃다발 |
| 71 | sMpzdgHrINs | sMpzdgHrINs_frame_00802.jpg | car_accident | 0.35 | 골목 차 헤드라이트 |
| 72 | sMpzdgHrINs | sMpzdgHrINs_frame_00848.jpg | car_accident | 0.34 | 영화 '베를린' 포스터 |
| 73 | sMpzdgHrINs | sMpzdgHrINs_frame_00905.jpg | explosion | 0.31 | 옥상 LED 전광판 |
| 74 | sMpzdgHrINs | sMpzdgHrINs_frame_00985.jpg | car_accident | 0.33 | 정비소 비닐 덮인 차 |
| 75 | sMpzdgHrINs | sMpzdgHrINs_frame_01134.jpg | car_accident | 0.44 | 노란 봉고차+경광등 |
| 76 | sMpzdgHrINs | sMpzdgHrINs_frame_01134.jpg | explosion | 0.31 | 경광등 빨간 불 |
| 77 | vyXEi00PVrw | vyXEi00PVrw_frame_00009.jpg | abuse | 0.31 | 채널 텍스트 '구독 버튼을 눌러줌' |
| 78 | vyXEi00PVrw | vyXEi00PVrw_frame_00009.jpg | abuse | 0.30 | 채널 텍스트 '리아군의 다락방' |
| 79 | vyXEi00PVrw | vyXEi00PVrw_frame_00018.jpg | explosion | 0.31 | 'R MOVIE' 채널 로고 |
| 80 | vyXEi00PVrw | vyXEi00PVrw_frame_00027.jpg | car_accident | 0.33 | 야간 교차로 정상 교통 |
| 81 | vyXEi00PVrw | vyXEi00PVrw_frame_00090.jpg | explosion | 0.36 | 장례식 화환 |
| 82 | vyXEi00PVrw | vyXEi00PVrw_frame_00099.jpg | car_accident | 0.31 | 장례식 검은 밴 |
| 83 | vyXEi00PVrw | vyXEi00PVrw_frame_00117.jpg | car_accident | 0.32 | 인물 클로즈업(배경 차) |
| 84 | vyXEi00PVrw | vyXEi00PVrw_frame_00287.jpg | car_accident | 0.30 | 주차장 차 클로즈업(옆 액션) |
| 85 | vyXEi00PVrw | vyXEi00PVrw_frame_00681.jpg | car_accident | 0.34 | 인화 사진들 |
| 86 | vyXEi00PVrw | vyXEi00PVrw_frame_00771.jpg | car_accident | 0.31 | 차 본넷 POV |
| 87 | vyXEi00PVrw | vyXEi00PVrw_frame_00807.jpg | explosion | 0.31 | 장례식 영정 화환 |
| 88 | vyXEi00PVrw | vyXEi00PVrw_frame_00807.jpg | explosion | 0.31 | 장례식 영정 화환 |
| 89 | vyXEi00PVrw | vyXEi00PVrw_frame_00852.jpg | explosion | 0.37 | 수중 부유물 신 |
| 90 | vyXEi00PVrw | vyXEi00PVrw_frame_00852.jpg | explosion | 0.32 | 수중 부유물 신 |
| 91 | vyXEi00PVrw | vyXEi00PVrw_frame_00870.jpg | abuse | 0.35 | 저작권 안내 텍스트 |
| 92 | vyXEi00PVrw | vyXEi00PVrw_frame_00879.jpg | explosion | 0.29 | 입자/파티클 전환 효과 |
| 93 | wBr3f72w-fg | wBr3f72w-fg_frame_00060.jpg | explosion | 0.35 | 배경 장식물 |
| 94 | wBr3f72w-fg | wBr3f72w-fg_frame_00166.jpg | car_accident | 0.33 | 폴더폰 화면 속 영상 |
| 95 | wBr3f72w-fg | wBr3f72w-fg_frame_00320.jpg | explosion | 0.33 | 야간 단풍잎 |
| 96 | wBr3f72w-fg | wBr3f72w-fg_frame_00391.jpg | explosion | 0.36 | 상점 보케 조명 |
| 97 | wBr3f72w-fg | wBr3f72w-fg_frame_00509.jpg | blood | 0.31 | 웨딩카 꽃 장식 |
| 98 | wBr3f72w-fg | wBr3f72w-fg_frame_00556.jpg | explosion | 0.35 | 화장실 꽃병 |
| 99 | wBr3f72w-fg | wBr3f72w-fg_frame_00580.jpg | explosion | 0.33 | 화분 |
| 100 | wBr3f72w-fg | wBr3f72w-fg_frame_00792.jpg | explosion | 0.32 | 크리스탈 그릇 |
| 101 | wBr3f72w-fg | wBr3f72w-fg_frame_00828.jpg | car_accident | 0.43 | 야간 정상 주차 차 |
| 102 | wBr3f72w-fg | wBr3f72w-fg_frame_00875.jpg | explosion | 0.32 | 회색 베개/쿠션 |
| 103 | wBr3f72w-fg | wBr3f72w-fg_frame_00958.jpg | explosion | 0.32 | 크리스마스 장식 |
| 104 | wBr3f72w-fg | wBr3f72w-fg_frame_01052.jpg | car_accident | 0.36 | 강변 정차 트럭 |
| 105 | wBr3f72w-fg | wBr3f72w-fg_frame_01064.jpg | explosion | 0.33 | 보케 조명 |
| 106 | x2PjLCMrfTk | x2PjLCMrfTk_frame_00018.jpg | car_accident | 0.40 | 헤드라이트 켠 주행 차 |
| 107 | x2PjLCMrfTk | x2PjLCMrfTk_frame_00036.jpg | car_accident | 0.36 | 식당 앞 정차 차 |
| 108 | x2PjLCMrfTk | x2PjLCMrfTk_frame_00323.jpg | explosion | 0.36 | 달력에 동그라미 친 '16' |
| 109 | x2PjLCMrfTk | x2PjLCMrfTk_frame_00431.jpg | car_accident | 0.37 | 골목 정차 차 |
| 110 | x2PjLCMrfTk | x2PjLCMrfTk_frame_00449.jpg | car_accident | 0.38 | 야간 주행 세단 |
| 111 | x2PjLCMrfTk | x2PjLCMrfTk_frame_00557.jpg | explosion | 0.32 | 니트 비니 모자(칼은 별도 라벨) |
| 112 | x2PjLCMrfTk | x2PjLCMrfTk_frame_00575.jpg | car_accident | 0.42 | 분식점 앞 봉고트럭 |
| 113 | x2PjLCMrfTk | x2PjLCMrfTk_frame_01113.jpg | car_accident | 0.32 | 대우 트럭 정면 |
| 115 | x2PjLCMrfTk | x2PjLCMrfTk_frame_01274.jpg | car_accident | 0.34 | 빗속 주행 차(충돌 없음) |
| 116 | x2PjLCMrfTk | x2PjLCMrfTk_frame_01364.jpg | explosion | 0.37 | 빨간 양보 표지판 |
| 118 | x2PjLCMrfTk | x2PjLCMrfTk_frame_01741.jpg | car_accident | 0.42 | 야간 어선 |

## 산출물

- 박스별 검수 이미지: `data/processed/vision_review/p1_violence_event/*.jpg`
- 판정 머신리더블: `data/processed/vision_review/p1_violence_event_verdicts.json`
- 생성 스크립트: `scripts/vision_review_prep.py`, `scripts/vision_review_merge.py`

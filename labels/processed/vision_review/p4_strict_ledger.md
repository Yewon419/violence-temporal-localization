# P4 strict re-review ledger (엄격: 술자리만 유지)

Criterion — KEEP only: 소주/맥주/양주병, 술잔(음주맥락), 담배.
DELETE: 찻잔·물컵·보온병·트로피·접시·일상장면 컵·음주맥락 없는 컵·하드 FP(객체 오검출).

Frame decision: keep_all / delete_all / mixed(delete idx...).
Idx = manifest idx (p4_objects_manifest.json). Final delete-idx list compiled at end.

## 3auH8hGUezI (내부자들)
- 00021 delete_all
- 00031 delete_all
- 00051 delete_all
- 00082 keep_all
- 00254 delete_all
- 00376 delete_all
- 00386 delete_all
- 00406 delete_all
- 00609 delete_all
- 00649 delete_all
- 00731 delete_all
- 00791 keep_all
- 00802 keep_all
- 00812 mixed: delete #27 (blue lighter FP)
- 00822 keep_all
- 00832 keep_all
- 00883 keep_all
- 00893 keep_all
- 00984 delete_all

## 69RJZ7TwDrQ (범죄와의전쟁)
- 00036 delete_all
- 00194 delete_all
- 00229 keep_all
- 00282 keep_all
- 00317 mixed: delete #50(thermos) #51(ashtray) #53(tissue box); keep #52(glass)
- 00353 keep_all
- 00441 delete_all
- 00494 delete_all
- 00546 delete_all
- 00634 delete_all
- 00652 keep_all
- 00705 delete_all
- 00811 keep_all
- 00916 delete_all
- 00934 delete_all
- 01128 keep_all
- 01145 keep_all
- 01233 keep_all
- 01110 keep_all (#81 술집/이자카야 — 술잔 맥락)
- 01321 mixed: delete #101(cup ambiguous) #102(놋쇠주전자 FP); keep #103(cigarette)
- 01445 keep_all
- 01744 delete_all

## LkSY-EuTb1E (마약왕)
- 00010 delete_all (만화 인트로 음료컵 일러스트)
- 00014 delete_all (만화 인트로 음료컵·팝콘 일러스트)
- 00042 delete_all (서류/봉투 FP)
- 00051 delete_all (지하 어두운 FP)
- 00079 delete_all (침실 바닥 소물 FP)
- 00083 delete_all (그릇가게 흰통 FP)
- 00088 delete_all (그릇가게 어두운 소물 FP)
- 00097 delete_all (토마토주스 캔·잔 — 술 아님)
- 00101 keep_all (#131 양주병)
- 00111 delete_all (야외 커피/물컵)
- 00134 delete_all (찻잔·디저트)
- 00138 delete_all (찻잔)
- 00147 delete_all (상점 소물 FP)
- 00152 keep_all (#139 담배)
- 00166 keep_all (#140 담배)
- 00175 keep_all (#141~148 요트 샴페인파티 — 술잔·샴페인병)
- 00184 delete_all (전화 수화기 FP)
- 00193 delete_all (전화 수화기 FP)
- 00244 delete_all (전화 수화기 FP)
- 00322 delete_all (장식품 FP)
- 00326 delete_all (장식품 FP)
- 00331 delete_all (창고 주전자 edge FP)
- 00340 delete_all (캔/조명기구 FP)
- 00368 delete_all (거리 소물 FP)
- 00391 delete_all (맨팔 클로즈업 FP)
- 00423 delete_all (마약테이블 투명컵 — 술 아님)

## Rqlf3zNPqgQ (달콤한 인생)
- 00001 delete_all (빈 식당 테이블 소물/조미료 FP)
- 00031 keep_all (라운지 바 — 술자리)
- 00062 delete_all (식사 물컵/공기 — 술 아님)
- 00108 keep_all (#175 담배)
- 00123 mixed: keep #180(담배); delete #176,#177,#178,#179,#181 (다과 찻잔·주전자)
- 00154 delete_all (어질러진 방 소물 FP)
- 00169 delete_all (녹색 소물 FP)
- 00184 delete_all (어수선한 방 FP)
- 00215 delete_all (벽 조명 FP)
- 00292 delete_all (사무실 단독 텀블러 — 음주맥락 없음)
- 00338 delete_all (이사 중 물잔)
- 00368 delete_all (식사 물잔)
- 00414 keep_all (라운지 술자리 — 양주병·잔)
- 00429 keep_all (라운지 술자리 — 양주병·잔)
- 00445 keep_all (라운지 술자리 — 양주병·잔·담배)
- 01088 keep_all (#214 바 양주병)
- 01134 delete_all (휴대폰 오검출 FP)
- 01165 delete_all (장식품 FP)
- 01195 delete_all (창고 선반 병 — 음주맥락 없음)
- 01395 keep_all (#218 라운지 병)

## sMpzdgHrINs
- 00001 keep_all (#219 담배)
- 00023 keep_all (#220~233 파티 술자리 — 병·잔)
- 00046 delete_all (#234 비닐봉지/티슈 FP)
- 00104 delete_all (트럭 캡 소물 — 운전중, 술 아님)

- 00149 keep_all (#237 뒤풀이 술자리 병)
- 00161 keep_all (#238 술자리 병)
- 00172 keep_all (#239~248 회식 술자리)
- 00241 delete_all (구내식당 물병)
- 00298 delete_all (허리 소물 FP)
- 00321 keep_all (#251 소주병 #252 술잔 — 옥상 술자리)
- 00344 delete_all (창고 플라스틱컵)
- 00390 keep_all (#254 담배)
- 00436 delete_all (밥공기)
- 00481 delete_all (군중 소물 FP)
- 00688 delete_all (커피컵)
- 00768 delete_all (사무실 찻잔)
- 00871 delete_all (정비소 소물 FP)
- 00905 delete_all (옥상 원거리 소물 FP)
- 00939 delete_all (바닥 잔해 FP)
- 00962 delete_all (군중 휴대폰 FP)
- 01042 delete_all (사무실 물병)
- 01065 delete_all (콜라 — 청량음료)
- 01100 delete_all (사무실 텀블러)
- 01134 delete_all (부둣가 생수병)

## vyXEi00PVrw (신세계)
- 00189 delete_all (경찰 계급장 FP)
- 00233 keep_all (#275 담배)
- 00242 keep_all (#276 담배)
- 00305 keep_all (#277~282 중식당 회식 술자리)
- 00314 delete_all (빈 크리스탈잔 — 음주맥락 없음)
- 00323 delete_all (트로피 — 사용자 지적 FP)
- 00413 keep_all (#287~292 와인 만찬)
- 00440 keep_all (#293 담배)
- 00466 keep_all (#294 담배)
- 00511 keep_all (#295 담배)
- 00574 keep_all (#296 소주병)
- 00628 delete_all (드럼통 FP)
- 00735 delete_all (소물 FP)
- 00807 delete_all (장례 화환 FP)

## wBr3f72w-fg (비열한 거리)
- 00036 keep_all (#301~303 방 소주 술자리)
- 00083 keep_all (#304~308 호텔 양주)
- 00154 delete_all (소물 FP)
- 00225 delete_all (진흙탕 소물 FP)
- 00249 delete_all (소물 FP)
- 00426 delete_all (식사 + 백자 FP)
- 00461 delete_all (사무실 소물 FP)
- 00485 keep_all (#317~321 룸 양주 술자리)
- 00556 delete_all (화장실 비누통 FP)
- 00568 mixed: delete #323,#324 (흰 찻잔/물컵); keep 트레이 술병
- 00592 delete_all (입가 FP — 담배 불명확)
- 00627 keep_all (#332~339 포장마차 소주 술자리)
- 00745 delete_all (통/박스 FP)
- 00792 delete_all (크리스탈 재떨이 FP)
- 00804 keep_all (#343,#344 와인 디너)
- 01029 delete_all (지게차 FP)
- 01100 keep_all (#347~353 룸 접대 술자리)

## x2PjLCMrfTk (황해)
- 00054 keep_all (#354~358 맥주병 술자리 잔해)
- 00180 delete_all (소품 FP)
- 00252 delete_all (밥공기·식기)
- 00467 delete_all (주방 양념/물통)
- 00485 delete_all (시장 좌판 소물 — 음주맥락 없음)
- 00628 delete_all (난간 크롬캡 FP)
- 00844 delete_all (트로피 FP)
- 00898 delete_all (바닥 식기)
- 00915 keep_all (#368 담배 추정)
- 00951 delete_all (도자기 항아리 FP)
- 01113 delete_all (안전봉/안내판 FP)
- 01220 delete_all (싸움 의류 FP)

## 검수 완료 (154/154 frames)

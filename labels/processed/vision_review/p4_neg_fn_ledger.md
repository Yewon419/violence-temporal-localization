# P4 negative false-negative 재검수 ledger

638개 미검수 빈 프레임(reviewed=false)을 9-up 컨택트시트로 스캔.
목적: GD가 놓친 진짜 타깃(명확한 술자리 술병 / 흡연)이 있는 프레임 = false negative →
negative 세트에서 제외(플래그). 나머지는 clean negative 확정.

플래그만 기록 (대다수는 clean → 무기록). 형식: `{vid}_{stem} — 사유`.

## FN 플래그 (negative에서 제외 권고)
- 69RJZ7TwDrQ_00511 — 좌하단 OB맥주 크레이트(맥주병 다수) + 술잔 트레이, 홀 술자리
- 69RJZ7TwDrQ_00828 — 룸 술자리, 왼쪽 남자 손에 양주잔(amber)

## 스캔 진행
- [x] 3auH8hGUezI (9시트) — clean, FN 0
- [x] 69RJZ7TwDrQ (9시트) — FN 2 (00511, 00828)
- [x] LkSY-EuTb1E (8시트) — clean, FN 0
- [x] Rqlf3zNPqgQ (9시트) — clean, FN 0 (01104 배경 장식병은 negative 유지)
- [x] sMpzdgHrINs (9시트) — clean, FN 0
- [x] vyXEi00PVrw (10시트) — clean, FN 0 (00207 바둑판·00431 인물·00753 칼부림 확인)
- [x] wBr3f72w-fg (10시트) — clean, FN 0 (단란주점 00095·00379·00733·01112 공연자만, 술 미노출)
- [x] x2PjLCMrfTk (10시트) — clean, FN 0 (01759 비탈 생수병=물, negative 유지)

## 최종 결과 (638 전수 재검수 완료)
- 전체 빈 프레임 734 중 FN(음주맥락 타깃 GD 누락) = **2건뿐** (둘 다 범죄와의전쟁)
- clean negative = **732** → `p4_negative_frames.json` (각 항목 fn_checked=true)
- FN 2건 = `p4_false_negative_frames.json` (negative 아님; 누락된 positive 후보, 팀이 재라벨 판단)
- 판정 원칙: 음주맥락 명확한 술병/술잔/흡연만 FN. 배경 장식병·생수·청량음료·노래방 공연자(술 미노출)·바둑판 등은 negative 유지(좋은 hard negative)

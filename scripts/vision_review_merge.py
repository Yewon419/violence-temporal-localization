"""Merge human vision verdicts into a review manifest and emit a markdown report.

Usage: vision_review_merge.py <group>   (default: p1_violence_event)
Verdicts are keyed by box idx. recommendation in {keep, delete, relabel}.
For relabel, the note starts with '→<label>: ...'.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(r"C:\Users\windg\Desktop\SCHOOL\3-1\데이터엔지니어링\project2")
REVIEW_DIR = ROOT / "data" / "processed" / "vision_review"


@dataclass(frozen=True)
class GroupMeta:
    title: str
    target_labels: str


GROUP_META: dict[str, GroupMeta] = {
    "p1_violence_event": GroupMeta(
        "우선순위 1 — explosion·car_accident·blood·abuse",
        "`explosion`·`car_accident`·`blood`·`abuse`",
    ),
    "p2_weapon_riot": GroupMeta(
        "우선순위 2 — weapon_knife·riot·weapon_gun",
        "`weapon_knife`·`riot`·`weapon_gun`",
    ),
}

# group -> {idx -> (recommendation, observed/note)}
VERDICTS: dict[str, dict[int, tuple[str, str]]] = {
    "p1_violence_event": {
        0: ("delete", "'리뷰쇼' 인트로 주황 원 로고"),
        1: ("delete", "여성 입술(립스틱)"),
        2: ("delete", "벽에 걸린 마늘 두름"),
        3: ("delete", "배경 선반의 붉은 음식(고추 등)"),
        4: ("delete", "렌즈 플레어/핑크 빛번짐"),
        5: ("delete", "흰 커튼/창"),
        6: ("delete", "어선"),
        7: ("delete", "멀리 떠 있는 배"),
        8: ("delete", "룸살롱 벽지 무늬"),
        9: ("delete", "거리 싸움 배경 주차 차량"),
        10: ("delete", "경찰서 꽃 엠블럼"),
        11: ("delete", "반찬 접시"),
        12: ("delete", "술집 빨간 네온사인"),
        13: ("delete", "술집 빨간 네온사인"),
        14: ("delete", "빨간 등"),
        15: ("delete", "정상 주차 세단(야간)"),
        16: ("delete", "주황 종이등"),
        17: ("delete", "벽 장식 접시"),
        18: ("delete", "배경 주차 차량"),
        19: ("delete", "모란 그림 액자"),
        20: ("delete", "꽃꽂이 붉은 열매"),
        21: ("delete", "산수화 액자"),
        22: ("delete", "경광등 단 차(검찰 체포신, 충돌 없음)"),
        23: ("delete", "몸싸움 중 멀쩡한 차(사고 아님)"),
        24: ("delete", "돌잔치 꽃 장식"),
        25: ("delete", "채널 인트로 영화관 의자 일러스트"),
        26: ("delete", "채널 인트로 의자 일러스트"),
        27: ("delete", "팝콘통 일러스트"),
        28: ("delete", "채널 인트로 의자 일러스트"),
        29: ("delete", "팝콘 일러스트"),
        30: ("delete", "마약왕 포스터 거친 한자 텍스처"),
        31: ("delete", "초록 선풍기"),
        32: ("delete", "저택 앞 정상 주차 차량"),
        33: ("delete", "장미밭"),
        34: ("delete", "밀짚 장식 램프"),
        35: ("delete", "밀짚 장식 램프"),
        36: ("delete", "정상 주차 세단"),
        37: ("delete", "검찰 무궁화 엠블럼"),
        38: ("delete", "신문 흑백사진 속 차량"),
        39: ("delete", "꽃다발"),
        40: ("delete", "부산 일몰 항공 뷰"),
        41: ("delete", "어두운 빈 영역"),
        42: ("delete", "정상 주차 클래식카"),
        43: ("delete", "붉은 조명 신(폭발 아님)"),
        44: ("delete", "백열 전구"),
        45: ("delete", "배경 꽃 그림"),
        46: ("delete", "창문 흐릿한 영역"),
        47: ("delete", "어선"),
        48: ("delete", "거리 주차 차량"),
        49: ("delete", "불티 날리는 배(차 아님)"),
        50: ("delete", "화분/꽃꽂이"),
        51: ("delete", "화분/꽃꽂이"),
        52: ("delete", "정상 주차 빨간 차"),
        53: ("delete", "야간 도로 주행 차량"),
        54: ("delete", "정상 주차 SUV"),
        55: ("delete", "헤드라이트 글레어 차량"),
        56: ("delete", "빛 보케"),
        57: ("delete", "담쟁이 흰꽃"),
        58: ("delete", "빛나는 램프갓"),
        59: ("delete", "다리 위 정상 주차 차"),
        60: ("delete", "흰 차 위 폭행 장면(폭력이나 car_accident 라벨 오류, 박스는 차)"),
        61: ("delete", "다리 위 정상 차(옆 도로 쓰러진 사람은 박스 밖)"),
        62: ("delete", "주차장 멀쩡한 차"),
        63: ("delete", "어두운 손/주먹"),
        64: ("delete", "보케 조명"),
        65: ("delete", "금발 머리카락"),
        66: ("delete", "원형 마스크 포스터 텍스트"),
        67: ("delete", "정비소 멀쩡한 차(절도 장면)"),
        68: ("delete", "야간 주행 머스탱"),
        69: ("delete", "검찰 수사관증 엠블럼"),
        70: ("delete", "꽃다발"),
        71: ("delete", "골목 차 헤드라이트"),
        72: ("delete", "영화 '베를린' 포스터"),
        73: ("delete", "옥상 LED 전광판"),
        74: ("delete", "정비소 비닐 덮인 차"),
        75: ("delete", "노란 봉고차+경광등"),
        76: ("delete", "경광등 빨간 불"),
        77: ("delete", "채널 텍스트 '구독 버튼을 눌러줌'"),
        78: ("delete", "채널 텍스트 '리아군의 다락방'"),
        79: ("delete", "'R MOVIE' 채널 로고"),
        80: ("delete", "야간 교차로 정상 교통"),
        81: ("delete", "장례식 화환"),
        82: ("delete", "장례식 검은 밴"),
        83: ("delete", "인물 클로즈업(배경 차)"),
        84: ("delete", "주차장 차 클로즈업(옆 액션)"),
        85: ("delete", "인화 사진들"),
        86: ("delete", "차 본넷 POV"),
        87: ("delete", "장례식 영정 화환"),
        88: ("delete", "장례식 영정 화환"),
        89: ("delete", "수중 부유물 신"),
        90: ("delete", "수중 부유물 신"),
        91: ("delete", "저작권 안내 텍스트"),
        92: ("delete", "입자/파티클 전환 효과"),
        93: ("delete", "배경 장식물"),
        94: ("delete", "폴더폰 화면 속 영상"),
        95: ("delete", "야간 단풍잎"),
        96: ("delete", "상점 보케 조명"),
        97: ("delete", "웨딩카 꽃 장식"),
        98: ("delete", "화장실 꽃병"),
        99: ("delete", "화분"),
        100: ("delete", "크리스탈 그릇"),
        101: ("delete", "야간 정상 주차 차"),
        102: ("delete", "회색 베개/쿠션"),
        103: ("delete", "크리스마스 장식"),
        104: ("delete", "강변 정차 트럭"),
        105: ("delete", "보케 조명"),
        106: ("delete", "헤드라이트 켠 주행 차"),
        107: ("delete", "식당 앞 정차 차"),
        108: ("delete", "달력에 동그라미 친 '16'"),
        109: ("delete", "골목 정차 차"),
        110: ("delete", "야간 주행 세단"),
        111: ("delete", "니트 비니 모자(칼은 별도 라벨)"),
        112: ("delete", "분식점 앞 봉고트럭"),
        113: ("delete", "대우 트럭 정면"),
        114: ("keep", "★ 진짜 car_accident — 트럭이 다수 차량과 충돌, 차량 박살·파편 비산 (황해 엔딩 추돌)"),
        115: ("delete", "빗속 주행 차(충돌 없음)"),
        116: ("delete", "빨간 양보 표지판"),
        117: ("keep", "앞범퍼 파손 차량(사고 후 차량 가능성, borderline — 대표님 최종 확인 권장)"),
        118: ("delete", "야간 어선"),
    },
    "p2_weapon_riot": {
        0: ("relabel", "→weapon_knife: 내부자들 칼(검) 뽑는 장면 (총 아님, borderline)"),
        1: ("relabel", "→weapon_knife: 위와 동일 frame 중복 박스 (검)"),
        2: ("relabel", "→weapon_knife: 빗속 장검 명확 (총 아님)"),
        3: ("delete", "롤렉스 시계(상자 안)"),
        4: ("delete", "롤렉스 시계(서랍 안)"),
        5: ("delete", "식탁 상추/음식"),
        6: ("delete", "식탁 그릇"),
        7: ("delete", "식탁 반찬"),
        8: ("delete", "식탁 소주병/젓가락"),
        9: ("delete", "연회 식탁"),
        10: ("delete", "채널 인트로 영화관 의자 일러스트"),
        11: ("keep", "마약왕 저택 벽 장식 장총(라이플) — 근접 명확"),
        12: ("keep", "마약왕 저택 벽 장식 장총 — 근접 명확"),
        13: ("keep", "마약왕 저택 벽 장식 장총 — 근접 명확"),
        14: ("keep", "마약왕 저택 벽 장식 장총 — 근접 명확"),
        15: ("keep", "마약왕 저택 벽 장식 장총 — 근접 명확"),
        16: ("keep", "마약왕 저택 벽 장총(와이드샷, 원거리·작음·저품질)"),
        17: ("keep", "마약왕 저택 벽 장총(와이드샷, 원거리·저품질)"),
        18: ("keep", "마약왕 저택 벽 장총(와이드샷, 원거리·저품질)"),
        19: ("keep", "마약왕 저택 벽 장총(와이드샷, 원거리·저품질)"),
        20: ("delete", "마약왕 폐허신 — 박스는 잔해 벽(칼 안 보임)"),
        21: ("keep", "마약왕 저택 벽 쌍열 산탄총 — 명확"),
        22: ("keep", "마약왕 저택 벽 장총(박스 약간 위로 헐거움)"),
        23: ("keep", "마약왕 저택 벽 산탄총 — 명확"),
        24: ("keep", "마약왕 저택 벽 장총(박스 약간 위로 헐거움)"),
        25: ("keep", "마약왕 저택 벽 쌍열 산탄총 — 명확"),
        26: ("keep", "마약왕 저택 벽 장총 — 명확"),
        27: ("keep", "마약왕 저택 벽 장총(박스 약간 위로 헐거움)"),
        28: ("keep", "마약왕 저택 벽 장총(박스 약간 위로 헐거움)"),
        29: ("delete", "어선"),
        30: ("delete", "'남산의 부장들' 포스터"),
        31: ("delete", "불티 날리는 배"),
        32: ("keep", "★ AK-47 소총 명확 (달콤한 인생)"),
        33: ("delete", "폴더폰(흑백)"),
        34: ("delete", "아시아나 비행기"),
        35: ("delete", "식탁 커틀러리(식사용 나이프, 무기 아님)"),
        36: ("delete", "문서 속 흑백 사진(총 확인 불가, 저해상)"),
        37: ("delete", "인화 사진들"),
        38: ("delete", "장례식 영정"),
        39: ("delete", "건설 철탑/크레인"),
        40: ("delete", "타이틀 글자 'f'"),
        41: ("delete", "식탁 그릇/숟가락"),
        42: ("delete", "서류"),
        43: ("delete", "식당 숟가락"),
        44: ("delete", "식당 숟가락"),
        45: ("delete", "공중전화 키패드"),
        46: ("delete", "눈밭 나뭇가지/막대기(총 아님)"),
        47: ("delete", "빗속 주행 차"),
        48: ("delete", "자막 텍스트 오버레이"),
        49: ("delete", "야간 어선"),
    },
}


def main(group: str) -> None:
    meta = GROUP_META[group]
    verdicts = VERDICTS[group]
    manifest = REVIEW_DIR / f"{group}_manifest.json"
    out_json = REVIEW_DIR / f"{group}_verdicts.json"
    out_md = ROOT / "docs" / f"vision_review_{group}_report.md"

    entries = json.loads(manifest.read_text(encoding="utf-8"))
    merged = []
    for e in entries:
        rec, note = verdicts[e["idx"]]
        merged.append({**e, "recommendation": rec, "observed": note})
    out_json.write_text(
        json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    keep = [m for m in merged if m["recommendation"] == "keep"]
    relabel = [m for m in merged if m["recommendation"] == "relabel"]
    delete = [m for m in merged if m["recommendation"] == "delete"]

    by_label: dict[str, dict[str, int]] = {}
    for m in merged:
        d = by_label.setdefault(
            m["cvat_label"], {"keep": 0, "relabel": 0, "delete": 0}
        )
        d[m["recommendation"]] += 1

    def fmt_sc(m: dict[str, object]) -> str:
        s = m["score"]
        return f"{s:.2f}" if isinstance(s, (int, float)) else "?"

    lines: list[str] = []
    lines.append(f"# Drama frames v2 — {meta.title} vision 전수 검수 보고서")
    lines.append("")
    lines.append(f"**대상**: CVAT v2 import 중 {meta.target_labels} 라벨 {len(merged)} bbox 전수")
    lines.append("**방법**: 박스별 단독 하이라이트 이미지 생성 후 vision Read 전수 판정")
    lines.append("**검수 일자**: 2026-05-30")
    lines.append("")
    lines.append("## 요약")
    lines.append("")
    lines.append(f"- 전체: **{len(merged)}** bbox")
    lines.append(f"- KEEP(유지): **{len(keep)}**")
    if relabel:
        lines.append(f"- RELABEL(라벨 교체): **{len(relabel)}**")
    lines.append(f"- DELETE(삭제): **{len(delete)}**")
    fp_rate = len(delete) / len(merged) * 100
    lines.append(f"- **삭제 비율(FP): {fp_rate:.1f}%** ({len(delete)}/{len(merged)})")
    lines.append("")
    lines.append("| 라벨 | 전체 | keep | relabel | delete |")
    lines.append("|---|---:|---:|---:|---:|")
    for lab, d in sorted(by_label.items(), key=lambda x: -sum(x[1].values())):
        tot = sum(d.values())
        lines.append(
            f"| {lab} | {tot} | {d['keep']} | {d['relabel']} | {d['delete']} |"
        )
    lines.append("")

    if keep:
        lines.append("## KEEP 목록 (유지/확인 대상)")
        lines.append("")
        lines.append("| idx | 영상 | frame | 라벨 | score | 이미지 | 관찰 |")
        lines.append("|---:|---|---|---|---:|---|---|")
        for m in keep:
            img = Path(m["image_out"]).name
            lines.append(
                f"| {m['idx']} | {m['vid']} | {m['frame']} | {m['cvat_label']} | "
                f"{fmt_sc(m)} | `{img}` | {m['observed']} |"
            )
        lines.append("")

    if relabel:
        lines.append("## RELABEL 목록 (라벨 교체 권고)")
        lines.append("")
        lines.append("| idx | 영상 | frame | 현재 라벨 | score | 이미지 | 권고 |")
        lines.append("|---:|---|---|---|---:|---|---|")
        for m in relabel:
            img = Path(m["image_out"]).name
            lines.append(
                f"| {m['idx']} | {m['vid']} | {m['frame']} | {m['cvat_label']} | "
                f"{fmt_sc(m)} | `{img}` | {m['observed']} |"
            )
        lines.append("")

    lines.append("## DELETE 목록 (삭제 권고 — 전체)")
    lines.append("")
    lines.append("| idx | 영상 | frame | 라벨 | score | 관찰(실제 내용) |")
    lines.append("|---:|---|---|---|---:|---|")
    for m in delete:
        lines.append(
            f"| {m['idx']} | {m['vid']} | {m['frame']} | {m['cvat_label']} | "
            f"{fmt_sc(m)} | {m['observed']} |"
        )
    lines.append("")
    lines.append("## 산출물")
    lines.append("")
    lines.append(f"- 박스별 검수 이미지: `data/processed/vision_review/{group}/*.jpg`")
    lines.append(f"- 판정 머신리더블: `data/processed/vision_review/{group}_verdicts.json`")
    lines.append("- 생성 스크립트: `scripts/vision_review_prep.py`, `scripts/vision_review_merge.py`")
    lines.append("")

    out_md.write_text("\n".join(lines), encoding="utf-8")
    n_rel = f" relabel={len(relabel)}" if relabel else ""
    print(f"[{group}] keep={len(keep)}{n_rel} delete={len(delete)} fp={fp_rate:.1f}%")
    print(f"wrote {out_json.relative_to(ROOT)}")
    print(f"wrote {out_md.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "p1_violence_event")

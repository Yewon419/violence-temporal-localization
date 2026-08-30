"""GD bbox 1차 자동 분류 — 규칙 기반.

대표님 결정 (2026-05-30): 검수자 부담 줄이기 위해 LLM 1차 분류.
본인(Claude)이 sample은 vision 검증, 나머지는 규칙 기반.

규칙:
- label = ''            → negative (post-process 실패)
- label = concat        → unknown
- bbox 면적 > 60% frame → negative (frame 통째 박스, 거의 100% FP)
- score < 0.30          → uncertain
- cigarette             → positive_smoking
- smoking               → positive_smoking_act
- bottle/cup/wine_glass/alcohol → positive_drinking
- drinking              → positive_drinking_act

출력:
    data/processed/gd_triage/{video_id}.json — frame별 verdict list
    data/processed/gd_triage/summary.json    — 전체 분포

실행:
    .venv\\Scripts\\python.exe scripts\\gd_auto_triage.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import TypedDict

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import PROCESSED_DIR

GD_OUT: Path = PROCESSED_DIR / "gd_demo_fps_v2"
FRAMES_DIR: Path = PROCESSED_DIR / "yt_drama_frames"
TRIAGE_OUT: Path = PROCESSED_DIR / "gd_triage_v2"

DRINKING_OBJECTS: set[str] = {"bottle", "cup", "wine_glass", "alcohol"}
WEAPON_OBJECTS: set[str] = {"knife", "gun", "hammer", "baseball bat", "bat"}
VIOLENCE_ACTS: set[str] = {"fighting", "shooting", "riot", "abuse"}
VIOLENCE_EVENTS: set[str] = {"explosion", "car accident", "accident"}
SMOKING_OBJECTS: set[str] = {"cigarette"}
SMOKING_ACTS: set[str] = {"smoking"}
DRINKING_ACTS: set[str] = {"drinking"}
BLOOD: set[str] = {"blood"}

KNOWN_TOKENS: set[str] = (
    DRINKING_OBJECTS | WEAPON_OBJECTS | VIOLENCE_ACTS | VIOLENCE_EVENTS
    | SMOKING_OBJECTS | SMOKING_ACTS | DRINKING_ACTS | BLOOD
)

LARGE_BOX_RATIO: float = 0.60
LOW_SCORE: float = 0.30


class BoxVerdict(TypedDict):
    bbox: list[float]
    score: float
    raw_label: str
    verdict: str
    category: str
    reason: str


class FrameVerdict(TypedDict):
    frame: str
    image_size: list[int]
    boxes: list[BoxVerdict]


def classify_box(
    bbox: list[float], score: float, raw_label: str, img_w: int, img_h: int
) -> tuple[str, str, str]:
    """Return (verdict, category, reason)."""
    x1, y1, x2, y2 = bbox
    box_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    frame_area = float(img_w * img_h)
    area_ratio = box_area / frame_area if frame_area > 0 else 0.0

    if area_ratio > LARGE_BOX_RATIO:
        return "negative", "frame_dominant", f"box covers {area_ratio:.0%} of frame"

    if raw_label == "":
        return "negative", "empty_label", "post-process matching failed"

    tokens = raw_label.split()
    is_concat = len(tokens) > 1 and any(t in KNOWN_TOKENS for t in tokens) and (
        not (raw_label in WEAPON_OBJECTS or raw_label in VIOLENCE_EVENTS)
    )
    if is_concat:
        return "unknown", "concat_label", f"label is concat '{raw_label}'"

    if score < LOW_SCORE:
        return "uncertain", "low_score", f"score {score:.2f} < {LOW_SCORE}"

    if raw_label in SMOKING_OBJECTS:
        return "positive", "smoking", f"cigarette object, score {score:.2f}"
    if raw_label in SMOKING_ACTS:
        return "positive", "smoking_act", f"smoking activity, score {score:.2f}"
    if raw_label in DRINKING_OBJECTS:
        return "positive", "drinking", f"{raw_label} object, score {score:.2f}"
    if raw_label in DRINKING_ACTS:
        return "positive", "drinking_act", f"drinking activity, score {score:.2f}"
    if raw_label in WEAPON_OBJECTS:
        weapon_class = (
            "weapon_blunt"
            if raw_label in {"hammer", "baseball bat", "bat"}
            else f"weapon_{raw_label}"
        )
        return "positive", weapon_class, f"{raw_label} weapon, score {score:.2f}"
    if raw_label in BLOOD:
        return "positive", "blood", f"blood, score {score:.2f}"
    if raw_label in VIOLENCE_ACTS:
        return "positive", raw_label, f"{raw_label} act, score {score:.2f}"
    if raw_label in VIOLENCE_EVENTS:
        event_class = "car_accident" if "accident" in raw_label else raw_label
        return "positive", event_class, f"{raw_label} event, score {score:.2f}"

    return "uncertain", "unknown_label", f"unrecognized label '{raw_label}'"


def triage_video(video_id: str) -> tuple[FrameVerdict, ...]:
    gd_dir = GD_OUT / video_id
    if not gd_dir.exists():
        return ()
    json_files = sorted(p for p in gd_dir.glob("*.json") if "_vis" not in p.stem)

    results: list[FrameVerdict] = []
    for jp in json_files:
        rec = json.loads(jp.read_text(encoding="utf-8"))
        frame_name = rec["frame"]
        img_path = FRAMES_DIR / frame_name
        if not img_path.exists():
            continue
        with Image.open(img_path) as im:
            w, h = im.size

        boxes_v: list[BoxVerdict] = []
        for bbox, score, raw_label in zip(
            rec["boxes"], rec["scores"], rec["labels"], strict=False
        ):
            verdict, category, reason = classify_box(bbox, score, raw_label, w, h)
            boxes_v.append(
                {
                    "bbox": bbox,
                    "score": score,
                    "raw_label": raw_label,
                    "verdict": verdict,
                    "category": category,
                    "reason": reason,
                }
            )
        results.append({"frame": frame_name, "image_size": [w, h], "boxes": boxes_v})
    return tuple(results)


def main() -> None:
    TRIAGE_OUT.mkdir(parents=True, exist_ok=True)
    video_ids = sorted(d.name for d in GD_OUT.iterdir() if d.is_dir())

    overall_verdict: Counter[str] = Counter()
    overall_category: Counter[str] = Counter()
    overall_reason: Counter[str] = Counter()
    per_video_summary: dict[str, dict[str, int]] = {}

    for vid in video_ids:
        frames = triage_video(vid)
        if not frames:
            continue

        out_path = TRIAGE_OUT / f"{vid}.json"
        out_path.write_text(
            json.dumps(frames, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        v_count: Counter[str] = Counter()
        c_count: Counter[str] = Counter()
        n_boxes = 0
        for fr in frames:
            for box in fr["boxes"]:
                v_count[box["verdict"]] += 1
                c_count[box["category"]] += 1
                overall_reason[box["reason"].split(",")[0]] += 1
                n_boxes += 1
        overall_verdict.update(v_count)
        overall_category.update(c_count)
        per_video_summary[vid] = {
            "frames": len(frames),
            "boxes": n_boxes,
            **{f"v_{k}": v for k, v in v_count.items()},
            **{f"c_{k}": v for k, v in c_count.items()},
        }
        print(f"[{vid}] {len(frames)} frames, {n_boxes} boxes, verdict={dict(v_count)}")

    summary = {
        "overall_verdict": dict(overall_verdict),
        "overall_category": dict(overall_category),
        "top_reasons": dict(overall_reason.most_common(10)),
        "per_video": per_video_summary,
    }
    (TRIAGE_OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("---")
    print(f"OVERALL verdict: {dict(overall_verdict)}")
    print(f"OVERALL category: {dict(overall_category)}")


if __name__ == "__main__":
    main()

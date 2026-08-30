"""Finalize the negative-frame manifest after the false-negative re-review.

All 638 unreviewed empty frames were scanned (9-up contact sheets + full-res spot
checks, see p4_neg_fn_ledger.md). Only two frames actually held a 음주-context target
that GD missed, so they are NOT clean negatives:
  - 69RJZ7TwDrQ_frame_00511 (OB맥주 크레이트 + 술잔 트레이, 홀 술자리)
  - 69RJZ7TwDrQ_frame_00828 (룸 술자리, 손에 양주잔)

Splits p4_negative_frames.json into:
  - p4_negative_frames.json  -> clean negatives only (FN removed), each tagged fn_checked
  - p4_false_negative_frames.json -> the FN frames (missed-positive candidates, NOT negatives)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import PROCESSED_DIR

REVIEW_DIR = PROCESSED_DIR / "vision_review"
NEG = REVIEW_DIR / "p4_negative_frames.json"
FN_OUT = REVIEW_DIR / "p4_false_negative_frames.json"

FN_FRAMES: dict[str, str] = {
    "69RJZ7TwDrQ_frame_00511.jpg": "OB맥주 크레이트(맥주병 다수) + 술잔 트레이, 홀 술자리",
    "69RJZ7TwDrQ_frame_00828.jpg": "룸 술자리, 손에 양주잔(amber)",
}


def main() -> None:
    entries = json.loads(NEG.read_text(encoding="utf-8"))
    clean: list[dict[str, object]] = []
    fn: list[dict[str, object]] = []
    for e in entries:
        frame = cast(str, e["frame"])
        if frame in FN_FRAMES:
            fn.append({"vid": e["vid"], "frame": frame, "reason": FN_FRAMES[frame]})
        else:
            e["fn_checked"] = True
            clean.append(e)

    if len(fn) != len(FN_FRAMES):
        found = {cast(str, e["frame"]) for e in fn}
        raise SystemExit(f"FN frames missing from manifest: {set(FN_FRAMES) - found}")

    NEG.write_text(json.dumps(clean, ensure_ascii=False, indent=1), encoding="utf-8")
    FN_OUT.write_text(json.dumps(fn, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"clean negatives: {len(clean)} -> {NEG.name}")
    print(f"false negatives (missed positives): {len(fn)} -> {FN_OUT.name}")


if __name__ == "__main__":
    main()

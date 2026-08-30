"""Read-only: list CVAT frames (tasks 11-18) that now hold zero annotations.

After the two review passes deleted FP / non-target boxes, any frame left with no
box is a background/negative image. These must be preserved as negatives for the
FP-mitigation track (a frame whose only boxes were a misdetected trophy/teacup is a
valuable hard negative), not silently dropped at export time.

Emits data/processed/vision_review/p4_negative_frames.json:
  { vid, frame, n_boxes_now(0), reviewed } per empty frame, where `reviewed` marks
  frames whose emptiness was human-confirmed in the strict P4 pass (delete_all).
Prints per-task empty/total counts. No mutation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

from cvat_sdk import make_client
from cvat_sdk.core.proxies.tasks import Task

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import PROCESSED_DIR

CVAT_HOST = "http://localhost:8080"
PROJECT_NAME = "DEproject2"
KEYS_DIR = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2")
REVIEW_DIR = PROCESSED_DIR / "vision_review"
DELETE_VERDICTS = REVIEW_DIR / "p4_strict_delete_verdicts.json"
OUT = REVIEW_DIR / "p4_negative_frames.json"


def creds() -> tuple[str, str]:
    return (
        (KEYS_DIR / "CVAT_username.txt").read_text(encoding="utf-8").strip(),
        (KEYS_DIR / "CVAT_password.txt").read_text(encoding="utf-8").strip(),
    )


def strict_emptied_frames() -> set[str]:
    """Frames the strict P4 pass deleted at least one box from (human-reviewed)."""
    verdicts = json.loads(DELETE_VERDICTS.read_text(encoding="utf-8"))
    return {cast(str, v["frame"]) for v in verdicts}


def task_frame_names(t: Task) -> dict[int, str]:
    return {i: cast(str, fr.to_dict()["name"]) for i, fr in enumerate(t.get_frames_info())}


def main() -> None:
    reviewed = strict_emptied_frames()
    out: list[dict[str, object]] = []
    with make_client(host=CVAT_HOST, credentials=creds()) as client:
        proj = next(p for p in client.projects.list() if p.name == PROJECT_NAME)
        tasks = sorted(
            (t for t in client.tasks.list() if t.project_id == proj.id),
            key=lambda t: t.id,
        )
        grand_empty = 0
        grand_total = 0
        for t in tasks:
            idx2frame = task_frame_names(t)
            shapes = cast(list[dict[str, object]], t.get_annotations().to_dict()["shapes"])
            counts: dict[str, int] = {name: 0 for name in idx2frame.values()}
            for sd in shapes:
                frame = idx2frame.get(cast(int, sd["frame"]), "?")
                counts[frame] = counts.get(frame, 0) + 1
            empty = sorted(fr for fr, n in counts.items() if n == 0)
            vid = t.name.split(" ")[0]
            for fr in empty:
                out.append(
                    {
                        "vid": vid,
                        "frame": fr,
                        "n_boxes_now": 0,
                        "reviewed": fr in reviewed,
                    }
                )
            grand_empty += len(empty)
            grand_total += len(idx2frame)
            print(
                f"task {t.id} {t.name}: frames={len(idx2frame)} "
                f"empty={len(empty)} annotated={len(idx2frame) - len(empty)}"
            )

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n_reviewed = sum(1 for e in out if e["reviewed"])
    print(
        f"TOTAL frames={grand_total} empty(negative)={grand_empty} "
        f"(human-reviewed-emptied={n_reviewed}) -> {OUT.name}"
    )


if __name__ == "__main__":
    main()

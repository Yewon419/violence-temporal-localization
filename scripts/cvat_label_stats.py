"""Read-only stats of CVAT v2 (DEproject2, tasks 11-18) for the YOLO export review.

Per task and overall: frame counts (total / annotated / empty) and per-label shape
counts. No mutation. Use before exporting Ultralytics YOLO Detection 1.0 to HF.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import cast

from cvat_sdk import make_client
from cvat_sdk.core.proxies.tasks import Task

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CVAT_HOST = "http://localhost:8080"
PROJECT_NAME = "DEproject2"
KEYS_DIR = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2")


def creds() -> tuple[str, str]:
    return (
        (KEYS_DIR / "CVAT_username.txt").read_text(encoding="utf-8").strip(),
        (KEYS_DIR / "CVAT_password.txt").read_text(encoding="utf-8").strip(),
    )


def task_frame_count(t: Task) -> int:
    return sum(1 for _ in t.get_frames_info())


def main() -> None:
    with make_client(host=CVAT_HOST, credentials=creds()) as client:
        proj = next(p for p in client.projects.list() if p.name == PROJECT_NAME)
        id2name = {lbl.id: lbl.name for lbl in proj.get_labels()}
        tasks = sorted(
            (t for t in client.tasks.list() if t.project_id == proj.id),
            key=lambda t: t.id,
        )

        grand_label: Counter[str] = Counter()
        tot_frames = tot_annot = tot_shapes = 0
        for t in tasks:
            n_frames = task_frame_count(t)
            shapes = cast(list[dict[str, object]], t.get_annotations().to_dict()["shapes"])
            label_ct: Counter[str] = Counter()
            frames_with_box: set[int] = set()
            for sd in shapes:
                label_ct[id2name.get(cast(int, sd["label_id"]), str(sd["label_id"]))] += 1
                frames_with_box.add(cast(int, sd["frame"]))
            annot = len(frames_with_box)
            tot_frames += n_frames
            tot_annot += annot
            tot_shapes += len(shapes)
            grand_label.update(label_ct)
            brk = " ".join(f"{k}={v}" for k, v in sorted(label_ct.items()))
            print(
                f"task {t.id} {t.name}: frames={n_frames} annotated={annot} "
                f"empty={n_frames - annot} shapes={len(shapes)} | {brk}"
            )

        print("-" * 60)
        print(
            f"TOTAL frames={tot_frames} annotated={tot_annot} "
            f"empty(negative)={tot_frames - tot_annot} shapes={tot_shapes}"
        )
        print("per-label shapes:")
        for k, v in sorted(grand_label.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {k:14s} {v}")


if __name__ == "__main__":
    main()

"""Recon + backup CVAT v2 tasks before applying vision-review verdicts.

- Lists DEproject2 tasks (id, name, size), project label name->id map.
- For each task: dumps annotations (shapes) + frame index->name to a backup JSON.
- Introspects the cvat_sdk TaskProxy + a sample shape so we use real API methods.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cvat_sdk import make_client

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import PROCESSED_DIR

CVAT_HOST = "http://localhost:8080"
PROJECT_NAME = "DEproject2"
KEYS_DIR = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2")
BACKUP_DIR = PROCESSED_DIR / "cvat_backup_2026-05-30"


def creds() -> tuple[str, str]:
    return (
        (KEYS_DIR / "CVAT_username.txt").read_text(encoding="utf-8").strip(),
        (KEYS_DIR / "CVAT_password.txt").read_text(encoding="utf-8").strip(),
    )


def main() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    with make_client(host=CVAT_HOST, credentials=creds()) as client:
        proj = next(p for p in client.projects.list() if p.name == PROJECT_NAME)
        label_map = {lbl.name: lbl.id for lbl in proj.get_labels()}
        print(f"project id={proj.id}")
        print(f"labels name->id: {json.dumps(label_map, ensure_ascii=False)}")

        tasks = sorted(
            (t for t in client.tasks.list() if t.project_id == proj.id),
            key=lambda t: t.id,
        )
        print(f"tasks ({len(tasks)}):")
        for t in tasks:
            print(f"  id={t.id} name={t.name!r} size={t.size}")

        # introspect TaskProxy methods once
        t0 = tasks[0]
        methods = [m for m in dir(t0) if not m.startswith("_")]
        print(f"TaskProxy methods: {methods}")

        ann = t0.get_annotations()
        print(f"annotations type: {type(ann).__name__}")
        print(f"annotations attrs: {[a for a in dir(ann) if not a.startswith('_')]}")
        print(f"  n_shapes={len(ann.shapes)} n_tags={len(ann.tags)} n_tracks={len(ann.tracks)}")
        if ann.shapes:
            s = ann.shapes[0]
            print(f"shape attrs: {[a for a in dir(s) if not a.startswith('_')]}")
            print(
                f"sample shape: id={s.id} label_id={s.label_id} frame={s.frame} "
                f"type={s.type} points={s.points}"
            )

        # frame index -> name for each task, + backup annotations
        id2name = {v: k for k, v in label_map.items()}
        for t in tasks:
            frames_info = t.get_frames_info()
            idx2frame = {i: fr.name for i, fr in enumerate(frames_info)}
            a = t.get_annotations()
            shapes = [
                {
                    "id": s.id,
                    "label_id": s.label_id,
                    "label": id2name.get(s.label_id, str(s.label_id)),
                    "frame": s.frame,
                    "frame_name": idx2frame.get(s.frame, "?"),
                    "type": str(s.type),
                    "points": list(s.points),
                }
                for s in a.shapes
            ]
            backup = {
                "task_id": t.id,
                "task_name": t.name,
                "size": t.size,
                "idx2frame": idx2frame,
                "shapes": shapes,
            }
            out = BACKUP_DIR / f"task_{t.id}.json"
            out.write_text(
                json.dumps(backup, ensure_ascii=False, indent=1), encoding="utf-8"
            )
            print(f"  backup task {t.id}: {len(shapes)} shapes -> {out.name}")

    print(f"backup dir: {BACKUP_DIR}")


if __name__ == "__main__":
    main()

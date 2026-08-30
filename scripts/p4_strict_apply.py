"""Apply the strict P4 re-review ('술자리만 유지') to CVAT v2 tasks 11-18.

The first apply (cvat_apply_review.py) bulk-KEPT every bottle/cup/cigarette box.
A second human vision pass over all 154 per-frame composites
(see data/processed/vision_review/p4_strict_ledger.md) judged each frame under
the strict criterion:
  KEEP only 소주/맥주/양주병, 술잔(음주맥락), 담배.
  DELETE 찻잔·물컵·보온병·트로피·접시·일상장면 컵·음주맥락 없는 컵·하드 FP.

Frame verdicts are encoded below as keep_all / mixed / (default) delete_all and
expanded against p4_objects_manifest.json into a per-box delete list, then matched
to CVAT shapes by (frame, label, x, y) with sub-pixel tolerance — identical to the
first apply. Only bottle/cup/cigarette shapes are ever touched; weapon_gun/
weapon_knife/car_accident/drinking_act remain untouched.

Usage:
    python scripts/p4_strict_apply.py dryrun [task_id]
    python scripts/p4_strict_apply.py apply
Backup must exist (cvat_backup_2026-05-30 from cvat_recon.py).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
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
MANIFEST = REVIEW_DIR / "p4_objects_manifest.json"
BACKUP_DIR = PROCESSED_DIR / "cvat_backup_2026-05-30"
OUT_VERDICTS = REVIEW_DIR / "p4_strict_delete_verdicts.json"

OBJECT_LABELS = {"bottle", "cup", "cigarette"}
MATCH_TOL = 0.5  # manifest coords are round(coco, 1); distinct boxes differ by many px

# Frames where every object box is kept (clear 술자리 or 담배). (vid, stem).
KEEP_ALL: frozenset[tuple[str, str]] = frozenset(
    {
        ("3auH8hGUezI", "00082"), ("3auH8hGUezI", "00791"), ("3auH8hGUezI", "00802"),
        ("3auH8hGUezI", "00822"), ("3auH8hGUezI", "00832"), ("3auH8hGUezI", "00883"),
        ("3auH8hGUezI", "00893"),
        ("69RJZ7TwDrQ", "00229"), ("69RJZ7TwDrQ", "00282"), ("69RJZ7TwDrQ", "00353"),
        ("69RJZ7TwDrQ", "00652"), ("69RJZ7TwDrQ", "00811"), ("69RJZ7TwDrQ", "01110"),
        ("69RJZ7TwDrQ", "01128"), ("69RJZ7TwDrQ", "01145"), ("69RJZ7TwDrQ", "01233"),
        ("69RJZ7TwDrQ", "01445"),
        ("LkSY-EuTb1E", "00101"), ("LkSY-EuTb1E", "00152"), ("LkSY-EuTb1E", "00166"),
        ("LkSY-EuTb1E", "00175"),
        ("Rqlf3zNPqgQ", "00031"), ("Rqlf3zNPqgQ", "00108"), ("Rqlf3zNPqgQ", "00414"),
        ("Rqlf3zNPqgQ", "00429"), ("Rqlf3zNPqgQ", "00445"), ("Rqlf3zNPqgQ", "01088"),
        ("Rqlf3zNPqgQ", "01395"),
        ("sMpzdgHrINs", "00001"), ("sMpzdgHrINs", "00023"), ("sMpzdgHrINs", "00149"),
        ("sMpzdgHrINs", "00161"), ("sMpzdgHrINs", "00172"), ("sMpzdgHrINs", "00321"),
        ("sMpzdgHrINs", "00390"),
        ("vyXEi00PVrw", "00233"), ("vyXEi00PVrw", "00242"), ("vyXEi00PVrw", "00305"),
        ("vyXEi00PVrw", "00413"), ("vyXEi00PVrw", "00440"), ("vyXEi00PVrw", "00466"),
        ("vyXEi00PVrw", "00511"), ("vyXEi00PVrw", "00574"),
        ("wBr3f72w-fg", "00036"), ("wBr3f72w-fg", "00083"), ("wBr3f72w-fg", "00485"),
        ("wBr3f72w-fg", "00627"), ("wBr3f72w-fg", "00804"), ("wBr3f72w-fg", "01100"),
        ("x2PjLCMrfTk", "00054"), ("x2PjLCMrfTk", "00915"),
    }
)

# Mixed frames keyed by (vid, stem) -> idxs to KEEP (delete the rest of that frame).
MIXED_KEEP: dict[tuple[str, str], frozenset[int]] = {
    ("69RJZ7TwDrQ", "00317"): frozenset({52}),
    ("Rqlf3zNPqgQ", "00123"): frozenset({180}),
}

# Mixed frames keyed by (vid, stem) -> idxs to DELETE (keep the rest of that frame).
MIXED_DELETE: dict[tuple[str, str], frozenset[int]] = {
    ("3auH8hGUezI", "00812"): frozenset({27}),
    ("69RJZ7TwDrQ", "01321"): frozenset({101, 102}),
    ("wBr3f72w-fg", "00568"): frozenset({323, 324}),
}


@dataclass
class Plan:
    task_id: int
    name: str
    total: int
    counts: dict[str, int]
    delete_ids: list[int] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


def creds() -> tuple[str, str]:
    return (
        (KEYS_DIR / "CVAT_username.txt").read_text(encoding="utf-8").strip(),
        (KEYS_DIR / "CVAT_password.txt").read_text(encoding="utf-8").strip(),
    )


def stem_of(frame: str) -> str:
    return Path(frame).stem.split("_")[-1]


def build_delete_verdicts() -> list[dict[str, object]]:
    """Expand frame verdicts against the manifest into per-box delete entries."""
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_frame: dict[tuple[str, str], list[dict[str, object]]] = {}
    for e in entries:
        key = (cast(str, e["vid"]), stem_of(cast(str, e["frame"])))
        by_frame.setdefault(key, []).append(e)

    # Coverage + validity checks (fail loud, never silently mis-delete).
    for key in (*MIXED_KEEP, *MIXED_DELETE, *KEEP_ALL):
        if key not in by_frame:
            raise SystemExit(f"verdict references unknown frame {key}")
    for key, keep in MIXED_KEEP.items():
        frame_idxs = {cast(int, e["idx"]) for e in by_frame[key]}
        if not keep <= frame_idxs:
            raise SystemExit(f"MIXED_KEEP {key}: {keep - frame_idxs} not in frame")
    for key, dele in MIXED_DELETE.items():
        frame_idxs = {cast(int, e["idx"]) for e in by_frame[key]}
        if not dele <= frame_idxs:
            raise SystemExit(f"MIXED_DELETE {key}: {dele - frame_idxs} not in frame")

    verdicts: list[dict[str, object]] = []
    for key, boxes in by_frame.items():
        if key in KEEP_ALL:
            continue
        keep_set = MIXED_KEEP.get(key)
        del_set = MIXED_DELETE.get(key)
        for e in boxes:
            idx = cast(int, e["idx"])
            if keep_set is not None:
                drop = idx not in keep_set
            elif del_set is not None:
                drop = idx in del_set
            else:  # delete_all (default)
                drop = True
            if drop:
                bbox = cast("list[float]", e["bbox_xywh"])
                verdicts.append(
                    {
                        "idx": idx,
                        "frame": e["frame"],
                        "cvat_label": e["cvat_label"],
                        "bbox_xywh": bbox,
                        "recommendation": "delete",
                    }
                )
    return verdicts


# (frame, label) -> list of (x, y, matched-flag index into a shared list)
DeleteMap = dict[tuple[str, str], list[int]]


def index_verdicts(
    verdicts: list[dict[str, object]],
) -> tuple[DeleteMap, list[tuple[float, float]], list[bool]]:
    dmap: DeleteMap = {}
    coords: list[tuple[float, float]] = []
    matched: list[bool] = []
    for v in verdicts:
        bbox = cast("list[float]", v["bbox_xywh"])
        coords.append((bbox[0], bbox[1]))
        matched.append(False)
        k = (cast(str, v["frame"]), cast(str, v["cvat_label"]))
        dmap.setdefault(k, []).append(len(coords) - 1)
    return dmap, coords, matched


def task_frame_names(t: Task) -> dict[int, str]:
    return {i: cast(str, fr.to_dict()["name"]) for i, fr in enumerate(t.get_frames_info())}


def plan_task(
    t: Task,
    id2name: dict[int, str],
    dmap: DeleteMap,
    coords: list[tuple[float, float]],
    matched: list[bool],
) -> Plan:
    idx2frame = task_frame_names(t)
    shapes = cast(list[dict[str, object]], t.get_annotations().to_dict()["shapes"])
    plan = Plan(
        task_id=t.id, name=t.name, total=len(shapes),
        counts={"keep": 0, "delete": 0, "skip": 0},
    )
    for sd in shapes:
        label = id2name.get(cast(int, sd["label_id"]), str(sd["label_id"]))
        if label not in OBJECT_LABELS:
            plan.counts["skip"] += 1  # weapon_gun/knife/car_accident/drinking_act
            continue
        frame = idx2frame.get(cast(int, sd["frame"]), "?")
        pts = cast("list[float]", sd["points"])
        x, y = pts[0], pts[1]
        best: tuple[float, int] | None = None
        for vi in dmap.get((frame, label), []):
            vx, vy = coords[vi]
            dist = max(abs(vx - x), abs(vy - y))
            if dist <= MATCH_TOL and (best is None or dist < best[0]):
                best = (dist, vi)
        if best is None:
            plan.counts["keep"] += 1
        else:
            matched[best[1]] = True
            plan.counts["delete"] += 1
            plan.delete_ids.append(cast(int, sd["id"]))
    return plan


def main() -> None:
    if not BACKUP_DIR.exists():
        raise SystemExit("backup missing — run cvat_recon.py first")
    mode = sys.argv[1] if len(sys.argv) > 1 else "dryrun"
    only = int(sys.argv[2]) if len(sys.argv) > 2 else None

    verdicts = build_delete_verdicts()
    OUT_VERDICTS.write_text(
        json.dumps(verdicts, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    dmap, coords, matched = index_verdicts(verdicts)
    print(f"delete verdicts: {len(verdicts)} boxes -> {OUT_VERDICTS.name}")

    with make_client(host=CVAT_HOST, credentials=creds()) as client:
        proj = next(p for p in client.projects.list() if p.name == PROJECT_NAME)
        label_map = {lbl.name: lbl.id for lbl in proj.get_labels()}
        id2name = {v: k for k, v in label_map.items()}
        tasks = sorted(
            (t for t in client.tasks.list() if t.project_id == proj.id),
            key=lambda t: t.id,
        )
        if only is not None:
            tasks = [t for t in tasks if t.id == only]

        grand = {"keep": 0, "delete": 0, "skip": 0}
        plans: list[tuple[Task, Plan]] = []
        for t in tasks:
            plan = plan_task(t, id2name, dmap, coords, matched)
            plans.append((t, plan))
            for k in grand:
                grand[k] += plan.counts[k]
            c = plan.counts
            print(
                f"task {plan.task_id} {plan.name}: total={plan.total} "
                f"keep={c['keep']} delete={c['delete']} skip={c['skip']}"
            )

        unmatched = [coords[i] for i, m in enumerate(matched) if not m]
        print(
            f"TOTAL keep={grand['keep']} delete={grand['delete']} "
            f"skip={grand['skip']} | unmatched_verdicts={len(unmatched)}"
        )
        # When scanning every task, every delete verdict must hit exactly one shape.
        if only is None and unmatched:
            for x, y in unmatched[:20]:
                print(f"    UNMATCHED verdict at ({round(x)},{round(y)})")

        if mode == "apply":
            if only is None and unmatched:
                raise SystemExit("unmatched delete verdicts — aborting apply")
            for t, plan in plans:
                if plan.delete_ids:
                    t.remove_annotations(ids=plan.delete_ids)
                    print(f"applied task {plan.task_id}: deleted {len(plan.delete_ids)}")
            print("apply done")
        else:
            print("dry-run only — no changes pushed")


if __name__ == "__main__":
    main()

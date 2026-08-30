"""Apply vision-review verdicts to CVAT v2 tasks (DEproject2, tasks 11-18).

Decision rules per shape (label):
- P1 (explosion/car_accident/blood/abuse) + P2 (weapon_knife/riot/weapon_gun):
  per-box verdict from {p1,p2}_verdicts.json matched by (frame, label, x, y).
    keep -> keep, delete -> delete, relabel -> set label to weapon_knife.
- unknown            -> delete (bulk, P3 sample concluded 일괄 삭제)
- bottle/cup/cigarette -> keep (bulk, P4 sample concluded 일괄 유지)
- drinking_act       -> keep (out of review scope; leave untouched)
- any other / unmatched -> keep + FLAG (never silently delete)

Usage:
    python scripts/cvat_apply_review.py dryrun [task_id]
    python scripts/cvat_apply_review.py apply
Backup must exist (run cvat_recon.py first).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from cvat_sdk import make_client
from cvat_sdk.api_client.models import (
    LabeledShapeRequest,
    PatchedLabeledDataRequest,
)
from cvat_sdk.core.proxies.annotations import AnnotationUpdateAction
from cvat_sdk.core.proxies.tasks import Task

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import PROCESSED_DIR

CVAT_HOST = "http://localhost:8080"
PROJECT_NAME = "DEproject2"
KEYS_DIR = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2")
REVIEW_DIR = PROCESSED_DIR / "vision_review"
BACKUP_DIR = PROCESSED_DIR / "cvat_backup_2026-05-30"

P1_P2_LABELS = {
    "explosion", "car_accident", "blood", "abuse",
    "weapon_knife", "riot", "weapon_gun",
}
RELABEL_TARGET = "weapon_knife"

# (frame, label) -> list of (x, y, recommendation)
VerdictMap = dict[tuple[str, str], list[tuple[float, float, str]]]

# manifest coords are round(coco, 1) so differ from CVAT full coords by <=0.05px;
# distinct GD boxes differ by many px, so a sub-pixel tolerance is unambiguous.
MATCH_TOL = 0.5


@dataclass
class Plan:
    task_id: int
    name: str
    total: int
    counts: dict[str, int]
    delete_ids: list[int] = field(default_factory=list)
    relabel: list[dict[str, object]] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


def creds() -> tuple[str, str]:
    return (
        (KEYS_DIR / "CVAT_username.txt").read_text(encoding="utf-8").strip(),
        (KEYS_DIR / "CVAT_password.txt").read_text(encoding="utf-8").strip(),
    )


def load_verdict_map() -> VerdictMap:
    """(frame_name, label) -> [(x, y, recommendation), ...]."""
    out: VerdictMap = {}
    for group in ("p1_violence_event", "p2_weapon_riot"):
        data = json.loads(
            (REVIEW_DIR / f"{group}_verdicts.json").read_text(encoding="utf-8")
        )
        for e in data:
            x, y = e["bbox_xywh"][0], e["bbox_xywh"][1]
            out.setdefault((e["frame"], e["cvat_label"]), []).append(
                (x, y, e["recommendation"])
            )
    return out


def decide(label: str, frame: str, x: float, y: float, vmap: VerdictMap) -> str:
    """action in {keep, delete, relabel, flag}."""
    if label in P1_P2_LABELS:
        candidates = vmap.get((frame, label), [])
        best: tuple[float, str] | None = None
        for vx, vy, rec in candidates:
            dist = max(abs(vx - x), abs(vy - y))
            if dist <= MATCH_TOL and (best is None or dist < best[0]):
                best = (dist, rec)
        if best is None:
            return "flag"
        rec = best[1]
        return rec if rec in {"keep", "delete", "relabel"} else "flag"
    if label == "unknown":
        return "delete"
    if label in {"bottle", "cup", "cigarette"}:
        return "keep"
    if label == "drinking_act":
        return "keep"
    return "flag"


def task_frame_names(t: Task) -> dict[int, str]:
    names: dict[int, str] = {}
    for i, fr in enumerate(t.get_frames_info()):
        names[i] = cast(str, fr.to_dict()["name"])
    return names


def plan_task(t: Task, label_map: dict[str, int], vmap: VerdictMap) -> Plan:
    id2name = {v: k for k, v in label_map.items()}
    idx2frame = task_frame_names(t)
    shapes = cast(list[dict[str, object]], t.get_annotations().to_dict()["shapes"])

    plan = Plan(
        task_id=t.id, name=t.name, total=len(shapes),
        counts={"keep": 0, "delete": 0, "relabel": 0, "flag": 0},
    )
    for sd in shapes:
        label = id2name.get(cast(int, sd["label_id"]), str(sd["label_id"]))
        frame = idx2frame.get(cast(int, sd["frame"]), "?")
        pts = cast("list[float]", sd["points"])
        x, y = pts[0], pts[1]
        action = decide(label, frame, x, y, vmap)
        plan.counts[action] += 1
        sid = cast(int, sd["id"])
        if action == "delete":
            plan.delete_ids.append(sid)
        elif action == "relabel":
            plan.relabel.append(sd)
        elif action == "flag":
            plan.flags.append(f"id={sid} label={label} frame={frame} pts=({round(x)},{round(y)})")
    return plan


def apply_task(t: Task, plan: Plan, target_label_id: int) -> None:
    if plan.relabel:
        reqs = [
            LabeledShapeRequest(
                type=cast(str, sd["type"]),
                frame=cast(int, sd["frame"]),
                label_id=target_label_id,
                points=cast("list[float]", sd["points"]),
                occluded=cast(bool, sd.get("occluded", False)),
                outside=cast(bool, sd.get("outside", False)),
                z_order=cast(int, sd.get("z_order", 0)),
                rotation=cast(float, sd.get("rotation", 0.0)),
                group=cast(int, sd.get("group", 0)),
                source=cast(str, sd.get("source", "manual")),
                attributes=[],
                id=cast(int, sd["id"]),
            )
            for sd in plan.relabel
        ]
        t.update_annotations(
            PatchedLabeledDataRequest(shapes=reqs),
            action=AnnotationUpdateAction.UPDATE,
        )
        print(f"  relabeled {len(reqs)} -> {RELABEL_TARGET}")
    if plan.delete_ids:
        t.remove_annotations(ids=plan.delete_ids)
        print(f"  deleted {len(plan.delete_ids)}")


def main() -> None:
    if not BACKUP_DIR.exists():
        raise SystemExit("backup missing — run cvat_recon.py first")
    mode = sys.argv[1] if len(sys.argv) > 1 else "dryrun"
    only = int(sys.argv[2]) if len(sys.argv) > 2 else None
    vmap = load_verdict_map()
    print(f"loaded {len(vmap)} per-box verdicts (p1+p2)")

    with make_client(host=CVAT_HOST, credentials=creds()) as client:
        proj = next(p for p in client.projects.list() if p.name == PROJECT_NAME)
        label_map = {lbl.name: lbl.id for lbl in proj.get_labels()}
        target_id = label_map[RELABEL_TARGET]
        tasks = sorted(
            (t for t in client.tasks.list() if t.project_id == proj.id),
            key=lambda t: t.id,
        )
        if only is not None:
            tasks = [t for t in tasks if t.id == only]

        grand = {"keep": 0, "delete": 0, "relabel": 0, "flag": 0}
        plans: list[tuple[Task, Plan]] = []
        for t in tasks:
            plan = plan_task(t, label_map, vmap)
            plans.append((t, plan))
            for k in grand:
                grand[k] += plan.counts[k]
            c = plan.counts
            print(
                f"task {plan.task_id} {plan.name}: total={plan.total} "
                f"keep={c['keep']} delete={c['delete']} relabel={c['relabel']} flag={c['flag']}"
            )
            for fl in plan.flags:
                print(f"    FLAG: {fl}")
        print(
            f"TOTAL keep={grand['keep']} delete={grand['delete']} "
            f"relabel={grand['relabel']} flag={grand['flag']}"
        )

        if mode == "apply":
            if grand["flag"] > 0:
                raise SystemExit("flags present — aborting apply, resolve first")
            for t, plan in plans:
                print(f"applying task {plan.task_id}...")
                apply_task(t, plan, target_id)
            print("apply done")
        else:
            print("dry-run only — no changes pushed")


if __name__ == "__main__":
    main()

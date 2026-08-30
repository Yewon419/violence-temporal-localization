"""CVAT 자동 셋업 — DEproject2 Project에 영상별 Task 10개 생성 + GD pre-annotation upload.

대표님 결정 (2026-05-30):
- 대표님이 superuser + Project (label 8개) 생성까지 진행
- 나머지(Task 생성·이미지 업로드·annotation upload)는 본인 자동화
- credentials: _keys/DEproject2/CVAT_{username,password}.txt

label 매핑 (GD raw → CVAT project label):
    cigarette → cigarette
    bottle → bottle
    cup → cup
    drinking → drinking_act
    smoking → smoking_act
    smoking drinking → unknown (concat label, 사람이 검수 시 split)
    bottle cup → unknown
    '' (empty) → unknown (post-process 실패 GD bbox)

실행:
    .venv\\Scripts\\python.exe scripts\\cvat_setup.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cvat_sdk import make_client
from cvat_sdk.api_client.models import (
    PatchedLabelRequest,
    PatchedProjectWriteRequest,
    TaskWriteRequest,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import PROCESSED_DIR

CVAT_HOST: str = "http://localhost:8080"
PROJECT_NAME: str = "DEproject2"
CVAT_IMPORT: Path = PROCESSED_DIR / "cvat_import"
KEYS_DIR: Path = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2")

VIDEOS: tuple[tuple[str, str], ...] = (
    ("vyXEi00PVrw", "신세계"),
    ("69RJZ7TwDrQ", "범죄와의 전쟁"),
    ("3auH8hGUezI", "내부자들"),
    ("Rqlf3zNPqgQ", "달콤한 인생"),
    ("LkSY-EuTb1E", "마약왕"),
    ("Tj7Doyo8XdQ", "친구"),
    ("wBr3f72w-fg", "비열한 거리"),
    ("sMpzdgHrINs", "베테랑"),
    ("x2PjLCMrfTk", "황해"),
    ("jGP1Z18maME", "흡연 컴파일"),
)

LABEL_MAP: dict[str, str] = {
    "cigarette": "cigarette",
    "bottle": "bottle",
    "cup": "cup",
    "drinking": "drinking_act",
    "smoking": "smoking_act",
    "smoking drinking": "unknown",
    "bottle cup": "unknown",
    "": "unknown",
}


def get_credentials() -> tuple[str, str]:
    return (
        (KEYS_DIR / "CVAT_username.txt").read_text(encoding="utf-8").strip(),
        (KEYS_DIR / "CVAT_password.txt").read_text(encoding="utf-8").strip(),
    )


def remap_coco(src_path: Path, project_labels: list[str]) -> Path:
    coco = json.loads(src_path.read_text(encoding="utf-8"))
    new_categories = [
        {"id": i + 1, "name": lbl, "supercategory": ""}
        for i, lbl in enumerate(project_labels)
    ]
    name_to_id = {lbl: i + 1 for i, lbl in enumerate(project_labels)}
    old_cat_id_to_name: dict[int, str] = {
        c["id"]: c["name"] for c in coco["categories"]
    }
    for ann in coco["annotations"]:
        old_name = old_cat_id_to_name[ann["category_id"]]
        new_name = LABEL_MAP.get(old_name, "unknown")
        ann["category_id"] = name_to_id[new_name]
    coco["categories"] = new_categories
    dst = src_path.parent / "coco_cvat.json"
    dst.write_text(json.dumps(coco, ensure_ascii=False, indent=2), encoding="utf-8")
    return dst


def main() -> None:
    creds = get_credentials()
    print(f"connecting to {CVAT_HOST} as {creds[0]}...")
    with make_client(host=CVAT_HOST, credentials=creds) as client:
        projects = list(client.projects.list())
        proj = next((p for p in projects if p.name == PROJECT_NAME), None)
        if not proj:
            print(f"project {PROJECT_NAME!r} not found", file=sys.stderr)
            sys.exit(1)

        project_labels = [lbl.name for lbl in proj.get_labels()]
        print(f"project id={proj.id} existing labels={project_labels}")

        if "unknown" not in project_labels:
            patch = PatchedProjectWriteRequest(
                labels=[PatchedLabelRequest(name="unknown", color="#808080")]
            )
            client.api_client.projects_api.partial_update(
                id=proj.id, patched_project_write_request=patch
            )
            project_labels.append("unknown")
            print("added 'unknown' label")

        existing_task_names = {
            t.name for t in client.tasks.list() if t.project_id == proj.id
        }

        for vid, label in VIDEOS:
            task_name = f"{vid} ({label})"
            if task_name in existing_task_names:
                print(f"[{vid}] task '{task_name}' already exists — skip")
                continue

            images_dir = CVAT_IMPORT / vid / "images"
            coco_src = CVAT_IMPORT / vid / "coco.json"
            if not images_dir.exists() or not coco_src.exists():
                print(f"[{vid}] missing src — skip")
                continue

            print(f"[{vid}] creating task '{task_name}'...")
            spec = TaskWriteRequest(name=task_name, project_id=proj.id)
            image_paths = sorted(str(p) for p in images_dir.glob("*.jpg"))
            task = client.tasks.create_from_data(spec=spec, resources=image_paths)
            print(f"  task id={task.id}, {len(image_paths)} images uploaded")

            coco_dst = remap_coco(coco_src, project_labels)
            ann_count = len(json.loads(coco_dst.read_text(encoding="utf-8"))["annotations"])
            if ann_count == 0:
                print(f"  [{vid}] no annotations to upload (0 boxes)")
                continue
            task.import_annotations(format_name="COCO 1.0", filename=str(coco_dst))
            print(f"  [{vid}] uploaded {ann_count} annotations")

    print("done")


if __name__ == "__main__":
    main()

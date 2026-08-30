"""zombie01 큐레이션 → CVAT 신규 task 1개 생성 + COCO pre-annotation import.

frame-level 큐레이션(zombie01_keep_frames.json)의 keep positive 프레임만 올린다.
keep 프레임의 GD 필터 박스(weapon_gun/knife/blunt/blood)를 COCO로 변환,
프로젝트 DEproject2 라벨 스키마에 name 매칭으로 import → 검수자가 박스 보정.

hard negative(candidate-but-drop)는 로컬 YOLO 셋(zombie01_yolo)에 빈 txt로 남김.

⚠ 기존 task(11~18)는 건드리지 않는다. 신규 task 1개만 생성.

    .venv\\Scripts\\python.exe scripts\\cvat_upload_zombie.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import TypedDict, cast

from cvat_sdk import make_client
from cvat_sdk.api_client.models import TaskWriteRequest
from PIL import Image

CVAT_HOST = "http://localhost:8080"
PROJECT_NAME = "DEproject2"
TASK_NAME = "zombie01 (뉴토피아) weapon·gore"
KEYS_DIR = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2")
BASE = Path(__file__).resolve().parents[1]
KEEP_JSON = BASE / "data/processed/vision_review/zombie01_keep_frames.json"
FILTERED_DIR = BASE / "data/processed/gd_zombie_filtered/zombie01"
FRAMES_DIR = BASE / "data/processed/zombie01_frames"
STAGE_DIR = BASE / "data/processed/cvat_import_zombie/zombie01"


class CocoImage(TypedDict):
    id: int
    file_name: str
    width: int
    height: int
    license: int
    flickr_url: str
    coco_url: str
    date_captured: int


class CocoAnnotation(TypedDict):
    id: int
    image_id: int
    category_id: int
    segmentation: list[float]
    area: float
    bbox: list[float]
    iscrowd: int


def get_credentials() -> tuple[str, str]:
    return (
        (KEYS_DIR / "CVAT_username.txt").read_text(encoding="utf-8").strip(),
        (KEYS_DIR / "CVAT_password.txt").read_text(encoding="utf-8").strip(),
    )


def build_coco(keep: list[int], cvat_labels: list[str]) -> tuple[Path, list[str], int]:
    img_dir = STAGE_DIR / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    name_to_id = {n: i + 1 for i, n in enumerate(cvat_labels)}

    images: list[CocoImage] = []
    annotations: list[CocoAnnotation] = []
    ann_id = 1
    box_count = 0
    for img_id, n in enumerate(sorted(keep), start=1):
        stem = f"zombie01_frame_{n:05d}"
        src = FRAMES_DIR / f"{stem}.jpg"
        jp = FILTERED_DIR / f"{stem}.json"
        if not src.exists() or not jp.exists():
            continue
        dst = img_dir / f"{stem}.jpg"
        if not dst.exists():
            shutil.copy2(src, dst)
        with Image.open(dst) as im:
            w, h = im.size
        images.append(
            {
                "id": img_id,
                "file_name": f"{stem}.jpg",
                "width": w,
                "height": h,
                "license": 0,
                "flickr_url": "",
                "coco_url": "",
                "date_captured": 0,
            }
        )
        rec = json.loads(jp.read_text(encoding="utf-8"))
        for b in cast(list[dict[str, object]], rec["boxes"]):
            label = cast(str, b["label"])
            if label not in name_to_id:
                continue
            x1, y1, x2, y2 = cast(list[float], b["box"])
            bw, bh = max(0.0, x2 - x1), max(0.0, y2 - y1)
            annotations.append(
                {
                    "id": ann_id,
                    "image_id": img_id,
                    "category_id": name_to_id[label],
                    "segmentation": [],
                    "area": bw * bh,
                    "bbox": [x1, y1, bw, bh],
                    "iscrowd": 0,
                }
            )
            ann_id += 1
            box_count += 1

    coco = {
        "info": {
            "description": "zombie01 (뉴토피아) frame-level curation, GD pre-annotation",
            "version": "1.0",
            "year": 2026,
            "contributor": "yewon",
            "date_created": "",
        },
        "licenses": [{"id": 0, "name": "Unknown", "url": ""}],
        "images": images,
        "annotations": annotations,
        "categories": [
            {"id": i + 1, "name": n, "supercategory": ""}
            for i, n in enumerate(cvat_labels)
        ],
    }
    coco_path = STAGE_DIR / "coco.json"
    coco_path.write_text(json.dumps(coco, ensure_ascii=False, indent=2), encoding="utf-8")
    image_paths = sorted(str(p) for p in img_dir.glob("*.jpg"))
    return coco_path, image_paths, box_count


def main() -> None:
    keep = cast(list[int], json.loads(KEEP_JSON.read_text(encoding="utf-8"))["keep_frames"])
    with make_client(host=CVAT_HOST, credentials=get_credentials()) as client:
        proj = next(p for p in client.projects.list() if p.name == PROJECT_NAME)
        cvat_labels = sorted(lbl.name for lbl in proj.get_labels())
        print(f"project id={proj.id}")

        existing = [t for t in client.tasks.list() if t.project_id == proj.id]
        print(f"existing tasks (보존): {[t.id for t in existing]}")
        if any(t.name == TASK_NAME for t in existing):
            raise SystemExit(f"task already exists: {TASK_NAME!r} — 중복 업로드 방지")

        coco_path, image_paths, box_count = build_coco(keep, cvat_labels)
        print(f"staged {len(image_paths)} images, {box_count} boxes")
        if not image_paths:
            raise SystemExit("no images staged")

        spec = TaskWriteRequest(name=TASK_NAME, project_id=proj.id)
        task = client.tasks.create_from_data(spec=spec, resources=image_paths)
        print(f"created task id={task.id} name={TASK_NAME!r} ({len(image_paths)} frames)")
        task.import_annotations(format_name="COCO 1.0", filename=str(coco_path))
        print(f"imported {box_count} boxes (COCO 1.0)")
        print("done")


if __name__ == "__main__":
    main()

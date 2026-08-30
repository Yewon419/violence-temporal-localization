"""GD inference 결과(JSON) → CVAT pre-annotation용 COCO 1.0 포맷 변환.

영상별로 호출 — 영상의 GD 결과 100 frame을 모아 단일 COCO JSON 생성 +
같은 폴더에 image 파일 복사 (CVAT 업로드용).

실행:
    python scripts/gd_to_cvat_coco.py --video-id vyXEi00PVrw
    python scripts/gd_to_cvat_coco.py --all  # gd_demo_fps의 모든 영상

출력:
    data/processed/cvat_import/{video_id}/coco.json
    data/processed/cvat_import/{video_id}/images/{frame}.jpg

CVAT Task 생성 시 위 images/ 폴더 전부 업로드 →
Actions → Upload annotations → Format COCO 1.0 → coco.json 선택.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import TypedDict, cast

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import PROCESSED_DIR

GD_OUT: Path = PROCESSED_DIR / "gd_demo_fps"
FRAMES_DIR: Path = PROCESSED_DIR / "yt_drama_frames"
CVAT_OUT: Path = PROCESSED_DIR / "cvat_import"


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
    score: float


def list_videos() -> list[str]:
    return sorted(d.name for d in GD_OUT.iterdir() if d.is_dir())


def convert_one(video_id: str) -> int:
    gd_dir = GD_OUT / video_id
    out_dir = CVAT_OUT / video_id
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(gd_dir.glob("*_frame_*.json"))
    if not json_files:
        json_files = sorted(p for p in gd_dir.glob("*.json") if "_vis" not in p.stem)
    if not json_files:
        print(f"[{video_id}] no GD json found")
        return 0

    label_set: set[str] = set()
    for jp in json_files:
        rec = json.loads(jp.read_text(encoding="utf-8"))
        for lbl in rec.get("labels", []):
            name = lbl if lbl else "unknown"
            label_set.add(name)
    categories = [
        {"id": i, "name": name, "supercategory": ""}
        for i, name in enumerate(sorted(label_set), start=1)
    ]
    cat_index: dict[str, int] = {
        cast(str, c["name"]): cast(int, c["id"]) for c in categories
    }

    images: list[CocoImage] = []
    annotations: list[CocoAnnotation] = []
    ann_id = 1

    for img_id, jp in enumerate(json_files, start=1):
        rec = json.loads(jp.read_text(encoding="utf-8"))
        frame_name = cast(str, rec["frame"])
        src_img = FRAMES_DIR / frame_name
        if not src_img.exists():
            print(f"[{video_id}] missing frame: {frame_name}", file=sys.stderr)
            continue
        dst_img = img_dir / frame_name
        if not dst_img.exists():
            shutil.copy2(src_img, dst_img)

        with Image.open(dst_img) as im:
            w, h = im.size

        images.append(
            {
                "id": img_id,
                "file_name": frame_name,
                "width": w,
                "height": h,
                "license": 0,
                "flickr_url": "",
                "coco_url": "",
                "date_captured": 0,
            }
        )

        boxes = rec.get("boxes", [])
        scores = rec.get("scores", [])
        labels = rec.get("labels", [])
        for box, score, lbl in zip(boxes, scores, labels, strict=False):
            x1, y1, x2, y2 = box
            bw = max(0.0, x2 - x1)
            bh = max(0.0, y2 - y1)
            name = lbl if lbl else "unknown"
            annotations.append(
                {
                    "id": ann_id,
                    "image_id": img_id,
                    "category_id": cat_index[name],
                    "segmentation": [],
                    "area": bw * bh,
                    "bbox": [x1, y1, bw, bh],
                    "iscrowd": 0,
                    "score": score,
                }
            )
            ann_id += 1

    coco = {
        "info": {
            "description": f"GD pre-annotation for {video_id}",
            "version": "1.0",
            "year": 2026,
            "contributor": "yewon",
            "date_created": "",
        },
        "licenses": [{"id": 0, "name": "Unknown", "url": ""}],
        "images": images,
        "annotations": annotations,
        "categories": categories,
    }
    out_json = out_dir / "coco.json"
    out_json.write_text(
        json.dumps(coco, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"[{video_id}] {len(images)} images, {len(annotations)} annotations, "
        f"{len(categories)} categories → {out_json}"
    )
    return len(images)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--video-id", help="single video id")
    g.add_argument("--all", action="store_true", help="every video under gd_demo_fps")
    args = parser.parse_args()

    videos = list_videos() if args.all else [args.video_id]

    total = 0
    for v in videos:
        total += convert_one(v)
    print(f"TOTAL: {total} images across {len(videos)} videos")


if __name__ == "__main__":
    main()

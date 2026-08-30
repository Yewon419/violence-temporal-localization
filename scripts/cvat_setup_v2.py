"""CVAT v2 셋업 — gd_triage_v2 자동 분류 결과 적용.

흐름:
1. 기존 task 1~10 삭제
2. 자동 분류 결과 (gd_triage_v2/{vid}.json) 읽기
3. positive bbox만 추려서 COCO 생성 (category → CVAT label 매핑)
4. 새 task 10개 생성 + COCO import
5. negative bbox 모은 JSON 별도 저장 (학습용 hard negative)

실행:
    .venv\\Scripts\\python.exe scripts\\cvat_setup_v2.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import TypedDict

from cvat_sdk import make_client
from cvat_sdk.api_client.models import TaskWriteRequest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import PROCESSED_DIR

CVAT_HOST: str = "http://localhost:8080"
PROJECT_NAME: str = "DEproject2"
TRIAGE_DIR: Path = PROCESSED_DIR / "gd_triage_v2"
FRAMES_DIR: Path = PROCESSED_DIR / "yt_drama_frames"
CVAT_OUT: Path = PROCESSED_DIR / "cvat_import_v2"
NEGATIVES_DIR: Path = PROCESSED_DIR / "gd_triage_v2" / "negatives"
KEYS_DIR: Path = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2")

VIDEO_TITLES: dict[str, str] = {
    "vyXEi00PVrw": "신세계",
    "69RJZ7TwDrQ": "범죄와의 전쟁",
    "3auH8hGUezI": "내부자들",
    "Rqlf3zNPqgQ": "달콤한 인생",
    "LkSY-EuTb1E": "마약왕",
    "wBr3f72w-fg": "비열한 거리",
    "sMpzdgHrINs": "베테랑",
    "x2PjLCMrfTk": "황해",
}


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


def cvat_label_from_raw(raw_label: str) -> str | None:
    if raw_label == "cigarette":
        return "cigarette"
    if raw_label == "smoking":
        return "smoking_act"
    if raw_label in {"bottle", "cup", "wine_glass", "alcohol"}:
        return raw_label
    if raw_label == "drinking":
        return "drinking_act"
    if raw_label in {"knife", "gun"}:
        return f"weapon_{raw_label}"
    if raw_label in {"hammer", "baseball bat", "bat"}:
        return "weapon_blunt"
    if raw_label == "blood":
        return "blood"
    if raw_label in {"fighting", "shooting", "riot", "abuse"}:
        return raw_label
    if raw_label == "explosion":
        return "explosion"
    if "accident" in raw_label:
        return "car_accident"
    return None


def get_credentials() -> tuple[str, str]:
    return (
        (KEYS_DIR / "CVAT_username.txt").read_text(encoding="utf-8").strip(),
        (KEYS_DIR / "CVAT_password.txt").read_text(encoding="utf-8").strip(),
    )


def build_coco_and_negatives(
    video_id: str, cvat_labels: list[str]
) -> tuple[Path | None, int, int]:
    triage_path = TRIAGE_DIR / f"{video_id}.json"
    if not triage_path.exists():
        print(f"  [{video_id}] no triage json")
        return None, 0, 0

    frames = json.loads(triage_path.read_text(encoding="utf-8"))
    out_dir = CVAT_OUT / video_id
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    name_to_id: dict[str, int] = {n: i + 1 for i, n in enumerate(cvat_labels)}

    images: list[CocoImage] = []
    annotations: list[CocoAnnotation] = []
    negatives: list[dict[str, object]] = []
    ann_id = 1
    pos_count = 0
    neg_count = 0

    for img_id, fr in enumerate(frames, start=1):
        frame_name = fr["frame"]
        src = FRAMES_DIR / frame_name
        if not src.exists():
            continue
        dst = img_dir / frame_name
        if not dst.exists():
            shutil.copy2(src, dst)
        with Image.open(dst) as im:
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

        for box in fr["boxes"]:
            verdict = box["verdict"]
            bbox = box["bbox"]
            score = box["score"]
            raw_label = box["raw_label"]
            x1, y1, x2, y2 = bbox
            bw, bh = max(0.0, x2 - x1), max(0.0, y2 - y1)

            if verdict == "negative":
                negatives.append(
                    {
                        "frame": frame_name,
                        "image_size": [w, h],
                        "bbox": bbox,
                        "score": score,
                        "raw_label": raw_label,
                        "reason": box["reason"],
                    }
                )
                neg_count += 1
                continue

            if verdict == "positive":
                cvat_label = cvat_label_from_raw(raw_label)
            elif verdict in {"uncertain", "unknown"}:
                cvat_label = "unknown"
            else:
                cvat_label = None

            if cvat_label is None or cvat_label not in name_to_id:
                continue

            annotations.append(
                {
                    "id": ann_id,
                    "image_id": img_id,
                    "category_id": name_to_id[cvat_label],
                    "segmentation": [],
                    "area": bw * bh,
                    "bbox": [x1, y1, bw, bh],
                    "iscrowd": 0,
                }
            )
            ann_id += 1
            pos_count += 1

    coco = {
        "info": {
            "description": f"GD v2 + auto triage for {video_id}",
            "version": "2.0",
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
    coco_path = out_dir / "coco.json"
    coco_path.write_text(
        json.dumps(coco, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if negatives:
        NEGATIVES_DIR.mkdir(parents=True, exist_ok=True)
        neg_path = NEGATIVES_DIR / f"{video_id}.json"
        neg_path.write_text(
            json.dumps(
                {"video_id": video_id, "negatives": negatives},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    return coco_path, pos_count, neg_count


def main() -> None:
    creds = get_credentials()
    with make_client(host=CVAT_HOST, credentials=creds) as client:
        proj = next(p for p in client.projects.list() if p.name == PROJECT_NAME)
        cvat_labels = sorted(lbl.name for lbl in proj.get_labels())
        print(f"project id={proj.id} labels={cvat_labels}")

        old_tasks = [t for t in client.tasks.list() if t.project_id == proj.id]
        print(f"deleting {len(old_tasks)} old tasks...")
        for t in old_tasks:
            client.api_client.tasks_api.destroy(id=t.id)
            print(f"  deleted task id={t.id} name={t.name!r}")

        total_pos = 0
        total_neg = 0
        for vid in sorted(VIDEO_TITLES):
            title = VIDEO_TITLES.get(vid, vid)
            print(f"--- {vid} ({title}) ---")
            coco_path, pos_count, neg_count = build_coco_and_negatives(vid, cvat_labels)
            total_pos += pos_count
            total_neg += neg_count
            if coco_path is None:
                continue

            images_dir = CVAT_OUT / vid / "images"
            image_paths = sorted(str(p) for p in images_dir.glob("*.jpg"))
            if not image_paths:
                print(f"  [{vid}] no images")
                continue

            spec = TaskWriteRequest(name=f"{vid} ({title})", project_id=proj.id)
            task = client.tasks.create_from_data(spec=spec, resources=image_paths)
            print(f"  task id={task.id} {len(image_paths)} images")

            if pos_count > 0:
                task.import_annotations(format_name="COCO 1.0", filename=str(coco_path))
                print(f"  [{vid}] imported {pos_count} positive/unknown boxes")
            print(f"  [{vid}] {neg_count} negatives saved separately")

    print(f"TOTAL positive/unknown: {total_pos}, negatives: {total_neg}")
    print("done")


if __name__ == "__main__":
    main()

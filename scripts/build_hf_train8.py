"""CVAT tasks 11~18(드라마 v2 흡연/음주, 영화 8편) → HF dataset_Ver2 train8 로컬 빌드.

각 task를 Ultralytics YOLO Detection 1.0으로 export → train8/<video_id>/ 구조로 재배치.
검수본(CVAT 현재 상태) 그대로. negative(박스0) 프레임은 이미지만, txt 없음(팀 컨벤션).
클래스 id는 CVAT 프로젝트 스킴 유지(remap 없음).

    .venv\\Scripts\\python.exe scripts\\build_hf_train8.py
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from cvat_sdk import make_client

CVAT_HOST = "http://localhost:8080"
TASK_IDS = list(range(11, 19))
KEYS_DIR = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2")
BASE = Path(__file__).resolve().parents[1]
EXPORT_DIR = BASE / "data/processed/cvat_export_old"
DST = BASE / "data/processed/hf_train8"
SUBSET = "train8"


def get_credentials() -> tuple[str, str]:
    return (
        (KEYS_DIR / "CVAT_username.txt").read_text(encoding="utf-8").strip(),
        (KEYS_DIR / "CVAT_password.txt").read_text(encoding="utf-8").strip(),
    )


def main() -> None:
    if DST.exists():
        shutil.rmtree(DST)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    total_img = 0
    total_lbl = 0
    with make_client(host=CVAT_HOST, credentials=get_credentials()) as client:
        for tid in TASK_IDS:
            task = client.tasks.retrieve(tid)
            vid = task.name.split()[0]
            zpath = EXPORT_DIR / f"task{tid}_{vid}.zip"
            task.export_dataset(
                format_name="Ultralytics YOLO Detection 1.0",
                filename=str(zpath),
                include_images=True,
            )
            xdir = EXPORT_DIR / f"task{tid}"
            if xdir.exists():
                shutil.rmtree(xdir)
            with zipfile.ZipFile(zpath) as zf:
                zf.extractall(xdir)

            dst_img = DST / "images/train" / SUBSET / vid
            dst_lbl = DST / "labels/train" / SUBSET / vid
            dst_img.mkdir(parents=True, exist_ok=True)
            dst_lbl.mkdir(parents=True, exist_ok=True)
            imgs = sorted((xdir / "images/train").glob("*.jpg"))
            lbls = sorted((xdir / "labels/train").glob("*.txt"))
            for p in imgs:
                shutil.copy2(p, dst_img / p.name)
            for p in lbls:
                shutil.copy2(p, dst_lbl / p.name)
            total_img += len(imgs)
            total_lbl += len(lbls)
            print(f"task{tid} {vid}: images={len(imgs)} labels={len(lbls)} neg={len(imgs) - len(lbls)}")

    print(f"TOTAL: images={total_img} labels={total_lbl} -> {DST}")


if __name__ == "__main__":
    main()

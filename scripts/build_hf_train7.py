"""CVAT task19 Ultralytics export → HF dataset_Ver2 train7 폴더 구조로 로컬 빌드.

팀 구조(images/train/trainN/<source>/..., labels 미러)에 맞춰 train7/zombie01 생성.
negative(박스 0) 프레임은 이미지만 두고 txt 없음 — 팀 컨벤션(img>label) 그대로.
클래스 id는 CVAT 프로젝트 스킴(data.yaml 0~17) 유지, remap 안 함.

    .venv\\Scripts\\python.exe scripts\\build_hf_train7.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "data/processed/cvat_export_zombie/task19"
DST = BASE / "data/processed/hf_train7"
SUBSET = "train7"
SOURCE = "zombie01"


def main() -> None:
    src_img = SRC / "images/train"
    src_lbl = SRC / "labels/train"
    dst_img = DST / "images/train" / SUBSET / SOURCE
    dst_lbl = DST / "labels/train" / SUBSET / SOURCE
    if DST.exists():
        shutil.rmtree(DST)
    dst_img.mkdir(parents=True, exist_ok=True)
    dst_lbl.mkdir(parents=True, exist_ok=True)

    images = sorted(src_img.glob("*.jpg"))
    labels = sorted(src_lbl.glob("*.txt"))
    for p in images:
        shutil.copy2(p, dst_img / p.name)
    for p in labels:
        shutil.copy2(p, dst_lbl / p.name)

    lbl_stems = {p.stem for p in labels}
    negatives = [p for p in images if p.stem not in lbl_stems]
    print(f"images={len(images)} labels={len(labels)} negatives(no txt)={len(negatives)}")
    print(f"images -> {dst_img}")
    print(f"labels -> {dst_lbl}")


if __name__ == "__main__":
    main()

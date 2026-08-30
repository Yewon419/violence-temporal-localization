"""로컬 hf_train7 → HuggingFace DEteam4/dataset_Ver2 push (train7 추가).

검수본(CVAT task19 Ultralytics export)을 팀 구조 그대로 올린다:
    images/train/train7/zombie01/*.jpg
    labels/train/train7/zombie01/*.txt
클래스 id는 CVAT 프로젝트 스킴(=movie-rating-violence names) 그대로 — remap 불필요.

토큰은 _keys에서 읽고 출력하지 않음. 기존 train1~6는 건드리지 않음(train7만 추가 커밋).

    .venv\\Scripts\\python.exe scripts\\push_hf_train7.py
"""

from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import HfApi

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

REPO = "DEteam4/dataset_Ver2"
BASE = Path(__file__).resolve().parents[1]
LOCAL = BASE / "data/processed/hf_train7"
TOKEN_PATH = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2\HF_TOKEN.txt")


def main() -> None:
    token = TOKEN_PATH.read_text(encoding="utf-8").strip()
    api = HfApi(token=token)

    existing = set(api.list_repo_files(REPO, repo_type="dataset"))
    if any(f.startswith("images/train/train7/") for f in existing):
        raise SystemExit("train7 already present in repo — 중복 push 방지")

    n_img = len(list((LOCAL / "images/train/train7/zombie01").glob("*.jpg")))
    n_lbl = len(list((LOCAL / "labels/train/train7/zombie01").glob("*.txt")))
    print(f"uploading train7: {n_img} images, {n_lbl} labels -> {REPO}")

    api.upload_folder(
        repo_id=REPO,
        repo_type="dataset",
        folder_path=str(LOCAL),
        path_in_repo="",
        commit_message="Add train7 (zombie01 뉴토피아): weapon/blood, 454 frames / 334 labeled / 120 neg",
        allow_patterns=["images/train/train7/**", "labels/train/train7/**"],
    )
    print("push done")


if __name__ == "__main__":
    main()

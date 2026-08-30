"""dataset_Ver2: train8 내용을 train7로 통합 이동 (우리 기여분 단일 배치화).

HF는 서버사이드 move가 없으므로: 로컬 hf_train8 빌드를 train7 경로로 재업로드 → repo의 train8 폴더 삭제.
train7/zombie01(기존)은 그대로 두고 8개 드라마 vid 폴더를 train7 하위에 형제로 추가.
토큰은 _keys에서 읽고 출력하지 않음.

    .venv\\Scripts\\python.exe scripts\\move_train8_to_train7.py
"""

from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import HfApi

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

REPO = "DEteam4/dataset_Ver2"
BASE = Path(__file__).resolve().parents[1]
LOCAL = BASE / "data/processed/hf_train8"
TOKEN_PATH = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2\HF_TOKEN.txt")


def main() -> None:
    token = TOKEN_PATH.read_text(encoding="utf-8").strip()
    api = HfApi(token=token)

    before = set(api.list_repo_files(REPO, repo_type="dataset"))
    if not any(f.startswith("images/train/train8/") for f in before):
        raise SystemExit("repo에 train8 없음 — 이동 대상 없음")

    # 1) train8 로컬 내용을 train7 경로로 업로드
    api.upload_folder(
        repo_id=REPO,
        repo_type="dataset",
        folder_path=str(LOCAL / "images/train/train8"),
        path_in_repo="images/train/train7",
        commit_message="Merge train8 images into train7 (우리 기여분 통합)",
    )
    api.upload_folder(
        repo_id=REPO,
        repo_type="dataset",
        folder_path=str(LOCAL / "labels/train/train8"),
        path_in_repo="labels/train/train7",
        commit_message="Merge train8 labels into train7 (우리 기여분 통합)",
    )

    # 2) repo의 train8 폴더 삭제
    api.delete_folder(
        path_in_repo="images/train/train8",
        repo_id=REPO,
        repo_type="dataset",
        commit_message="Remove train8 after merge into train7",
    )
    api.delete_folder(
        path_in_repo="labels/train/train8",
        repo_id=REPO,
        repo_type="dataset",
        commit_message="Remove train8 after merge into train7",
    )
    print("move done")


if __name__ == "__main__":
    main()

"""로컬 빌드 폴더 → HuggingFace DEteam4/dataset_Ver2 push (trainN 서브셋 추가).

build_hf_trainN.py가 만든 `<local>/images/train/<subset>/...` + labels 미러를 그대로 올린다.
토큰은 _keys에서 읽고 출력하지 않음. 해당 subset만 allow_patterns로 올려 기존 train 보존.
중복 push 가드 포함.

    .venv\\Scripts\\python.exe scripts\\push_hf_subset.py --local data/processed/hf_train8 --subset train8 \
        --message "Add train8 (드라마 v2 흡연/음주, 영화 8편): 800 frames / 114 labeled / 307 boxes"
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import cast

from huggingface_hub import HfApi

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

REPO = "DEteam4/dataset_Ver2"
TOKEN_PATH = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2\HF_TOKEN.txt")


def main() -> None:
    ap = argparse.ArgumentParser(description="Push a built trainN subset to dataset_Ver2.")
    ap.add_argument("--local", type=Path, required=True)
    ap.add_argument("--subset", required=True, help="e.g. train8")
    ap.add_argument("--message", required=True)
    args = ap.parse_args()
    local = cast(Path, args.local)
    subset = cast(str, args.subset)
    message = cast(str, args.message)

    token = TOKEN_PATH.read_text(encoding="utf-8").strip()
    api = HfApi(token=token)

    existing = set(api.list_repo_files(REPO, repo_type="dataset"))
    if any(f.startswith(f"images/train/{subset}/") for f in existing):
        raise SystemExit(f"{subset} already present in repo — 중복 push 방지")

    n_img = len(list((local / "images/train" / subset).rglob("*.jpg")))
    n_lbl = len(list((local / "labels/train" / subset).rglob("*.txt")))
    print(f"uploading {subset}: {n_img} images, {n_lbl} labels -> {REPO}")

    api.upload_folder(
        repo_id=REPO,
        repo_type="dataset",
        folder_path=str(local),
        path_in_repo="",
        commit_message=message,
        allow_patterns=[f"images/train/{subset}/**", f"labels/train/{subset}/**"],
    )
    print("push done")


if __name__ == "__main__":
    main()

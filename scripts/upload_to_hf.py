"""Upload a category folder to a private Hugging Face dataset repo.

Run:
    python scripts/upload_to_hf.py --repo-id <user>/movie-rating-violence

Requires:
    HF_TOKEN env var (write-scope token from
    https://huggingface.co/settings/tokens)

Behaviour:
    - Creates the dataset repo private on first run (no-op if it exists).
    - ``upload_folder`` is idempotent: HF compares file hashes and skips
      unchanged files, so re-running after partial extraction safely
      uploads only what's new.
    - Default folder is ``data/processed/violence``; ``--folder`` and
      ``--path-in-repo`` allow uploading any category.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huggingface_hub import HfApi, create_repo

from src.config import PROCESSED_DIR

DEFAULT_FOLDER: Path = PROCESSED_DIR / "violence"
DEFAULT_PATH_IN_REPO: str = "violence"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--repo-id",
        required=True,
        help='Target dataset repo, e.g. "yewon419/movie-rating-violence"',
    )
    p.add_argument(
        "--folder",
        type=Path,
        default=DEFAULT_FOLDER,
        help=f"Local folder to upload. Default: {DEFAULT_FOLDER}",
    )
    p.add_argument(
        "--path-in-repo",
        default=DEFAULT_PATH_IN_REPO,
        help=(
            "Sub-path inside the repo where this folder lands. "
            'Default: "violence" so files end up at violence/{class}/*.jpg'
        ),
    )
    p.add_argument(
        "--split-by-class",
        action="store_true",
        help=(
            "Upload each immediate sub-folder of --folder as a separate commit. "
            "Avoids 504 Gateway Time-out on large commits (>10k files in one go)."
        ),
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    token: str | None = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError(
            "HF_TOKEN env var not set. Generate a write-scope token at "
            "https://huggingface.co/settings/tokens and export it."
        )

    folder: Path = args.folder.resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Upload folder not found or not a directory: {folder}")

    api = HfApi(token=token)

    # Create the dataset repo if it does not yet exist. private=True by default.
    try:
        create_repo(
            repo_id=args.repo_id,
            token=token,
            repo_type="dataset",
            private=True,
            exist_ok=True,
        )
        print(f"Repo ready: {args.repo_id} (private dataset)")
    except Exception as e:
        raise RuntimeError(f"create_repo failed for {args.repo_id}: {e}") from e

    if args.split_by_class:
        class_dirs = sorted(p for p in folder.iterdir() if p.is_dir())
        if not class_dirs:
            raise RuntimeError(
                f"--split-by-class set but no sub-folders found under {folder}"
            )
        for cls_dir in class_dirs:
            sub_path = f"{args.path_in_repo}/{cls_dir.name}"
            print(f"Uploading: {cls_dir}  →  {args.repo_id}:{sub_path}/")
            commit = api.upload_folder(
                folder_path=str(cls_dir),
                repo_id=args.repo_id,
                repo_type="dataset",
                path_in_repo=sub_path,
                commit_message=f"Upload {sub_path}",
            )
            print(f"  commit: {commit}")
    else:
        print(f"Uploading: {folder}  →  {args.repo_id}:{args.path_in_repo}/")
        commit = api.upload_folder(
            folder_path=str(folder),
            repo_id=args.repo_id,
            repo_type="dataset",
            path_in_repo=args.path_in_repo,
            commit_message=f"Upload {args.path_in_repo} from {folder.name}",
        )
        print(f"Commit: {commit}")


if __name__ == "__main__":
    main()

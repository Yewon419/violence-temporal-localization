from __future__ import annotations

from pathlib import Path

from huggingface_hub import HfApi

TOKEN = Path(r"C:/Users/windg/Desktop/PROJECT/_keys/DEproject2/HF_TOKEN.txt").read_text(encoding="utf-8").strip()
SRC = Path(r"C:/Users/windg/Desktop/SCHOOL/3-1/데이터엔지니어링/project2/data/processed/violence_curated_500")
REPO = "DEteam4/movie-rating-violence"


def main() -> None:
    api = HfApi(token=TOKEN)
    n = sum(1 for _ in SRC.rglob("*.jpg"))
    print(f"uploading {n} jpgs from {SRC} -> {REPO}:xd_sampled/")
    api.upload_folder(
        repo_id=REPO,
        repo_type="dataset",
        folder_path=str(SRC),
        path_in_repo="xd_sampled",
        allow_patterns=["*.jpg"],
        commit_message="Add xd_sampled: curated XD-Violence frames (bbox-meaningful, content-reviewed), 5851 imgs across 6 categories",
    )
    print("upload complete")


if __name__ == "__main__":
    main()

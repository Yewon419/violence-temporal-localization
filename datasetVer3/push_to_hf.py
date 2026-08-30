r"""datasetVer3 → HuggingFace 업로드 (화이트리스트 방식).

**프레임 이미지(*.jpg)와 어노테이션 텍스트(raw_txt/*.txt, *.jsonl)만** 올라간다.
원본 mp4·파이썬 캐시 등 그 외 파일은 allow_patterns에 없으므로 자동 제외 → 실수로 무거운/불필요 파일이 올라갈 일이 없다.

토큰: 환경변수 HF_TOKEN. 없으면 `huggingface-cli login` 캐시를 쓴다.
  PowerShell:  $env:HF_TOKEN = (Get-Content C:\Users\windg\Desktop\PROJECT\_keys\DEproject2\HF_TOKEN.txt)
  실행:        python push_to_hf.py
"""

from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import HfApi

BASE_DIR = Path(__file__).resolve().parent
REPO_ID = "DEteam4/datasetVer3"
REPO_TYPE = "dataset"

# 올릴 수 있는 것: 프레임 jpg + 어노테이션 텍스트(원본 txt·jsonl) + 영상 메타. 그 외 전부 제외.
ALLOW_PATTERNS = [
    "frames/**/*.jpg",
    "annotations/raw_txt/*.txt",
    "annotations/annotations.jsonl",
    "annotations/videos.jsonl",
]


def main() -> None:
    token = os.environ.get("HF_TOKEN")
    api = HfApi(token=token)
    who = api.whoami()
    print("auth as:", who.get("name"))
    api.upload_folder(
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        folder_path=str(BASE_DIR),
        allow_patterns=ALLOW_PATTERNS,
        commit_message="프레임·어노테이션 업로드",
    )
    print(f"업로드 완료 → {REPO_ID} (allow={ALLOW_PATTERNS})")


if __name__ == "__main__":
    main()

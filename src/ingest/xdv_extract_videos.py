from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import XDV_TEST_VIDEOS_DIR, XDV_TEST_VIDEOS_ZIP_PATH

# The XD-Violence test zip wraps everything in a top-level "videos/" folder.
# We strip that so files land directly under ``XDV_TEST_VIDEOS_DIR``.
ZIP_INTERNAL_PREFIX: str = "videos/"
READ_CHUNK: int = 4 * 1024 * 1024


def extract_xdv_test_videos(
    zip_path: Path | None = None,
    dest_dir: Path = XDV_TEST_VIDEOS_DIR,
) -> dict[str, int]:
    """Flatten the ``videos/`` prefix and extract mp4 files into ``dest_dir``.

    Idempotent: files already on disk with matching ``file_size`` are
    skipped. Safe to re-run after a partial extraction or after raw
    cleanup (``data/raw/xdviolence_test/*.mp4`` removed but zip kept).
    """
    if zip_path is None:
        zip_path = XDV_TEST_VIDEOS_ZIP_PATH
    if not zip_path.exists():
        raise FileNotFoundError(
            f"XD-Violence zip not found: {zip_path}. "
            "Download Test Videos from the official SharePoint link and place "
            f"as videos.zip in {zip_path.parent}."
        )

    dest_dir.mkdir(parents=True, exist_ok=True)
    n_extracted = 0
    n_skipped = 0
    n_total = 0

    with zipfile.ZipFile(zip_path) as z:
        members = [m for m in z.infolist() if not m.is_dir()]
        n_total = len(members)
        for info in members:
            name = info.filename
            if name.startswith(ZIP_INTERNAL_PREFIX):
                name = name[len(ZIP_INTERNAL_PREFIX):]
            target = dest_dir / name
            if target.exists() and target.stat().st_size == info.file_size:
                n_skipped += 1
                continue
            with z.open(info) as src, open(target, "wb") as dst:
                while True:
                    buf = src.read(READ_CHUNK)
                    if not buf:
                        break
                    dst.write(buf)
            n_extracted += 1

    return {
        "total_in_zip": n_total,
        "extracted": n_extracted,
        "skipped_existing": n_skipped,
    }


def main() -> None:
    stats = extract_xdv_test_videos()
    print("=== XD-V test videos extraction ===")
    for key, value in stats.items():
        print(f"  {key:20s}: {value}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import sys
from pathlib import Path

import rarfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import MENDELEY_SMOKER_RAR_PATH, PROCESSED_DIR

# Mendeley Smoker Detection (CC BY 4.0, Khan et al., Sensors 2022,
# doi:10.17632/j45dj8bgfc.1) ships 1,120 images split by **filename
# prefix** (smoking_*.jpg = 560, notsmoking_*.jpg = 560). The on-disk
# layout uses Training/Validation/Testing as the *split* axis, not the
# class axis. We only need the Smoking class — it is merged into
# ``smoking/cigarette/`` as plain auxiliary supervision. notsmoking_
# files are intentionally dropped.

SMOKING_ROOT: Path = PROCESSED_DIR / "smoking"
TARGET_FOLDER: str = "cigarette"
SMOKING_FILENAME_PREFIX: str = "smoking_"
IMAGE_EXTS: tuple[str, ...] = (".jpg", ".jpeg", ".png")
FILENAME_PREFIX: str = "mds_"


def _is_smoking_filename(name: str) -> bool:
    """Whether the archive member is a smoking-class image by filename prefix.

    The dataset uses ``smoking_NNNN.jpg`` vs ``notsmoking_NNNN.jpg`` to
    distinguish classes. ``startswith("smoking_")`` correctly excludes
    ``notsmoking_`` (which starts with ``n``) without an extra guard.
    """
    return Path(name).name.lower().startswith(SMOKING_FILENAME_PREFIX)


def extract_mendeley_smoker(
    rar_path: Path | None = None,
    dest_root: Path = SMOKING_ROOT,
) -> dict[str, int]:
    """Copy Mendeley Smoker Detection (Smoking class only) into smoking/cigarette/.

    Requires an ``unrar`` / ``bsdtar`` / ``7z`` backend on PATH (see
    rarfile docs). Filenames are prefixed with ``mds_``.
    """
    if rar_path is None:
        rar_path = MENDELEY_SMOKER_RAR_PATH
    if not rar_path.exists():
        raise FileNotFoundError(f"Mendeley Smoker rar not found: {rar_path}")

    (dest_root / TARGET_FOLDER).mkdir(parents=True, exist_ok=True)

    total_images = 0
    skipped_not_smoking = 0
    saved = 0

    with rarfile.RarFile(rar_path) as r:
        for name in r.namelist():
            if not name.lower().endswith(IMAGE_EXTS):
                continue
            total_images += 1
            if not _is_smoking_filename(name):
                skipped_not_smoking += 1
                continue
            img_bytes = r.read(name)
            dst_name = f"{FILENAME_PREFIX}{Path(name).name}"
            dst = dest_root / TARGET_FOLDER / dst_name
            if dst.exists():
                continue
            dst.write_bytes(img_bytes)
            saved += 1

    return {
        "total_images_scanned": total_images,
        "skipped_non_smoking_class": skipped_not_smoking,
        TARGET_FOLDER: saved,
    }


def main() -> None:
    stats = extract_mendeley_smoker()
    print("=== Mendeley Smoker extraction ===")
    for key, value in stats.items():
        print(f"  {key:22s}: {value}")


if __name__ == "__main__":
    main()

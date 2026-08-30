from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import PROCESSED_DIR, ROBOFLOW_SMOKING_DRINKING_ZIP_PATH

# YOLO class index → destination folder.
# Source class list (data.yaml `names`):
#   0: drinking, 1: smoking
# Labels are YOLOv8-OBB (4-vertex polygons), but the first whitespace
# token is still the class index — the existing line parser is reused.
ROBOFLOW_SMOKING_CLASS_TO_FOLDER: dict[int, str] = {
    1: "cigarette",  # Roboflow "smoking" annotates the smoking act → cigarette folder
}

ROBOFLOW_DRINKING_CLASS_TO_FOLDER: dict[int, str] = {
    0: "alcohol",  # Roboflow "drinking" annotates the drinking act → alcohol folder
}

SMOKING_ROOT: Path = PROCESSED_DIR / "smoking"
DRINKING_ROOT: Path = PROCESSED_DIR / "drinking"
SPLITS: tuple[str, ...] = ("train", "valid", "test")
FILENAME_PREFIX: str = "rfsd_"


def parse_yolo_classes(label_text: str) -> set[int]:
    """Return distinct YOLO class indices present in a label file."""
    classes: set[int] = set()
    for line in label_text.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        try:
            classes.add(int(parts[0]))
        except ValueError:
            continue
    return classes


def extract_roboflow_smoking(
    zip_path: Path | None = None,
    dest_root: Path = SMOKING_ROOT,
) -> dict[str, int]:
    """Copy Roboflow S&D smoking-class images + OBB labels into ``smoking/cigarette/``.

    The original ``*.txt`` label file (YOLOv8-OBB 4-vertex polygon: ``class
    x1 y1 x2 y2 x3 y3 x4 y4``) is copied alongside each image as
    ``rfsd_<stem>.txt``. Filenames are prefixed with ``rfsd_`` to distinguish
    from HOD (``hod_``) and Mendeley (``mds_``) sources.
    """
    if zip_path is None:
        zip_path = ROBOFLOW_SMOKING_DRINKING_ZIP_PATH
    if not zip_path.exists():
        raise FileNotFoundError(f"Roboflow S&D zip not found: {zip_path}")

    target_folders: set[str] = set(ROBOFLOW_SMOKING_CLASS_TO_FOLDER.values())
    for folder in target_folders:
        (dest_root / folder).mkdir(parents=True, exist_ok=True)

    saved_per_class: dict[str, int] = {f: 0 for f in target_folders}
    total_scanned = 0
    no_label_count = 0
    multi_class_count = 0
    matched_images = 0
    labels_copied = 0

    with zipfile.ZipFile(zip_path) as z:
        for split in SPLITS:
            img_prefix = f"{split}/images/"
            label_prefix = f"{split}/labels/"
            for info in z.infolist():
                if not info.filename.startswith(img_prefix):
                    continue
                if not info.filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                total_scanned += 1
                img_name = Path(info.filename).name
                stem = Path(info.filename).stem
                label_path = label_prefix + stem + ".txt"

                try:
                    label_bytes = z.read(label_path)
                except KeyError:
                    no_label_count += 1
                    continue
                label_text = label_bytes.decode("utf-8")

                classes = parse_yolo_classes(label_text)
                matching: set[str] = {
                    ROBOFLOW_SMOKING_CLASS_TO_FOLDER[c]
                    for c in classes
                    if c in ROBOFLOW_SMOKING_CLASS_TO_FOLDER
                }
                if not matching:
                    continue
                if len(matching) > 1:
                    multi_class_count += 1
                matched_images += 1

                img_bytes = z.read(info.filename)
                dst_name = f"{FILENAME_PREFIX}{img_name}"
                dst_label_name = f"{FILENAME_PREFIX}{stem}.txt"
                for folder in matching:
                    dst = dest_root / folder / dst_name
                    if not dst.exists():
                        dst.write_bytes(img_bytes)
                        saved_per_class[folder] += 1
                    dst_label = dest_root / folder / dst_label_name
                    if not dst_label.exists():
                        dst_label.write_bytes(label_bytes)
                        labels_copied += 1

    return {
        "total_scanned": total_scanned,
        "no_label_skipped": no_label_count,
        "matched_images": matched_images,
        "multi_class_images": multi_class_count,
        "labels_copied": labels_copied,
        **saved_per_class,
    }


def extract_roboflow_drinking(
    zip_path: Path | None = None,
    dest_root: Path = DRINKING_ROOT,
) -> dict[str, int]:
    """Copy Roboflow S&D drinking-class images + OBB labels into ``drinking/alcohol/``.

    Same scan pattern as :func:`extract_roboflow_smoking`.
    """
    if zip_path is None:
        zip_path = ROBOFLOW_SMOKING_DRINKING_ZIP_PATH
    if not zip_path.exists():
        raise FileNotFoundError(f"Roboflow S&D zip not found: {zip_path}")

    target_folders: set[str] = set(ROBOFLOW_DRINKING_CLASS_TO_FOLDER.values())
    for folder in target_folders:
        (dest_root / folder).mkdir(parents=True, exist_ok=True)

    saved_per_class: dict[str, int] = {f: 0 for f in target_folders}
    total_scanned = 0
    no_label_count = 0
    multi_class_count = 0
    matched_images = 0
    labels_copied = 0

    with zipfile.ZipFile(zip_path) as z:
        for split in SPLITS:
            img_prefix = f"{split}/images/"
            label_prefix = f"{split}/labels/"
            for info in z.infolist():
                if not info.filename.startswith(img_prefix):
                    continue
                if not info.filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                total_scanned += 1
                img_name = Path(info.filename).name
                stem = Path(info.filename).stem
                label_path = label_prefix + stem + ".txt"

                try:
                    label_bytes = z.read(label_path)
                except KeyError:
                    no_label_count += 1
                    continue
                label_text = label_bytes.decode("utf-8")

                classes = parse_yolo_classes(label_text)
                matching: set[str] = {
                    ROBOFLOW_DRINKING_CLASS_TO_FOLDER[c]
                    for c in classes
                    if c in ROBOFLOW_DRINKING_CLASS_TO_FOLDER
                }
                if not matching:
                    continue
                if len(matching) > 1:
                    multi_class_count += 1
                matched_images += 1

                img_bytes = z.read(info.filename)
                dst_name = f"{FILENAME_PREFIX}{img_name}"
                dst_label_name = f"{FILENAME_PREFIX}{stem}.txt"
                for folder in matching:
                    dst = dest_root / folder / dst_name
                    if not dst.exists():
                        dst.write_bytes(img_bytes)
                        saved_per_class[folder] += 1
                    dst_label = dest_root / folder / dst_label_name
                    if not dst_label.exists():
                        dst_label.write_bytes(label_bytes)
                        labels_copied += 1

    return {
        "total_scanned": total_scanned,
        "no_label_skipped": no_label_count,
        "matched_images": matched_images,
        "multi_class_images": multi_class_count,
        "labels_copied": labels_copied,
        **saved_per_class,
    }


def main() -> None:
    print("=== Roboflow S&D smoking extraction ===")
    for key, value in extract_roboflow_smoking().items():
        print(f"  {key:22s}: {value}")
    print("=== Roboflow S&D drinking extraction ===")
    for key, value in extract_roboflow_drinking().items():
        print(f"  {key:22s}: {value}")


if __name__ == "__main__":
    main()

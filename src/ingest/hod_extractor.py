from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import HOD_ZIP_PATH, PROCESSED_DIR

# YOLO class index → violence sub-folder. Other HOD classes
# (alcohol=0, insulting_gesture=1, cigarette=3) belong to different
# categories and are intentionally skipped here.
HOD_CLASS_TO_FOLDER: dict[int, str] = {
    2: "상해(피)",  # blood
    4: "총기",       # gun
    5: "흉기",       # knife
}

# HOD class index → smoking sub-folder. cigarette (3) only.
HOD_SMOKING_CLASS_TO_FOLDER: dict[int, str] = {
    3: "cigarette",
}

# HOD class index → drinking sub-folder. alcohol (0) only.
HOD_DRINKING_CLASS_TO_FOLDER: dict[int, str] = {
    0: "alcohol",
}

VIOLENCE_ROOT: Path = PROCESSED_DIR / "violence"
SMOKING_ROOT: Path = PROCESSED_DIR / "smoking"
DRINKING_ROOT: Path = PROCESSED_DIR / "drinking"
SPLITS: tuple[str, ...] = ("training", "validation", "test")


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


def extract_hod_violence(
    zip_path: Path | None = None,
    dest_root: Path = VIOLENCE_ROOT,
) -> dict[str, int]:
    if zip_path is None:
        zip_path = HOD_ZIP_PATH
    """Copy HOD images for violence-relevant classes from zip → folder layout.

    Multi-class images (e.g. gun + blood bboxes in one frame) are copied
    into every matching class folder. Source filename is prefixed with
    ``hod_`` to avoid collision with XD-V keyframes already in the folder.
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"HOD zip not found: {zip_path}")

    for folder in HOD_CLASS_TO_FOLDER.values():
        (dest_root / folder).mkdir(parents=True, exist_ok=True)

    saved_per_class: dict[str, int] = {f: 0 for f in HOD_CLASS_TO_FOLDER.values()}
    total_scanned = 0
    no_label_count = 0
    multi_class_count = 0
    matched_images = 0

    with zipfile.ZipFile(zip_path) as z:
        for split in SPLITS:
            img_prefix = f"yolo_all/{split}/images/"
            label_prefix = f"yolo_all/{split}/labels/"
            for info in z.infolist():
                if not info.filename.startswith(img_prefix):
                    continue
                if not info.filename.endswith(".jpg"):
                    continue
                total_scanned += 1
                img_name = Path(info.filename).name
                label_path = label_prefix + Path(info.filename).stem + ".txt"

                try:
                    label_text = z.read(label_path).decode("utf-8")
                except KeyError:
                    no_label_count += 1
                    continue

                classes = parse_yolo_classes(label_text)
                matching: set[str] = {
                    HOD_CLASS_TO_FOLDER[c] for c in classes if c in HOD_CLASS_TO_FOLDER
                }
                if not matching:
                    continue
                if len(matching) > 1:
                    multi_class_count += 1
                matched_images += 1

                img_bytes = z.read(info.filename)
                dst_name = f"hod_{img_name}"
                for folder in matching:
                    dst = dest_root / folder / dst_name
                    if dst.exists():
                        continue
                    dst.write_bytes(img_bytes)
                    saved_per_class[folder] += 1

    return {
        "total_scanned": total_scanned,
        "no_label_skipped": no_label_count,
        "matched_images": matched_images,
        "multi_class_images": multi_class_count,
        **saved_per_class,
    }


def extract_hod_smoking(
    zip_path: Path | None = None,
    dest_root: Path = SMOKING_ROOT,
) -> dict[str, int]:
    """Copy HOD cigarette images + YOLO bbox labels into ``smoking/cigarette/``.

    Same scan pattern as :func:`extract_hod_violence` but with a different
    class-to-folder map and destination root. The original ``*.txt`` label
    file (YOLOv5 format: ``class cx cy w h`` per line) is copied alongside
    each image as ``hod_<stem>.txt`` so detection-style training can use
    the bboxes. Filenames keep the ``hod_`` prefix to remain attributable
    across categories.
    """
    if zip_path is None:
        zip_path = HOD_ZIP_PATH
    if not zip_path.exists():
        raise FileNotFoundError(f"HOD zip not found: {zip_path}")

    for folder in HOD_SMOKING_CLASS_TO_FOLDER.values():
        (dest_root / folder).mkdir(parents=True, exist_ok=True)

    saved_per_class: dict[str, int] = {f: 0 for f in HOD_SMOKING_CLASS_TO_FOLDER.values()}
    total_scanned = 0
    no_label_count = 0
    multi_class_count = 0
    matched_images = 0
    labels_copied = 0

    with zipfile.ZipFile(zip_path) as z:
        for split in SPLITS:
            img_prefix = f"yolo_all/{split}/images/"
            label_prefix = f"yolo_all/{split}/labels/"
            for info in z.infolist():
                if not info.filename.startswith(img_prefix):
                    continue
                if not info.filename.endswith(".jpg"):
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
                    HOD_SMOKING_CLASS_TO_FOLDER[c]
                    for c in classes
                    if c in HOD_SMOKING_CLASS_TO_FOLDER
                }
                if not matching:
                    continue
                if len(matching) > 1:
                    multi_class_count += 1
                matched_images += 1

                img_bytes = z.read(info.filename)
                dst_name = f"hod_{img_name}"
                dst_label_name = f"hod_{stem}.txt"
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


def extract_hod_drinking(
    zip_path: Path | None = None,
    dest_root: Path = DRINKING_ROOT,
) -> dict[str, int]:
    """Copy HOD alcohol images + YOLO bbox labels into ``drinking/alcohol/``.

    Same scan pattern as :func:`extract_hod_smoking`.
    """
    if zip_path is None:
        zip_path = HOD_ZIP_PATH
    if not zip_path.exists():
        raise FileNotFoundError(f"HOD zip not found: {zip_path}")

    for folder in HOD_DRINKING_CLASS_TO_FOLDER.values():
        (dest_root / folder).mkdir(parents=True, exist_ok=True)

    saved_per_class: dict[str, int] = {f: 0 for f in HOD_DRINKING_CLASS_TO_FOLDER.values()}
    total_scanned = 0
    no_label_count = 0
    multi_class_count = 0
    matched_images = 0
    labels_copied = 0

    with zipfile.ZipFile(zip_path) as z:
        for split in SPLITS:
            img_prefix = f"yolo_all/{split}/images/"
            label_prefix = f"yolo_all/{split}/labels/"
            for info in z.infolist():
                if not info.filename.startswith(img_prefix):
                    continue
                if not info.filename.endswith(".jpg"):
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
                    HOD_DRINKING_CLASS_TO_FOLDER[c]
                    for c in classes
                    if c in HOD_DRINKING_CLASS_TO_FOLDER
                }
                if not matching:
                    continue
                if len(matching) > 1:
                    multi_class_count += 1
                matched_images += 1

                img_bytes = z.read(info.filename)
                dst_name = f"hod_{img_name}"
                dst_label_name = f"hod_{stem}.txt"
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
    stats = extract_hod_violence()
    print("=== HOD violence extraction ===")
    for key, value in stats.items():
        print(f"  {key:20s}: {value}")


if __name__ == "__main__":
    main()

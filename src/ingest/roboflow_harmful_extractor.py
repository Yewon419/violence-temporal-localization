from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import PROCESSED_DIR, ROBOFLOW_HARMFUL_ZIP_PATH

# YOLO class index → violence sub-folder.
# Source class list (data.yaml `names`):
#   [Axe, Chainsaw, Chisel, Coin, Drink, Dumbbell,
#    Fork, Hammer, Knife, Scissors, Screwdriver, Stapler]
ROBOFLOW_CLASS_TO_FOLDER: dict[int, str] = {
    0: "둔기",   # Axe — blunt-force usage common in film violence
    1: "흉기",   # Chainsaw — rotating blade, edged
    2: "흉기",   # Chisel
    5: "둔기",   # Dumbbell
    6: "흉기",   # Fork
    7: "둔기",   # Hammer
    8: "흉기",   # Knife
    9: "흉기",   # Scissors
    10: "흉기",  # Screwdriver
    # 3 Coin / 4 Drink / 11 Stapler — not weapons, skipped
}

VIOLENCE_ROOT: Path = PROCESSED_DIR / "violence"
SPLITS: tuple[str, ...] = ("train", "valid", "test")
FILENAME_PREFIX: str = "rfh_"


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


def extract_roboflow_harmful(
    zip_path: Path | None = None,
    dest_root: Path = VIOLENCE_ROOT,
) -> dict[str, int]:
    """Copy violence-relevant Roboflow Harmful Objects images into folders.

    Multi-class images are copied into every matching class folder
    (둔기 + 흉기 both, etc). Filename is prefixed with ``rfh_`` to
    distinguish from XD-V (no prefix) and HOD (``hod_``) sources.
    """
    if zip_path is None:
        zip_path = ROBOFLOW_HARMFUL_ZIP_PATH
    if not zip_path.exists():
        raise FileNotFoundError(f"Roboflow zip not found: {zip_path}")

    target_folders: set[str] = set(ROBOFLOW_CLASS_TO_FOLDER.values())
    for folder in target_folders:
        (dest_root / folder).mkdir(parents=True, exist_ok=True)

    saved_per_class: dict[str, int] = {f: 0 for f in target_folders}
    total_scanned = 0
    no_label_count = 0
    multi_class_count = 0
    matched_images = 0

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
                label_path = label_prefix + Path(info.filename).stem + ".txt"

                try:
                    label_text = z.read(label_path).decode("utf-8")
                except KeyError:
                    no_label_count += 1
                    continue

                classes = parse_yolo_classes(label_text)
                matching: set[str] = {
                    ROBOFLOW_CLASS_TO_FOLDER[c]
                    for c in classes
                    if c in ROBOFLOW_CLASS_TO_FOLDER
                }
                if not matching:
                    continue
                if len(matching) > 1:
                    multi_class_count += 1
                matched_images += 1

                img_bytes = z.read(info.filename)
                dst_name = f"{FILENAME_PREFIX}{img_name}"
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


def main() -> None:
    stats = extract_roboflow_harmful()
    print("=== Roboflow Harmful Objects extraction ===")
    for key, value in stats.items():
        print(f"  {key:20s}: {value}")


if __name__ == "__main__":
    main()

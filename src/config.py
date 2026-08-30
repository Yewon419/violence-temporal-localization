from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
ANNOTATED_DIR: Path = DATA_DIR / "annotated"

XDV_TEST_VIDEOS_DIR: Path = RAW_DIR / "xdviolence_test"
XDV_TEST_KEYFRAMES_DIR: Path = PROCESSED_DIR / "xdviolence_test"
XDV_TEST_ANNOTATIONS: Path = ANNOTATED_DIR / "xdv_test_annotations.txt"

# Downloaded source archives live under the user's Downloads folder by
# default so the codebase is portable across teammates' machines.
DOWNLOADS_DIR: Path = Path.home() / "Downloads"
XDV_TEST_VIDEOS_ZIP_PATH: Path = DOWNLOADS_DIR / "videos.zip"
HOD_ZIP_PATH: Path = DOWNLOADS_DIR / "yolo_v5_dataset.zip"
ROBOFLOW_HARMFUL_ZIP_PATH: Path = DOWNLOADS_DIR / "harmful objects.v1i.yolov8.zip"
ROBOFLOW_SMOKING_DRINKING_ZIP_PATH: Path = (
    DOWNLOADS_DIR / "Smoking and Drinking Detection.v2-test-yolov5m.yolov8-obb.zip"
)
MENDELEY_SMOKER_RAR_PATH: Path = DOWNLOADS_DIR / "Smoker Detection.rar"

DB_PATH: Path = PROJECT_ROOT / "movie_rating.sqlite"
SCHEMA_PATH: Path = PROJECT_ROOT / "src" / "db" / "schema.sql"

KEYFRAMES_PER_MINUTE: int = 30
FRAME_SIZE: int = 224

CATEGORIES: tuple[str, ...] = ("violence", "sexual", "smoking", "drinking", "horror", "drug")
ACTIVE_CATEGORIES: tuple[str, ...] = ("violence", "smoking", "drinking")

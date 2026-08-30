"""물리폭력 구간 어노테이션 MVP — Flask 백엔드.

흐름:
  1. mp4 업로드(또는 로컬 경로) → 2fps 프레임 추출 → images/{movie_id}/
  2. 프론트(index.html)에서 프레임 넘기며 단축키(1=violence, 2=neg_hard)로 구간 지정
  3. 저장 시 표시 안 된 구간을 neg_easy로 자동 채우고 scene_num 부여 → output/{movie_id}.txt

출력 한 줄 형식: [movie_id, scene_num, start_frame, end_frame, label]
  (frame index는 2fps 기준. label은 GT에 필수라 스펙에 추가함)
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

import cv2
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask.typing import ResponseReturnValue

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
OUTPUT_DIR = BASE_DIR / "output"
TARGET_FPS = 2.0
VALID_LABELS = frozenset({"violence", "neg_hard"})

app = Flask(__name__)

# movie_id -> {"saved": int, "total": int, "done": bool, "error": str}
PROGRESS: dict[str, dict[str, object]] = {}


@dataclass(frozen=True)
class Segment:
    """사람이 직접 찍은 구간 (violence 또는 neg_hard)."""

    start_frame: int
    end_frame: int
    label: str


@dataclass(frozen=True)
class Scene:
    """타임라인 전체를 빈틈없이 덮는 최종 scene (neg_easy 자동 포함)."""

    scene_num: int
    start_frame: int
    end_frame: int
    label: str


def safe_movie_id(name: str) -> str:
    """파일명 → 폴더/URL 안전 식별자. 한글(isalnum=True)은 보존, 특수문자만 '_'."""
    stem = Path(name).stem
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in stem)


def extract_frames(video_path: Path, movie_id: str) -> int:
    """video_path를 2fps로 샘플해 images/{movie_id}/frame_NNNNNN.jpg 저장. 저장 프레임 수 반환."""
    out_dir = IMAGES_DIR / movie_id
    out_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"영상을 열 수 없음: {video_path}")
    video_fps = float(capture.get(cv2.CAP_PROP_FPS))
    if video_fps <= 0.0:
        capture.release()
        raise ValueError(f"영상 fps가 비정상: {video_fps}")
    step = max(1, round(video_fps / TARGET_FPS))
    total_src = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    total_expected = max(1, total_src // step)
    PROGRESS[movie_id] = {"saved": 0, "total": total_expected, "done": False, "error": ""}
    saved = 0
    source_idx = 0
    while True:
        # keep 프레임만 retrieve(전체 decode), 나머지는 grab으로 스킵 → 대폭 빠름
        if not capture.grab():
            break
        if source_idx % step == 0:
            ok, frame = capture.retrieve()
            if ok:
                # cv2.imwrite는 윈도우 한글 경로에서 실패 → imencode + write_bytes
                encoded, buffer = cv2.imencode(".jpg", frame)
                if encoded:
                    (out_dir / f"frame_{saved:06d}.jpg").write_bytes(buffer.tobytes())
                    saved += 1
                    if saved % 20 == 0:
                        PROGRESS[movie_id]["saved"] = saved
        source_idx += 1
    capture.release()
    PROGRESS[movie_id] = {"saved": saved, "total": total_expected, "done": True, "error": ""}
    return saved


def count_frames(movie_id: str) -> int:
    folder = IMAGES_DIR / movie_id
    if not folder.is_dir():
        return 0
    return sum(1 for _ in folder.glob("frame_*.jpg"))


def build_scenes(segments: list[Segment], n_frames: int) -> list[Scene]:
    """사람이 찍은 구간 사이/바깥의 빈 구간을 neg_easy로 채워 0..n_frames-1을 전부 덮고 scene_num 부여."""
    marked = sorted(segments, key=lambda s: s.start_frame)
    scenes: list[Scene] = []
    cursor = 0
    num = 0
    for seg in marked:
        if seg.start_frame < cursor:
            raise ValueError(f"구간 겹침: frame {seg.start_frame} (이전 구간이 {cursor - 1}까지 점유)")
        if seg.start_frame > cursor:
            scenes.append(Scene(num, cursor, seg.start_frame - 1, "neg_easy"))
            num += 1
        scenes.append(Scene(num, seg.start_frame, seg.end_frame, seg.label))
        num += 1
        cursor = seg.end_frame + 1
    if cursor <= n_frames - 1:
        scenes.append(Scene(num, cursor, n_frames - 1, "neg_easy"))
    return scenes


def parse_segments(raw: object) -> list[Segment]:
    if not isinstance(raw, list):
        raise ValueError("segments는 리스트여야 함")
    segments: list[Segment] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("segment 항목은 객체여야 함")
        label = str(item.get("label", ""))
        if label not in VALID_LABELS:
            raise ValueError(f"허용되지 않은 label: {label!r}")
        start = int(item["start_frame"])
        end = int(item["end_frame"])
        if start > end:
            raise ValueError(f"start({start}) > end({end})")
        segments.append(Segment(start, end, label))
    return segments


@app.get("/")
def index() -> ResponseReturnValue:
    return render_template("index.html")


@app.get("/movies")
def list_movies() -> ResponseReturnValue:
    """이미 추출된 영화 목록(이어서 작업용)."""
    if not IMAGES_DIR.is_dir():
        return jsonify([])
    movies = [
        {"movie_id": folder.name, "n_frames": count_frames(folder.name)}
        for folder in sorted(IMAGES_DIR.iterdir())
        if folder.is_dir()
    ]
    return jsonify(movies)


def _run_extract(video_path: Path, movie_id: str) -> None:
    """백그라운드 추출 스레드. 예외는 삼키지 않고 PROGRESS로 노출(스레드 밖 전파 불가)."""
    try:
        extract_frames(video_path, movie_id)
    except Exception as exc:  # noqa: BLE001 - 스레드 경계: 진행률로 surface
        PROGRESS[movie_id] = {"saved": 0, "total": 1, "done": True, "error": str(exc)}


@app.post("/extract")
def extract() -> ResponseReturnValue:
    path_str = request.form.get("path", "").strip()
    upload = request.files.get("file")
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    if path_str:
        video_path = Path(path_str)
        if not video_path.is_file():
            return jsonify({"error": f"경로에 파일이 없음: {path_str}"}), 400
        movie_id = safe_movie_id(video_path.name)
    elif upload is not None and upload.filename:
        movie_id = safe_movie_id(upload.filename)
        video_path = IMAGES_DIR / f"_upload_{movie_id}.mp4"
        upload.save(str(video_path))
    else:
        return jsonify({"error": "파일 업로드 또는 경로 입력 필요"}), 400

    PROGRESS[movie_id] = {"saved": 0, "total": 1, "done": False, "error": ""}
    threading.Thread(target=_run_extract, args=(video_path, movie_id), daemon=True).start()
    return jsonify({"movie_id": movie_id})


@app.get("/progress/<movie_id>")
def progress(movie_id: str) -> ResponseReturnValue:
    default: dict[str, object] = {"saved": 0, "total": 1, "done": False, "error": "작업 없음"}
    return jsonify(PROGRESS.get(movie_id, default))


@app.get("/images/<movie_id>/<path:filename>")
def serve_frame(movie_id: str, filename: str) -> ResponseReturnValue:
    return send_from_directory(IMAGES_DIR / movie_id, filename)


@app.post("/save")
def save() -> ResponseReturnValue:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "잘못된 JSON"}), 400
    movie_id = str(data.get("movie_id", "")).strip()
    if not movie_id:
        return jsonify({"error": "movie_id 없음"}), 400
    n_frames = int(data.get("n_frames", 0))
    try:
        segments = parse_segments(data.get("segments"))
        scenes = build_scenes(segments, n_frames)
    except (ValueError, KeyError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{movie_id}.txt"
    lines = [
        f"[{movie_id}, {sc.scene_num}, {sc.start_frame}, {sc.end_frame}, {sc.label}]"
        for sc in scenes
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return jsonify({"saved": str(out_path), "scenes": len(scenes)})


@app.get("/load/<movie_id>")
def load(movie_id: str) -> ResponseReturnValue:
    """기존 output/{movie_id}.txt 에서 사람이 찍은 구간(violence/neg_hard)만 복원. neg_easy는 파생이라 제외."""
    out_path = OUTPUT_DIR / f"{movie_id}.txt"
    restored: list[dict[str, object]] = []
    if out_path.is_file():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            row = line.strip().strip("[]").strip()
            if not row:
                continue
            parts = [p.strip() for p in row.split(",")]
            if len(parts) < 5 or parts[-1] not in VALID_LABELS:
                continue
            try:
                restored.append({
                    "start_frame": int(parts[-3]),
                    "end_frame": int(parts[-2]),
                    "label": parts[-1],
                })
            except ValueError:
                continue
    return jsonify({"segments": restored})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

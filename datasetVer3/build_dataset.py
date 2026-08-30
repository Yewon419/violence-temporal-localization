"""violence_annotator 출력(images/·output/)을 datasetVer3 구조로 조립한다.

하는 일:
  1. output/{한글_id}.txt 파싱 → scene 리스트
  2. images/{한글_id}/ 프레임을 frames/{ascii_id}/ 로 복사
  3. annotations/raw_txt/{ascii_id}.txt 로 원본 txt 보존
  4. annotations/annotations.jsonl 생성 (영상당 1줄, segment nested)
  5. annotations/videos.jsonl 의 n_frames·annotated 갱신

HF 업로드는 하지 않는다(별도 push 단계). 어노테이션이 된 영상만 처리한다.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, replace
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ANNOTATOR_DIR = BASE_DIR.parent / "violence_annotator"
IMAGES_DIR = ANNOTATOR_DIR / "images"
OUTPUT_DIR = ANNOTATOR_DIR / "output"
FRAMES_DIR = BASE_DIR / "frames"
ANN_DIR = BASE_DIR / "annotations"
RAW_TXT_DIR = ANN_DIR / "raw_txt"
VIDEOS_JSONL = ANN_DIR / "videos.jsonl"
ANNOTATIONS_JSONL = ANN_DIR / "annotations.jsonl"

VALID_LABELS = frozenset({"violence", "neg_hard", "neg_easy"})

# 폴더당 최대 프레임. HF/git는 폴더당 파일 1만 개 넘으면 느려짐.
# 프레임 수가 이 값 이하면 frames/{video_id}/frame_NNNNNN.jpg 로 그냥 한 폴더(flat).
# 초과하는 (아주 긴) 영상만 frames/{video_id}/{shard}/... 로 쪼갠다.
# shard 폴더명 = 그 샤드의 시작 프레임(6자리). 예: 10240번 → 폴더 "010000".
FRAMES_PER_SHARD = 10000

# 어노테이터(images/·output/)의 한글 키 → 데이터셋 ascii video_id
SOURCE_MAP: dict[str, str] = {
    "신세계": "sinsegye",
    "범죄도시": "beomjoedosi",
    "비열한거리": "biyeolhan_geori",
    "고지전": "gojijeon",
    "친구": "chingu",
    "서울의봄": "seoului_bom",
    "군체": "gunche",
    "달콤한인생": "dalkomhan_insaeng",
    "범죄도시_싸움씬_버스": "beomjoedosi_fight_bus",
    "범죄도시_싸움씬_화장실": "beomjoedosi_fight_toilet",
}


@dataclass(frozen=True)
class Scene:
    scene_num: int
    start_frame: int
    end_frame: int
    label: str


@dataclass(frozen=True)
class VideoAnnotation:
    video_id: str
    title: str
    n_frames: int
    scenes: tuple[Scene, ...]


@dataclass(frozen=True)
class VideoMeta:
    video_id: str
    title: str
    movie: str
    youtube_id: str
    source_url: str
    width: int
    height: int
    codec: str
    extract_fps: int
    duration_sec: float
    n_frames: int | None
    annotated: bool


def parse_raw_txt(text: str, source_id: str) -> tuple[Scene, ...]:
    """어노테이터 txt 한 본문 → Scene 튜플. 형식 위반은 즉시 raise."""
    scenes: list[Scene] = []
    for line in text.splitlines():
        row = line.strip().strip("[]").strip()
        if not row:
            continue
        parts = [p.strip() for p in row.split(",")]
        if len(parts) < 5:
            raise ValueError(f"{source_id}: 필드 부족 → {line!r}")
        label = parts[-1]
        if label not in VALID_LABELS:
            raise ValueError(f"{source_id}: 허용되지 않은 label {label!r}")
        scenes.append(
            Scene(
                scene_num=int(parts[-4]),
                start_frame=int(parts[-3]),
                end_frame=int(parts[-2]),
                label=label,
            )
        )
    if not scenes:
        raise ValueError(f"{source_id}: scene이 비어있음")
    return tuple(scenes)


def load_videos(path: Path) -> list[VideoMeta]:
    """videos.jsonl → VideoMeta 리스트(파일 순서 보존)."""
    metas: list[VideoMeta] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        n_frames_raw = row["n_frames"]
        metas.append(
            VideoMeta(
                video_id=str(row["video_id"]),
                title=str(row["title"]),
                movie=str(row["movie"]),
                youtube_id=str(row["youtube_id"]),
                source_url=str(row["source_url"]),
                width=int(row["width"]),
                height=int(row["height"]),
                codec=str(row["codec"]),
                extract_fps=int(row["extract_fps"]),
                duration_sec=float(row["duration_sec"]),
                n_frames=None if n_frames_raw is None else int(n_frames_raw),
                annotated=bool(row["annotated"]),
            )
        )
    return metas


def frame_number(jpg: Path) -> int:
    """frame_001024.jpg → 1024."""
    return int(jpg.stem.split("_")[-1])


def shard_name(frame: int) -> str:
    """프레임 번호 → 하위 폴더명(그 샤드의 시작 프레임, 6자리)."""
    return f"{(frame // FRAMES_PER_SHARD) * FRAMES_PER_SHARD:06d}"


def copy_frames(src_dir: Path, dst_dir: Path) -> int:
    """images/{한글_id}/ 의 frame_*.jpg 를 frames/{ascii_id}/ 로 복사. 복사 수 반환.

    프레임 ≤ FRAMES_PER_SHARD: 한 폴더(flat). 초과: {shard}/ 하위 폴더로 분할.
    """
    jpgs = sorted(src_dir.glob("frame_*.jpg"))
    if not jpgs:
        raise ValueError(f"프레임 0장: {src_dir}")
    sharded = len(jpgs) > FRAMES_PER_SHARD
    for jpg in jpgs:
        target = dst_dir / shard_name(frame_number(jpg)) if sharded else dst_dir
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(jpg, target / jpg.name)
    return len(jpgs)


def write_annotations(path: Path, annotations: list[VideoAnnotation]) -> None:
    lines: list[str] = []
    for ann in annotations:
        record = {
            "video_id": ann.video_id,
            "title": ann.title,
            "fps": 2,
            "n_frames": ann.n_frames,
            "segments": [
                {
                    "scene_num": sc.scene_num,
                    "start_frame": sc.start_frame,
                    "end_frame": sc.end_frame,
                    "label": sc.label,
                }
                for sc in ann.scenes
            ],
        }
        lines.append(json.dumps(record, ensure_ascii=False))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_videos(path: Path, metas: list[VideoMeta]) -> None:
    lines: list[str] = []
    for m in metas:
        record = {
            "video_id": m.video_id,
            "title": m.title,
            "movie": m.movie,
            "youtube_id": m.youtube_id,
            "source_url": m.source_url,
            "width": m.width,
            "height": m.height,
            "codec": m.codec,
            "extract_fps": m.extract_fps,
            "duration_sec": m.duration_sec,
            "n_frames": m.n_frames,
            "annotated": m.annotated,
        }
        lines.append(json.dumps(record, ensure_ascii=False))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not OUTPUT_DIR.is_dir():
        raise SystemExit(f"어노테이터 output 폴더 없음: {OUTPUT_DIR}")
    RAW_TXT_DIR.mkdir(parents=True, exist_ok=True)

    metas = load_videos(VIDEOS_JSONL)
    by_id = {m.video_id: m for m in metas}

    annotations: list[VideoAnnotation] = []
    for source_id, video_id in SOURCE_MAP.items():
        txt_path = OUTPUT_DIR / f"{source_id}.txt"
        if not txt_path.is_file():
            continue
        if video_id not in by_id:
            raise SystemExit(f"videos.jsonl 에 없는 video_id: {video_id}")

        raw = txt_path.read_text(encoding="utf-8")
        scenes = parse_raw_txt(raw, source_id)

        src_frames = IMAGES_DIR / source_id
        if src_frames.is_dir():
            n_frames = copy_frames(src_frames, FRAMES_DIR / video_id)
        else:
            n_frames = scenes[-1].end_frame + 1  # 추출 전: 어노테이션 길이로 대체

        (RAW_TXT_DIR / f"{video_id}.txt").write_text(raw, encoding="utf-8")
        title = by_id[video_id].title
        annotations.append(VideoAnnotation(video_id, title, n_frames, scenes))
        by_id[video_id] = replace(by_id[video_id], n_frames=n_frames, annotated=True)

    if not annotations:
        raise SystemExit("처리할 어노테이션(output/*.txt)이 없음")

    updated = [by_id[m.video_id] for m in metas]
    write_annotations(ANNOTATIONS_JSONL, annotations)
    write_videos(VIDEOS_JSONL, updated)
    print(f"완료: {len(annotations)}편 → {ANNOTATIONS_JSONL.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()

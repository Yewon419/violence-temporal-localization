"""Grounding DINO inference — fps=1 frame에 zero-shot bbox.

대표님 결정:
- env: CPU torch (GPU 없음)
- prompt: "cigarette. smoking. drinking. bottle. cup."
- sample: 영상당 균등 100장

출력:
    data/processed/gd_demo_fps/{video_id}/{frame_stem}.json
    data/processed/gd_demo_fps/{video_id}/{frame_stem}_vis.jpg

실행:
    .venv\\Scripts\\python.exe scripts\\gd_dry_run.py vyXEi00PVrw 69RJZ7TwDrQ
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

import torch
from PIL import Image, ImageDraw
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import PROCESSED_DIR

FRAMES_DIR: Path = PROCESSED_DIR / "yt_drama_frames"
GD_OUT: Path = PROCESSED_DIR / "gd_demo_fps_v2"

SAMPLE_SIZE: int = 100
PROMPT: str = (
    "cigarette. smoking. drinking. bottle. cup. "
    "knife. gun. hammer. baseball bat. blood. "
    "fighting. shooting. riot. abuse. explosion. car accident."
)
MODEL_ID: str = "IDEA-Research/grounding-dino-tiny"
BOX_THRESHOLD: float = 0.25
TEXT_THRESHOLD: float = 0.25


def sample_frames(frames_dir: Path, video_id: str, n: int) -> list[Path]:
    all_frames = sorted(frames_dir.glob(f"{video_id}_frame_*.jpg"))
    if not all_frames:
        raise FileNotFoundError(f"no frames for {video_id} in {frames_dir}")
    if len(all_frames) <= n:
        return all_frames
    step = len(all_frames) / n
    return [all_frames[int(i * step)] for i in range(n)]


def draw_boxes(
    image: Image.Image,
    boxes: list[list[float]],
    scores: list[float],
    labels: list[str],
) -> Image.Image:
    vis = image.copy()
    draw = ImageDraw.Draw(vis)
    for box, score, label in zip(boxes, scores, labels, strict=False):
        x1, y1, x2, y2 = box
        draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
        text = f"{label}: {score:.2f}"
        draw.text((x1, max(0, y1 - 15)), text, fill="red")
    return vis


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_ids", nargs="+", help="video IDs to process")
    parser.add_argument(
        "--frames-dir", type=Path, default=FRAMES_DIR, help="dir of {id}_frame_*.jpg"
    )
    parser.add_argument("--out-dir", type=Path, default=GD_OUT, help="output root")
    parser.add_argument("--prompt", default=PROMPT, help="Grounding DINO text prompt")
    parser.add_argument(
        "--sample", type=int, default=SAMPLE_SIZE, help="frames sampled per video"
    )
    parser.add_argument("--box-threshold", type=float, default=BOX_THRESHOLD)
    parser.add_argument("--text-threshold", type=float, default=TEXT_THRESHOLD)
    args = parser.parse_args()

    print(f"loading model {MODEL_ID}...")
    processor = AutoProcessor.from_pretrained(MODEL_ID)  # type: ignore[no-untyped-call]
    model = AutoModelForZeroShotObjectDetection.from_pretrained(MODEL_ID)
    device = "cpu"
    model = model.to(device)
    model.eval()
    prompt = cast(str, args.prompt)
    box_threshold = cast(float, args.box_threshold)
    text_threshold = cast(float, args.text_threshold)
    print(f"prompt: {prompt!r}")
    print(f"threshold={box_threshold} text_threshold={text_threshold}")

    for video_id in args.video_ids:
        out_dir = cast(Path, args.out_dir) / video_id
        out_dir.mkdir(parents=True, exist_ok=True)
        frames = sample_frames(cast(Path, args.frames_dir), video_id, cast(int, args.sample))
        print(f"--- {video_id}: sampling {len(frames)} frames ---")

        total_boxes = 0
        frames_with_box = 0
        label_counter: dict[str, int] = {}

        for i, frame_path in enumerate(frames, 1):
            img = Image.open(frame_path).convert("RGB")
            inputs = processor(images=img, text=prompt, return_tensors="pt").to(device)
            with torch.no_grad():
                outputs = model(**inputs)
            target_sizes = torch.tensor([img.size[::-1]])
            post = processor.post_process_grounded_object_detection(
                outputs,
                inputs.input_ids,
                threshold=box_threshold,
                text_threshold=text_threshold,
                target_sizes=target_sizes,
            )
            results = post[0]
            boxes_list = cast(list[list[float]], results["boxes"].tolist())
            scores_list = cast(list[float], results["scores"].tolist())
            raw_labels = results["labels"]
            if isinstance(raw_labels, list):
                labels_list = [str(x) for x in raw_labels]
            else:
                labels_list = [str(x) for x in raw_labels.tolist()]

            record = {
                "frame": frame_path.name,
                "prompt": prompt,
                "boxes": boxes_list,
                "scores": scores_list,
                "labels": labels_list,
            }
            out_json = out_dir / f"{frame_path.stem}.json"
            out_json.write_text(
                json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            vis = draw_boxes(img, boxes_list, scores_list, labels_list)
            out_vis = out_dir / f"{frame_path.stem}_vis.jpg"
            vis.save(out_vis, "JPEG", quality=85)

            total_boxes += len(boxes_list)
            if boxes_list:
                frames_with_box += 1
            for lbl in labels_list:
                label_counter[lbl] = label_counter.get(lbl, 0) + 1

            if i % 10 == 0:
                print(
                    f"  [{i}/{len(frames)}] frames_with_box={frames_with_box} "
                    f"total_boxes={total_boxes}"
                )

        print(f"  >> {video_id}: {frames_with_box}/{len(frames)} frames, "
              f"{total_boxes} boxes, labels={label_counter}")


if __name__ == "__main__":
    main()

"""Tile a directory of frames into labeled contact sheets for fast visual curation.

Generic version of p4_neg_sheets.py: grids every {name}_frame_*.jpg (in order) so a
whole movie is scanned at a glance to locate target segments (e.g. gore 구간 in a
zombie movie). Each cell is tagged with its frame number; ambiguous cells get a
full-res spot-check from the source frame.

    python scripts/make_contact_sheets.py --frames-dir data/processed/zombie01_frames \
        --name zombie01 --out-dir data/processed/zombie01_sheets [--cols 5 --rows 4]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for n in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default()


def frame_no(path: Path) -> str:
    parts = path.stem.split("_")
    if parts[-1] == "vis" and len(parts) >= 2:
        return parts[-2]
    return parts[-1]


def main() -> None:
    ap = argparse.ArgumentParser(description="Build labeled contact sheets from frames.")
    ap.add_argument("--frames-dir", type=Path, required=True)
    ap.add_argument("--name", required=True, help="frame filename prefix")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--rows", type=int, default=4)
    ap.add_argument("--cell-w", type=int, default=288)
    ap.add_argument("--cell-h", type=int, default=162)
    args = ap.parse_args()

    frames_dir: Path = args.frames_dir
    out_dir: Path = args.out_dir
    cols: int = args.cols
    rows: int = args.rows
    cw: int = args.cell_w
    ch: int = args.cell_h
    per = cols * rows

    out_dir.mkdir(parents=True, exist_ok=True)
    frames = sorted(frames_dir.glob(f"{args.name}_frame_*.jpg"))
    if not frames:
        raise SystemExit(f"no frames {args.name}_frame_*.jpg in {frames_dir}")

    f = font(20)
    n_sheets = 0
    for start in range(0, len(frames), per):
        chunk = frames[start : start + per]
        sheet = Image.new("RGB", (cols * cw, rows * ch), (0, 0, 0))
        draw = ImageDraw.Draw(sheet)
        for i, frame in enumerate(chunk):
            cell = Image.open(frame).convert("RGB").resize((cw, ch))
            cx = (i % cols) * cw
            cy = (i // cols) * ch
            sheet.paste(cell, (cx, cy))
            tag = frame_no(frame)
            draw.rectangle([cx, cy, cx + 56, cy + 18], fill=(0, 0, 0))
            draw.text((cx + 2, cy + 1), tag, fill=(255, 235, 0), font=f)
        sheet_no = start // per
        sheet.save(out_dir / f"{args.name}_sheet_{sheet_no:03d}.jpg", quality=86)
        n_sheets += 1
    print(f"{len(frames)} frames -> {n_sheets} sheets ({cols}x{rows}) in {out_dir}")


if __name__ == "__main__":
    main()

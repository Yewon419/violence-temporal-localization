from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data/processed/violence"
REV = ROOT.parent / "vision_review"
DATA = json.loads((REV / "xdv_quality_scores.json").read_text(encoding="utf-8"))

TILE = 240
COLS = 4


def sheet(items: list[dict], out: Path, label: str) -> None:
    rows = (len(items) + COLS - 1) // COLS
    cell_h = TILE + 28
    canvas = Image.new("RGB", (COLS * TILE, rows * cell_h), (20, 20, 20))
    draw = ImageDraw.Draw(canvas)
    for i, d in enumerate(items):
        r, c = divmod(i, COLS)
        p = ROOT / d["cat"] / d["name"]
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((TILE, TILE))
        except Exception:
            im = Image.new("RGB", (TILE, TILE), (80, 0, 0))
        x, y = c * TILE, r * cell_h
        canvas.paste(im, (x, y))
        cap = f"blur={d['blur']} std={d['std']} m={d['mean']} {d['cat'][:4]}"
        draw.text((x + 2, y + TILE + 2), cap, fill=(255, 255, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    print(f"{label}: {len(items)} -> {out}")


def main() -> None:
    ok = [d for d in DATA if "error" not in d]
    by_blur = sorted(ok, key=lambda d: d["blur"])
    # bucket samples spread across each range
    def spread(lo: float, hi: float, n: int) -> list[dict]:
        pool = [d for d in by_blur if lo <= d["blur"] < hi]
        if not pool:
            return []
        step = max(1, len(pool) // n)
        return pool[::step][:n]

    sheet(by_blur[:16], REV / "sheet_blur_000-worst.png", "worst16")
    sheet(spread(5, 20, 16), REV / "sheet_blur_05-20.png", "blur5-20")
    sheet(spread(20, 50, 16), REV / "sheet_blur_20-50.png", "blur20-50")
    sheet(spread(50, 100, 16), REV / "sheet_blur_50-100.png", "blur50-100")
    flat = sorted([d for d in ok if d["std"] < 14 or d["mean"] < 18 or d["mean"] > 238],
                  key=lambda d: d["std"])[:16]
    sheet(flat, REV / "sheet_flat_dark.png", "flat/dark")


if __name__ == "__main__":
    main()

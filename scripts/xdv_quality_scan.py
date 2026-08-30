from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data/processed/violence"
XDV_DIRS = ["Abuse", "Car Accident", "Explosion", "Fighting", "Riot", "Shooting"]
OUT = ROOT.parent / "vision_review" / "xdv_quality_scores.json"

_LAP = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float64)


def laplacian_var(gray: np.ndarray) -> float:
    # valid convolution with 3x3 laplacian, variance of response = focus measure
    g = gray
    out = (
        -4.0 * g[1:-1, 1:-1]
        + g[:-2, 1:-1]
        + g[2:, 1:-1]
        + g[1:-1, :-2]
        + g[1:-1, 2:]
    )
    return float(out.var())


def analyze(path: Path) -> dict[str, float | int | str]:
    with Image.open(path) as im:
        im = im.convert("L")
        w, h = im.size
        # downscale large frames for speed, keep aspect
        scale = 480 / max(w, h) if max(w, h) > 480 else 1.0
        if scale < 1.0:
            im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))))
        g = np.asarray(im, dtype=np.float64)
    blur = laplacian_var(g)
    return {
        "blur": round(blur, 2),
        "w": w,
        "h": h,
        "min_side": min(w, h),
        "mean": round(float(g.mean()), 2),
        "std": round(float(g.std()), 2),
        "bytes": path.stat().st_size,
    }


def main() -> None:
    results: list[dict] = []
    for d in XDV_DIRS:
        folder = ROOT / d
        files = sorted(folder.glob("*.jpg"))
        for f in files:
            try:
                m = analyze(f)
            except Exception as e:
                m = {"error": str(e)}
            m["cat"] = d
            m["name"] = f.name
            results.append(m)
        print(f"{d}: {len(files)} done")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(results)} -> {OUT}")


if __name__ == "__main__":
    main()

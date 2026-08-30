from __future__ import annotations

import json
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data/processed/violence"
REV = ROOT.parent / "vision_review"
BATCH = 52
CATS = ["Abuse", "Explosion", "Fighting", "Riot", "Shooting"]


def main() -> None:
    descriptors: list[dict] = []
    bdir = REV / "review_batches"
    bdir.mkdir(parents=True, exist_ok=True)
    for cat in CATS:
        files = sorted((ROOT / cat).glob("*.jpg"))
        names = [f.name for f in files]
        (REV / f"index_map_{cat.replace(' ', '_')}.json").write_text(
            json.dumps(names, ensure_ascii=False), encoding="utf-8"
        )
        cdir = bdir / cat.replace(" ", "_")
        cdir.mkdir(parents=True, exist_ok=True)
        n = math.ceil(len(names) / BATCH)
        for b in range(n):
            chunk = names[b * BATCH : (b + 1) * BATCH]
            items = [
                {"idx": b * BATCH + i, "path": str((ROOT / cat / nm).resolve())}
                for i, nm in enumerate(chunk)
            ]
            bp = cdir / f"batch_{b:03d}.json"
            bp.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
            descriptors.append({"cat": cat, "batch": b, "path": str(bp.resolve()), "n": len(chunk)})
        print(f"{cat}: {len(names)} imgs -> {n} batches")

    (REV / "review_descriptors.json").write_text(
        json.dumps(descriptors, ensure_ascii=False), encoding="utf-8"
    )
    print(f"total batches: {len(descriptors)}")


if __name__ == "__main__":
    main()

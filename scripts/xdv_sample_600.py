from __future__ import annotations

import json
import random
import shutil
from pathlib import Path

ROOT = Path(r"C:/Users/windg/Desktop/SCHOOL/3-1/데이터엔지니어링/project2/data/processed/violence")
DEST = ROOT.parent / "violence_sampled_600"
REV = ROOT.parent / "vision_review"
SEED = 42
N = 600
CATS = ["Abuse", "Car Accident", "Explosion", "Fighting", "Riot", "Shooting"]


def main() -> None:
    rng = random.Random(SEED)
    manifest: dict[str, list[str]] = {}
    summary: list[tuple[str, int, int]] = []
    for cat in CATS:
        files = sorted((ROOT / cat).glob("*.jpg"))
        pool = [f.name for f in files]
        take = min(N, len(pool))
        picked = sorted(rng.sample(pool, take))
        out_dir = DEST / cat
        out_dir.mkdir(parents=True, exist_ok=True)
        for name in picked:
            shutil.copy2(ROOT / cat / name, out_dir / name)
        manifest[cat] = picked
        summary.append((cat, len(pool), take))

    REV.mkdir(parents=True, exist_ok=True)
    (REV / "xdv_sample_600_manifest.json").write_text(
        json.dumps({"seed": SEED, "n": N, "picks": manifest}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"{'category':14}{'pool':>7}{'sampled':>9}")
    tot = 0
    for cat, pool, take in summary:
        tot += take
        print(f"{cat:14}{pool:7}{take:9}")
    print("-" * 30)
    print(f"{'TOTAL':14}{'':7}{tot:9}")
    print(f"copied -> {DEST}")


if __name__ == "__main__":
    main()

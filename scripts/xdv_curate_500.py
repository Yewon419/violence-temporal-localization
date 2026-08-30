from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data/processed/violence"
DEST = ROOT.parent / "violence_curated_500"
REV = ROOT.parent / "vision_review"
TARGET = 500
CATS = ["Abuse", "Car Accident", "Explosion", "Fighting", "Riot", "Shooting"]
SEG_RX = re.compile(r"^(.*)_seg(\d+)_kf(\d+)\.jpg$")

# brightness gate: skip near-black / blown-out frames (defensive; most already gone)
MEAN_LO, MEAN_HI = 25.0, 235.0


def load_scores() -> dict[tuple[str, str], dict]:
    raw = json.loads((REV / "xdv_quality_scores.json").read_text(encoding="utf-8"))
    return {(d["cat"], d["name"]): d for d in raw if "error" not in d}


def select_for_cat(cat: str, scores: dict) -> list[str]:
    files = sorted((ROOT / cat).glob("*.jpg"))  # existing (post-deletion) only
    segs: dict[str, list[tuple[float, int, str]]] = defaultdict(list)
    for f in files:
        m = SEG_RX.match(f.name)
        key = f"{m.group(1)}_seg{m.group(2)}" if m else f.name
        kf = int(m.group(3)) if m else 0
        sc = scores.get((cat, f.name), {})
        mean = sc.get("mean", 128.0)
        blur = sc.get("blur", 0.0)
        if not (MEAN_LO <= mean <= MEAN_HI):
            continue
        segs[key].append((blur, kf, f.name))
    # within each segment: sharpest first
    for k in segs:
        segs[k].sort(key=lambda t: -t[0])
    # round-robin across segments by descending segment sharpness order
    seg_keys = sorted(segs, key=lambda k: -segs[k][0][0])
    picked: list[str] = []
    rnd = 0
    while len(picked) < TARGET:
        progressed = False
        for k in seg_keys:
            if rnd < len(segs[k]):
                picked.append(segs[k][rnd][2])
                progressed = True
                if len(picked) >= TARGET:
                    break
        if not progressed:
            break
        rnd += 1
    return picked


def main() -> None:
    scores = load_scores()
    manifest: dict[str, list[str]] = {}
    summary: list[tuple[str, int, int]] = []
    for cat in CATS:
        avail = len(list((ROOT / cat).glob("*.jpg")))
        picks = select_for_cat(cat, scores)
        out_dir = DEST / cat
        out_dir.mkdir(parents=True, exist_ok=True)
        for name in picks:
            shutil.copy2(ROOT / cat / name, out_dir / name)
        manifest[cat] = picks
        summary.append((cat, avail, len(picks)))

    REV.mkdir(parents=True, exist_ok=True)
    (REV / "xdv_curated_500_manifest.json").write_text(
        json.dumps({"target": TARGET, "method": "segment-roundrobin-sharpness", "picks": manifest},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"{'category':14}{'avail':>7}{'picked':>8}")
    tot = 0
    for cat, avail, n in summary:
        tot += n
        print(f"{cat:14}{avail:7}{n:8}")
    print("-" * 29)
    print(f"{'TOTAL':14}{'':7}{tot:8}")


if __name__ == "__main__":
    main()

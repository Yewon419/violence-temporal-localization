"""Clip-balanced downsample of an XD-V violence sub-folder.

Run:
    # dry-run (no files removed) — see what would happen
    python scripts/downsample.py --folder data/processed/violence/Riot --target 1500 --dry-run

    # actually delete
    python scripts/downsample.py --folder data/processed/violence/Riot --target 1500

Files prefixed with ``hod_`` or ``rfh_`` (i.e. not XD-V origin) are not
touched. Only XD-V keyframes (``{clip_id}_seg{si}_kf{ki}.jpg``) are subject
to clip-balanced selection.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.postprocess.downsample import downsample_folder


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--folder", type=Path, required=True, help="Folder to downsample")
    p.add_argument("--target", type=int, required=True, help="Approximate target file count")
    p.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    p.add_argument("--dry-run", action="store_true", help="Report only; do not delete files")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    stats = downsample_folder(
        folder=args.folder,
        target=args.target,
        seed=args.seed,
        dry_run=args.dry_run,
    )
    print(f"folder        : {args.folder}")
    print(f"target        : {args.target}")
    print(f"clips         : {stats['clips']}")
    print(f"before        : {stats['before']}")
    print(f"keep          : {stats['keep']}")
    print(f"delete        : {stats['delete']}")
    if args.dry_run:
        print("(dry-run — no files modified)")
    else:
        print("Files deleted.")


if __name__ == "__main__":
    main()

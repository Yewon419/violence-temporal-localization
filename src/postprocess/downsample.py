from __future__ import annotations

import random
import re
from collections import defaultdict
from pathlib import Path

# XD-V keyframe filename: ``{clip_id}_seg{si:03d}_kf{ki:04d}.jpg``.
# Files matching other patterns (hod_/rfh_ prefixed) are not from XD-V
# and are intentionally untouched by clip-balanced downsampling.
XDV_FILENAME = re.compile(r"^(.+?)_seg\d+_kf\d+\.jpg$")


def group_by_clip(folder: Path) -> dict[str, list[Path]]:
    """Group jpg files in ``folder`` by their XD-V ``clip_id`` prefix."""
    groups: dict[str, list[Path]] = defaultdict(list)
    for f in folder.iterdir():
        if not f.is_file() or f.suffix.lower() != ".jpg":
            continue
        m = XDV_FILENAME.match(f.name)
        if not m:
            continue
        groups[m.group(1)].append(f)
    return dict(groups)


def select_keep(
    groups: dict[str, list[Path]],
    target: int,
    seed: int = 42,
) -> tuple[list[Path], list[Path]]:
    """Pick a clip-balanced subset of files to keep.

    Each clip contributes at most ``ceil(target / num_clips)`` files; clips
    with fewer files are kept entirely. Selection within a clip is
    deterministic via the provided ``seed``. Returns ``(keep, delete)``.
    """
    rng = random.Random(seed)
    n_clips = len(groups)
    if n_clips == 0 or target <= 0:
        return [], [f for files in groups.values() for f in files]

    per_clip = max(1, -(-target // n_clips))
    keep: list[Path] = []
    delete: list[Path] = []
    for files in groups.values():
        if len(files) <= per_clip:
            keep.extend(files)
            continue
        shuffled = list(files)
        rng.shuffle(shuffled)
        keep.extend(shuffled[:per_clip])
        delete.extend(shuffled[per_clip:])
    return keep, delete


def downsample_folder(
    folder: Path,
    target: int,
    seed: int = 42,
    dry_run: bool = False,
) -> dict[str, int]:
    """Clip-balanced downsample ``folder`` to roughly ``target`` files.

    Returns a stats dict with ``clips`` / ``before`` / ``keep`` / ``delete``.
    With ``dry_run=True`` no files are removed.
    """
    if not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")
    groups = group_by_clip(folder)
    before = sum(len(v) for v in groups.values())
    keep, delete = select_keep(groups, target, seed)
    if not dry_run:
        for p in delete:
            p.unlink()
    return {
        "clips": len(groups),
        "before": before,
        "keep": len(keep),
        "delete": len(delete),
    }

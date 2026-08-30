from __future__ import annotations

import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import XDV_TEST_ANNOTATIONS

# XD-Violence class code → our category. All non-Normal codes collapse to violence=1.
# A=Normal is never written as an annotation line, but kept for completeness.
XDV_CLASS_TO_CATEGORY: dict[str, str] = {
    "A": "normal",
    "B1": "violence",  # Fighting
    "B2": "violence",  # Shooting
    "B4": "violence",  # Riot
    "B5": "violence",  # Abuse
    "B6": "violence",  # Car accident
    "G":  "violence",  # Explosion
}


@dataclass(frozen=True)
class XdvSegment:
    """A single violent segment within a clip, expressed in frame indices."""

    start_frame: int
    end_frame: int

    def __post_init__(self) -> None:
        if self.start_frame < 0 or self.end_frame < self.start_frame:
            raise ValueError(
                f"Invalid segment: start={self.start_frame}, end={self.end_frame}"
            )


@dataclass(frozen=True)
class XdvAnnotation:
    """One line of the XD-Violence test annotation file.

    clip_id is the raw identifier from the source (e.g. ``v=S-7rRLrxnVQ__#1`` or
    ``City.of.God.2002__#01-24-10_01-25-10``). class_codes preserve the original
    dash-separated tail (e.g. ``["B4", "0", "0"]``) for traceability — only the
    first non-zero code is meaningful for category mapping.
    """

    clip_id: str
    class_codes: tuple[str, ...]
    segments: tuple[XdvSegment, ...]

    @property
    def primary_class(self) -> str:
        for code in self.class_codes:
            if code != "0":
                return code
        return "0"

    @property
    def category(self) -> str:
        return XDV_CLASS_TO_CATEGORY.get(self.primary_class, "unknown")


def parse_annotation_line(line: str) -> XdvAnnotation:
    """Parse one line of XD-Violence test annotation.

    Format: ``{clip_id}_label_{C1}-{C2}-{C3} f1 f2 f3 f4 ...``
    where (f1,f2),(f3,f4),... are (start,end) frame index pairs.
    """
    tokens = line.strip().split()
    if len(tokens) < 3:
        raise ValueError(f"Annotation line too short: {line!r}")

    head = tokens[0]
    clip_id, sep, label_part = head.rpartition("_label_")
    if not sep:
        raise ValueError(f"Missing '_label_' delimiter in head: {head!r}")

    # Some annotation lines accidentally include a trailing ".mp4" extension
    # in the head (14 / 500 cases in the official test_annotations.txt).
    if label_part.endswith(".mp4"):
        label_part = label_part[:-4]

    class_codes: tuple[str, ...] = tuple(label_part.split("-"))

    indices = [int(tok) for tok in tokens[1:]]
    if len(indices) % 2 != 0:
        raise ValueError(
            f"Odd number of frame indices ({len(indices)}) in line: {line!r}"
        )

    segments: tuple[XdvSegment, ...] = tuple(
        XdvSegment(start_frame=indices[i], end_frame=indices[i + 1])
        for i in range(0, len(indices), 2)
    )
    return XdvAnnotation(clip_id=clip_id, class_codes=class_codes, segments=segments)


def iter_annotations(path: Path = XDV_TEST_ANNOTATIONS) -> Iterator[XdvAnnotation]:
    if not path.exists():
        raise FileNotFoundError(f"Annotation file not found: {path}")
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            yield parse_annotation_line(line)


def load_annotations(path: Path = XDV_TEST_ANNOTATIONS) -> list[XdvAnnotation]:
    return list(iter_annotations(path))


def summarize(records: Iterable[XdvAnnotation]) -> dict[str, int]:
    summary: dict[str, int] = {
        "clips": 0,
        "segments": 0,
        "violence_clips": 0,
        "unknown_class_clips": 0,
    }
    for rec in records:
        summary["clips"] += 1
        summary["segments"] += len(rec.segments)
        if rec.category == "violence":
            summary["violence_clips"] += 1
        elif rec.category == "unknown":
            summary["unknown_class_clips"] += 1
    return summary


if __name__ == "__main__":
    records = load_annotations()
    summary = summarize(records)
    print("=== XD-V test annotations ===")
    for key, value in summary.items():
        print(f"  {key:24s}: {value}")
    print()
    print("=== first 3 records ===")
    for rec in records[:3]:
        print(f"  clip_id      : {rec.clip_id}")
        print(f"  class_codes  : {rec.class_codes} (primary={rec.primary_class}, category={rec.category})")
        print(f"  segments     : {[(s.start_frame, s.end_frame) for s in rec.segments]}")
        print()

    classes_seen: dict[str, int] = {}
    for rec in records:
        classes_seen[rec.primary_class] = classes_seen.get(rec.primary_class, 0) + 1
    print("=== primary class distribution ===")
    for cls, cnt in sorted(classes_seen.items(), key=lambda kv: -kv[1]):
        print(f"  {cls:6s}: {cnt}")

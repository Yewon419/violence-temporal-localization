"""Prepare per-box highlighted images for vision review of the CVAT v2 import.

Source of truth is the CVAT import COCO (data/processed/cvat_import_v2/<vid>/coco.json)
— i.e. exactly the boxes that were imported into CVAT and therefore need review.
For a priority group of labels, render one image per box with ONLY that box
highlighted (red, thick) + a label/score caption. GD score is recovered by
matching the box back to the triage JSON. Output -> data/processed/vision_review/<group>/.
Also emits <group>_manifest.json describing every box.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"C:\Users\windg\Desktop\SCHOOL\3-1\데이터엔지니어링\project2")
CVAT_DIR = ROOT / "data" / "processed" / "cvat_import_v2"
TRIAGE_DIR = ROOT / "data" / "processed" / "gd_triage_v2"
FRAMES_DIR = ROOT / "data" / "processed" / "yt_drama_frames"
OUT_BASE = ROOT / "data" / "processed" / "vision_review"

GROUPS: dict[str, set[str]] = {
    "p1_violence_event": {"explosion", "car_accident", "blood", "abuse"},
    "p2_weapon_riot": {"weapon_knife", "riot", "weapon_gun"},
    "p3_unknown": {"unknown"},
    "p4_objects": {"bottle", "cup", "cigarette"},
}


@dataclass(frozen=True)
class BoxEntry:
    idx: int
    vid: str
    frame: str
    cvat_label: str
    score: float | None
    verdict: str
    category: str
    bbox_xywh: tuple[float, float, float, float]
    image_out: str


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_triage_index(vid: str) -> dict[tuple[str, int, int], tuple[float, str, str]]:
    """frame + rounded(x0,y0) -> (score, verdict, category)."""
    idx: dict[tuple[str, int, int], tuple[float, str, str]] = {}
    tri = TRIAGE_DIR / f"{vid}.json"
    if not tri.exists():
        return idx
    for fr in json.loads(tri.read_text(encoding="utf-8")):
        for b in fr["boxes"]:
            x0, y0 = b["bbox"][0], b["bbox"][1]
            idx[(fr["frame"], round(x0), round(y0))] = (
                round(float(b["score"]), 4),
                b["verdict"],
                b.get("category", ""),
            )
    return idx


def main(group: str) -> None:
    labels = GROUPS[group]
    out_dir = OUT_BASE / group
    out_dir.mkdir(parents=True, exist_ok=True)
    font = load_font(28)

    entries: list[BoxEntry] = []
    idx = 0
    for vdir in sorted(CVAT_DIR.iterdir()):
        coco_path = vdir / "coco.json"
        if not coco_path.exists():
            continue
        vid = vdir.name
        coco = json.loads(coco_path.read_text(encoding="utf-8"))
        id2name = {c["id"]: c["name"] for c in coco["categories"]}
        id2file = {im["id"]: im["file_name"] for im in coco["images"]}
        tri_idx = build_triage_index(vid)

        for ann in coco["annotations"]:
            label = id2name[ann["category_id"]]
            if label not in labels:
                continue
            frame = id2file[ann["image_id"]]
            src = FRAMES_DIR / frame
            if not src.exists():
                print(f"MISSING frame {src}")
                continue
            x, y, w, h = (float(v) for v in ann["bbox"])
            score, verdict, category = tri_idx.get(
                (frame, round(x), round(y)), (None, "?", "")
            )
            img = Image.open(src).convert("RGB")
            draw = ImageDraw.Draw(img)
            draw.rectangle([x, y, x + w, y + h], outline=(255, 0, 0), width=5)
            sc = f"{score:.2f}" if score is not None else "?"
            cap = f"{label} {sc} [{verdict}]"
            tw = draw.textlength(cap, font=font)
            ty = max(0.0, y - 34)
            draw.rectangle([x, ty, x + tw + 8, ty + 34], fill=(255, 0, 0))
            draw.text((x + 4, ty + 2), cap, fill=(255, 255, 255), font=font)
            stem = Path(frame).stem.split("_")[-1]
            out_name = f"{idx:03d}_{vid}_{stem}_{label}.jpg"
            out_path = out_dir / out_name
            img.save(out_path, quality=88)
            entries.append(
                BoxEntry(
                    idx=idx,
                    vid=vid,
                    frame=frame,
                    cvat_label=label,
                    score=score,
                    verdict=verdict,
                    category=category,
                    bbox_xywh=(round(x, 1), round(y, 1), round(w, 1), round(h, 1)),
                    image_out=str(out_path.relative_to(ROOT)),
                )
            )
            idx += 1

    manifest = OUT_BASE / f"{group}_manifest.json"
    manifest.write_text(
        json.dumps([asdict(e) for e in entries], ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    by_label: dict[str, int] = {}
    for e in entries:
        by_label[e.cvat_label] = by_label.get(e.cvat_label, 0) + 1
    print(f"group={group} boxes={len(entries)} -> {out_dir}")
    print("by label:", by_label)


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "p1_violence_event")

# 드라마 frame 데이터 파이프라인 — 사용 안내

mp4 영상이 준비된 후, 아래 순서대로 진행하면 됩니다.
각 단계의 코드 블록은 노션에서 복사 → Python 또는 PowerShell에 그대로 paste 가능합니다.

영상 다운로드는 각자 (yt-dlp 등).

## 한눈에 보는 흐름

```
mp4 영상 (입력)
    ↓ ① Frame 추출 (ffmpeg fps=1)
jpg frame
    ↓ ② Hugging Face 업로드
HF dataset
    ↓ ③ Grounding DINO 자동 bbox
bbox JSON
    ↓ ④ CVAT용 COCO 1.0 변환
COCO JSON
    ↓ ⑤ CVAT에 자동 import
CVAT Task
    ↓ ⑥ 사람이 검수
정제된 bbox
    ↓ ⑦ Export + HF push
학습 데이터
```

---

## 사전 준비 (한 번만)

### Python venv + 의존성

```powershell
cd C:\Users\windg\Desktop\SCHOOL\3-1\데이터엔지니어링\project2
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pip install yt-dlp imageio-ffmpeg torch torchvision transformers cvat-sdk --index-url https://download.pytorch.org/whl/cpu
```

### mp4 영상 배치

받아온 영상을 아래 경로에 두면 됩니다 (파일명 자유, video_id를 stem으로):
```
data/raw/yt_drama/{video_id}.mp4
```

예: `data/raw/yt_drama/vyXEi00PVrw.mp4`

`{video_id}`는 이후 모든 단계에서 같은 ID로 추적됩니다.

---

## ① Frame 추출 (ffmpeg fps=1)

영상을 1초당 1 frame으로 추출.

**왜 1초당 1장?** 영화 요약 영상은 cut이 1~3초 → 모든 cut에 1장 이상 들어갑니다. 음주·흡연 cut을 시간 비율 그대로 잡습니다.

### 코드

```python
"""① ffmpeg fps=1 frame 추출."""
from __future__ import annotations
import subprocess
from pathlib import Path

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VIDEO_DIR = Path("data/raw/yt_drama")
FRAMES_DIR = Path("data/processed/yt_drama_frames")
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

for mp4 in VIDEO_DIR.glob("*.mp4"):
    video_id = mp4.stem
    out_pattern = FRAMES_DIR / f"{video_id}_frame_%05d.jpg"
    existing = list(FRAMES_DIR.glob(f"{video_id}_frame_*.jpg"))
    if existing:
        print(f"[{video_id}] {len(existing)} frames already extracted — skip")
        continue
    print(f"[{video_id}] extracting...")
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error",
           "-i", str(mp4), "-vf", "fps=1", "-qscale:v", "2",
           "-y", str(out_pattern)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FAILED: {result.stderr[-300:]}")
        continue
    n = len(list(FRAMES_DIR.glob(f"{video_id}_frame_*.jpg")))
    print(f"  saved {n} frames")
```

**결과**: `data/processed/yt_drama_frames/{video_id}_frame_{NNNNN}.jpg`

---

## ② Hugging Face 업로드

추출한 frame을 HF private dataset `DEteam4/movie-rating-violence`에
`smoking/drama_frames/{video_id}/` + `drinking/drama_frames/{video_id}/` 양쪽에 push.

**왜 양쪽?** 한 frame에 음주·흡연 둘 다 등장 가능하기 때문 (multi-class 정책).

### 토큰 준비

`_keys\DEproject2\HF_TOKEN.txt`에 본인 HF write 토큰 저장.

### 코드

```python
"""② Hugging Face push (smoking + drinking 양쪽)."""
from __future__ import annotations
from pathlib import Path
from huggingface_hub import HfApi, CommitOperationAdd

REPO_ID = "DEteam4/movie-rating-violence"
FRAMES_DIR = Path("data/processed/yt_drama_frames")
TOKEN_PATH = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2\HF_TOKEN.txt")
TARGETS = ("smoking/drama_frames", "drinking/drama_frames")

token = TOKEN_PATH.read_text(encoding="utf-8").strip()
api = HfApi(token=token)

# video_id 자동 추출
video_ids = sorted({
    fp.stem.rsplit("_frame_", 1)[0]
    for fp in FRAMES_DIR.glob("*_frame_*.jpg")
})

for vid in video_ids:
    files = sorted(FRAMES_DIR.glob(f"{vid}_frame_*.jpg"))
    if not files:
        continue
    ops = [
        CommitOperationAdd(
            path_in_repo=f"{t}/{vid}/{fp.name}",
            path_or_fileobj=str(fp),
        )
        for fp in files for t in TARGETS
    ]
    api.create_commit(
        repo_id=REPO_ID, repo_type="dataset",
        operations=ops,
        commit_message=f"Add drama_frames: {vid} ({len(files)} frames x 2 paths)",
    )
    print(f"[{vid}] pushed {len(files)} frames x 2 paths")
```

**결과 (Hugging Face)**
```
smoking/drama_frames/{video_id}/{video_id}_frame_NNNNN.jpg
drinking/drama_frames/{video_id}/{video_id}_frame_NNNNN.jpg
```

> ⚠ HF는 폴더당 10,000 파일 한계 — `video_id` 서브폴더로 분리해야 안전합니다.

---

## ③ Grounding DINO 자동 bbox

각 영상에서 100 frame 균등 sampling 후 Grounding DINO로 zero-shot bbox.

- prompt: `cigarette. smoking. drinking. bottle. cup.`
- threshold 0.25
- CPU 추론 — 영상당 10~17분

### 코드

```python
"""③ Grounding DINO inference."""
from __future__ import annotations
import json, sys
from pathlib import Path

import torch
from PIL import Image, ImageDraw
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

FRAMES_DIR = Path("data/processed/yt_drama_frames")
GD_OUT = Path("data/processed/gd_demo_fps")
SAMPLE_SIZE = 100
PROMPT = "cigarette. smoking. drinking. bottle. cup."
MODEL_ID = "IDEA-Research/grounding-dino-tiny"
THRESHOLD = 0.25

processor = AutoProcessor.from_pretrained(MODEL_ID)
model = AutoModelForZeroShotObjectDetection.from_pretrained(MODEL_ID).to("cpu")
model.eval()

video_ids = sorted({
    fp.stem.rsplit("_frame_", 1)[0]
    for fp in FRAMES_DIR.glob("*_frame_*.jpg")
})

for vid in video_ids:
    frames = sorted(FRAMES_DIR.glob(f"{vid}_frame_*.jpg"))
    if not frames:
        continue
    if len(frames) > SAMPLE_SIZE:
        step = len(frames) / SAMPLE_SIZE
        frames = [frames[int(i * step)] for i in range(SAMPLE_SIZE)]
    out_dir = GD_OUT / vid
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"--- {vid}: {len(frames)} frames ---")

    for i, fp in enumerate(frames, 1):
        img = Image.open(fp).convert("RGB")
        inputs = processor(images=img, text=PROMPT, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        post = processor.post_process_grounded_object_detection(
            outputs, inputs.input_ids,
            threshold=THRESHOLD, text_threshold=THRESHOLD,
            target_sizes=torch.tensor([img.size[::-1]]),
        )[0]
        boxes = post["boxes"].tolist()
        scores = post["scores"].tolist()
        labels = post["labels"] if isinstance(post["labels"], list) else post["labels"].tolist()
        labels = [str(x) for x in labels]

        # JSON 저장
        (out_dir / f"{fp.stem}.json").write_text(
            json.dumps({"frame": fp.name, "prompt": PROMPT,
                        "boxes": boxes, "scores": scores, "labels": labels},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # 시각화 저장
        vis = img.copy()
        draw = ImageDraw.Draw(vis)
        for b, s, l in zip(boxes, scores, labels):
            draw.rectangle(b, outline="red", width=3)
            draw.text((b[0], max(0, b[1] - 15)), f"{l}: {s:.2f}", fill="red")
        vis.save(out_dir / f"{fp.stem}_vis.jpg", "JPEG", quality=85)

        if i % 10 == 0:
            print(f"  [{i}/{len(frames)}]")
```

**결과**
```
data/processed/gd_demo_fps/{video_id}/
├── {frame_stem}.json       # bbox + score + label
└── {frame_stem}_vis.jpg    # 시각화 (빨간 박스)
```

---

## ④ CVAT용 COCO 1.0 변환

GD JSON → CVAT의 표준 import 포맷 (COCO).
검수자가 보기 편하게 label도 매핑:

| GD raw | CVAT label |
|---|---|
| cigarette / bottle / cup | (그대로) |
| drinking | drinking_act |
| smoking | smoking_act |
| smoking drinking, bottle cup, `''` | unknown (검수자가 결정) |

### 코드

```python
"""④ GD JSON → COCO 1.0 변환."""
from __future__ import annotations
import json, shutil
from pathlib import Path
from PIL import Image

GD_OUT = Path("data/processed/gd_demo_fps")
FRAMES_DIR = Path("data/processed/yt_drama_frames")
CVAT_OUT = Path("data/processed/cvat_import")

# CVAT Project label에 맞춰서 매핑
CVAT_LABELS = ["cigarette", "bottle", "cup", "wine_glass", "alcohol",
               "smoking_act", "drinking_act", "unknown"]
LABEL_MAP = {
    "cigarette": "cigarette", "bottle": "bottle", "cup": "cup",
    "drinking": "drinking_act", "smoking": "smoking_act",
    "smoking drinking": "unknown", "bottle cup": "unknown", "": "unknown",
}
name_to_id = {name: i + 1 for i, name in enumerate(CVAT_LABELS)}

for vid_dir in sorted(GD_OUT.iterdir()):
    if not vid_dir.is_dir():
        continue
    vid = vid_dir.name
    out_dir = CVAT_OUT / vid
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    images, annotations = [], []
    ann_id = 1
    json_files = sorted(p for p in vid_dir.glob("*.json") if "_vis" not in p.stem)
    for img_id, jp in enumerate(json_files, 1):
        rec = json.loads(jp.read_text(encoding="utf-8"))
        frame_name = rec["frame"]
        src = FRAMES_DIR / frame_name
        if not src.exists():
            continue
        dst = img_dir / frame_name
        if not dst.exists():
            shutil.copy2(src, dst)
        with Image.open(dst) as im:
            w, h = im.size
        images.append({"id": img_id, "file_name": frame_name,
                       "width": w, "height": h, "license": 0,
                       "flickr_url": "", "coco_url": "", "date_captured": 0})

        for b, s, l in zip(rec["boxes"], rec["scores"], rec["labels"]):
            x1, y1, x2, y2 = b
            bw, bh = max(0, x2 - x1), max(0, y2 - y1)
            cvat_label = LABEL_MAP.get(l, "unknown")
            annotations.append({
                "id": ann_id, "image_id": img_id,
                "category_id": name_to_id[cvat_label],
                "segmentation": [], "area": bw * bh,
                "bbox": [x1, y1, bw, bh],
                "iscrowd": 0, "score": s,
            })
            ann_id += 1

    coco = {
        "info": {"description": f"GD pre-annotation for {vid}",
                 "version": "1.0", "year": 2026, "contributor": "", "date_created": ""},
        "licenses": [{"id": 0, "name": "Unknown", "url": ""}],
        "images": images, "annotations": annotations,
        "categories": [{"id": i + 1, "name": n, "supercategory": ""}
                       for i, n in enumerate(CVAT_LABELS)],
    }
    (out_dir / "coco.json").write_text(
        json.dumps(coco, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[{vid}] {len(images)} images, {len(annotations)} annotations")
```

**결과**
```
data/processed/cvat_import/{video_id}/
├── coco.json   ← CVAT pre-annotation
└── images/     ← Task에 업로드할 frame 100장
```

---

## ⑤ CVAT 자동 셋업

### 처음 한 번만: CVAT Docker

```powershell
cd C:\Users\windg\Desktop\PROJECT
git clone https://github.com/cvat-ai/cvat.git
cd cvat
docker compose up -d
docker exec -it cvat_server bash -c "python3 manage.py createsuperuser"
```

브라우저 `http://localhost:8080` 로그인 → Project `DEproject2` 생성 + 아래 label 추가 (KMRB 심의 항목 전체):

**smoking·drinking (7개)**
`cigarette, bottle, cup, wine_glass, alcohol, smoking_act, drinking_act`

**violence (10개)**
`weapon_knife, weapon_gun, weapon_blunt, blood, fighting, shooting, riot, abuse, explosion, car_accident`

(`unknown`은 아래 스크립트가 자동 추가)

### 토큰 준비

`_keys\DEproject2\CVAT_username.txt` + `CVAT_password.txt`.

### Task 자동 생성 코드

```python
"""⑤ CVAT Task 10개 자동 생성 + GD bbox import."""
from __future__ import annotations
import sys
from pathlib import Path
from cvat_sdk import make_client
from cvat_sdk.api_client.models import (
    PatchedLabelRequest, PatchedProjectWriteRequest, TaskWriteRequest,
)

CVAT_HOST = "http://localhost:8080"
PROJECT_NAME = "DEproject2"
CVAT_IMPORT = Path("data/processed/cvat_import")
KEYS = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2")

u = (KEYS / "CVAT_username.txt").read_text(encoding="utf-8").strip()
p = (KEYS / "CVAT_password.txt").read_text(encoding="utf-8").strip()

with make_client(host=CVAT_HOST, credentials=(u, p)) as client:
    proj = next(p for p in client.projects.list() if p.name == PROJECT_NAME)
    project_labels = [lbl.name for lbl in proj.get_labels()]
    print(f"project id={proj.id} labels={project_labels}")

    if "unknown" not in project_labels:
        client.api_client.projects_api.partial_update(
            id=proj.id,
            patched_project_write_request=PatchedProjectWriteRequest(
                labels=[PatchedLabelRequest(name="unknown", color="#808080")]
            ),
        )
        print("added 'unknown' label")

    existing = {t.name for t in client.tasks.list() if t.project_id == proj.id}

    for vid_dir in sorted(CVAT_IMPORT.iterdir()):
        if not vid_dir.is_dir():
            continue
        vid = vid_dir.name
        name = f"{vid}"  # 한글 영화명 붙이려면 dict 만들기
        if name in existing:
            print(f"[{vid}] exists — skip")
            continue
        images_dir = vid_dir / "images"
        coco = vid_dir / "coco.json"
        if not (images_dir.exists() and coco.exists()):
            print(f"[{vid}] missing src — skip")
            continue
        print(f"[{vid}] creating task...")
        task = client.tasks.create_from_data(
            spec=TaskWriteRequest(name=name, project_id=proj.id),
            resources=sorted(str(p) for p in images_dir.glob("*.jpg")),
        )
        print(f"  task id={task.id}, importing annotations...")
        task.import_annotations(format_name="COCO 1.0", filename=str(coco))
        print(f"  [{vid}] done")
```

---

## ⑥ 사람 검수 (CVAT)

### 접속

브라우저: `http://localhost:8080/projects/1`

> 외부 접속(다른 PC)은 별도 tunnel 필요 (ngrok / tailscale / 학교 망).

### Task 목록 (현재 활성 8개)

| Task ID | 영상 | positive/unknown bbox | URL |
|:---:|---|---:|---|
| 11 | 내부자들 | 91 | `http://localhost:8080/tasks/11/jobs/11` |
| 12 | 범죄와의 전쟁 | 156 | `/tasks/12/jobs/12` |
| 13 | 마약왕 | 136 | `/tasks/13/jobs/13` |
| 14 | 달콤한 인생 | 135 | `/tasks/14/jobs/14` |
| 15 | 베테랑 | 126 | `/tasks/15/jobs/15` |
| 16 | 신세계 | 77 | `/tasks/16/jobs/16` |
| 17 | 비열한 거리 | 114 | `/tasks/17/jobs/17` |
| 18 | 황해 | 81 | `/tasks/18/jobs/18` |
| | **합** | **916** | |

> 친구 / 흡연 컴파일은 제외됨 (GD 검출 0 / 다른 팀원 담당).

### 검수 우선 순위 (vision 검증 기반)

GD bbox를 LLM이 1차 분류한 결과 — **검수자가 봐야 할 916 bbox** 외에 1,314개의 frame_dominant negative는 이미 자동 제거됨.

| 카테고리 | 수 | 검수 전략 |
|---|---:|---|
| **`unknown`** | **373** | 가장 많음 — 진짜 class로 변경 또는 삭제 (concat label / low score) |
| `bottle` / `cup` | 354 | 진짜 술병·잔 다수 — 빠른 keep, 식기·물잔은 삭제 |
| `explosion` / `car_accident` | 106 | ⚠ **FP 비율 매우 높음** — 풍경·실내 cut을 잘못 매핑하는 패턴 다수, 의심스러우면 삭제 |
| `weapon_gun` | 23 | 비교적 정확 (진짜 총기 cut에서 잡힘) |
| `cigarette` | 19 | 진짜 담배 잘 잡음 — 빠른 keep |
| `weapon_knife` | 11 | ⚠ 식기 칼을 잘못 매핑하기도 — frame context로 판단 |
| `blood` | 10 | ⚠ 빨간 그릇·양념 등 빨간색 객체를 잘못 매핑 |
| `riot` / `abuse` | 19 | 행위 — frame 전체 context로 판단 |

**사용되지 않은 label** (필요 시 검수자가 `N`으로 직접 그리기):
`smoking_act`, `wine_glass`, `alcohol`, `weapon_blunt`, `fighting`, `shooting`

### Label 의미 (KMRB 심의 항목)

**smoking·drinking**
| label | 의미 |
|---|---|
| `cigarette` | 담배 |
| `bottle` | 술병 |
| `cup` | 술잔·cup |
| `wine_glass` | 와인잔 |
| `alcohol` | 그 외 술 (캔 등) |
| `smoking_act` | 흡연 행위 (사람+담배 compositional) |
| `drinking_act` | 음주 행위 (사람+잔 compositional) |

**violence** (GD는 이 label들을 자동 잡지 않습니다 — 검수자가 frame 보고 `N`으로 직접 그리기)
| label | 의미 |
|---|---|
| `weapon_knife` | 칼·도끼·기타 날카로운 무기 |
| `weapon_gun` | 권총·소총 등 화기 |
| `weapon_blunt` | 망치·야구방망이·덤벨 등 둔기 |
| `blood` | 피·상처 |
| `fighting` | 격투 행위 (사람끼리) |
| `shooting` | 총격 행위 |
| `riot` | 폭동·집단 폭력 |
| `abuse` | 학대 |
| `explosion` | 폭발 |
| `car_accident` | 차량 사고 |

**기타**
| label | 의미 |
|---|---|
| `unknown` | GD가 분류 실패 — **반드시 진짜 class로 변경하거나 삭제** |

### 검수 룰

| 보이는 것 | 어떻게 |
|---|---|
| bbox 정확함 | 그대로 둠 |
| 크기·위치 어긋남 | 박스 더블클릭 → drag로 resize |
| label 잘못 | 박스 클릭 → 우측 패널 label dropdown 변경 |
| 객체 아닌데 박스 | 박스 선택 + `Delete` |
| 진짜 객체인데 박스 없음 | `N` → label 선택 → drag로 그리기 |
| frame 전체가 박스 (>50%) | 거의 100% FP → 삭제 |

### 단축키

| 키 | 동작 |
|---|---|
| `F` | 다음 frame |
| `D` | 이전 frame |
| `N` | 새 박스 그리기 |
| `Delete` | 선택 박스 삭제 |
| `Esc` | 그리기 취소 |
| `Ctrl + 마우스 휠` | zoom |

### 자주 나오는 케이스

- **회식 장면에 cup 박스 다발** — 진짜 술잔만 keep, 식기·물잔은 삭제
- **smoking_act / drinking_act 박스가 큰 편** — compositional이라 자연스러움 (단 80%+면 삭제)
- **어두운 / blur 객체** — 식별 불가하면 삭제
- **자막·로고 박스** — 항상 삭제

### 폭력 객체는 직접 그리기

GD는 흡연·음주만 자동 잡습니다. **frame에 무기·피·격투·폭발 등이 보이면 `N`키로 박스 추가**:

1. `N` 키 → 우측 패널에서 알맞은 violence label 선택 (예: `weapon_knife`)
2. drag로 영역 그리기
3. 같은 frame에 여러 객체 있으면 반복

영화 요약 영상은 음주·흡연 외에 폭력 장면도 많이 등장 (액션·누아르 작품일수록 빈도↑).

자동 저장됨 (수동 저장 `Ctrl+S`).

---

## ⑦ Export + Hugging Face push (검수 끝난 후)

CVAT Project → **Actions → Export project dataset** → format **YOLO 1.1** → zip 다운로드.

### Export 후 zip 해제 + HF push 코드

```python
"""⑦ CVAT YOLO export → HF push."""
from __future__ import annotations
import zipfile
from pathlib import Path
from huggingface_hub import HfApi, CommitOperationAdd

REPO_ID = "DEteam4/movie-rating-violence"
EXPORT_ZIP = Path("data/processed/cvat_export/yolo.zip")  # CVAT에서 다운받은 위치
EXPORT_DIR = Path("data/processed/cvat_export/extracted")
TOKEN_PATH = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2\HF_TOKEN.txt")
TARGETS = ("smoking/drama_frames_labels", "drinking/drama_frames_labels")

# zip 해제
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(EXPORT_ZIP) as zf:
    zf.extractall(EXPORT_DIR)

# YOLO txt 라벨을 video_id별로 그룹화 + HF push
token = TOKEN_PATH.read_text(encoding="utf-8").strip()
api = HfApi(token=token)

txt_files = sorted(EXPORT_DIR.rglob("*.txt"))
by_vid: dict[str, list[Path]] = {}
for fp in txt_files:
    vid = fp.stem.rsplit("_frame_", 1)[0]
    by_vid.setdefault(vid, []).append(fp)

for vid, files in by_vid.items():
    ops = [
        CommitOperationAdd(
            path_in_repo=f"{t}/{vid}/{fp.name}",
            path_or_fileobj=str(fp),
        )
        for fp in files for t in TARGETS
    ]
    api.create_commit(
        repo_id=REPO_ID, repo_type="dataset",
        operations=ops,
        commit_message=f"Add drama_frames_labels: {vid} ({len(files)} txt x 2)",
    )
    print(f"[{vid}] pushed {len(files)} labels x 2 paths")
```

**결과 (Hugging Face)**
```
smoking/drama_frames_labels/{video_id}/{frame_stem}.txt
drinking/drama_frames_labels/{video_id}/{frame_stem}.txt
```

---

## 부록 A — 의존성

Python 3.10 venv에 자동 설치되어 있습니다.

| 패키지 | 용도 |
|---|---|
| imageio-ffmpeg | ffmpeg 바이너리 번들 |
| huggingface_hub | HF 업로드 |
| torch (CPU) | Grounding DINO |
| transformers 5.x | Grounding DINO 모델 |
| cvat-sdk | CVAT API |
| Pillow / opencv-python | 이미지 처리 |

시스템:
- Docker Desktop (CVAT용, 메모리 8GB 권장)
- Python venv (`project2/.venv`)

---

## 부록 B — 회의에서 합의해야 할 것

- `cigatette` 오타 라벨 정리 시점
- 최종 label class 합의 (현재 8 + unknown)
- false positive 판정 기준 통일 (검수자 편차)
- Job 분할 방식 — 영상별 vs frame 균등
- 검수 후 review (2차 검수) 필요 여부
- 외부 접속 방법 — ngrok / tailscale / 학교 망
- 학습 시 사용 방식 — class 99 sentinel vs 별도 폴더

---

## 부록 C — 알려진 주의사항

- **HF는 폴더당 10,000 파일 한계** — `video_id` 서브폴더 분리 필수.
- **GD empty label (`''`)이 많음** — post-process에서 단어 매칭 실패. `unknown`으로 자동 매핑 → 검수자가 결정.
- **CVAT은 한 Job을 두 명이 동시 편집 시 conflict** — assignee 1인 원칙.
- **CVAT label은 Project 단위로 한 번 정하면 도중 변경 영향 큼** — 회의에서 사전 확정.

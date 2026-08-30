# 영화 심의 보조 시스템 — 데이터셋 빌드 파이프라인

영등위(KMRB) 등급 심의 보조용 카테고리별 이미지 데이터셋을 자동 구성합니다.
폴더 구조 자체가 라벨(ImageFolder convention) — CSV·DB 라벨링 없음.

현재 구현 카테고리: **violence**, **smoking**, **drinking**. 선정성·공포 등은 동일 패턴으로 팀원이 추가합니다 (아래 「새 카테고리 추가 가이드」 참고).

---

## Quick start

```powershell
# 1. venv 생성 + 의존성 설치
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# 2. 데이터셋 다운로드 (docs/datasets.md 절차 참고)
#    - XD-Violence test (videos.zip + annotations.txt)
#    - HOD YOLOv5 (yolo_v5_dataset.zip)
#    - Roboflow Harmful Objects (harmful objects.v1i.yolov8.zip)
#    - Roboflow Smoking and Drinking Detection (YOLOv8-OBB zip)
#    - Mendeley Smoker Detection (Smoker Detection.rar) — unrar 백엔드 필요

# 3. 카테고리별 빌드 (각 카테고리당 단일 entrypoint)
python scripts/build_violence.py
python scripts/build_smoking.py
python scripts/build_drinking.py
```

빌드 결과는 `data/processed/{category}/{class_name}/*.jpg` 평탄 구조로 떨어집니다. 자세한 통계는 빌드 마지막에 출력됩니다.

---

## 디렉토리 구조

```
project2/
├── README.md                           ← 이 파일
├── pyproject.toml                      ← 의존성·mypy·ruff 설정
├── docs/
│   ├── datasets.md                     ← 데이터셋별 출처·라이선스·다운로드 절차·매핑
│   └── decisions.md                    ← 모든 설계 결정 사항 + 이유
├── scripts/
│   ├── build_violence.py               ← XD-V + HOD + Roboflow Harmful
│   ├── build_smoking.py                ← HOD(cigarette) + Roboflow S&D(smoking) + Mendeley
│   └── build_drinking.py               ← HOD(alcohol) + Roboflow S&D(drinking)
├── src/
│   ├── config.py                       ← 경로·하이퍼파라미터 상수
│   ├── ingest/
│   │   ├── xdv_annotations.py          ← XD-Violence annotation 파서
│   │   ├── hod_extractor.py            ← HOD YOLO zip → violence/smoking/drinking 분기 복사
│   │   ├── roboflow_harmful_extractor.py
│   │   ├── roboflow_smoking_drinking_extractor.py   ← Roboflow S&D → smoking/drinking 분기
│   │   └── mendeley_smoker_extractor.py             ← Mendeley rar → smoking/cigarette/
│   ├── preprocess/
│   │   ├── segment_cutter.py           ← ffmpeg로 violence segment cut
│   │   ├── katna_extractor.py          ← Katna keyframe 추출 + cv2 unicode-safe 저장
│   │   └── build_violence_dataset.py   ← XD-V end-to-end (cut → Katna → 폴더 분류)
│   └── db/
│       ├── schema.sql                  ← PostgreSQL 호환 DDL (현재 미사용, 향후 확장용)
│       └── init_db.py
└── data/                               ← .gitignore (커밋 X)
    ├── raw/xdviolence_test/            ← XD-V mp4 800편
    ├── processed/violence/             ← 최종 산출물 (10 폴더)
    └── annotated/xdv_test_annotations.txt
```

---

## 검증

코드 변경 후 항상:

```powershell
.venv\Scripts\python.exe -m mypy src
.venv\Scripts\python.exe -m ruff check .
```

둘 다 통과해야 합니다 (strict mode + Any 금지).

---

## 새 카테고리 추가 가이드 (팀원용)

예: **선정성(sexual)** 카테고리를 담당한다면 — 다음 4단계.

### 1. 데이터셋 선정 + 다운로드

- 사용할 데이터셋 목록을 만들고 라이선스 확인 (research-only / commercial 자유 등)
- 브라우저로 다운로드해 `~/Downloads/`에 저장
- 결정 사항은 `docs/decisions.md`에 새 섹션으로 누적 기록

### 2. 데이터셋 어댑터 모듈 작성

`src/ingest/<dataset_name>_extractor.py`를 새로 만들고 기존 `hod_extractor.py` / `roboflow_harmful_extractor.py` 패턴을 그대로 따릅니다:

- `<DATASET>_CLASS_TO_FOLDER: dict[int, str]` — YOLO class index → 우리 폴더명
- `extract_<dataset>(zip_path, dest_root) -> dict[str, int]` — zip에서 직접 분기 복사
- 파일명 prefix는 출처 식별을 위해 다르게 (`hod_`, `rfh_`, …)
- multi-class 정책은 통일: 두 폴더에 다 복사 (이미지 중복은 허용)
- Inference 기반(NudeNet 등) 데이터셋은 별도 패턴이 필요할 수 있으니 `xdv_annotations.py` + `build_violence_dataset.py` 조합도 참고

### 3. 카테고리별 build script 작성

`scripts/build_<category>.py`를 만들고 `build_violence.py`를 참고해 각 추출 함수를 순차 호출하도록 작성합니다. 끝에 `print_folder_counts()` 호출.

### 4. 문서 갱신

- `docs/datasets.md` — 데이터셋 정보 추가
- `docs/decisions.md` — 클래스 매핑·정책 결정 이유 누적
- `README.md`의 Quick start 카테고리 목록 갱신
- `src/config.py`에 `<DATASET>_ZIP_PATH` 추가 (팀원 시스템 호환을 위해 `DOWNLOADS_DIR` 기준)

mypy/ruff 통과 후 PR/공유.

---

## 알려진 한계

- KMRB(영등위) 공식 기준은 "도구 종류축"이 아니라 "표현 정도축"입니다. 우리 폴더 구조는 객체 검출 보조용 자체 분류 체계입니다 — 자세한 framing은 `docs/decisions.md` 참고.
- smoking/cigarette/, drinking/alcohol/ 폴더는 객체 라벨 + 행위 라벨(Roboflow S&D, Mendeley smoking)이 단순 합산된 혼합 신호입니다. 행위·객체 framing 분리 시점은 `docs/decisions.md §11~13` 참고.
- Mendeley Smoker Detection은 rar 형식 → `rarfile` 패키지 + 시스템 7z/unrar/bsdtar 백엔드 중 하나가 PATH에 있어야 합니다. Windows는 **7-Zip (winget `7zip.7zip`)** 권장 (FOSS, command-line 포함). 설치 후 `C:\Program Files\7-Zip`을 사용자 PATH에 추가.
- Mendeley 클래스 축은 폴더가 아니라 **파일명 prefix** (`smoking_*.jpg` vs `notsmoking_*.jpg`). 폴더는 train/val/test split일 뿐 — 우리 어댑터는 prefix로 분기.
- 영상 fps는 영상별로 `cv2.CAP_PROP_FPS`로 읽습니다 (XD-V 영상 다수가 24fps, 표준 25fps 가정과 다름).
- Windows `cv2.imwrite`는 unicode 경로(데이터엔지니어링 등)에서 실패하므로 `cv2.imencode` + `Path.write_bytes`로 우회합니다.

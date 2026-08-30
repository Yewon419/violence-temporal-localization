# 데이터셋 — 출처·라이선스·다운로드·매핑

> **아카이브 문서입니다.**
> 폐기된 객체검출 트랙의 작업 기록으로, 당시 상태를 그대로 보존한 것입니다.
> 현재 파이프라인은 [저장소 README](../../README.md)를 참고하세요.
> 이 트랙을 왜 접었는지는 README의 「전환 1」 절에 정리했습니다.

카테고리별로 사용된 데이터셋을 출처와 처리 결과 단위로 정리합니다. 새 카테고리 추가 시 동일 형식으로 섹션을 늘려가세요.

- violence: §1 XD-Violence + §2 HOD + §3 Roboflow Harmful Objects
- smoking: §2 HOD(cigarette) + §4 Roboflow S&D(smoking class) + §5 Mendeley Smoker
- drinking: §2 HOD(alcohol) + §4 Roboflow S&D(drinking class)

---

## 1. XD-Violence (test set)

| | |
|---|---|
| **종류** | 영화·드라마 클립 mp4 + frame-level annotation |
| **공식** | https://roc-ng.github.io/XD-Violence/ |
| **paper** | Wu et al., ECCV 2020 |
| **라이선스** | research only (논문 인용 조건) |
| **용량** | mp4 800편 약 10GB zip (`videos.zip`) + annotation 텍스트 (kB) |
| **클래스** | A(Normal) / B1(Fighting) / B2(Shooting) / B4(Riot) / B5(Abuse) / B6(Car Accident) / G(Explosion) — 다중 라벨 가능 (`B6-G-0` 등) |

### 다운로드 절차 (브라우저 — SharePoint anonymous CLI 다운로드는 막힘)

1. 공식 페이지에서 OneDrive 링크 확인 (Test Videos / Test Annotations 별도)
2. Test Annotations 링크 → 브라우저 미리보기 페이지 → **다운로드** 클릭 → `~/Downloads/annotations.txt` → `data/annotated/xdv_test_annotations.txt`로 이동·이름 변경
3. Test Videos 링크 → 페이지에서 **다운로드** 클릭 → `~/Downloads/videos.zip` (약 10GB, 시간 소요) → 압축 풀어 `data/raw/xdviolence_test/`에 평탄 배치 (`videos/` 1단계 prefix 제거)

압축 해제와 키프레임 추출까지 `python scripts/build_violence.py` 안에서 자동 진행됩니다 (단, 영상 파일은 사전에 풀려 있어야 함).

### 매핑

| XD-V 코드 | 폴더명 |
|---|---|
| B1 | `Fighting` |
| B2 | `Shooting` |
| B4 | `Riot` |
| B5 | `Abuse` |
| B6 | `Car Accident` |
| G | `Explosion` |
| A | (annotation 없음 — 사용 안 함) |

multi-class 라인은 첫 non-zero class만 사용 (47/500 클립이 multi-class이지만 영향 미미).

### 처리 결과

- 500 annotation 라인 중 498편 처리 (2편은 짧은 segment + Katna 0장 반환 케이스, 무시 결정)
- **3,733 keyframe**: Riot 1,826 / Fighting 827 / Car Accident 503 / Explosion 284 / Shooting 273 / Abuse 20

---

## 2. HOD (Harmful Object Detection)

| | |
|---|---|
| **종류** | 웹 수집 이미지 + YOLO bbox |
| **공식 repo** | https://github.com/poori-nuna/HOD-Benchmark-Dataset |
| **paper** | Ha et al., arXiv:2310.05192 (WACV 2024 Workshop) |
| **라이선스** | research only (LICENSE 파일 없음, repo 설명 기준) |
| **용량** | YOLOv5 패키지 약 1.2GB (`yolo_v5_dataset.zip`) |
| **클래스** | alcohol / insulting_gesture / blood / cigarette / gun / knife (6) — index 0~5 |

### 다운로드 절차

1. repo의 README에서 OneDrive 링크 확인 (YOLOv5 또는 Faster R-CNN 포맷)
2. **YOLOv5 권장** (디렉토리 단순) → 브라우저로 `~/Downloads/yolo_v5_dataset.zip`
3. 압축 해제 불필요 — `extract_hod_violence()`가 zip에서 직접 읽어 분기 복사

zip 구조:
```
yolo_all/{training|validation|test}/{images|labels}/...
yolo_hard/...
yolo_normal/...
```
우리는 `yolo_all`(normal + hard 합본)만 사용해 중복 회피.

### 매핑

| HOD class (index) | violence 폴더 | smoking 폴더 | drinking 폴더 |
|---|---|---|---|
| alcohol (0) | — | — | `alcohol` |
| insulting_gesture (1) | — | — | — |
| blood (2) | `상해(피)` | — | — |
| cigarette (3) | — | `cigarette` | — |
| gun (4) | `총기` | — | — |
| knife (5) | `흉기` | — | — |

smoking·drinking 카테고리에서는 이미지뿐 아니라 **YOLOv5 bbox 라벨 (`*.txt`)도 같이 복사** (파일명 `hod_<stem>.txt`, jpg와 같은 폴더). multi-bbox 이미지는 cigarette/alcohol 외 다른 class 줄(예: blood)도 그대로 포함된 원본 라벨이 들어감 — 학습 시점 필터링은 사용 측 책임. 자세한 framing은 `decisions.md §16` 참고. (violence 폴더는 라벨 미포함 — 결정 §16 참고)

multi-class 이미지는 두 폴더에 다 복사 (정책 통일).
파일명 prefix: `hod_`

### 처리 결과

- 10,631장 스캔 → 6,307장 매칭 (multi-class 295장)
- **6,602 저장**: 흉기 3,279 / 상해(피) 1,721 / 총기 1,602

---

## 3. Roboflow Harmful Objects

| | |
|---|---|
| **종류** | 웹 수집 이미지 + YOLO bbox |
| **공식** | https://universe.roboflow.com/harmfull-objects/harmful-objects-wmmdi |
| **라이선스** | **CC BY 4.0** (commercial OK) |
| **용량** | YOLOv8 패키지 약 306MB (`harmful objects.v1i.yolov8.zip`) |
| **클래스** | Axe / Chainsaw / Chisel / Coin / Drink / Dumbbell / Fork / Hammer / Knife / Scissors / Screwdriver / Stapler (12) |

### 다운로드 절차

1. Roboflow Universe 페이지 → 우상단 **Download Dataset**
2. 포맷 **YOLOv8** 선택 (또는 YOLOv5 — 우리 코드는 둘 다 호환되지만 v8 권장)
3. **download zip to computer** 선택 (Show download code 아님)
4. 무료 계정 로그인 필요 (Google/GitHub 빠름) → `~/Downloads/harmful objects.v1i.yolov8.zip`

### 매핑

| Roboflow class (index) | 폴더명 |
|---|---|
| Axe (0) | `둔기` (도끼는 영화 폭력에서 통상 둔기로 가격 사용) |
| Hammer (7), Dumbbell (5) | `둔기` |
| Chainsaw (1) | `흉기` (회전 칼날) |
| Knife (8), Scissors (9), Fork (6), Chisel (2), Screwdriver (10) | `흉기` |
| Coin (3) / Drink (4) / Stapler (11) | 폭력 도구 아님 — skip |

multi-class 두 폴더 다 복사. 파일명 prefix: `rfh_`.

### 처리 결과

- 5,917장 스캔 → 3,383장 매칭 (multi-class 5장)
- **3,388 저장**: 흉기 2,865 / 둔기 523

---

## 4. Roboflow Smoking and Drinking Detection

| | |
|---|---|
| **종류** | 웹 수집 이미지 + YOLOv8-OBB (Oriented Bounding Box) |
| **공식** | https://universe.roboflow.com/yolo-dataset-rtznj/smoking-and-drinking-detection |
| **라이선스** | **CC BY 4.0** (commercial OK) — `README.dataset.txt` 명시 |
| **용량** | YOLOv8-OBB 패키지 약 24.7MB (`Smoking and Drinking Detection.v2-test-yolov5m.yolov8-obb.zip`) |
| **클래스** | `0: drinking` / `1: smoking` (행위 라벨) |
| **전처리** | 416×416 stretch resize |

### 다운로드 절차

1. Roboflow Universe 페이지 → 우상단 **Download Dataset**
2. 포맷 **YOLOv8 Oriented Object Detection** 선택
3. **download zip to computer** → `~/Downloads/` (무료 계정 로그인 필요)

zip 구조:
```
train/{images|labels}/
valid/{images|labels}/
test/{images|labels}/
data.yaml
```

OBB 라벨은 4꼭짓점 형식(`class x1 y1 x2 y2 x3 y3 x4 y4`)이지만 첫 토큰이 class index인 점은 일반 YOLO와 동일 — 기존 `parse_yolo_classes()` 그대로 재사용.

### 매핑

| Roboflow class (index) | smoking 폴더 | drinking 폴더 |
|---|---|---|
| drinking (0) | — | `alcohol` |
| smoking (1) | `cigarette` | — |

행위 라벨(smoking/drinking)을 객체 폴더(cigarette/alcohol)에 합산하는 framing에 대해서는 `docs/decisions.md §11`을 참조.

multi-class 두 폴더 다 복사. 파일명 prefix: `rfsd_`. **OBB 라벨(`rfsd_<stem>.txt`, 4꼭짓점 polygon)도 같이 복사** — jpg와 같은 폴더 (decisions.md §16).

### 처리 결과

- smoking: 1,030장 스캔 → 680장 매칭
- drinking: 1,030장 스캔 → 356장 매칭

---

## 5. Mendeley Smoker Detection

| | |
|---|---|
| **종류** | 웹 수집 이미지 + classification (**파일명 prefix가 라벨**, 폴더는 train/val/test split) |
| **공식** | https://data.mendeley.com/datasets/j45dj8bgfc/1 |
| **paper** | A. Khan, S. Khan, B. Hassan, Z. Zheng, *"CNN-Based Smoker Classification and Detection in Smart City Application,"* Sensors, vol. 22, no. 3, p. 892, 2022 |
| **라이선스** | **CC BY 4.0** (citation required) |
| **용량** | rar 약 65MB (`Smoker Detection.rar`) |
| **클래스** | Smoking (560) / NotSmoking (560) — 250×250 resize |

### 다운로드 절차

1. Mendeley Data 페이지 → **Download All Files** → `~/Downloads/Smoker Detection.rar`
2. rar 직접 읽기를 위해 `rarfile` Python 패키지 + 시스템 **7z / unrar / bsdtar 백엔드** 중 하나가 PATH에 있어야 함
3. **7-Zip (winget id `7zip.7zip`) 권장** — FOSS, command-line `7z.exe` 포함, `rarfile`가 자동 인식. 설치 후 `C:\Program Files\7-Zip`을 사용자 PATH에 추가

### 내부 구조 (실측)

```
Smoker Detection/
├── Training/      ← smoking_NNNN.jpg + notsmoking_NNNN.jpg 혼재
├── Validation/    ← smoking_NNNN.jpg + notsmoking_NNNN.jpg 혼재
└── Testing/       ← smoking_NNNN.jpg + notsmoking_NNNN.jpg 혼재
```

폴더 축은 **train/val/test split**, 클래스 축은 **파일명 prefix**(`smoking_` vs `notsmoking_`).

### 매핑

| Mendeley filename prefix | smoking 폴더 |
|---|---|
| `smoking_*.jpg` (560장) | `cigarette` (합산) |
| `notsmoking_*.jpg` (560장) | — (skip) |

파일명 prefix: `mds_`

### 처리 결과

- 1,120장 스캔 → notsmoking 560장 skip → **smoking 560장 → smoking/cigarette/**

---

## smoking 카테고리 최종 통계 (2026-05-27)

| 폴더 | HOD | Roboflow S&D | Mendeley | 합계 |
|---|---:|---:|---:|---:|
| **cigarette** (이미지) | 2,143 | 680 | 560 | **3,383** |
| cigarette (bbox txt) | 2,143 | 680 | 0 | **2,823** |

Mendeley는 classification 데이터셋이라 bbox 없음 → txt 미동반.

## drinking 카테고리 최종 통계 (2026-05-27)

| 폴더 | HOD | Roboflow S&D | 합계 |
|---|---:|---:|---:|
| **alcohol** (이미지) | 1,625 | 356 | **1,981** |
| alcohol (bbox txt) | 1,625 | 356 | **1,981** |

---

## violence 카테고리 최종 통계 (2026-05-25)

| 폴더 | XD-V | HOD | Roboflow | 합계 |
|---|---:|---:|---:|---:|
| **흉기** | — | 3,279 | 2,865 | **6,144** |
| **Riot** | 1,826 | — | — | 1,826 |
| **상해(피)** | — | 1,721 | — | 1,721 |
| **총기** | — | 1,602 | — | 1,602 |
| **Fighting** | 827 | — | — | 827 |
| **둔기** | — | — | 523 | 523 |
| **Car Accident** | 503 | — | — | 503 |
| **Explosion** | 284 | — | — | 284 |
| **Shooting** | 273 | — | — | 273 |
| **Abuse** | 20 | — | — | 20 |
| **합계** | 3,733 | 6,602 | 3,388 | **13,723** |

디스크 770MB.

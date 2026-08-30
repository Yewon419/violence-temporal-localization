# Smoking · Drinking 카테고리 데이터 작업 보고

> **아카이브 문서입니다.**
> 폐기된 객체검출 트랙의 작업 기록으로, 당시 상태를 그대로 보존한 것입니다.
> 현재 파이프라인은 [저장소 README](../../README.md)를 참고하세요.
> 이 트랙을 왜 접었는지는 README의 「전환 1」 절에 정리했습니다.

작업 기간: 2026-05-27
담당: 예원

---

## 한 줄 요약

영화 심의 보조 시스템의 **흡연·음주** 카테고리 데이터 풀 — 이미지 **5,364장 (3,383 + 1,981)**, bbox 라벨 **4,804개 (2,823 + 1,981)**. 같은 HF private dataset의 sub-path로 sync 완료. violence와 동일 패턴.

---

## 결과

### Hugging Face Datasets (private)

```
https://huggingface.co/datasets/DEteam4/movie-rating-violence
```

폴더 구조 (sub-path별 단일 폴더 시작):

```
smoking/cigarette/{hod,rfsd,mds}_*.jpg + {hod,rfsd}_*.txt
drinking/alcohol/{hod,rfsd}_*.jpg + {hod,rfsd}_*.txt
```

### 카운트 분포

| 카테고리/폴더 | 이미지 | bbox txt | 출처 |
|---|---:|---:|---|
| smoking/cigarette | **3,383** | **2,823** | HOD + Roboflow S&D + Mendeley |
| drinking/alcohol | **1,981** | **1,981** | HOD + Roboflow S&D |

출처별 분해:

| 출처 | smoking/cigarette | drinking/alcohol |
|---|---:|---:|
| HOD (YOLOv5 bbox) | 2,143 img + 2,143 txt | 1,625 img + 1,625 txt |
| Roboflow S&D (YOLOv8-OBB) | 680 img + 680 txt | 356 img + 356 txt |
| Mendeley Smoker (classification) | 560 img (라벨 없음) | — |

---

## 사용 데이터셋 (3개)

| 데이터셋 | 라이선스 | 용도 |
|---|---|---|
| HOD (Harmful Object Detection) | research-only | cigarette(class 3) → smoking, alcohol(class 0) → drinking. violence와 같은 zip 재사용 |
| Roboflow Smoking and Drinking Detection (YOLOv8-OBB) | **CC BY 4.0** | smoking(class 1) → smoking/cigarette, drinking(class 0) → drinking/alcohol. 행위 라벨 |
| Mendeley Smoker Detection (Khan et al., Sensors 2022, doi:10.17632/j45dj8bgfc.1) | **CC BY 4.0** (citation 의무) | smoking 클래스 560장 → smoking/cigarette 합산. classification 데이터셋이라 bbox 없음 |

출처 추적용 파일명 prefix: `hod_` / `rfsd_` / `mds_`. txt 라벨도 jpg와 동일 prefix·stem.

---

## 처리 핵심

- **단일 폴더 시작** — smoking/cigarette/, drinking/alcohol/ 한 폴더씩. 도구 종류축 세분화(맥주병/와인잔/소주병 또는 담배/시가/전자담배)는 1차 빌드 결과 보고 결정 보류. 보강 데이터셋 없이 인위적으로 쪼개면 빈 폴더 생김.
- **bbox 라벨 동시 보존** — HOD YOLOv5(`class cx cy w h`) + Roboflow OBB(`class x1 y1 x2 y2 x3 y3 x4 y4`) 원본 그대로 같은 폴더에 복사. ImageFolder는 jpg만 검출하므로 무해.
- **multi-bbox 라벨 그대로 복사** — cigarette/alcohol 외 다른 class 줄(예: HOD blood) 섞여 있을 수 있음. 학습 시점 필터링은 사용 측 책임. 이유: 정보 손실 회피.
- **Mendeley 구조 가정 오류 → 수정** — 초기 어댑터가 `Smoking/`·`NotSmoking/` 폴더 가정으로 0장 매칭. 실제는 `Training/Validation/Testing/`(split 축) + 파일명 prefix `smoking_`/`notsmoking_`(class 축). 어댑터를 prefix 매칭으로 교체.
- **Mendeley rar 처리** — `rarfile` 패키지 + 시스템 7z 백엔드. **7-Zip (winget `7zip.7zip`)** 설치 + user PATH에 `C:\Program Files\7-Zip` 추가하면 `rarfile`가 자동 인식.
- **Roboflow S&D OBB 호환성** — OBB 4꼭짓점 라벨도 첫 토큰이 class index인 점은 동일 → 기존 `parse_yolo_classes()` 재사용.

---

## 폴더 분류 framing (중요)

KMRB(영등위) 공식 등급분류기준은 **도구 종류축**이 아니라 **표현 정도축**으로 분류함. 우리 폴더(cigarette / alcohol)는 violence와 동일하게 **객체 검출 보조용 자체 분류 체계**.

추가로 smoking·drinking 폴더는 한 가지 framing 갈래가 더 있음:
- HOD cigarette/alcohol = **객체축** (cigarette 객체 bbox / alcohol bottle bbox)
- Roboflow S&D smoking/drinking = **행위축** (person + cigarette/bottle compositional bbox)
- Mendeley smoking = **행위축** (person-level classification)

세 출처가 한 폴더(cigarette / alcohol)에 합산되어 **객체축 + 행위축 혼합 신호**가 됨. 추후 행위축/객체축 분리가 필요해지면 폴더 재배치 (`docs/decisions.md §12·§13·§16`).

→ 발표·문서에서 "객체 검출 단일 layer"라고 단정하면 부정확. "객체 + 행위 보조 신호의 단일 폴더 합산"으로 framing.

---

## 데이터 사용법 (팀원)

### 1. 접근 권한

DEteam4 조직 멤버는 본인 HF write 토큰으로 즉시 접근 가능. 토큰 발급: https://huggingface.co/settings/tokens (type: Write).

### 2. 다운로드

```python
import os
from huggingface_hub import snapshot_download

local_dir = snapshot_download(
    repo_id="DEteam4/movie-rating-violence",
    repo_type="dataset",
    token=os.environ["HF_TOKEN"],
    # 흡연·음주만 받으려면 sub-path filter:
    allow_patterns=["smoking/**", "drinking/**"],
)
# local_dir/smoking/cigarette/*.jpg + *.txt
# local_dir/drinking/alcohol/*.jpg + *.txt
```

### 3. PyTorch ImageFolder로 로드 (classification 학습)

```python
from torchvision.datasets import ImageFolder
from torchvision import transforms

ds = ImageFolder(
    root=f"{local_dir}/smoking",
    transform=transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ]),
)
# ds.classes — ["cigarette"]  (현재는 단일 폴더)
```

ImageFolder는 jpg/png/jpeg만 검출하므로 같은 폴더의 `*.txt`는 자동 무시. classification 학습에 바로 사용 가능.

### 4. YOLO detection 학습 (bbox 사용)

같은 폴더에 `hod_<stem>.jpg ↔ hod_<stem>.txt` 페어가 들어있음. **multi-bbox 라벨에 다른 class 줄이 섞여 있을 수 있다는 점에 주의** — 학습 직전에 cigarette/alcohol class index만 남기도록 필터링 권장.

```python
# 예: HOD cigarette는 class 3
for txt in Path(local_dir, "smoking/cigarette").glob("hod_*.txt"):
    lines = [l for l in txt.read_text().splitlines() if l.strip().startswith("3 ")]
    # ...학습용 라벨로 사용
```

Roboflow S&D OBB는 class 1(smoking) / class 0(drinking) — 자세한 매핑은 `docs/datasets.md §4` 참고.

---

## 알려진 한계

- **단일 폴더** — 도구 종류축 세분화 학습 불가. 술 종류(맥주/와인/소주) 또는 흡연 도구(담배/시가/전자담배) 구분이 필요하면 추가 데이터셋 + 폴더 재배치 필요.
- **Mendeley 도메인 gap** — Mendeley Smoking은 250×250 web 이미지 / classification 데이터셋. 영화 frame과 외관 차이 존재. 학습 시 일반화 검증 필요.
- **multi-bbox 라벨 노이즈** — smoking/cigarette/ txt 안에 HOD blood(class 2) bbox 등 다른 카테고리 줄이 섞여 있을 수 있음. 학습 코드에서 필터링 필수.
- **드링킹 분포 부족** — alcohol 1,981장은 violence(20,766장) 대비 절대량이 작음. 학습 결과 양호하지 않으면 Roboflow alcohol 단독 데이터셋(DataCluster Labs 등) 추가 보강 검토.
- **bbox 미보존 카테고리 1개** — Mendeley 560장은 원본부터 라벨 없음. classification 신호로만 활용.

---

## 다음 단계

### 단기 — 같은 패턴 (팀원 분담)

- **공포 / 선정성** 카테고리: `README.md`의 「새 카테고리 추가 가이드」 따라 진행. NudeNet inference 또는 공포 표정/장면 데이터셋 선정 단계부터.

### 중기 — 모델 학습 + 평가

- ResNet 또는 YOLO 기반 1차 학습 → smoking·drinking detection recall 측정
- 학습 결과 보고 세분화 결정 (술 종류 / 흡연 도구 분리 필요성 판단)

---

## 코드·문서 위치

`C:\Users\windg\Desktop\SCHOOL\3-1\데이터엔지니어링\project2`

- `scripts/build_smoking.py` — smoking 카테고리 단일 entrypoint (HOD + Roboflow + Mendeley)
- `scripts/build_drinking.py` — drinking 카테고리 단일 entrypoint (HOD + Roboflow)
- `scripts/upload_to_hf.py` — HF 업로드 (`--split-by-class` 권장)
- `src/ingest/hod_extractor.py` — HOD violence/smoking/drinking 분기 (3 함수)
- `src/ingest/roboflow_smoking_drinking_extractor.py` — Roboflow S&D smoking·drinking 분기
- `src/ingest/mendeley_smoker_extractor.py` — Mendeley rar 처리 (rarfile + 7z 백엔드)
- `docs/datasets.md` — §2 HOD / §4 Roboflow S&D / §5 Mendeley 상세
- `docs/decisions.md` — §10~16 흡연·음주 결정 7개
- `docs/violence_report.md` — violence 카테고리 보고 (참고)

# Violence 카테고리 데이터 작업 보고

작업 기간: 2026-05-24 ~ 2026-05-25
담당: 예원

---

## 한 줄 요약

영화 심의 보조 시스템의 violence 카테고리 데이터 풀 — **10 폴더 / 20,766장 / 1.2GB**, HF private dataset에 sync 완료. 팀원이 다른 카테고리 작업 시 동일 패턴으로 진행 가능.

---

## 결과

### Hugging Face Datasets (private)

```
https://huggingface.co/datasets/DEteam4/movie-rating-violence
```

폴더 구조: `violence/{class_name}/{image}.jpg` (ImageFolder convention)

### 클래스별 분포

| 폴더 | 이미지 | 출처 |
|---|---:|---|
| 흉기 | 6,144 | HOD + Roboflow |
| Riot | 5,599 | XD-V |
| Fighting | 2,520 | XD-V |
| 상해(피) | 1,721 | HOD |
| 총기 | 1,602 | HOD |
| Car Accident | 1,054 | XD-V |
| Explosion | 817 | XD-V |
| Shooting | 721 | XD-V |
| 둔기 | 523 | Roboflow |
| Abuse | 65 | XD-V |
| **합계** | **20,766** | |

---

## 사용 데이터셋 (3개)

| 데이터셋 | 라이선스 | 용도 |
|---|---|---|
| XD-Violence test (500편 + frame-level annotation) | research-only | 영화·CCTV 폭력 keyframe 추출 (B1=Fighting / B2=Shooting / B4=Riot / B5=Abuse / B6=Car Accident / G=Explosion) |
| HOD (Harmful Object Detection) | research-only | 객체 이미지 (blood→상해(피), gun→총기, knife→흉기) |
| Roboflow Harmful Objects | CC BY 4.0 | 무기 객체 보강 (Axe/Hammer/Dumbbell→둔기, Knife/Scissors/Fork/Chisel/Screwdriver/Chainsaw→흉기) |

출처 추적용 파일명 prefix: XD-V (no prefix) / `hod_` / `rfh_`

---

## 처리 핵심

- **B-plan (segment cut → Katna)** — XD-V 영상에서 ffmpeg로 violence segment만 잘라낸 후 Katna 적용. A안(전체 영상 처리 후 필터) 대비 3-5배 빠름.
- **분당 30 keyframe** (KEYFRAMES_PER_MINUTE = 30) — N=10 첫 시도 후 데이터 양 부족 판단해 3배 증가.
- **cv2 균등 sampling fallback** — 짧은 segment에서 Katna가 0장 반환할 때 cv2로 균등 추출 (Abuse 20→65 효과 확인).
- **Multi-class 처리** — HOD·Roboflow는 두 폴더에 다 복사, XD-V는 첫 non-zero class.
- **OpenCV imwrite Windows unicode 버그 우회** — `cv2.imencode` + `Path.write_bytes`.

---

## 폴더 분류 framing (중요)

KMRB(영등위) 공식 등급분류기준은 **도구 종류축**이 아니라 **표현 정도축**(약함 → 경미 → 현실적 → 노골적)으로 분류함. 우리 폴더(총기/흉기/둔기/상해(피)/Fighting/…)는 **객체 검출 보조용 자체 분류 체계**이며 KMRB 기준의 직접 매핑이 아님.

→ 발표·문서에서 "KMRB 기준 그대로"라고 표현 금지. "객체 검출 layer가 폭력 도구·행위 등장 여부를 검출하여 심의 검토 보조" 정도로 framing.

---

## 데이터 사용법 (팀원)

### 1. 접근 권한

예원에게 본인 HF username 알려주면 dataset repo의 collaborator로 추가. 그 후 본인 HF write 토큰으로 접근 가능.

토큰 발급: https://huggingface.co/settings/tokens (type: Write)

### 2. 다운로드

```python
import os
from huggingface_hub import snapshot_download

local_dir = snapshot_download(
    repo_id="DEteam4/movie-rating-violence",
    repo_type="dataset",
    token=os.environ["HF_TOKEN"],
)
# local_dir/violence/{class_name}/*.jpg
```

### 3. PyTorch ImageFolder로 로드

```python
from torchvision.datasets import ImageFolder
from torchvision import transforms

ds = ImageFolder(
    root=f"{local_dir}/violence",
    transform=transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ]),
)
# ds.classes — 10 폴더 이름 (라벨)
```

---

## 알려진 한계

- **분포 불균형**: 흉기 6,144 ↔ Abuse 65 (약 94배 차이). 학습 시 class-weighted loss 또는 oversampling 필요.
- **Abuse 절대량 부족**: XD-V test annotation 라인이 8개뿐이라 한계. 공개 데이터셋에서 추가 보강도 100-200장 수준 (윤리·privacy 이슈).
- **도메인 gap**: HOD·Roboflow는 웹 수집 이미지라 영화 frame과 외관 차이 있음. 학습 시 일반화 검증 필요.

---

## 다음 단계 — 다른 카테고리 (팀원)

`README.md`의 "새 카테고리 추가 가이드" 참고. 패턴:

1. 데이터셋 선정·다운로드 → `~/Downloads/`
2. `src/ingest/<dataset>_extractor.py` 작성 (`hod_extractor.py` 패턴 참고)
3. `scripts/build_<category>.py` 작성 (`build_violence.py` 패턴 참고)
4. `docs/datasets.md` + `docs/decisions.md` 갱신
5. mypy/ruff 통과 후 HF 업로드 (`scripts/upload_to_hf.py --split-by-class`)

지원하는 카테고리 후보 (PDF 초안 기준): 선정성 (NudeNet pretrained model로 inference) / 흡연 / 음주 / 공포 / (조건부) 약물.

---

## 코드·문서 위치

`C:\Users\windg\Desktop\SCHOOL\3-1\데이터엔지니어링\project2`

- `scripts/build_violence.py` — 단일 entrypoint
- `scripts/upload_to_hf.py` — HF 업로드 (split-by-class 권장)
- `scripts/downsample.py` — 클립 균형 다운샘플 (사용 안 함)
- `src/ingest/` — 데이터셋별 어댑터
- `src/preprocess/` — Katna keyframe + segment cut
- `docs/datasets.md` — 데이터셋 출처·라이선스·매핑 상세
- `docs/decisions.md` — 설계 결정 9개 + 이유
- `README.md` — 빠른 시작 + 카테고리 추가 가이드

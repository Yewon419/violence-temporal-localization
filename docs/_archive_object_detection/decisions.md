# 설계 결정 로그

> **아카이브 문서입니다.**
> 폐기된 객체검출 트랙의 작업 기록으로, 당시 상태를 그대로 보존한 것입니다.
> 현재 파이프라인은 [저장소 README](../../README.md)를 참고하세요.
> 이 트랙을 왜 접었는지는 README의 「전환 1」 절에 정리했습니다.

본 프로젝트에서 내린 모든 핵심 결정과 그 이유를 시간순으로 누적합니다. 새 카테고리·새 데이터셋을 추가할 때 결정 이유를 같이 적어 코드만 봐서는 알 수 없는 맥락을 보존하세요.

---

## 0. 출력 형식 — 폴더가 라벨 (ImageFolder convention)

**결정**: CSV·DB labels 테이블 사용하지 않음. `data/processed/{category}/{class_name}/*.jpg` 평탄 구조 자체가 라벨.

**이유**:
- PyTorch `torchvision.datasets.ImageFolder`와 즉시 호환
- B2 / R2 / 학교 클라우드 등 어디든 폴더 그대로 sync만 하면 끝
- multi-label 표현은 한 이미지를 여러 폴더에 복사하는 것으로 충분 (multi-class 비율이 데이터셋별 0~9%로 낮음)
- DB schema (`src/db/schema.sql`)는 살려두지만 현재 카테고리에서는 미사용. 향후 segment-level human annotation이 필요할 때 활용 가능.

---

## 1. 카테고리 분류 축 — KMRB 기준과의 관계

**결정**: 우리 폴더 구조(violence/총기·흉기·둔기·상해(피)·Fighting·Shooting·…)는 **객체 검출 보조용 자체 분류 체계**임. KMRB 공식 등급분류기준의 직접 매핑이 아님.

**이유**: KMRB 공식 기준(영상물등급위원회) verbatim 확인 결과 —
- 폭력성 항목: "신체, 도구 등을 이용한 물리적 폭력이 [경미/현실적/노골적]으로 표현된 것"
- 모방위험 항목: "범죄 수법, **무기·흉기류** 사용 등 …"
- "둔기" / "총기" / "칼" / "피" 같은 도구 종류축 분류는 **어디에도 명시되지 않음**. KMRB는 "표현 정도축"으로만 등급화함.

**함의**:
- 발표·README에서 "KMRB 기준 그대로"라고 표현하지 말 것
- 우리 시스템은 객체 단위 검출(detection layer) → 향후 표현 정도·연속성·문맥 분석(judgment layer)이 결합되어야 KMRB 등급을 직접 보조할 수 있음. 현 단계는 detection layer만 다룸
- "둔기" 폴더 유지 사유: 영화 폭력씬에 둔기가 빈번히 등장 → 검출 보조 시스템으로서 누락하지 않기 위함 (사용자 결정, 2026-05-25)

---

## 2. 학습 라벨 검수 — 자동 전파만, 사람 검수 X

**결정**: 학습 단계에서 사람이 자동 라벨을 검수하지 않음. annotation/source 데이터셋의 라벨을 그대로 신뢰.

**이유**:
- XD-V는 frame-level annotation을 공식 제공 (논문 수반), HOD·Roboflow는 검수된 bbox 라벨
- 검수 단계를 도입하면 워크로드 폭발 (한 명당 17시간+) 대비 정확도 개선폭 불확실
- "쉽게 가자" 방향 (사용자, 2026-05-24)
- 검수가 필요해지면 추후 Label Studio + 자동 라벨 pre-fill 패턴으로 확장 가능

---

## 3. XD-V 처리 방식 — B-plan (segment cut → Katna)

**결정**: 영상 전체에 Katna를 돌리고 segment로 필터링(A안)하지 않음. ffmpeg로 violence segment를 먼저 cut한 다음 그 cut된 영상에만 Katna 적용 (B안).

**이유**: 처리 시간 차이 결정적
- A안: 500편 × 평균 5분 = 42시간 입력에 Katna LUV cluster를 전부 수행 → 25-40h
- B안: violence segment 분량만 (영상의 약 16%) → 4-8h + ffmpeg cut 1h

**구현 디테일**:
- ffmpeg cut은 **재인코딩** (libx264, `-c:v` 명시) — stream copy는 nearest keyframe부터 잘라 frame 정확도 떨어짐
- segment 길이에 비례해 `no_of_frames = max(1, int(seg_sec * 10 / 60))`
- segment 미만 1초 영상에서 Katna가 0장 반환하는 경우 발생 (2건, 무시)
- 영상 fps는 cv2.CAP_PROP_FPS로 영상별로 읽음 (XD-V 다수가 24fps이며 표준 25 가정과 다름)

---

## 4. multi-class 이미지 처리

**결정**: 모든 데이터셋에서 multi-class 이미지를 매칭되는 모든 폴더에 복사 (정책 통일).

**이유**:
- ImageFolder convention에서 multi-label은 "한 이미지를 여러 폴더에 두는 것"으로 표현 가능
- 객체 검출 학습 시 한 이미지에 gun+blood가 동시에 있으면 양쪽 모두 학습 신호로 사용해야 자연스러움
- 디스크 중복은 미미 (multi-class 비율: HOD 4.7%, Roboflow 0.1%, XD-V는 첫 class만 사용)

**예외**: XD-V annotation의 multi-class 라인(`B6-G-0` 등)은 **첫 non-zero class만** 사용. 영상→segment cut 비용이 크기 때문 (segment 한 번 cut을 두 폴더에 처리하는 코드 복잡도 vs 47/500 영상 영향 = trade-off에서 단순화 선택).

---

## 5. cv2.imwrite Windows unicode 버그 회피

**결정**: `cv2.imwrite` 대신 `cv2.imencode` + `Path.write_bytes`.

**이유**: OpenCV의 `cv2.imwrite`는 Windows에서 unicode 경로 (예: `데이터엔지니어링`) 또는 특수문자 (`=`, `#`)가 포함되면 silently fail. dry-run에서 발견되어 즉시 우회.

```python
ok, encoded = cv2.imencode(".jpg", frame)
if not ok:
    raise RuntimeError(...)
path.write_bytes(encoded.tobytes())
```

---

## 6. DB 백엔드 — SQLite 시작, PostgreSQL 호환 DDL

**결정**: 로컬 SQLite 파일 + PostgreSQL 호환 DDL (`src/db/schema.sql`). 현재 라벨링은 폴더 구조로 처리하므로 DB 미사용. 향후 4인 팀 공유 필요 시 Supabase free tier로 그대로 이전 가능.

**이유**:
- 단일 카테고리·단일 작업자 단계에서 Docker Postgres는 overkill
- DDL을 처음부터 PostgreSQL 호환으로 작성해 두면 마이그레이션이 mechanical
- SQLite는 `PRAGMA foreign_keys = ON` 필요, ENUM은 CHECK 제약으로 표현

---

## 7. 파일명 prefix 정책

**결정**: 출처별로 파일명 prefix 다르게.

| 출처 | prefix | 예 |
|---|---|---|
| XD-Violence (영상 추출) | (없음) | `v=xe4ee56aHSg__#1_seg000_kf0000.jpg` |
| HOD | `hod_` | `hod_image_001.jpg` |
| Roboflow Harmful Objects | `rfh_` | `rfh_img_42.jpg` |

**이유**: 폴더에서 출처 추적 가능. 같은 파일명 충돌 회피. 새 데이터셋 추가 시 prefix 추가 권장.

---

## 8. 클라우드 / 데이터 공유 — 보류

**결정**: 현재 로컬만. 향후 4인 팀 공유 시작 시 데이터셋(이미지) → Cloudflare R2 또는 학교 OneDrive, 메타데이터(필요해지면) → Supabase free tier.

**이유**:
- R2: 다운로드 빈번한 패턴에서 egress 무료가 결정적 (B2 $0.01/GB 대비)
- 학교 OneDrive(1TB 무료) 있으면 0원 — rclone으로 마운트
- 지금 단계는 단일 작업자라 로컬이 빠름

---

## 9. 둔기 폴더 — 유지 결정

**결정**: 둔기 폴더 유지. "흉기"로 통합하지 않음.

**이유**: 폭력 씬에 둔기(hammer / bat / axe / dumbbell)가 자주 등장하므로 검출 보조 시스템으로서 누락하지 않기 위함. KMRB 공식 기준에 없는 분류이지만 객체 검출 layer 관점에서 시각 feature가 칼·총과 다르므로 분리 학습이 유리.

**보강 데이터셋 후보** (현재 미사용 — 부족 시 단계적 도입):
- Open Images V7 (Baseball bat, Wrench subset)
- OD-WeaponDetection (gun/knife 추가 보강)
- 영화 frame 수동 큐레이션 (blood 보강용 — HOD가 사실상 유일한 공개 옵션이라 양 부족 시 필요)

---

## 10. 흡연·음주 — 별도 카테고리로 분리

**결정**: smoking / drinking을 각각 별도 카테고리로 분리. 단일 "substance" 카테고리로 통합하지 않음.

**이유**: KMRB 위해성 항목은 둘을 묶어 평가하지만, 객체 검출 layer 관점에서 시각 feature가 완전히 다름.
- 담배: 작고 손에 들림, 연기 동반, 입과의 접촉
- 술병/술잔: 크고 테이블에 놓임, 액체 컨테이너 특성

violence 카테고리와 동일한 "도구 종류축 자체 분류" 패턴. KMRB 직접 매핑 아님 (`§1` 동일 framing).

---

## 11. 흡연·음주 — 단일 폴더 시작, 세분화 보류

**결정**: smoking/cigarette/, drinking/alcohol/ 한 폴더씩으로 시작. 술 종류축(맥주/와인/소주) 또는 흡연 도구축(담배/시가/파이프/전자담배) 세분화는 1차 빌드 결과 보고 결정.

**이유**: violence의 폴더 세분화(흉기/총기/둔기/Riot/…)는 데이터셋 클래스가 그렇게 주어졌기 때문. 흡연·음주 데이터셋(HOD·Roboflow S&D)은 cigarette / alcohol 단일 클래스만 제공. 보강 데이터셋 없이 인위적으로 세분화하면 비어있는 폴더가 생김. 양·다양성을 먼저 확인하고 필요하면 추가 보강 데이터셋과 함께 세분화.

**향후 재검토 조건**: smoking/cigarette/ 또는 drinking/alcohol/ 한 폴더에 모인 시각 feature 분산이 너무 커서 모델 학습이 잘 안 되는 경우 (예: 영화 frame 내 cigarette 검출 recall < 0.5).

---

## 12. Mendeley classification 데이터셋 — 객체 검출 폴더로 단순 합산

**결정**: Mendeley Smoker Detection의 Smoking 클래스 560장을 smoking/cigarette/에 단순 합산. NotSmoking 클래스(560장)는 사용하지 않음.

**이유**:
- Mendeley는 person-level "흡연 여부" classification 데이터셋. 우리 폴더는 도구 종류축(cigarette).
- framing 차이 있음: Smoking 클래스 이미지는 "사람이 담배를 든 모습"이라 cigarette 객체가 어쨌든 frame 안에 들어 있음 → 객체 검출 학습 신호로도 활용 가능.
- NotSmoking는 cigarette 부재 이미지라 우리 분류에 신호 없음 → 버림.
- 행위/객체 framing 차이는 decisions.md에 명시(이 항목) — 발표에서 "객체 검출 단일 layer"라고 단정하지 말 것.

**향후 재검토 조건**: Mendeley 합산 이미지가 영화 frame 분포와 너무 멀어서 학습에 노이즈를 주는 경우, 별도 폴더(`smoking/smoker_person/`)로 분리하는 옵션 검토 (KMRB 측에 행위·객체 양축이 둘 다 필요해질 때).

---

## 13. Roboflow S&D 행위 라벨 → 객체 폴더 매핑

**결정**: Roboflow Smoking and Drinking Detection의 `0: drinking` / `1: smoking`(행위 라벨)을 각각 `drinking/alcohol/` / `smoking/cigarette/` (객체 폴더)에 매핑.

**이유**:
- Roboflow 라벨은 person + bottle/cigarette compositional bbox(OBB). 객체축으로 분리되어 있지 않음.
- 매핑하지 않으면 사용 불가. 영화 frame 분포(행위가 frame 안에서 동반됨)와 가까운 신호.
- §12 Mendeley와 동일한 framing 누락 인정: cigarette 폴더는 "객체 + 흡연 행위" 혼합 신호로 사용됨.
- 향후 객체축/행위축 분리가 필요해지면 별도 폴더로 옮기는 방향 (단일 폴더 시작 결정과 충돌 시점에 같이 검토).

---

## 14. Mendeley rar — rarfile 의존성 + 외부 7-Zip 백엔드

**결정**: Mendeley가 rar 형식으로 배포되므로 `rarfile>=4.1` Python 의존성을 추가하고, 시스템에 7z/unrar/bsdtar 백엔드를 PATH에 두어야 함. **7-Zip (winget `7zip.7zip`) 선택**.

**이유**:
- Mendeley 페이지에 zip 옵션이 없음. 수동 압축 해제는 ImageFolder 폴더로 두는 옵션도 있었으나, violence의 다른 어댑터(zip 직접 읽기) 패턴과 통일성을 위해 코드가 rar 직접 처리.
- `rarfile`은 백엔드로 unrar/bsdtar/7z 중 하나만 있으면 동작. Windows 11에는 기본 백엔드 없음 → 외부 설치 필요.
- 7-Zip을 unrar.exe 대신 선택한 이유: FOSS (LGPL/BSD), winget 표준 패키지, command-line + GUI 동봉, rar 외 다른 압축 형식도 처리해 향후 효용성 큼.
- 설치 후 `C:\Program Files\7-Zip`을 user PATH에 영구 추가 → 새 shell에서 `7z` 명령 자동 인식 → `rarfile`가 자동 검출.

**구현 디테일**: pyproject.toml의 mypy overrides에 `rarfile` 추가 (third-party stubs 없음). 코드에는 백엔드 경로를 박지 않음 (PATH 의존, 팀원 환경 portable).

---

## 15. Mendeley 클래스 축 — 파일명 prefix (폴더 아님)

**결정**: Mendeley Smoker Detection의 클래스 축이 폴더가 아닌 **파일명 prefix**(`smoking_*.jpg` vs `notsmoking_*.jpg`)임을 어댑터에서 prefix 매칭으로 처리.

**이유**:
- 초기 가정(`Smoking/` / `NotSmoking/` 폴더)으로 작성한 첫 어댑터가 0장 매칭 — 1,120장 모두 `notsmoking_class`로 skip되는 버그로 드러남.
- 실제 구조: `Smoker Detection/{Training|Validation|Testing}/` 아래에 두 prefix 파일이 혼재. 폴더 = split 축, 파일명 prefix = class 축.
- 어댑터를 `_is_smoking_filename(name)`로 교체 → `Path(name).name.lower().startswith("smoking_")` 검사. `notsmoking_`은 자연스럽게 제외 (앞에 "not" 있음).

**향후 재검토 조건**: Mendeley v2 이상에서 폴더 분류로 재구성된다면 어댑터 재작성 — `data.mendeley.com/datasets/j45dj8bgfc/2` 등 새 버전 확인 시점.

---

## 16. smoking·drinking — bbox 라벨(txt) 동시 보존

**결정**: smoking·drinking 카테고리는 어댑터가 이미지뿐 아니라 원본 데이터셋의 bbox 라벨 txt도 같은 폴더에 동반 복사. violence는 미적용.

**범위**:
- HOD smoking → `smoking/cigarette/hod_<stem>.txt` (YOLOv5 5-token bbox)
- HOD drinking → `drinking/alcohol/hod_<stem>.txt`
- Roboflow S&D smoking/drinking → 각각 `rfsd_<stem>.txt` (YOLOv8-OBB 9-token polygon)
- Mendeley Smoker: 원본이 classification only → 라벨 없음, txt 미생성

**이유**:
- §0 "폴더가 라벨" 결정은 이미지 단위 멀티라벨 학습이 1차 가정. 그러나 같은 데이터를 future detection 모델 학습에도 쓸 수 있도록 정보 보존을 같이 가져감.
- 추가 비용 미미 (smoking 라벨 2,823개 ~수백KB, drinking 1,981개 ~수백KB). HF re-sync도 jpg는 hash skip되고 txt만 추가됨.
- ImageFolder convention과 충돌 없음: torchvision의 ImageFolder는 image extension만 검출 → txt는 무해 무시.

**multi-bbox 정책 (재확인)**: 한 이미지에 cigarette 외 다른 class(예: HOD blood)도 bbox로 있으면 그대로 보존 (필터링 X). 즉 `smoking/cigarette/hod_X.txt` 안에 `class=2 (blood)` 라인이 섞여 있을 수 있음. 학습 시점에 필요한 class만 골라 쓰는 책임은 사용 측. 이유: 정보 손실 회피, 어댑터 단순성, 사용자 결재(2026-05-27).

**violence 미적용 이유**: violence/{흉기·총기·둔기·상해(피)} 폴더는 HOD/Roboflow Harmful 출처라 원본에 bbox가 존재. 그러나 본 결정 시점에서 사용자가 명시적으로 smoking·drinking로만 범위 한정. violence 추가는 별도 결재 시 동일 패턴으로 어댑터 한 줄 추가하면 됨 (XD-V 출처 6폴더는 영상 segment annotation이라 이미지 bbox 원래 없음 — 적용 대상 아님).

**파일명 페어**: jpg와 txt는 stem 동일, 폴더 동일. dst.exists() 체크로 idempotent — 빌드 재실행 시 이미지·라벨 각각 따로 skip.

---

## 결정 추가 시 형식

```markdown
## N. 짧은 결정 한 줄 (제목)

**결정**: 한 줄 요약

**이유**: 글머리 또는 짧은 문단

**구현 디테일** (있을 때): 코드/패턴/숫자

**향후 재검토 조건** (있을 때): "X가 발생하면 다시 본다"
```

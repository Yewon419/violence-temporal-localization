# CVAT 워크플로우 — drama_frames false positive 검수

GD가 생성한 bbox를 CVAT에 미리 깔아두고 팀원 6명이 검수하는 흐름.
대표님 자체 호스팅 → 팀원 invite → Project/Task/Job 분담 → YOLO export → HF push.

---

## 1. CVAT 셋업 (대표님 PC 1회만)

### 1.1 사전 조건
- Docker Desktop (AutoStock 운영 중이라 이미 설치됨)
- 메모리: Docker에 최소 8GB 할당 권장 (Settings → Resources → Memory)
- 디스크: 약 5GB (이미지·DB·redis)
- 포트 8080 사용 가능

### 1.2 설치
```powershell
cd C:\Users\windg\Desktop\PROJECT
git clone https://github.com/cvat-ai/cvat.git
cd cvat
docker compose up -d
```

5-10분 후 컨테이너 전부 healthy 확인:
```powershell
docker compose ps
```

### 1.3 admin 계정 생성
```powershell
docker exec -it cvat_server bash -c "python3 manage.py createsuperuser"
```
- username: `yewon` (또는 본인 ID)
- email: `windgarden05@gmail.com`
- password: 강력하게

### 1.4 첫 접속
`http://localhost:8080` → admin 로그인

---

## 2. Project + label class 사전 정의

### 2.1 Project 생성
- **Tasks** 메뉴 → **+ Create new project**
- Name: `drama_frames_fp_review`
- Labels: 아래 7개 추가 (`+ Add label` 반복):

| label name | color | 의미 |
|---|---|---|
| cigarette | 빨강 | 담배 객체 |
| bottle | 노랑 | 술병 (소주병·맥주병·와인병 등) |
| cup | 주황 | 술잔·일반 cup |
| wine_glass | 보라 | 와인잔 (선택) |
| alcohol | 파랑 | 술 전반 (캔·기타) |
| smoking_act | 분홍 | 흡연 행위 (사람 + 담배 compositional) |
| drinking_act | 청록 | 음주 행위 |

회의에서 정확히 확정. 일단 GD가 뱉은 raw label + 행위 단어 분리 안.

### 2.2 그 외 옵션
- Issue tracker: off (학교 프로젝트)
- Assignee: 비워둠 (Task 단위에서 분배)

---

## 3. GD pre-annotation 변환 → Task import

### 3.1 변환 스크립트
`scripts/gd_to_cvat_coco.py` 실행 → 영상별 COCO 1.0 JSON 생성.

```powershell
.venv\Scripts\python.exe scripts\gd_to_cvat_coco.py --video-id vyXEi00PVrw
# 출력: data/processed/cvat_import/vyXEi00PVrw/coco.json + 이미지들
```

산출물:
- `data/processed/cvat_import/{video_id}/coco.json` — COCO format
- `data/processed/cvat_import/{video_id}/images/*.jpg` — frame 파일 (CVAT에 같이 업로드)

### 3.2 CVAT Task 생성
- Project 안에서 **+ Create new task**
- Name: `{video_id} ({label})` (예: `vyXEi00PVrw (신세계)`)
- Subset: `default`
- **Select files** → 위 images/ 폴더 드래그
- Submit → Task 생성됨

### 3.3 pre-annotation upload
- Task 상세 페이지 → **Actions** → **Upload annotations**
- Format: **COCO 1.0**
- 위 `coco.json` 선택 → upload

→ Frame 열면 GD bbox 미리 그려져 있음 ✅

---

## 4. Job 분할 + 팀원 분배

### 4.1 자동 split
- Task 생성 시 **Segment size**로 자동 분할 (예: 영상 1000 frame → 200 frame씩 5 Job)
- 또는 Task 생성 후 **Actions → Job Configuration**

### 4.2 팀원 invite
- 사이드바 **Organization** → 본인 org 생성 → 팀원 6명 email invite
- Project 우상단 **Memberships** → 멤버 추가
- Job 별 **Assignee** 지정 (한 사람당 평균 200 frame)

### 4.3 분담 안 (예시 — 10 video 6 사람)
| 검수자 | 담당 영상 | frame |
|---|---|---|
| 1 | 황해 + 친구 | 1794 + 459 = 2253 |
| 2 | 범죄와의 전쟁 | 1761 |
| 3 | 달콤한 인생 | 1532 |
| 4 | 비열한 거리 + 마약왕 | 1182 + 459 = 1641 |
| 5 | 베테랑 + 흡연 컴파일 | 1145 + 651 = 1796 |
| 6 | 내부자들 + 신세계 | 1014 + 896 = 1910 |

**근데 우리 Task는 frame 100장씩 sampling된 GD 결과 기준** → 분담 더 줄어듦 (각자 약 100~200 frame).

---

## 5. 검수 단축키 (CVAT 기본)

| 키 | 동작 |
|---|---|
| `N` | 새 bbox 그리기 |
| `Delete` | 선택 bbox 삭제 |
| `D` / `F` | 이전 / 다음 frame |
| `Q` | bbox 잠금/해제 |
| `Ctrl+S` | 저장 |
| `Esc` | 그리기 취소 |
| 마우스 휠 + Ctrl | zoom |

**검수 규칙 (회의 합의 안)**:
- ✅ GD bbox가 정확 → 그대로 두기
- ✏️ bbox 크기·위치 어긋남 → 정확히 resize
- 🔄 label 잘못 (예: cigarette → bottle) → label 변경
- ❌ bbox 자체가 false positive (객체 아님) → **Delete**
- ➕ GD가 놓친 객체 → **N**으로 새 bbox 추가

---

## 6. export → HF push

### 6.1 CVAT export
- Project 메뉴 → **Actions** → **Export project dataset**
- Format: **YOLO 1.1**
- 다운로드 zip → `data/processed/cvat_export/yolo.zip`

### 6.2 HF 변환 + push
- zip 해제 → `{video_id}/{frame_stem}.txt` (YOLO 5-token)
- 별도 스크립트 `scripts/upload_cvat_labels.py` 작성 예정
- HF push 경로: 회의 결정 (예: `smoking/drama_frames_labels/{video_id}/*.txt`)

---

## 7. 알려진 한계 + 트러블슈팅

- **포트 충돌**: 8080 이미 사용 중이면 `docker-compose.yml`의 `CVAT_HOST` + 포트 변경 또는 다른 서비스 끄기
- **메모리 부족**: Docker Desktop이 OOM kill 발생 시 Memory 늘리기
- **느린 image upload**: 1,000 frame 한 task에 올리면 5-10분. 인내심
- **label class 변경**: Project 단위. 도중 변경 시 기존 annotation 영향 — **회의에서 사전 확정 필수**
- **multi-user 동기화**: 한 Job을 두 명이 동시 편집 시 conflict. assignee 1인 원칙
- **YOLO export class index**: CVAT가 알파벳 순 또는 생성 순으로 index 부여. README에 매핑표 적어둘 것

---

## 8. 다음 단계

1. **대표님**: 1·2번 셋업 직접 진행 + 막히는 부분 본인에게 보고
2. **본인**: GD → COCO 변환 스크립트(`scripts/gd_to_cvat_coco.py`) 작성
3. **회의**: label class 7개 확정 + 검수 규칙 합의
4. **팀원 onboarding**: 본 문서 정제판 공유 + Slack/Zoom 30분 시연

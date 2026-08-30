# 폭력 구간 탐지 데모 (Violence Temporal Localization Demo)

업로드한 임의 영상에서 사람 대 사람 물리폭력 구간(start~end)을 찾아
타임라인으로 보여주는 로컬 Streamlit 데모. 발표 요구사항의 "working demonstration"에 해당.

- 코드: `DE_PJ2/demo_app.py` (단일 파일)
- 모델: `DE_PJ2/violence_transformer.pth`
- 실행: 로컬 CPU (학습은 별도 Colab GPU, `pj2_lstm4.ipynb`)

---

## 1. 파이프라인

학습(`build_clips.py` + `violence_annotator/app.py` + `pj2_lstm4.ipynb`)과 **수치까지 동일**하게 맞춤.
어긋나면 모델이 다른 분포를 보고 헛돌기 때문.

```
영상(mp4 등)
 → ① cv2 2fps 프레임 추출 (0-base, jpg encode/decode 재현)
 → ② ResNet50(IMAGENET1K_V1, fc 제거 + avgpool) → 프레임당 2048-d 벡터
 → ③ clip_len=4 / stride=2 슬라이딩 (영상 전체) → 클립 (N,4,2048)
 → ④ 영상 단위 StandardScaler 정규화
 → ⑤ Transformer Encoder(.pth) → 클립별 violence 확률
 → ⑥ Gaussian 스무딩 → 히스테리시스 병합 → 짧은 구간 제거
 → 폭력 구간(start~end)
```

### 학습 일치 상수 (변경 금지)
| 항목 | 값 | 출처 |
|---|---|---|
| 프레임 추출 | 2fps, cv2, `frame_{idx:06d}.jpg`, 0부터 | `annotator/app.py` |
| 시간 매핑 | 프레임 k = k/2 초 | 위 |
| 백본 | resnet50 `IMAGENET1K_V1`, `children()[:-1]` (avgpool까지) | `build_clips.py` |
| 입력 변환 | Resize(224,224) + ImageNet normalize | `build_clips.py` |
| 피처 | 프레임당 2048-d **벡터** (feature map 아님, GAP됨) | 위 |
| 클립 | clip_len=4, stride=2 | `build_clips.py` |
| 클립 j 시각 | 프레임 [2j … 2j+3] = [j … j+1.5] 초 | 계산 |
| 정규화 | 영상 단위 StandardScaler | `pj2_lstm4` test 셀 |

> **학습과의 유일한 차이**: `build_clips.py`는 어노테이션된 구간만 클립화하지만,
> 데모는 어노테이션이 없으므로 영상 전체를 stride=2로 슬라이딩한다.

---

## 2. 모델

- **Transformer Encoder** (`ViolenceTransformer`) — LSTM 아님.
  - `d_model=2048, nhead=8, num_layers=2, dim_feedforward=512`, 마지막 토큰 → `Linear(2048, 2)`
  - 체크포인트 `violence_transformer.pth`가 위 구조와 1:1 (load_state_dict 통과 확인됨)
- 비교군(노트북): LSTM / TCN / BiLSTM / Transformer+Scheduler. **Test Acc 최고가 plain Transformer(0.72)** 라 데모에 채택.
- 2-클래스: `violence` vs `neg`. (학습 시 `neg_hard`를 `neg_easy`에 통합 → 사실상 violence/non-violence 이진분류)

---

## 3. 후처리 — 액션 사이 틈 메우기 (A+B)

클립 예측은 노이즈가 있어 단일 threshold로 자르면 짧은 dip에서 끊긴다. 두 표준 기법으로 해결(전부 후처리, 재학습 불필요).

### A. 히스테리시스 병합 (이중 threshold)
- 시작은 `t_high`(기본 0.45) 넘어야 구간 개시.
- 일단 켜지면 `t_low`(= t_high − 0.15) 밑으로 떨어질 때까지 **유지** → 중간 dip 무시.
- `t_low` 밑이라도 `max_gap`(1클립)까지는 메워서 잇는다.
- 출처: Canny edge / 음성구간검출의 hysteresis thresholding.

### B. Gaussian 가중 스무딩
- 기존 균등 이동평균(window=3) 교체. `sigma=1.0`.
- 가까운 강한 이웃일수록 크게, 멀수록 약하게 확률을 끌어올림(거리 감쇠) → 강한 액션이 옆 dip을 위로 당김.

### 동작
| 상황 | 결과 |
|---|---|
| 액션 사이 짧고 얕은 틈 | 이어붙임 |
| 길거나 깊은 틈 | 끊음 (별개 구간) |

### 후처리 파라미터 (`demo_app.py` 상단 상수)
| 상수 | 기본값 | 의미 |
|---|---|---|
| `DEFAULT_THRESHOLD` | 0.45 | 구간 시작 t_high (사이드바 슬라이더 기본값) |
| `HYST_DELTA` | 0.15 | t_low = t_high − delta |
| `GAUSS_SIGMA` | 1.0 | 스무딩 강도(클립 단위) |
| `MAX_GAP_CLIPS` | 1 | t_low 밑이어도 메우는 클립 수 |
| `MIN_DURATION_SEC` | 2.0 | 이보다 짧은 구간 제거 |

---

## 4. UI / 출력

- **커스텀 HTML5 플레이어** (`render_player`): 영상을 base64로 임베드하고 진행바를 직접 그림.
  - 진행바에 폭력 구간을 **빨갛게 색칠**.
  - 바를 클릭하면 그 시각으로 이동+재생. **빨간 구간 안을 클릭하면 그 구간의 첫 프레임(start)으로 스냅**.
  - 재생 진행/플레이헤드 실시간 표시, 재생/일시정지, `현재시각 / 전체길이`.
  - (native `st.video`는 진행바 스타일링이 불가능해 커스텀으로 대체.)
- **타임라인 차트** (matplotlib): smoothed 확률 곡선 + `t_high`/`t_low` 선 + 폭력 구간 음영.
- **구간 표**: 구간(mm:ss~mm:ss) / 길이 / 최고확률.
- **메트릭 카드**: 영상 길이, 클립 수, 폭력 구간 수, **영상 내** 폭력 클립 비율(상대값 — 영상 간 비교 금지, §8.5).
- **사이드바**: `t_high` 슬라이더 하나(유지값·sigma는 자동/상수). 발표용으로 노브 최소화.
- **캐싱**: 업로드 바이트 해시로 피처 캐시 → 같은 영상 재분석 즉시.

---

## 5. 실행

### 로컬
```
.venv\Scripts\streamlit run DE_PJ2\demo_app.py
```
→ http://localhost:8501 . 같은 와이파이면 Network URL로 다른 기기 접속 가능.

### 원격(팀 테스트) — 임시 공개 터널
터널 들어오면 Host가 바뀌어 websocket이 막힐 수 있어 CORS/XSRF를 끄고 띄운다.
```
# 1) 터널 호환 플래그로 서버
.venv\Scripts\streamlit run DE_PJ2\demo_app.py --server.headless true ^
  --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false

# 2) cloudflared quick tunnel (계정 불필요, 임시 https URL 발급)
cloudflared tunnel --url http://localhost:8501
```
- 발급 URL은 **임시** — 서버/터널 끄거나 PC 절전·재부팅 시 죽고, 재실행하면 새 URL.
- 링크 아는 사람은 누구나 접속·업로드 가능 → 팀 채팅에만 공유.
- CPU 추론이라 동시 업로드는 직렬 처리로 느려짐 → "짧은 클립, 한 명씩" 안내.

---

## 6. 환경 / 의존성

- Python 3.10 (`project2/.venv`)
- torch **2.12.0+cpu** (CPU 추론), torchvision, opencv-python, scikit-learn, numpy, pillow
- streamlit 1.58, matplotlib 3.10 (데모용으로 추가 설치)
- cloudflared (원격 터널 시)

---

## 7. 검증 상태

- `mypy`(strict) + `ruff`: **에러 0**.
- 실제 영상 end-to-end 스모크: 32초 클립 → 65프레임 → (65,2048) 피처 → 31클립 → 확률 정상 분포.
- 체크포인트 load_state_dict 통과(구조 일치).
- 후처리 합성 신호 테스트: 얕은 dip 1구간 병합 / 깊은 dip 2구간 분리 / Gaussian 레벨 보존 확인.

---

## 8. 알려진 제약 / 주의

- **데모 영상은 학습/test 71편(movie_id) 밖에서** 골라야 함. 안 그러면 "본 영상" 반박.
  (`clipped/x2PjLCMrfTk_*`는 학습 영화 → 금지)
- 모델 천장이 Test Acc ~0.72, violence recall ~0.6. 어떤 모델로 바꿔도 비슷 → feature/데이터가 병목. 발표에서 정확도 과장 금지.
- base64 임베드라 수백 MB 영상은 브라우저 전송이 느림 → 짧은 클립 권장.
- 발표는 사전 렌더(미리 한 번 돌려 캡처/녹화) 권장 — 현장 로딩·네트워크 사고 방지.
- "CNN feature map"이라 쓰지 말 것 — 실제는 GAP된 2048-d **벡터**. "ResNet50 frame embedding(2048-d)"가 정확.
- **'영상 내 폭력 클립 비율' 메트릭은 영상 단위 상대값** — 서로 다른 영상끼리 비교해 "어느 영화가 더 폭력적"인지 판단 금지. UI에도 경고 캡션 달아둠. (근거는 §8.5)
- feature는 ResNet만 전체 변환·학습됨. **optical flow는 팀원 WIP(부분집합), VideoMAE는 GPU 비용으로 보류** → 데모는 ResNet 고정, 둘 다 향후 과제.

---

## 8.5 분석: 영화 단위 폭력비율은 이 시스템으로 측정 불가

"폭력 많은 영화와 적은 영화의 폭력 클립 비율이 비슷하게 나온다"는 관찰을 검증함
(`DE_PJ2/exp_norm_compare.py`, 라벨 있는 test 9편으로 per-video vs global 정규화 비교).

| 정규화 | 예측 폭력비율 범위 | 표준편차 | GT 상관 |
|---|---|---|---|
| per-video (현재) | 31~37% | 1.9%p | 0.06 |
| global (학습 통계) | 14~51% | 11.6%p | -0.06 |

결론:
1. **per-video StandardScaler 가 원인** — 영화 간 절대 강도를 지워 모든 영화를 비슷한 비율(~35%)로 압축. 모델 성능 문제가 아님.
2. **그런데 GT 폭력비율도 전 영화 40.0%로 동일(std 0.0%p)** — `build_clips.py`의 `neg_ratio=1.5`가 영화마다 1:1.5 (=40%)로 클립을 균형 샘플링해서 저장했기 때문. 즉 **데이터 자체에 "영화가 얼마나 폭력적인가" 신호가 없음.**
3. **global 정규화는 해결책 아님** — 비율이 퍼지긴 하나 GT 상관 ≈ 0. 모델이 per-movie 정규화로 학습돼 생긴 분포 불일치 노이즈일 뿐.

따라서 **영화 단위 폭력 강도/등급은 이 파이프라인의 유효한 출력이 아니다.**
두 설계(per-movie 정규화 + per-movie 균형 샘플링)가 독립적으로 cross-movie 강도를 제거하며,
둘 다 본래 과제인 **temporal localization("이 영화 어디가 폭력인가")** 에는 정확히 부합한다.
영화 단위 등급이 필요하면: ① per-movie 균형 안 한 데이터 ② global/무정규화 ③ 실제 영화별
폭력비율 있는 held-out 재학습·검증 — 데이터+학습 재설계(팀 결정 사안).

---

## 9. 향후 (미구현, 후보)

- 심의 보조 지표(총 폭력시간/런타임 %, 최장 연속 구간, 분당 빈도)
- GT 비교 모드(라벨 클립에서 예측 vs 정답 오버레이)
- 처리 효율 지표(추출+추론 시간, 초당 처리 프레임)
- (영화 단위 등급이 필요하면) §8.5 의 데이터+정규화 재설계

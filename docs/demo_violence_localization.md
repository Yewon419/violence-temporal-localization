# 폭력 구간 탐지 데모 사양

업로드한 영상에서 사람 대 사람 물리폭력 구간(start~end)을 찾아 타임라인으로 보여주는
로컬 Streamlit 앱의 전체 사양입니다. 이 프로젝트에서 가장 상세한 기술 문서입니다.

- 코드: [`../DE_PJ2/demo_app.py`](../DE_PJ2/demo_app.py) 단일 파일
- 모델: `violence_transformer.pth` ([Release](../../releases)에서 받아 `DE_PJ2/` 아래에 둡니다)
- 실행: 로컬 CPU 추론. 학습은 별도 Colab GPU에서 진행했고 노트북은 `../DE_PJ2/pj2_lstm4.ipynb`

---

## 1. 파이프라인

학습 경로(`build_clips.py` + `violence_annotator/app.py` + `pj2_lstm4.ipynb`)와 **수치까지 동일**하게 맞췄습니다.
전처리가 한 군데라도 어긋나면 모델이 학습 때와 다른 분포를 보게 되어 그대로 헛돕니다.

```
영상(mp4 등)
 → ① cv2 2fps 프레임 추출 (0-base, jpg encode/decode 재현)
 → ② ResNet50(IMAGENET1K_V1, fc 제거 + avgpool) → 프레임당 2048-d 벡터
 → ③ clip_len=4 / stride=2 슬라이딩 (영상 전체) → 클립 (N, 4, 2048)
 → ④ 영상 단위 StandardScaler 정규화
 → ⑤ Transformer Encoder → 클립별 violence 확률
 → ⑥ Gaussian 스무딩 → 히스테리시스 병합 → 짧은 구간 제거
 → 폭력 구간 [start, end]
```

### 학습과 일치시켜야 하는 상수

이 값들은 임의로 바꾸면 안 됩니다. 학습 시점의 전처리와 1:1로 대응합니다.

| 항목 | 값 | 근거 |
|---|---|---|
| 프레임 추출 | 2fps, cv2, `frame_{idx:06d}.jpg`, 0부터 | `violence_annotator/app.py` |
| 시간 매핑 | 프레임 k = k/2 초 | 위와 동일 |
| 백본 | resnet50 `IMAGENET1K_V1`, `children()[:-1]` (avgpool까지) | `build_clips.py` |
| 입력 변환 | Resize(224, 224) + ImageNet normalize | `build_clips.py` |
| 피처 | 프레임당 2048-d **벡터** (feature map이 아니라 GAP된 결과) | 위와 동일 |
| 클립 | clip_len=4, stride=2 | `build_clips.py` |
| 클립 j의 시각 | 프레임 [2j … 2j+3] = [j … j+1.5] 초 | 위에서 계산 |
| 정규화 | 영상 단위 StandardScaler | `pj2_lstm4.ipynb` test 셀 |

> **학습 경로와의 유일한 차이**: `build_clips.py`는 어노테이션된 구간만 클립으로 만들지만,
> 데모는 어노테이션이 없으므로 영상 전체를 stride=2로 슬라이딩합니다.

---

## 2. 모델

**Transformer Encoder** (`ViolenceTransformer`)입니다. 이름과 달리 LSTM이 아닙니다.

- `d_model=2048, nhead=8, num_layers=2, dim_feedforward=512`, 마지막 토큰을 `Linear(2048, 2)`로
- 체크포인트가 위 구조와 1:1로 대응합니다 (`load_state_dict` 통과 확인)
- 2-클래스 분류입니다. 학습 시 `neg_hard`를 `neg_easy`에 통합했으므로 사실상 violence / non-violence 이진분류입니다

비교군으로 LSTM, TCN, BiLSTM, Transformer+Scheduler를 돌렸고 **plain Transformer가 Test Acc 0.72로 가장 높아** 데모에 채택했습니다.

---

## 3. 후처리: 액션 사이의 틈 메우기

클립 예측에는 노이즈가 있어서 단일 threshold로 자르면 액션 중간의 짧은 dip에서 구간이 끊깁니다.
한 번의 싸움이 서너 개 구간으로 쪼개져 나오는 문제입니다.
재학습 없이 후처리 두 가지로 해결했습니다.

### A. 히스테리시스 병합 (이중 threshold)

- 구간을 시작하려면 `t_high`(기본 0.45)를 넘어야 합니다
- 일단 켜지면 `t_low`(= t_high − 0.15) 밑으로 떨어질 때까지 **유지**합니다. 중간 dip을 무시하게 됩니다
- `t_low` 밑이라도 `max_gap`(1클립)까지는 메워서 잇습니다

Canny edge detection과 음성 구간 검출에서 쓰는 이중 threshold와 같은 발상입니다.

### B. Gaussian 가중 스무딩

- 기존의 균등 이동평균(window=3)을 대체했습니다. `sigma=1.0`
- 가까운 강한 이웃일수록 크게, 멀수록 약하게 반영합니다(거리 감쇠).
  강한 액션이 옆의 dip을 위로 끌어올리는 효과가 있습니다

### 결과

| 상황 | 동작 |
|---|---|
| 액션 사이의 짧고 얕은 틈 | 이어붙임 |
| 길거나 깊은 틈 | 끊음 (별개 구간) |

### 파라미터 (`demo_app.py` 상단 상수)

| 상수 | 기본값 | 의미 |
|---|---|---|
| `DEFAULT_THRESHOLD` | 0.45 | 구간 시작 t_high (사이드바 슬라이더 기본값) |
| `HYST_DELTA` | 0.15 | t_low = t_high − delta |
| `GAUSS_SIGMA` | 1.0 | 스무딩 강도 (클립 단위) |
| `MAX_GAP_CLIPS` | 1 | t_low 밑이어도 메우는 클립 수 |
| `MIN_DURATION_SEC` | 2.0 | 이보다 짧은 구간은 제거 |

---

## 4. UI

**커스텀 HTML5 플레이어** (`render_player`): 영상을 base64로 임베드하고 진행바를 직접 그립니다.

- 진행바에 폭력 구간을 빨갛게 칠합니다
- 바를 클릭하면 그 시각으로 이동해 재생하고, **빨간 구간 안을 클릭하면 그 구간의 첫 프레임으로 스냅**합니다
- 재생 진행과 플레이헤드를 실시간 표시하고, 재생·일시정지와 `현재시각 / 전체길이`를 보여줍니다

Streamlit 기본 `st.video`는 진행바 스타일링이 불가능해서 직접 만들었습니다.

그 외 구성 요소는 다음과 같습니다.

- **타임라인 차트**(matplotlib): smoothed 확률 곡선 + `t_high`/`t_low` 선 + 폭력 구간 음영
- **구간 표**: 구간(mm:ss~mm:ss) / 길이 / 최고확률
- **메트릭 카드**: 영상 길이, 클립 수, 폭력 구간 수, 영상 내 폭력 클립 비율
  (상대값입니다. 영상 간 비교 금지. 근거는 6장)
- **사이드바**: `t_high` 슬라이더 하나만 둡니다. 나머지는 상수로 고정했습니다
- **캐싱**: 업로드 바이트 해시로 피처를 캐시해 같은 영상은 즉시 재분석됩니다

---

## 5. 실행

```bash
pip install -r requirements.txt
streamlit run DE_PJ2/demo_app.py
```

http://localhost:8501 에서 열립니다. 같은 네트워크의 다른 기기에서는 Network URL로 접속할 수 있습니다.

### 임시 공개 링크로 공유하기

터널을 거치면 Host가 바뀌어 websocket이 막힐 수 있으므로 CORS와 XSRF를 끄고 띄웁니다.

```bash
streamlit run DE_PJ2/demo_app.py --server.headless true \
  --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false

cloudflared tunnel --url http://localhost:8501
```

발급되는 URL은 임시입니다. 서버나 터널을 끄면 죽고 재실행하면 새 URL이 나옵니다.
링크를 아는 사람은 누구나 접속해 영상을 올릴 수 있으니 공유 범위에 주의해야 합니다.
CPU 추론이라 동시 업로드는 직렬로 처리되어 느려집니다.

---

## 6. 영화 단위 폭력 비율은 측정할 수 없습니다

"폭력이 많은 영화와 적은 영화의 예측 폭력 비율이 비슷하게 나온다"는 관찰을 검증한 결과입니다.
검증 코드는 [`../DE_PJ2/exp_norm_compare.py`](../DE_PJ2/exp_norm_compare.py)이고,
라벨이 있는 test 9편으로 per-video 정규화와 global 정규화를 비교했습니다.

| 정규화 | 예측 폭력비율 범위 | 표준편차 | GT 상관 |
|---|---|---|---|
| per-video (현재) | 31~37% | 1.9%p | 0.06 |
| global (학습 통계) | 14~51% | 11.6%p | -0.06 |

원인이 두 개, 그것도 서로 독립적으로 있었습니다.

1. **per-video StandardScaler가 원인입니다.** 영화 간 절대 강도를 지워 모든 영화를 35% 근처로 압축합니다.
   모델 성능 문제가 아닙니다.
2. **그런데 GT 폭력비율도 전 영화가 40.0%로 동일합니다(표준편차 0.0%p).**
   `build_clips.py`의 `neg_ratio=1.5`가 영화마다 1:1.5로 균형 샘플링해 저장했기 때문입니다.
   즉 데이터 자체에 "이 영화가 얼마나 폭력적인가"라는 신호가 없습니다.
3. **global 정규화는 해결책이 아닙니다.** 비율이 퍼지기는 하나 GT 상관이 0에 가깝습니다.
   모델이 per-movie 정규화로 학습됐기 때문에 생기는 분포 불일치 노이즈일 뿐입니다.

따라서 **영화 단위 폭력 강도나 등급은 이 파이프라인의 유효한 출력이 아닙니다.**
두 설계가 각각 독립적으로 cross-movie 강도를 제거하며,
둘 다 본래 과제인 temporal localization("이 영화의 어디가 폭력인가")에는 정확히 부합합니다.

영화 단위 등급이 필요하다면 다음이 전제되어야 합니다.

1. per-movie 균형 샘플링을 하지 않은 데이터
2. global 정규화 또는 무정규화
3. 실제 영화별 폭력비율을 가진 held-out 셋으로 재학습·검증

데이터와 학습을 함께 재설계해야 하는 문제입니다.

---

## 7. 검증 상태

- `mypy` strict와 `ruff` 모두 에러 0
- 실제 영상 end-to-end 스모크 테스트: 32초 클립 → 65프레임 → (65, 2048) 피처 → 31클립 → 확률 정상 분포
- 체크포인트 `load_state_dict` 통과 (구조 일치 확인)
- 후처리 합성 신호 테스트: 얕은 dip은 1구간으로 병합, 깊은 dip은 2구간으로 분리, Gaussian 레벨 보존 확인

---

## 8. 알려진 제약

- **데모 영상은 학습·test에 쓰인 71편(movie_id) 밖에서 골라야 합니다.**
  학습에 쓴 영상으로 시연하면 결과를 신뢰할 수 없습니다
- 모델 천장이 Test Acc 약 0.72, violence recall 약 0.6입니다.
  모델을 바꿔도 비슷하므로 병목은 feature와 데이터입니다. 정확도를 과장하지 않는 것이 맞습니다
- base64 임베드 방식이라 수백 MB 영상은 브라우저 전송이 느립니다. 짧은 클립을 권장합니다
- **"CNN feature map"이라는 표현은 부정확합니다.** 실제로는 GAP된 2048-d 벡터이므로
  "ResNet50 frame embedding(2048-d)"가 정확한 표현입니다
- 영상 내 폭력 클립 비율은 영상 단위 상대값입니다. 서로 다른 영상끼리 비교해
  어느 쪽이 더 폭력적인지 판단하면 안 됩니다. UI에도 경고 캡션을 달아뒀습니다 (근거는 6장)
- feature는 ResNet만 전체 변환과 학습을 마쳤습니다.
  optical flow는 팀원이 진행 중이던 부분집합이고 VideoMAE는 GPU 비용으로 보류했습니다. 둘 다 향후 과제입니다

---

## 9. 향후 후보

- 심의 보조 지표: 총 폭력시간 대비 런타임 비율, 최장 연속 구간, 분당 빈도
- GT 비교 모드: 라벨이 있는 클립에서 예측과 정답을 오버레이
- 처리 효율 지표: 추출과 추론 시간, 초당 처리 프레임
- 영화 단위 등급이 필요할 경우 6장의 데이터·정규화 재설계

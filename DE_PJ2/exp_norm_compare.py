"""per-video vs global 정규화가 영화별 폭력비율 분리력에 미치는 영향 검증.

가설: per-video StandardScaler 는 영화 간 절대 강도를 지워 폭력 많은/적은 영화의
예측 폭력비율을 비슷하게 만든다. global(학습 코퍼스 고정 통계) 정규화는 절대 강도를
살려 GT 폭력비율과 더 잘 분리·상관된다.

라벨 있는 test 세트로 평가(영상/ResNet 불필요). 모델은 violence_transformer.pth.
주의: 모델은 per-movie 정규화로 학습됐으므로 global 은 train/test 분포 불일치 — 가설 검증용.
"""

from __future__ import annotations

import glob
from pathlib import Path
from typing import cast

import demo_app as m
import numpy as np
import torch
from numpy.typing import NDArray
from sklearn.preprocessing import StandardScaler  # type: ignore[import-untyped]

BASE = Path(__file__).resolve().parent / "npyForLSTM"
LABEL_MAP = {"neg_easy": 0, "violence": 1}
EPS = 1e-6


def global_stats() -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """train 코퍼스 전체에서 feature별 mean/std 스트리밍 계산 (flatten 8192-d)."""
    dim = m.CLIP_LEN * m.INPUT_SIZE
    s = np.zeros(dim, dtype=np.float64)
    sq = np.zeros(dim, dtype=np.float64)
    n = 0
    for f in sorted(glob.glob(str(BASE / "trainandval" / "*_X.npy"))):
        x = np.load(f).astype(np.float64).reshape(-1, dim)
        s += x.sum(axis=0)
        sq += (x**2).sum(axis=0)
        n += len(x)
    mean = s / n
    var = np.maximum(sq / n - mean**2, EPS)
    return mean, np.sqrt(var)


def load_test() -> tuple[NDArray[np.float32], NDArray[np.int64], NDArray[np.str_]]:
    xs, ys, ms = [], [], []
    for xf in sorted(glob.glob(str(BASE / "test" / "*_X.npy"))):
        name = xf.replace("_X.npy", "")
        xs.append(np.load(xf).astype(np.float32))
        ys.append(np.load(name + "_y.npy"))
        ms.append(np.load(name + "_movie_ids.npy"))
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(ms)


def norm_per_video(clips: NDArray[np.float32]) -> NDArray[np.float32]:
    flat = clips.reshape(len(clips), -1)
    scaled = StandardScaler().fit_transform(flat).reshape(clips.shape).astype(np.float32)
    return cast(NDArray[np.float32], scaled)


def norm_global(
    clips: NDArray[np.float32], mean: NDArray[np.float64], std: NDArray[np.float64]
) -> NDArray[np.float32]:
    flat = clips.reshape(len(clips), -1).astype(np.float64)
    return ((flat - mean) / std).reshape(clips.shape).astype(np.float32)


def pred_ratio(model: m.ViolenceTransformer, clips: NDArray[np.float32]) -> float:
    """argmax 기준 violence 예측 클립 비율."""
    probs = m.predict_violence_prob(model, clips)
    return float((probs >= 0.5).mean())


def main() -> None:
    print("global 통계 계산 중...")
    mean, std = global_stats()
    feats, y_str, movies = load_test()
    y = np.array([LABEL_MAP[str(v)] for v in y_str], dtype=np.int64)

    model = m.ViolenceTransformer()
    model.load_state_dict(torch.load(str(m.DEFAULT_MODEL_PATH), map_location="cpu"))
    model.eval()

    rows = []
    for movie in sorted(set(movies)):
        idx = np.where(movies == movie)[0]
        clips = feats[idx]
        gt = float((y[idx] == 1).mean())
        pv = pred_ratio(model, norm_per_video(clips))
        gl = pred_ratio(model, norm_global(clips, mean, std))
        rows.append((str(movie), gt, pv, gl, len(idx)))

    print(f"\n{'movie':<14}{'GT_vio%':>9}{'pred_perVid%':>14}{'pred_global%':>14}{'n':>7}")
    for name, gt, pv, gl, n in rows:
        print(f"{name:<14}{gt*100:>8.1f}{pv*100:>13.1f}{gl*100:>13.1f}{n:>7}")

    gts = np.array([r[1] for r in rows])
    pvs = np.array([r[2] for r in rows])
    gls = np.array([r[3] for r in rows])
    print("\n--- 분리력 / GT 상관 ---")
    print(f"GT 비율      범위 {gts.min()*100:.1f}~{gts.max()*100:.1f}%  표준편차 {gts.std()*100:.1f}%p")
    print(f"per-video    범위 {pvs.min()*100:.1f}~{pvs.max()*100:.1f}%  표준편차 {pvs.std()*100:.1f}%p  corr(GT)={np.corrcoef(gts,pvs)[0,1]:.3f}")
    print(f"global       범위 {gls.min()*100:.1f}~{gls.max()*100:.1f}%  표준편차 {gls.std()*100:.1f}%p  corr(GT)={np.corrcoef(gts,gls)[0,1]:.3f}")


if __name__ == "__main__":
    main()

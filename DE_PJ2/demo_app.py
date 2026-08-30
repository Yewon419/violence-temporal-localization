"""Violence temporal localization demo (Streamlit, local, CPU).

업로드한 임의 영상에서 폭력 구간(start~end)을 찾아 타임라인 차트로 보여준다.
파이프라인은 학습(`build_clips.py` + `violence_annotator/app.py` + `pj2_lstm4.ipynb`)과
수치까지 동일하게 맞춘다:

    영상 → cv2 2fps 프레임(0-base) → ResNet50 2048-dim 피처
        → clip_len=4 / stride=2 슬라이딩(영상 전체) → 영상 단위 StandardScaler
        → ViolenceTransformer(.pth) → 클립별 violence 확률
        → 스무딩 + threshold + 구간 병합 → 타임라인

프레임 인덱스 k 의 시각은 k/2 초. 클립 c(시작 프레임 = c*stride)는
프레임 [c*stride .. c*stride+3] 을 덮으므로 시각 구간 [start/2 .. (start+3)/2] 초.

실행:
    .venv/Scripts/streamlit run DE_PJ2/demo_app.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import cv2
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import torch
import torch.nn as nn
import torchvision.models as models  # type: ignore[import-untyped]
import torchvision.transforms as transforms  # type: ignore[import-untyped]
from matplotlib.figure import Figure
from numpy.typing import NDArray
from PIL import Image
from sklearn.preprocessing import StandardScaler  # type: ignore[import-untyped]

# ── 학습과 일치시켜야 하는 상수 (변경 금지) ──────────────────────────────
TARGET_FPS: float = 2.0
CLIP_LEN: int = 4
STRIDE: int = 2
INPUT_SIZE: int = 2048
IMAGENET_MEAN: tuple[float, float, float] = (0.485, 0.456, 0.406)
IMAGENET_STD: tuple[float, float, float] = (0.229, 0.224, 0.225)
LABEL_NAMES: tuple[str, str] = ("neg_easy", "violence")
VIDEO_MIME: dict[str, str] = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
}

DEFAULT_MODEL_PATH: Path = Path(__file__).resolve().parent / "violence_transformer.pth"
DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"
FEATURE_BATCH: int = 32

# 후처리 기본값 (데모용으로 고정 — 슬라이더 대신 상수)
DEFAULT_THRESHOLD: float = 0.45  # 구간 시작 임계값 t_high
HYST_DELTA: float = 0.15  # 유지 임계값 t_low = t_high - delta (히스테리시스)
GAUSS_SIGMA: float = 1.0  # Gaussian 스무딩 sigma (클립 단위) — 이웃 영향, 가까울수록 강함
MAX_GAP_CLIPS: int = 1  # t_low 밑으로 떨어져도 이만큼 클립은 메워서 잇는다
MIN_DURATION_SEC: float = 2.0

_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(list(IMAGENET_MEAN), list(IMAGENET_STD)),
    ]
)


# ── 모델 (pj2_lstm4.ipynb 의 ViolenceTransformer 와 1:1) ─────────────────
class ViolenceTransformer(nn.Module):
    def __init__(
        self,
        input_size: int = INPUT_SIZE,
        nhead: int = 8,
        num_layers: int = 2,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=input_size,
            nhead=nhead,
            dim_feedforward=512,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc = nn.Linear(input_size, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.transformer(x)
        return cast(torch.Tensor, self.fc(out[:, -1, :]))


@dataclass(frozen=True)
class Interval:
    start_sec: float
    end_sec: float
    peak_prob: float

    @property
    def duration(self) -> float:
        return self.end_sec - self.start_sec


@dataclass(frozen=True)
class DetectionConfig:
    t_high: float  # 구간 시작 임계값
    t_low: float  # 구간 유지 임계값 (히스테리시스)
    max_gap_clips: int
    min_duration_sec: float


# ── 캐시되는 무거운 리소스 ──────────────────────────────────────────────
@st.cache_resource(show_spinner="ResNet50 로딩...")
def load_resnet() -> nn.Module:
    """build_clips.py 와 동일: resnet50 IMAGENET1K_V1, 마지막 fc 제거."""
    backbone = models.resnet50(weights="IMAGENET1K_V1")
    feature_extractor = nn.Sequential(*list(backbone.children())[:-1])
    feature_extractor.eval().to(DEVICE)
    return feature_extractor


@st.cache_resource(show_spinner="Transformer 로딩...")
def load_transformer(model_path: str) -> ViolenceTransformer:
    model = ViolenceTransformer().to(DEVICE)
    state = torch.load(model_path, map_location=DEVICE)
    model.load_state_dict(state)
    model.eval()
    return model


# ── 파이프라인 ──────────────────────────────────────────────────────────
def extract_frames(video_path: str) -> list[NDArray[np.uint8]]:
    """annotator/app.py 와 동일하게 2fps 로 샘플. jpg encode/decode 까지 재현해
    학습 피처(잗 압축 프레임)와 분포를 맞춘다. RGB 배열 리스트 반환(프레임 0-base)."""
    capture = cv2.VideoCapture(video_path)
    video_fps = float(capture.get(cv2.CAP_PROP_FPS))
    if video_fps <= 0.0:
        capture.release()
        raise ValueError(f"영상 fps 가 비정상: {video_fps}")
    step = max(1, round(video_fps / TARGET_FPS))

    frames: list[NDArray[np.uint8]] = []
    source_idx = 0
    while True:
        if not capture.grab():
            break
        if source_idx % step == 0:
            ok, frame = capture.retrieve()
            if ok:
                encoded, buffer = cv2.imencode(".jpg", frame)
                if encoded:
                    decoded = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
                    if decoded is None:
                        continue
                    rgb = cv2.cvtColor(decoded, cv2.COLOR_BGR2RGB)
                    frames.append(rgb.astype(np.uint8))
        source_idx += 1
    capture.release()
    return frames


def frames_to_features(
    frames: list[NDArray[np.uint8]], resnet: nn.Module
) -> NDArray[np.float32]:
    """프레임마다 2048-dim. build_clips.extract_cnn_feature 를 배치로 한 것."""
    feats: list[NDArray[np.float32]] = []
    for i in range(0, len(frames), FEATURE_BATCH):
        batch = frames[i : i + FEATURE_BATCH]
        tensors = torch.stack([_TRANSFORM(Image.fromarray(f)) for f in batch]).to(DEVICE)
        with torch.no_grad():
            out = resnet(tensors).squeeze(-1).squeeze(-1).cpu().numpy()
        feats.append(out.astype(np.float32))
    if not feats:
        return np.zeros((0, INPUT_SIZE), dtype=np.float32)
    return np.concatenate(feats, axis=0)


def build_clips(
    features: NDArray[np.float32],
) -> tuple[NDArray[np.float32], NDArray[np.int64]]:
    """영상 전체를 clip_len=4 / stride=2 슬라이딩. (M,4,2048) + 각 클립 시작 프레임 인덱스."""
    clips: list[NDArray[np.float32]] = []
    starts: list[int] = []
    for start in range(0, len(features) - CLIP_LEN + 1, STRIDE):
        clips.append(features[start : start + CLIP_LEN])
        starts.append(start)
    if not clips:
        return (
            np.zeros((0, CLIP_LEN, INPUT_SIZE), dtype=np.float32),
            np.zeros((0,), dtype=np.int64),
        )
    return np.stack(clips).astype(np.float32), np.array(starts, dtype=np.int64)


def normalize_clips(clips: NDArray[np.float32]) -> NDArray[np.float32]:
    """영상 단위 StandardScaler (pj2_lstm4 test 셀과 동일)."""
    if len(clips) <= 1:
        return clips
    flat = clips.reshape(len(clips), -1)
    scaled = StandardScaler().fit_transform(flat)
    return cast(NDArray[np.float32], scaled.reshape(clips.shape).astype(np.float32))


def predict_violence_prob(
    model: ViolenceTransformer, clips: NDArray[np.float32]
) -> NDArray[np.float32]:
    if len(clips) == 0:
        return np.zeros((0,), dtype=np.float32)
    probs: list[NDArray[np.float32]] = []
    tensor = torch.tensor(clips, dtype=torch.float32)
    with torch.no_grad():
        for i in range(0, len(tensor), 256):
            batch = tensor[i : i + 256].to(DEVICE)
            logits = model(batch)
            p = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
            probs.append(p.astype(np.float32))
    return np.concatenate(probs, axis=0)


def gaussian_smooth(probs: NDArray[np.float32], sigma: float) -> NDArray[np.float32]:
    """Gaussian 가중 스무딩. 가까운 이웃일수록 강하게 끌어올린다(거리 감쇠).
    균등 이동평균과 달리 강한 이웃이 옆 dip 을 위로 당겨 액션 사이 틈을 메우는 효과."""
    if sigma <= 0.0 or len(probs) == 0:
        return probs
    radius = max(1, round(3.0 * sigma))
    x = np.arange(-radius, radius + 1, dtype=np.float32)
    kernel = np.exp(-(x**2) / (2.0 * sigma * sigma))
    kernel /= kernel.sum()
    return np.convolve(probs, kernel, mode="same").astype(np.float32)


def clip_time_bounds(start_frame: int) -> tuple[float, float]:
    """클립이 덮는 시각 구간 [start, end] 초 (프레임 k = k/2 초)."""
    return start_frame / TARGET_FPS, (start_frame + CLIP_LEN - 1) / TARGET_FPS


def merge_intervals(
    probs: NDArray[np.float32],
    starts: NDArray[np.int64],
    config: DetectionConfig,
) -> list[Interval]:
    """히스테리시스 병합: prob 가 t_high 를 넘으면 구간 시작, 일단 켜지면 t_low 밑으로
    떨어질 때까지 유지(짧은 dip 무시). t_low 밑이라도 max_gap 클립까지는 메워서 잇는다.
    짧은 구간(min_duration 미만)은 버린다."""
    intervals: list[Interval] = []
    run_start_idx: int | None = None
    gap = 0
    for i, p in enumerate(probs):
        if run_start_idx is None:
            if p >= config.t_high:  # 시작은 높은 임계값
                run_start_idx = i
                gap = 0
        elif p >= config.t_low:  # 유지: 낮은 임계값 위면 계속
            gap = 0
        else:  # t_low 밑 — max_gap 까지는 메우고, 넘으면 종료
            gap += 1
            if gap > config.max_gap_clips:
                intervals.append(_make_interval(probs, starts, run_start_idx, i - gap))
                run_start_idx = None
                gap = 0
    if run_start_idx is not None:
        intervals.append(_make_interval(probs, starts, run_start_idx, len(probs) - 1 - gap))

    return [iv for iv in intervals if iv.duration >= config.min_duration_sec]


def _make_interval(
    probs: NDArray[np.float32],
    starts: NDArray[np.int64],
    first_clip: int,
    last_clip: int,
) -> Interval:
    start_sec, _ = clip_time_bounds(int(starts[first_clip]))
    _, end_sec = clip_time_bounds(int(starts[last_clip]))
    peak = float(probs[first_clip : last_clip + 1].max())
    return Interval(start_sec=start_sec, end_sec=end_sec, peak_prob=peak)


def fmt_time(seconds: float) -> str:
    minutes = int(seconds) // 60
    secs = seconds - minutes * 60
    return f"{minutes:02d}:{secs:04.1f}"


# ── 시각화 ──────────────────────────────────────────────────────────────
def timeline_figure(
    probs: NDArray[np.float32],
    starts: NDArray[np.int64],
    intervals: list[Interval],
    config: DetectionConfig,
) -> Figure:
    centers = np.array(
        [sum(clip_time_bounds(int(s))) / 2.0 for s in starts], dtype=np.float32
    )
    fig, ax = plt.subplots(figsize=(14, 3.2))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.plot(centers, probs, color="#2563EB", linewidth=1.8, label="violence prob (smoothed)")
    ax.fill_between(centers, probs, color="#2563EB", alpha=0.06)
    ax.axhline(config.t_high, color="#94A3B8", linestyle="--", linewidth=1, label=f"t_high={config.t_high:.2f} (start)")
    ax.axhline(config.t_low, color="#CBD5E1", linestyle=":", linewidth=1, label=f"t_low={config.t_low:.2f} (hold)")
    for iv in intervals:
        ax.axvspan(iv.start_sec, iv.end_sec, color="#DC2626", alpha=0.16)
    ax.set_xlabel("time (sec)", color="#475569")
    ax.set_ylabel("violence probability", color="#475569")
    ax.set_ylim(0.0, 1.0)
    if len(centers) > 0:
        ax.set_xlim(0.0, float(centers[-1]) + 1.0)
    ax.set_title("Violence timeline", color="#0F172A", fontweight="bold", loc="left")
    ax.tick_params(colors="#64748B")
    ax.grid(axis="y", color="#F1F5F9", linewidth=1)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#E2E8F0")
    ax.legend(loc="upper right", framealpha=0.9, edgecolor="#E2E8F0")
    fig.tight_layout()
    return fig


_PLAYER_TEMPLATE = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Fira+Sans:wght@400;500;600&display=swap');
  * { box-sizing: border-box; }
  .vwrap { font-family: 'Fira Sans', sans-serif; color: #0F172A; }
  #vid { width: 100%; max-height: 420px; background: #000; display: block; border-radius: 10px; }
  #bar { position: relative; height: 24px; background: #E2E8F0; cursor: pointer;
         margin-top: 10px; border-radius: 6px; overflow: hidden; }
  .seg { position: absolute; top: 0; height: 100%; background: #DC2626; opacity: 0.82; z-index: 1;
         box-shadow: 0 0 6px rgba(220,38,38,0.45); }
  #prog { position: absolute; top: 0; left: 0; height: 100%; width: 0;
          background: rgba(37,99,235,0.28); z-index: 2; }
  #head { position: absolute; top: 0; left: 0; width: 2px; height: 100%; background: #0F172A; z-index: 3; }
  .ctl { margin-top: 10px; display: flex; align-items: center; gap: 12px; font-size: 14px; color: #334155; }
  #pp { cursor: pointer; border: 1px solid #2563EB; color: #2563EB; background: #fff; border-radius: 8px;
        padding: 4px 14px; font-size: 14px; font-family: 'Fira Sans', sans-serif; transition: all .15s ease; }
  #pp:hover { background: #2563EB; color: #fff; }
  #t { font-family: 'Fira Code', monospace; font-variant-numeric: tabular-nums; color: #0F172A; }
  .leg { display: inline-block; width: 12px; height: 12px; background: #DC2626;
         vertical-align: middle; margin-right: 6px; border-radius: 3px; }
</style>
<div class="vwrap">
  <video id="vid" src="__SRC__" preload="metadata"></video>
  <div id="bar"><div id="prog"></div><div id="head"></div></div>
  <div class="ctl">
    <button id="pp">&#9654; 재생</button>
    <span id="t">0:00 / 0:00</span>
    <span style="margin-left:auto"><span class="leg"></span>폭력 구간 (바를 클릭하면 이동)</span>
  </div>
</div>
<script>
(function() {
  var v = document.getElementById('vid'), bar = document.getElementById('bar');
  var prog = document.getElementById('prog'), head = document.getElementById('head');
  var pp = document.getElementById('pp'), t = document.getElementById('t');
  var segs = __SEGS__;
  function fmt(s) { var m = Math.floor(s/60), x = Math.floor(s%60); return m + ':' + (x<10?'0':'') + x; }
  function draw() {
    var d = v.duration; if (!isFinite(d) || d <= 0) return;
    bar.querySelectorAll('.seg').forEach(function(e){ e.remove(); });
    segs.forEach(function(s) {
      var el = document.createElement('div'); el.className = 'seg';
      el.style.left = (s[0]/d*100) + '%'; el.style.width = ((s[1]-s[0])/d*100) + '%';
      el.title = fmt(s[0]) + ' ~ ' + fmt(s[1]);
      bar.insertBefore(el, bar.firstChild);
    });
  }
  v.addEventListener('loadedmetadata', function(){ draw(); t.textContent = '0:00 / ' + fmt(v.duration); });
  v.addEventListener('timeupdate', function() {
    var d = v.duration || 0;
    if (d > 0) { var f = v.currentTime/d; prog.style.width = (f*100) + '%'; head.style.left = (f*100) + '%'; }
    t.textContent = fmt(v.currentTime) + ' / ' + fmt(d);
  });
  v.addEventListener('play', function(){ pp.innerHTML = '&#10074;&#10074; 일시정지'; });
  v.addEventListener('pause', function(){ pp.innerHTML = '&#9654; 재생'; });
  bar.addEventListener('click', function(e) {
    if (!isFinite(v.duration)) return;
    var r = bar.getBoundingClientRect();
    var f = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
    var ct = f * v.duration;
    // 빨간 폭력 구간 안을 클릭하면 그 구간의 첫 프레임(시작)으로 스냅
    for (var i = 0; i < segs.length; i++) {
      if (ct >= segs[i][0] && ct <= segs[i][1]) { ct = segs[i][0]; break; }
    }
    v.currentTime = ct; v.play();
  });
  pp.addEventListener('click', function(){ if (v.paused) v.play(); else v.pause(); });
})();
</script>
"""


def render_player(video_bytes: bytes, suffix: str, intervals: list[Interval]) -> None:
    """커스텀 HTML5 플레이어: 진행바에 폭력 구간을 빨갛게 칠하고, 바 클릭 시 그 시각으로 이동."""
    mime = VIDEO_MIME.get(suffix.lower(), "video/mp4")
    src = f"data:{mime};base64,{base64.b64encode(video_bytes).decode('ascii')}"
    segs = "[" + ",".join(f"[{iv.start_sec:.3f},{iv.end_sec:.3f}]" for iv in intervals) + "]"
    html = _PLAYER_TEMPLATE.replace("__SRC__", src).replace("__SEGS__", segs)
    components.html(html, height=520, scrolling=False)


# ── Streamlit UI ────────────────────────────────────────────────────────
_APP_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Fira+Sans:wght@300;400;500;600;700&display=swap');
  html, body, [data-testid="stAppViewContainer"], .stApp, [data-testid="stSidebar"] {
    font-family: 'Fira Sans', sans-serif;
  }
  #MainMenu, [data-testid="stToolbar"], footer { visibility: hidden; }
  [data-testid="stMainBlockContainer"] { max-width: 1080px; padding-top: 2.5rem; }
  .app-title { font-size: 1.9rem; font-weight: 700; letter-spacing: -0.02em; color: #0F172A;
               display: flex; align-items: center; gap: 11px; margin-bottom: 2px; }
  .app-title .dot { width: 12px; height: 12px; border-radius: 50%; background: #DC2626;
                    box-shadow: 0 0 8px rgba(220,38,38,0.5); }
  [data-testid="stMetric"] { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px;
                             padding: 14px 18px; }
  [data-testid="stMetricValue"] { font-family: 'Fira Code', monospace; font-variant-numeric: tabular-nums;
                                  color: #0F172A; font-size: 1.55rem; }
  [data-testid="stMetricLabel"] p { color: #64748B; font-weight: 500; }
  [data-testid="stTable"] td:first-child { font-family: 'Fira Code', monospace; }
</style>
"""


@st.cache_data(show_spinner="프레임 추출 + ResNet 피처 (CPU, 수십 초)...")
def video_to_features(video_bytes: bytes, suffix: str) -> NDArray[np.float32]:
    """업로드 바이트 단위로 캐시. 같은 영상 재업로드 시 즉시 반환."""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name
    try:
        frames = extract_frames(tmp_path)
        return frames_to_features(frames, load_resnet())
    finally:
        Path(tmp_path).unlink(missing_ok=True)


LIBRARY_DIR: Path = Path(__file__).resolve().parent / ".demo_library"


@dataclass(frozen=True)
class LibraryItem:
    key: str
    name: str
    suffix: str


def _ensure_library() -> None:
    LIBRARY_DIR.mkdir(exist_ok=True)
    gi = LIBRARY_DIR / ".gitignore"
    if not gi.exists():
        gi.write_text("*\n", encoding="utf-8")  # 영상 커밋 방지


def list_library() -> list[LibraryItem]:
    """분석 완료된 영상 목록 (추가된 순). 디스크 스캔이라 새로고침·서버 재시작에도 유지."""
    _ensure_library()
    items: list[LibraryItem] = []
    for d in sorted(LIBRARY_DIR.iterdir(), key=lambda p: p.stat().st_mtime):
        meta = d / "meta.json"
        if d.is_dir() and meta.exists():
            m = json.loads(meta.read_text(encoding="utf-8"))
            items.append(LibraryItem(key=d.name, name=m["name"], suffix=m["suffix"]))
    return items


def save_library_item(
    key: str, name: str, suffix: str, video_bytes: bytes, features: NDArray[np.float32]
) -> None:
    """영상 + ResNet 피처(npy) + 메타 저장 → 재선택 시 ResNet 재추출 없이 즉시 복원."""
    _ensure_library()
    d = LIBRARY_DIR / key
    d.mkdir(exist_ok=True)
    (d / f"video{suffix}").write_bytes(video_bytes)
    np.save(d / "features.npy", features)
    (d / "meta.json").write_text(
        json.dumps({"name": name, "suffix": suffix}, ensure_ascii=False), encoding="utf-8"
    )


def load_library_item(item: LibraryItem) -> tuple[bytes, NDArray[np.float32]]:
    d = LIBRARY_DIR / item.key
    video_bytes = (d / f"video{item.suffix}").read_bytes()
    features = np.load(d / "features.npy").astype(np.float32)
    return video_bytes, features


def delete_library_item(key: str) -> None:
    d = LIBRARY_DIR / key
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


def main() -> None:
    st.set_page_config(page_title="Violence Localization Demo", layout="wide")
    st.markdown(_APP_CSS, unsafe_allow_html=True)
    st.markdown(
        "<div class='app-title'><span class='dot'></span>영화 폭력 구간 탐지 데모</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "영상 업로드 → 폭력 구간(start~end) 타임라인. "
        "ResNet50 피처 + Transformer (test Acc 0.72). 학습/test 71편 외 영상으로 데모하세요."
    )

    with st.sidebar:
        st.header("설정")
        t_raw = st.query_params.get("t")
        t_default = float(t_raw) if t_raw else DEFAULT_THRESHOLD
        t_high = st.slider("threshold (구간 시작 t_high)", 0.0, 1.0, t_default, 0.05)
        if f"{t_high:.2f}" != st.query_params.get("t"):
            st.query_params["t"] = f"{t_high:.2f}"  # 새로고침에도 유지
        t_low = max(0.0, t_high - HYST_DELTA)
        st.caption(f"히스테리시스: 시작 {t_high:.2f} / 유지 {t_low:.2f} · Gaussian sigma={GAUSS_SIGMA}")
        st.caption(f"device: {DEVICE} | fps={TARGET_FPS} | clip={CLIP_LEN}/stride={STRIDE}")

    config = DetectionConfig(
        t_high=t_high,
        t_low=t_low,
        max_gap_clips=MAX_GAP_CLIPS,
        min_duration_sec=MIN_DURATION_SEC,
    )

    model_path = str(DEFAULT_MODEL_PATH)
    if not Path(model_path).exists():
        st.error(f"모델 파일이 없습니다: {model_path}")
        return

    # ── 영상 라이브러리 (새로고침·재선택에도 결과 유지) ──
    library = list_library()
    keys = [it.key for it in library]
    meta_by_key = {it.key: it for it in library}

    uploaded = st.file_uploader(
        "새 영상 추가 (업로드 시 자동 분석)", type=["mp4", "mkv", "mov", "webm", "avi"]
    )
    if uploaded is not None:
        vb = uploaded.getvalue()
        key = hashlib.md5(vb).hexdigest()[:12]
        if st.session_state.get("_last_upload") != key:  # 업로드당 1회만 처리
            st.session_state["_last_upload"] = key
            if key not in keys:
                suffix_new = Path(uploaded.name).suffix or ".mp4"
                feats = video_to_features(vb, suffix_new)
                if len(feats) < CLIP_LEN:
                    st.warning(f"프레임이 너무 적습니다 ({len(feats)}개). 더 긴 영상을 넣어주세요.")
                    return
                save_library_item(key, uploaded.name, suffix_new, vb, feats)
            st.query_params["v"] = key
            st.rerun()

    if not library:
        st.info("영상을 업로드하면 분석을 시작합니다. 분석한 영상은 목록에 저장돼 새로고침해도 다시 볼 수 있어요.")
        return

    current = st.query_params.get("v")
    if current not in keys:
        current = keys[-1]
    selected = st.selectbox(
        "분석된 영상", keys, index=keys.index(current),
        format_func=lambda k: meta_by_key[k].name,
    )
    if selected != current:
        st.query_params["v"] = selected
        current = selected

    with st.expander("영상 관리"):
        st.caption(f"선택: {meta_by_key[current].name}")
        if st.button("이 영상 라이브러리에서 삭제", type="secondary"):
            delete_library_item(current)
            remaining = [k for k in keys if k != current]
            if remaining:
                st.query_params["v"] = remaining[-1]
            elif "v" in st.query_params:
                del st.query_params["v"]
            st.rerun()

    item = meta_by_key[current]
    video_bytes, features = load_library_item(item)
    suffix = item.suffix
    digest = current

    clips, starts = build_clips(features)
    clips = normalize_clips(clips)
    model = load_transformer(model_path)
    raw_probs = predict_violence_prob(model, clips)
    probs = gaussian_smooth(raw_probs, GAUSS_SIGMA)
    intervals = merge_intervals(probs, starts, config)

    duration_sec = (len(features) - 1) / TARGET_FPS
    cols = st.columns(4)
    cols[0].metric("영상 길이", fmt_time(duration_sec))
    cols[1].metric("클립 수", f"{len(clips)}")
    cols[2].metric("폭력 구간", f"{len(intervals)}개")
    cols[3].metric("영상 내 폭력 클립 비율", f"{float((raw_probs >= config.t_high).mean()) * 100:.0f}%")
    st.caption(
        "⚠️ '영상 내 폭력 클립 비율'은 **이 영상 안에서의 상대값**입니다. 피처가 영상 단위로 정규화되므로 "
        "서로 다른 영상끼리 이 수치를 비교해 '어느 영화가 더 폭력적인가'를 판단하면 안 됩니다 "
        "(영화 단위 폭력 강도는 이 시스템의 유효한 출력이 아님)."
    )

    # 진행바에 폭력 구간을 색칠한 커스텀 플레이어 (바 클릭 → 그 시각으로 이동)
    render_player(video_bytes, suffix, intervals)

    st.pyplot(timeline_figure(probs, starts, intervals, config))

    st.subheader("탐지된 폭력 구간")
    if not intervals:
        st.write("threshold 이상 구간 없음. threshold 를 낮춰보세요.")
    else:
        st.table(
            {
                "구간": [f"{fmt_time(iv.start_sec)} ~ {fmt_time(iv.end_sec)}" for iv in intervals],
                "길이(초)": [f"{iv.duration:.1f}" for iv in intervals],
                "최고확률": [f"{iv.peak_prob:.2f}" for iv in intervals],
            }
        )

    st.caption(f"cache key: {digest}")


if __name__ == "__main__":
    main()

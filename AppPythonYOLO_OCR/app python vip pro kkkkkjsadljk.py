# -*- coding: utf-8 -*-
"""
HCMUS VN Plate OCR Lab - V4 Best Hybrid
=================================

Giao diện ít nút:
- Choose YOLO .pt
- Choose input ảnh/video
- Choose folder ảnh
- RUN
- Open output

Tự xử lý:
- Ảnh đơn
- Folder ảnh
- Video mp4/mkv/webm/mov/avi... giữ ffmpeg/bin để encode + mux audio
- YOLO .pt detect biển
- FastALPR OCR hoặc fast_plate_ocr tùy chọn
- Rotate fallback 90/270 cho biển dọc
- Gamma fallback cho ảnh tối
- Split collage fallback cho ảnh ghép 2 biển
- Moto 4-digit support: ví dụ 61T32222 -> 61T3 2222
- Track smoothing + OCR voting cho video
- Clean display: ẩn UNKNOWN, cùng vùng chỉ giữ 1 biển tốt nhất

Install:
    pip install -r requirements.txt

Run:
    python hcmus_vn_plate_clean_app.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import statistics
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageTk

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

try:
    from fast_alpr.default_ocr import DefaultOCR
except Exception:
    DefaultOCR = None

try:
    from fast_plate_ocr import LicensePlateRecognizer
except Exception:
    LicensePlateRecognizer = None


APP_DIR = Path(__file__).resolve().parent
OUT_DIR = APP_DIR / "outputs_hcmus_image_first_final"
IMG_ANNOT_DIR = OUT_DIR / "annotated_images"
CROP_DIR = OUT_DIR / "crops"
for d in (OUT_DIR, IMG_ANNOT_DIR, CROP_DIR):
    d.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUT_DIR / "results.csv"
CONFIG_PATH = OUT_DIR / "config.json"
FINAL_APP_VERSION = "HCMUS_VNPLATE_NHOM5_V4_BEST_HYBRID_2026_04"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v", ".ts", ".mts", ".m2ts"}

# HCMUS-ish palette
BG = "#f3f7ff"
PANEL = "#ffffff"
PANEL_2 = "#eaf1ff"
BLUE = "#005baa"
BLUE_DARK = "#003f7d"
RED = "#e31b23"
TEXT = "#10233f"
MUTED = "#5d6f88"
BORDER = "#b8c7e6"
CANVAS_BG = "#10131a"

VN_PROVINCE_CODES = {
    "11", "12", "14", "15", "16", "17", "18", "19",
    "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
    "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    "40", "41", "43", "47", "48", "49",
    "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
    "60", "61", "62", "63", "64", "65", "66", "67", "68", "69",
    "70", "71", "72", "73", "74", "75", "76", "77", "78", "79",
    "80", "81", "82", "83", "84", "85", "86", "88", "89",
    "90", "92", "93", "94", "95", "97", "98", "99",
}
VN_PLATE_RE = re.compile(r"^\d{2}[A-Z]{1,2}\d{4,6}$")
VN_MOTO_SERIES_RE = re.compile(r"^\d{2}[A-Z]\d\d{4,5}$")
DIGIT_FIX = str.maketrans({"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "T": "7", "S": "5", "B": "8", "G": "6", "Z": "2"})
LETTER_FIX = str.maketrans({"0": "O", "1": "I", "2": "Z", "5": "S", "6": "G", "7": "T", "8": "B"})


PRESETS = {
    # Dùng khi demo bình thường: không quá chậm, vẫn giữ nhiều biển hơn bản cũ.
    "Balanced": {
        "sample_fps": 12.0,
        "conf": 0.24,
        "imgsz": 768,
        "smooth": 0.28,
        "hold_s": 0.55,
        "min_hits": 1,
        "max_show": 4,
        "min_reliability": 0.38,
        "region_iou": 0.30,
        "center_margin": 0.10,
        "only_valid_vn": False,
        "hide_unknown": True,
        "rotate_fallback": True,
        "rotate_always": False,
        "gamma_fallback": True,
        "split_collage": True,
        "tile_fallback": True,
        "tile_rows": 2,
        "tile_cols": 2,
        "tile_overlap": 0.10,
        "variant_stop_boxes": 4,
        "classical_fallback": False,
        "anti_sign_guard": True,
        "crop_pad": 0.08,
        "whole_scene_fallback": False,
        "wide_ratio": 1.45,
    },

    # Profile chính cho 2 ảnh bãi xe như bạn gửi: nhiều xe, biển nhỏ, góc nhìn lộn xộn.
    "Image / Multi plates": {
        "sample_fps": 12.0,
        "conf": 0.12,
        "imgsz": 960,
        "smooth": 0.25,
        "hold_s": 0.55,
        "min_hits": 1,
        "max_show": 12,
        "min_reliability": 0.18,
        "region_iou": 0.42,
        "center_margin": 0.04,
        "only_valid_vn": False,
        "hide_unknown": True,
        "rotate_fallback": True,
        "rotate_always": True,
        "gamma_fallback": True,
        "split_collage": True,
        "tile_fallback": True,
        "tile_rows": 2,
        "tile_cols": 3,
        "tile_overlap": 0.14,
        "variant_stop_boxes": 99,
        "classical_fallback": False,
        "anti_sign_guard": True,
        "crop_pad": 0.08,
        "whole_scene_fallback": False,
        "wide_ratio": 1.15,
    },

    # Khi YOLO bỏ sót vì confidence thấp: quét nặng hơn, chấp nhận ứng viên yếu hơn.
    "Low confidence rescue": {
        "sample_fps": 8.0,
        "conf": 0.08,
        "imgsz": 1280,
        "smooth": 0.20,
        "hold_s": 0.80,
        "min_hits": 1,
        "max_show": 20,
        "min_reliability": 0.10,
        "region_iou": 0.45,
        "center_margin": 0.03,
        "only_valid_vn": False,
        "hide_unknown": False,
        "rotate_fallback": True,
        "rotate_always": True,
        "gamma_fallback": True,
        "split_collage": True,
        "tile_fallback": True,
        "tile_rows": 3,
        "tile_cols": 3,
        "tile_overlap": 0.18,
        "variant_stop_boxes": 99,
        "classical_fallback": True,
        "anti_sign_guard": True,
        "crop_pad": 0.08,
        "whole_scene_fallback": False,
        "wide_ratio": 1.05,
    },

    # Video ưu tiên tốc độ.
    "Fast video": {
        "sample_fps": 24.0,
        "conf": 0.36,
        "imgsz": 640,
        "smooth": 0.40,
        "hold_s": 0.20,
        "min_hits": 1,
        "max_show": 3,
        "min_reliability": 0.45,
        "region_iou": 0.25,
        "center_margin": 0.12,
        "only_valid_vn": True,
        "hide_unknown": True,
        "rotate_fallback": True,
        "rotate_always": False,
        "gamma_fallback": True,
        "split_collage": True,
        "tile_fallback": False,
        "tile_rows": 1,
        "tile_cols": 1,
        "tile_overlap": 0.08,
        "variant_stop_boxes": 2,
        "classical_fallback": True,
        "anti_sign_guard": True,
        "crop_pad": 0.08,
        "whole_scene_fallback": False,
        "wide_ratio": 1.55,
    },

    # Video chậm nhưng ổn định hơn, phù hợp quay bãi xe hoặc camera rung.
    "Slow video": {
        "sample_fps": 8.0,
        "conf": 0.18,
        "imgsz": 768,
        "smooth": 0.18,
        "hold_s": 0.85,
        "min_hits": 1,
        "max_show": 6,
        "min_reliability": 0.25,
        "region_iou": 0.35,
        "center_margin": 0.08,
        "only_valid_vn": False,
        "hide_unknown": True,
        "rotate_fallback": True,
        "rotate_always": False,
        "gamma_fallback": True,
        "split_collage": True,
        "tile_fallback": True,
        "tile_rows": 2,
        "tile_cols": 2,
        "tile_overlap": 0.10,
        "variant_stop_boxes": 4,
        "classical_fallback": True,
        "anti_sign_guard": True,
        "crop_pad": 0.08,
        "whole_scene_fallback": False,
        "wide_ratio": 1.45,
    },
}

def clean_text(s) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def fix_digits(s):
    return str(s or "").upper().translate(DIGIT_FIX)


def fix_letters(s):
    return str(s or "").upper().translate(LETTER_FIX)


def valid_plate(t) -> bool:
    t = clean_text(t)
    return (bool(VN_PLATE_RE.fullmatch(t)) or bool(VN_MOTO_SERIES_RE.fullmatch(t))) and t[:2] in VN_PROVINCE_CODES


def old_numeric_plate(t) -> bool:
    """Older/loose VN numeric plate style such as 51-107.96 -> 5110796."""
    t = clean_text(t)
    return bool(re.fullmatch(r"\d{7,8}", t)) and t[:2] in VN_PROVINCE_CODES


def plausible_plate_text(t) -> bool:
    t = clean_text(t)
    return valid_plate(t) or old_numeric_plate(t)


def source_raw_text(source: str) -> str:
    src = str(source or "")
    left = src.split("|", 1)[0]
    if ":" in left:
        return clean_text(left.rsplit(":", 1)[-1])
    return clean_text(left)


def looks_like_parking_area_code(text: str, source: str = "") -> bool:
    """Reject parking-slot / column labels like D28, D29, D29D28."""
    t = clean_text(text)
    raw = source_raw_text(source) or t

    if plausible_plate_text(t):
        return False

    if 1 <= len(t) <= 5:
        return True

    for x in {t, raw}:
        if re.fullmatch(r"[A-Z]\d{1,3}([A-Z]\d{1,3})?", x):
            return True
        if re.fullmatch(r"[A-Z]{1,2}\d{1,4}", x):
            return True
        if x.startswith(("D", "P", "B", "C")) and len(x) <= 7 and not re.match(r"^\d{2}", x):
            return True

    if not re.match(r"^\d{2}", t):
        return True
    if t[:2] not in VN_PROVINCE_CODES:
        return True

    return False


def compact_number(raw):
    num = re.sub(r"\D", "", fix_digits(raw))
    variants = {num[:6], num[-6:], num[:5], num[-5:], num[:4], num[-4:]}
    if len(num) >= 7 and num[0] == num[1]:
        variants.add(num[1:-1])
        variants.add(num[1:6])
    for i in range(len(num)):
        s1 = num[:i] + num[i + 1:]
        if 4 <= len(s1) <= 6:
            variants.add(s1)
    return [v for v in variants if 4 <= len(v) <= 6]


def normalize_plate(raw):
    """Light VN plate normalization, preserving raw FastALPR-style text.

    No auto-add patch:
    - Do not add leading 0.
    - Do not add suffix 1.
    - Do not force 29Y -> 29Y1.
    """
    t = clean_text(raw)
    if len(t) < 5:
        return t

    best = []

    def add_candidate(cand, score):
        cand = clean_text(cand)
        if 6 <= len(cand) <= 10:
            if valid_plate(cand):
                score += 100
            if len(cand) in (7, 8, 9):
                score += 3
            best.append((score, cand))

    add_candidate(t, 10)

    for cut in range(2, min(5, len(t) - 3)):
        code = re.sub(r"\D", "", fix_digits(t[:cut]))[-2:]
        if len(code) != 2 or code not in VN_PROVINCE_CODES:
            continue
        rest = t[cut:]

        # Normal car/one-row: code + 1/2 letters + 4..6 digits.
        for n_letter in (1, 2):
            if len(rest) < n_letter + 4:
                continue
            series = re.sub(r"[^A-Z]", "", fix_letters(rest[:n_letter]))
            if len(series) != n_letter:
                continue
            num = re.sub(r"\D", "", fix_digits(rest[n_letter:]))
            for keep in {num, num[:6], num[-6:], num[:5], num[-5:], num[:4], num[-4:]}:
                if 4 <= len(keep) <= 6:
                    add_candidate(code + series + keep, 20 + len(keep))

        # Motorcycle two-line header only if OCR explicitly reads letter+digit.
        if len(rest) >= 6:
            s0 = fix_letters(rest[0])[:1]
            s1 = fix_digits(rest[1])[:1]
            if re.fullmatch(r"[A-Z]", s0) and re.fullmatch(r"\d", s1):
                num = re.sub(r"\D", "", fix_digits(rest[2:]))
                for keep in {num, num[:5], num[-5:], num[:4], num[-4:]}:
                    if 4 <= len(keep) <= 5:
                        add_candidate(code + s0 + s1 + keep, 18 + len(keep))

    if best:
        best.sort(reverse=True)
        return best[0][1]
    return t


def format_plate(t) -> str:
    """Final raw FastALPR-style display: no dash/dot/spacing."""
    return clean_text(t)


def format_plate_moto(t) -> str:
    return clean_text(t)


def bbox_aspect(bbox) -> float:
    try:
        x1, y1, x2, y2 = map(float, bbox)
        return max(1.0, x2 - x1) / max(1.0, y2 - y1)
    except Exception:
        return 99.0


def format_plate_smart(t, bbox=None) -> str:
    """Final display uses raw normalized OCR text, like FastALPR source output."""
    return clean_text(t)


def bbox_iou(a, b) -> float:
    ax1, ay1, ax2, ay2 = map(float, a)
    bx1, by1, bx2, by2 = map(float, b)
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    aa = max(1.0, (ax2 - ax1) * (ay2 - ay1))
    bb = max(1.0, (bx2 - bx1) * (by2 - by1))
    return inter / max(1.0, aa + bb - inter)


def ema_box(old, new, new_weight: float) -> list[float]:
    a = max(0.02, min(1.0, float(new_weight)))
    return [float(o) * (1.0 - a) + float(n) * a for o, n in zip(old, new)]


def plate_vote_weight(text: str, ocr_conf: float) -> float:
    t = clean_text(text)
    if not t or t in {"UNKNOWN", "NO_OCR", "NOOCR"}:
        return 0.0
    w = max(0.05, float(ocr_conf or 0.0))
    if valid_plate(t):
        w += 2.0
    if len(t) in (7, 8, 9):
        w += 0.25
    return w


def parse_fraction(s: str, default: float = 30.0) -> float:
    try:
        if "/" in str(s):
            a, b = str(s).split("/", 1)
            b = float(b)
            return float(a) / b if b else default
        return float(s)
    except Exception:
        return default


def bundled_exe(name: str) -> str:
    candidates = [
        APP_DIR / "ffmpeg" / "bin" / name,
        APP_DIR / name,
    ]
    if name.endswith(".exe"):
        candidates += [
            APP_DIR / "ffmpeg" / "bin" / name.replace(".exe", ""),
            APP_DIR / name.replace(".exe", ""),
        ]
    for p in candidates:
        if p.exists():
            return str(p)
    return shutil.which(name) or shutil.which(name.replace(".exe", "")) or ""


def ffprobe_from_ffmpeg(ffmpeg_path: str) -> str:
    p = Path(ffmpeg_path)
    if p.exists():
        probe_name = "ffprobe.exe" if p.name.endswith(".exe") else "ffprobe"
        probe = p.with_name(probe_name)
        if probe.exists():
            return str(probe)
    return bundled_exe("ffprobe.exe")


def get_video_info(ffprobe_path: str, video_path: str) -> dict:
    cmd = [
        ffprobe_path, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate,r_frame_rate,nb_frames,codec_name",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path,
    ]
    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
    if cp.returncode != 0:
        raise RuntimeError("ffprobe failed:\n" + cp.stderr[:2500])
    data = json.loads(cp.stdout or "{}")
    stream = (data.get("streams") or [{}])[0]
    fmt = data.get("format") or {}
    width = int(stream.get("width") or 0)
    height = int(stream.get("height") or 0)
    fps = parse_fraction(stream.get("avg_frame_rate") or stream.get("r_frame_rate"), 30.0)
    duration = float(fmt.get("duration") or 0.0)
    nb_frames = stream.get("nb_frames")
    total_frames = int(nb_frames) if nb_frames and str(nb_frames).isdigit() else int(duration * fps) if duration and fps else 0
    if width <= 0 or height <= 0:
        raise RuntimeError("Cannot read video width/height from ffprobe.")
    return {"width": width, "height": height, "fps": fps if fps > 0 else 30.0, "duration": duration, "total_frames": total_frames, "codec": stream.get("codec_name", "")}


def expand_box(b, w, h, pad=0.08):
    x1, y1, x2, y2 = map(float, b)
    bw, bh = max(1, x2 - x1), max(1, y2 - y1)
    return [
        max(0, min(w - 1, x1 - bw * pad)),
        max(0, min(h - 1, y1 - bh * pad)),
        max(0, min(w - 1, x2 + bw * pad)),
        max(0, min(h - 1, y2 + bh * pad)),
    ]


def crop_box(img, b):
    h, w = img.shape[:2]
    x1, y1, x2, y2 = [int(round(v)) for v in expand_box(b, w, h, 0)]
    if x2 <= x1 or y2 <= y1:
        return None
    return img[y1:y2, x1:x2].copy()


def confidence_value(conf):
    if conf is None:
        return 0.0
    if isinstance(conf, (list, tuple)):
        vals = [float(x) for x in conf if x is not None]
        return float(statistics.mean(vals)) if vals else 0.0
    try:
        return float(conf)
    except Exception:
        return 0.0


def cv2_ascii_label(s: str) -> str:
    s = str(s or "")
    s = s.replace("·", "|").replace("–", "-").replace("—", "-")
    s = s.encode("ascii", "ignore").decode("ascii")
    return " ".join(s.split())



def clamp01(x) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0


def reliability_score(text: str, det_conf: float, ocr_conf: float, bbox=None) -> float:
    """Practical demo/report confidence score.

    Not a scientific probability; it combines OCR confidence, detector confidence,
    and a small bonus when the OCR string looks like a Vietnamese plate.
    """
    t = clean_text(text)
    if not t or t in {"UNKNOWN", "NOOCR", "NO_OCR"}:
        return 0.0

    det = clamp01(det_conf)
    ocr = clamp01(ocr_conf)

    score = 0.50 * ocr + 0.33 * det
    if valid_plate(t):
        score += 0.12
    if len(t) in (7, 8, 9):
        score += 0.05
    if not valid_plate(t):
        score = min(score, 0.72)
    if det < 0.08:
        score = min(score, 0.65)

    return clamp01(score)


def reliability_percent(text: str, det_conf: float, ocr_conf: float, bbox=None) -> int:
    return int(round(reliability_score(text, det_conf, ocr_conf, bbox) * 100))


def reliability_text(text: str, det_conf: float, ocr_conf: float, bbox=None) -> str:
    return f"{reliability_percent(text, det_conf, ocr_conf, bbox)}%"


def cv2_ascii_label(s: str) -> str:
    """cv2.putText uses Hershey fonts, so keep overlay text ASCII-only."""
    s = str(s or "")
    s = s.replace("·", "|").replace("–", "-").replace("—", "-")
    s = s.encode("ascii", "ignore").decode("ascii")
    return " ".join(s.split())


@dataclass
class PlateResult:
    bbox: list[float]
    det_conf: float
    text: str
    display: str
    ocr_conf: float
    source: str
    crop_path: str = ""


class FastALPROCR:
    """Stable FastALPR DefaultOCR wrapper with light two-line retry.

    No auto-add patch:
    - Single OCR model only, no ensemble.
    - No auto-add leading 0.
    - No auto-add suffix 1.
    - No I/L -> 1 forced top-header correction.
    - Raw FastALPR-style display.
    """
    def __init__(self, model_name: str = "cct-s-v2-global-model", device: str = "auto"):
        if DefaultOCR is None:
            raise RuntimeError('fast-alpr is not installed. Run: pip install "fast-alpr[onnx]"')
        self.model_name = model_name
        self.device = device
        try:
            self.ocr = DefaultOCR(hub_ocr_model=model_name, device=device, force_download=False)
        except TypeError:
            self.ocr = DefaultOCR(hub_ocr_model=model_name, device=device)

    def _predict_raw(self, img_bgr: np.ndarray) -> tuple[str, float]:
        if img_bgr is None or img_bgr.size == 0:
            return "", 0.0
        result = self.ocr.predict(img_bgr)
        if isinstance(result, (list, tuple)) and result:
            result = result[0]
        if result is None:
            return "", 0.0

        raw = (
            getattr(result, "text", None)
            or getattr(result, "plate", None)
            or getattr(result, "ocr", None)
            or ""
        )
        conf = (
            getattr(result, "confidence", None)
            or getattr(result, "conf", None)
            or getattr(result, "score", None)
            or 0.0
        )

        if isinstance(conf, np.ndarray):
            conf = conf.tolist()
        if isinstance(conf, (list, tuple)):
            vals = [float(x) for x in conf if x is not None]
            conf_value = float(np.mean(vals)) if vals else 0.0
        else:
            conf_value = confidence_value(conf)

        return clean_text(raw), conf_value

    def _enhance(self, crop_bgr: np.ndarray) -> np.ndarray:
        try:
            gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
            sharp = cv2.addWeighted(clahe, 1.45, cv2.GaussianBlur(clahe, (3, 3), 0), -0.45, 0)
            return cv2.cvtColor(sharp, cv2.COLOR_GRAY2BGR)
        except Exception:
            return crop_bgr

    def _extract_header_candidates(self, top_raw: str):
        """Only accept OCR-explicit headers: 29Y1, 29H1, 61T3, etc."""
        top = clean_text(top_raw)
        out = []
        for mm in re.finditer(r"(\d{2}[A-Z]\d)", top):
            out.append(mm.group(1))

        seen, dedup = set(), []
        for h in out:
            h = clean_text(h)
            if h and h not in seen:
                seen.add(h)
                dedup.append(h)
        return dedup

    def _two_line_candidates(self, crop_bgr: np.ndarray):
        h, w = crop_bgr.shape[:2]
        if h < 32 or w < 32:
            return []

        mid = h // 2
        ov = max(3, h // 10)
        top = crop_bgr[: min(h, mid + ov), :]
        bot = crop_bgr[max(0, mid - ov):, :]

        pairs = [
            ("plain", top, bot),
            ("sharp", self._enhance(top), self._enhance(bot)),
        ]

        candidates = []
        for tag, top_img, bot_img in pairs:
            try:
                top_raw, top_conf = self._predict_raw(top_img)
                bot_raw, bot_conf = self._predict_raw(bot_img)
            except Exception:
                continue

            headers = self._extract_header_candidates(top_raw)
            bot_digits = re.sub(r"\D", "", fix_digits(bot_raw))
            num_candidates = set()

            if 4 <= len(bot_digits) <= 6:
                num_candidates.add(bot_digits)
            if len(bot_digits) >= 5:
                num_candidates.add(bot_digits[:5])
                num_candidates.add(bot_digits[-5:])
            if len(bot_digits) >= 4:
                num_candidates.add(bot_digits[:4])
                num_candidates.add(bot_digits[-4:])

            for head in headers:
                if not re.fullmatch(r"\d{2}[A-Z]\d", head):
                    continue
                for num in num_candidates:
                    if not (4 <= len(num) <= 5):
                        continue
                    cand = normalize_plate(head + num)
                    conf = (top_conf + bot_conf) / 2.0
                    score = conf + 0.50 + (1.0 if valid_plate(cand) else 0.0)
                    candidates.append((cand, conf, f"two_line:{tag}:{top_raw}|{bot_raw}", score))

        return candidates

    def read(self, crop_bgr: np.ndarray) -> tuple[str, float, str]:
        if crop_bgr is None or crop_bgr.size == 0:
            return "", 0.0, "empty_crop"

        try:
            candidates = []

            raw, conf = self._predict_raw(crop_bgr)
            if raw:
                text = normalize_plate(raw)
                score = conf + (1.0 if valid_plate(text) else 0.0)
                candidates.append((text, conf, f"fastalpr:{self.model_name}:{raw}", score))

            sharp = self._enhance(crop_bgr)
            raw_s, conf_s = self._predict_raw(sharp)
            if raw_s:
                text_s = normalize_plate(raw_s)
                score_s = conf_s + (1.0 if valid_plate(text_s) else 0.0)
                candidates.append((text_s, conf_s, f"fastalpr_sharp:{self.model_name}:{raw_s}", score_s))

            candidates.extend(self._two_line_candidates(crop_bgr))

            if not candidates:
                return "", 0.0, f"fastalpr:{self.model_name}:empty"

            best_text, best_conf, best_src, best_score = max(
                candidates,
                key=lambda x: (
                    1 if valid_plate(x[0]) else 0,
                    x[3],
                    len(clean_text(x[0])),
                    x[1],
                )
            )
            return clean_text(best_text), float(best_conf), best_src
        except Exception as e:
            return "", 0.0, "fastalpr_error:" + repr(e)[:120]


def preprocess_plate_debug(plate_bgr: np.ndarray) -> np.ndarray:
    """Friend-app style crop preview/preprocess: equalize + resize + Otsu.

    This is used for optional debug/fast_plate_ocr candidate generation. It is
    not forced onto FastALPR because FastALPR expects a normal BGR crop.
    """
    try:
        gray = cv2.cvtColor(plate_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresholded
    except Exception:
        return np.zeros((1, 1), dtype=np.uint8)


class FastPlateOCRWrapper:
    """Optional backend from your friend's app: fast_plate_ocr.run_one().

    The rest of this app uses the same read(crop_bgr) interface as FastALPROCR.
    """
    def __init__(self, model_name: str = "cct-s-v2-global-model", device: str = "cpu"):
        if LicensePlateRecognizer is None:
            raise RuntimeError('fast_plate_ocr is not installed. Run: pip install fast-plate-ocr')
        self.model_name = model_name
        self.device = device
        self.ocr = LicensePlateRecognizer(model_name, device=device)

    def _predict_raw(self, crop_bgr: np.ndarray) -> tuple[str, float]:
        if crop_bgr is None or crop_bgr.size == 0:
            return "", 0.0
        # friend app passes RGB crop into fast_plate_ocr
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        pred = self.ocr.run_one(crop_rgb, return_confidence=True)
        raw = getattr(pred, "plate", None) or getattr(pred, "text", None) or ""
        probs = getattr(pred, "char_probs", None)
        if probs is not None and len(probs):
            conf = float(np.mean(probs))
        else:
            conf = confidence_value(getattr(pred, "confidence", 0.0))
        return clean_text(raw), conf

    def read(self, crop_bgr: np.ndarray) -> tuple[str, float, str]:
        try:
            candidates = []
            raw, conf = self._predict_raw(crop_bgr)
            if raw:
                text = normalize_plate(raw)
                score = conf + (1.0 if valid_plate(text) else 0.0)
                candidates.append((text, conf, f"fast_plate_ocr:{self.model_name}:{raw}", score))

            # A light contrast candidate helps with blurry basement/parking images.
            sharp = cv2.cvtColor(preprocess_plate_debug(crop_bgr), cv2.COLOR_GRAY2BGR)
            raw_s, conf_s = self._predict_raw(sharp)
            if raw_s:
                text_s = normalize_plate(raw_s)
                score_s = conf_s + (1.0 if valid_plate(text_s) else 0.0)
                candidates.append((text_s, conf_s, f"fast_plate_ocr_otsu:{self.model_name}:{raw_s}", score_s))

            if not candidates:
                return "", 0.0, f"fast_plate_ocr:{self.model_name}:empty"
            best_text, best_conf, best_src, _ = max(
                candidates,
                key=lambda x: (1 if plausible_plate_text(x[0]) else 0, x[3], len(clean_text(x[0])), x[1]),
            )
            return clean_text(best_text), float(best_conf), best_src
        except Exception as e:
            return "", 0.0, "fast_plate_ocr_error:" + repr(e)[:120]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HCMUS - VN Plate OCR V5 Clean Stop - 22DTV_CLC1 - Nhóm 5")
        self.geometry("1200x760")
        self.minsize(1000, 650)
        self.configure(bg=BG)

        self.model = None
        self.ocr = None
        self.loaded_model_path = ""
        self.loaded_ocr_key = ""
        self.photo = None
        self.cancel_flag = False
        self.worker = None
        self.dec_proc = None
        self.enc_proc = None
        self.run_button = None
        self.stop_button = None
        self.advanced_visible = False
        self.rows: list[dict] = []
        self.latest_output = ""

        self.model_var = tk.StringVar(value=self.find_default_model())
        self.input_var = tk.StringVar()
        self.preset_var = tk.StringVar(value="Balanced")
        self.encoder_var = tk.StringVar(value="Auto")
        self.ocr_backend_var = tk.StringVar(value="Auto")
        self.status_var = tk.StringVar(value="Chọn model .pt + input rồi RUN.")
        self.summary_var = tk.StringVar(value="Đề tài: Phát hiện và nhận dạng biển số phương tiện dựa trên YOLO và OCR")
        self.progress_var = tk.DoubleVar(value=0.0)

        # User-tunable inference controls.
        # Values are loaded from the selected profile, but the user can override them directly in GUI.
        base_cfg = PRESETS.get(self.preset_var.get(), PRESETS["Balanced"])
        self.det_conf_var = tk.DoubleVar(value=float(base_cfg.get("conf", 0.25)))
        self.trust_var = tk.DoubleVar(value=float(base_cfg.get("min_reliability", 0.25)))
        self.max_show_var = tk.IntVar(value=int(base_cfg.get("max_show", 4)))
        self.imgsz_var = tk.IntVar(value=int(base_cfg.get("imgsz", 768)))
        self.crop_pad_var = tk.DoubleVar(value=float(base_cfg.get("crop_pad", 0.08)))
        self.only_valid_var = tk.BooleanVar(value=bool(base_cfg.get("only_valid_vn", False)))
        self.show_unknown_var = tk.BooleanVar(value=not bool(base_cfg.get("hide_unknown", True)))
        self.heavy_scan_var = tk.BooleanVar(value=bool(base_cfg.get("tile_fallback", True) or base_cfg.get("rotate_always", False)))
        self.classical_fallback_var = tk.BooleanVar(value=bool(base_cfg.get("classical_fallback", True)))
        self.anti_sign_var = tk.BooleanVar(value=bool(base_cfg.get("anti_sign_guard", True)))
        self.det_conf_label_var = tk.StringVar()
        self.trust_label_var = tk.StringVar()
        self.max_show_label_var = tk.StringVar()
        self.imgsz_label_var = tk.StringVar()
        self.crop_pad_label_var = tk.StringVar()
        self.crop_photo = None
        self.row_by_iid: dict[str, dict] = {}
        self.profile_lock = False

        self.ffmpeg_path = bundled_exe("ffmpeg.exe")
        self.output_video_path = str(OUT_DIR / "annotated_video.mp4")

        self.configure_style()
        self.build_ui()
        self.load_config()

    def configure_style(self):
        self.option_add("*Font", ("Segoe UI", 10))
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Treeview", rowheight=28, background="#f8fbff", fieldbackground="#f8fbff", foreground=TEXT)
        style.configure("Treeview.Heading", background=PANEL_2, foreground=TEXT, font=("Segoe UI", 10, "bold"))

    def button(self, parent, text, command, accent=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=BLUE if accent else "white",
            fg="white" if accent else TEXT,
            activebackground=BLUE_DARK if accent else PANEL_2,
            activeforeground="white" if accent else TEXT,
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            font=("Segoe UI", 10, "bold" if accent else "normal"),
        )


    def refresh_control_labels(self, *_):
        try:
            self.det_conf_label_var.set(f"YOLO conf: {float(self.det_conf_var.get()):.2f}")
            self.trust_label_var.set(f"Min trust: {int(round(float(self.trust_var.get()) * 100))}%")
            self.max_show_label_var.set(f"Max plates: {int(self.max_show_var.get())}")
            self.imgsz_label_var.set(f"imgsz: {int(self.imgsz_var.get())}")
            self.crop_pad_label_var.set(f"Crop pad: {float(self.crop_pad_var.get()):.2f}")
        except Exception:
            pass

    def apply_profile_to_controls(self, *_):
        """Load profile values into the visible controls."""
        if self.profile_lock:
            return
        self.profile_lock = True
        try:
            cfg = PRESETS.get(self.preset_var.get(), PRESETS["Balanced"])
            self.det_conf_var.set(float(cfg.get("conf", self.det_conf_var.get())))
            self.trust_var.set(float(cfg.get("min_reliability", self.trust_var.get())))
            self.max_show_var.set(int(cfg.get("max_show", self.max_show_var.get())))
            self.imgsz_var.set(int(cfg.get("imgsz", self.imgsz_var.get())))
            self.crop_pad_var.set(float(cfg.get("crop_pad", self.crop_pad_var.get())))
            self.only_valid_var.set(bool(cfg.get("only_valid_vn", self.only_valid_var.get())))
            self.show_unknown_var.set(not bool(cfg.get("hide_unknown", not self.show_unknown_var.get())))
            self.heavy_scan_var.set(bool(cfg.get("tile_fallback", False) or cfg.get("rotate_always", False)))
            self.classical_fallback_var.set(bool(cfg.get("classical_fallback", True)))
            self.anti_sign_var.set(bool(cfg.get("anti_sign_guard", True)))
            self.refresh_control_labels()
        finally:
            self.profile_lock = False

    def scale_row(self, parent, row, col, label_var, var, frm, to, resolution, width=160):
        box = tk.Frame(parent, bg=PANEL)
        box.grid(row=row, column=col, sticky="w", padx=6, pady=4)
        tk.Label(box, textvariable=label_var, bg=PANEL, fg=TEXT, width=15, anchor="w", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        scale = tk.Scale(
            box,
            from_=frm,
            to=to,
            resolution=resolution,
            orient="horizontal",
            variable=var,
            showvalue=False,
            length=width,
            bg=PANEL,
            fg=TEXT,
            highlightthickness=0,
            troughcolor=PANEL_2,
            command=lambda _=None: self.refresh_control_labels(),
        )
        scale.pack(anchor="w")
        return scale

    def build_ui(self):
        # V5: clean/student-demo UI. Main screen keeps only the actions needed in class.
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=16, pady=(10, 6))

        brand = tk.Frame(header, bg=BG)
        brand.pack(side="left", fill="x", expand=True)
        title_line = tk.Frame(brand, bg=BG)
        title_line.pack(anchor="w")
        tk.Label(title_line, text="HCMUS", bg=BG, fg=BLUE, font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(title_line, text=" VN Plate OCR", bg=BG, fg=TEXT, font=("Segoe UI", 21, "bold")).pack(side="left")
        tk.Label(title_line, text="  Nhóm 5", bg=BG, fg=RED, font=("Segoe UI", 12, "bold")).pack(side="left", pady=(8, 0))
        tk.Label(
            brand,
            text="Nhập môn trí tuệ nhân tạo - 22DTV_CLC1 • YOLO detect + OCR • Image / Folder / Video FFmpeg",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        top_actions = tk.Frame(header, bg=BG)
        top_actions.pack(side="right")
        self.button(top_actions, "Output", lambda: self.open_path(OUT_DIR)).pack(side="right", padx=4)
        self.advanced_button = self.button(top_actions, "Advanced ▾", self.toggle_advanced)
        self.advanced_button.pack(side="right", padx=4)

        panel = tk.Frame(self, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        panel.pack(fill="x", padx=16, pady=(0, 10))
        panel.columnconfigure(1, weight=1)

        tk.Label(panel, text="Model", bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 5))
        ttk.Entry(panel, textvariable=self.model_var).grid(row=0, column=1, columnspan=3, sticky="ew", padx=8, pady=(10, 5))
        self.button(panel, "Chọn", self.choose_model).grid(row=0, column=4, padx=8, pady=(10, 5))

        tk.Label(panel, text="Input", bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", padx=12, pady=5)
        ttk.Entry(panel, textvariable=self.input_var).grid(row=1, column=1, columnspan=3, sticky="ew", padx=8, pady=5)
        self.input_button = self.button(panel, "Chọn", self.choose_input)
        self.input_button.grid(row=1, column=4, padx=8, pady=5)

        simple = tk.Frame(panel, bg=PANEL)
        simple.grid(row=2, column=0, columnspan=5, sticky="ew", padx=10, pady=(4, 8))
        simple.columnconfigure(1, weight=1)

        tk.Label(simple, text="Profile", bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(2, 6))
        self.profile_combo = ttk.Combobox(simple, textvariable=self.preset_var, values=list(PRESETS.keys()), width=20, state="readonly")
        self.profile_combo.grid(row=0, column=1, sticky="w", padx=(0, 10))
        self.profile_combo.bind("<<ComboboxSelected>>", lambda _e: self.apply_profile_to_controls())

        compact_sliders = tk.Frame(simple, bg=PANEL)
        compact_sliders.grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.scale_row(compact_sliders, 0, 0, self.det_conf_label_var, self.det_conf_var, 0.03, 0.80, 0.01, 145)
        self.scale_row(compact_sliders, 0, 1, self.trust_label_var, self.trust_var, 0.00, 0.95, 0.01, 145)

        self.run_button = self.button(simple, "RUN", self.start, accent=True)
        self.run_button.grid(row=0, column=3, sticky="ew", padx=(6, 4))
        self.stop_button = self.button(simple, "STOP", self.stop_processing)
        self.stop_button.grid(row=0, column=4, sticky="ew", padx=(4, 0))
        try:
            self.stop_button.configure(state="disabled")
        except Exception:
            pass

        self.advanced_panel = tk.Frame(panel, bg=PANEL_2, highlightthickness=1, highlightbackground=BORDER)
        self.advanced_panel.columnconfigure(1, weight=1)

        tk.Label(self.advanced_panel, text="Encoder video", bg=PANEL_2, fg=TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))
        ttk.Combobox(
            self.advanced_panel,
            textvariable=self.encoder_var,
            values=["Auto", "CPU x264", "NVIDIA NVENC", "AMD AMF", "Intel QuickSync"],
            width=18,
            state="readonly",
        ).grid(row=0, column=1, sticky="w", padx=6, pady=(8, 4))

        tk.Label(self.advanced_panel, text="OCR backend", bg=PANEL_2, fg=TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", padx=(18, 6), pady=(8, 4))
        ttk.Combobox(
            self.advanced_panel,
            textvariable=self.ocr_backend_var,
            values=["Auto", "FastALPR DefaultOCR", "fast_plate_ocr"],
            width=18,
            state="readonly",
        ).grid(row=0, column=3, sticky="w", padx=6, pady=(8, 4))

        adv_sliders = tk.Frame(self.advanced_panel, bg=PANEL_2)
        adv_sliders.grid(row=1, column=0, columnspan=4, sticky="w", padx=4, pady=2)
        self.scale_row(adv_sliders, 0, 0, self.max_show_label_var, self.max_show_var, 1, 30, 1, 135)
        self.scale_row(adv_sliders, 0, 1, self.imgsz_label_var, self.imgsz_var, 480, 1280, 32, 155)
        self.scale_row(adv_sliders, 0, 2, self.crop_pad_label_var, self.crop_pad_var, 0.00, 0.25, 0.01, 155)

        opt_box = tk.Frame(self.advanced_panel, bg=PANEL_2)
        opt_box.grid(row=2, column=0, columnspan=4, sticky="w", padx=8, pady=(2, 8))
        tk.Checkbutton(opt_box, text="Chỉ biển đúng format VN", variable=self.only_valid_var, bg=PANEL_2, fg=TEXT, activebackground=PANEL_2).pack(side="left", padx=(0, 12))
        tk.Checkbutton(opt_box, text="Hiện UNKNOWN", variable=self.show_unknown_var, bg=PANEL_2, fg=TEXT, activebackground=PANEL_2).pack(side="left", padx=(0, 12))
        tk.Checkbutton(opt_box, text="Heavy scan", variable=self.heavy_scan_var, bg=PANEL_2, fg=TEXT, activebackground=PANEL_2).pack(side="left", padx=(0, 12))
        tk.Checkbutton(opt_box, text="Classical fallback", variable=self.classical_fallback_var, bg=PANEL_2, fg=TEXT, activebackground=PANEL_2).pack(side="left", padx=(0, 12))
        tk.Checkbutton(opt_box, text="Chặn cột bãi xe", variable=self.anti_sign_var, bg=PANEL_2, fg=TEXT, activebackground=PANEL_2).pack(side="left", padx=(0, 12))

        tk.Label(panel, textvariable=self.summary_var, bg=PANEL, fg=MUTED, anchor="w", font=("Segoe UI", 9)).grid(row=4, column=0, columnspan=5, sticky="ew", padx=12, pady=(0, 8))
        self.refresh_control_labels()

        main = ttk.Panedwindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        left = tk.Frame(main, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        right = tk.Frame(main, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        main.add(left, weight=3)
        main.add(right, weight=2)

        tk.Label(left, text="Preview", bg=PANEL, fg=TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(8, 4))
        self.canvas = tk.Canvas(left, bg=CANVAS_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        tk.Label(right, text="Results", bg=PANEL, fg=TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(8, 4))
        cols = ("input", "time", "plate", "trust", "det", "ocr", "src")
        self.table = ttk.Treeview(right, columns=cols, show="headings")
        for col, width in zip(cols, [150, 60, 120, 60, 55, 55, 135]):
            self.table.heading(col, text=col)
            self.table.column(col, width=width, anchor="w")
        self.table.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        self.table.bind("<<TreeviewSelect>>", self.on_result_select)

        crop_panel = tk.Frame(right, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        crop_panel.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(crop_panel, text="Crop preview", bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(6, 2))
        self.crop_canvas = tk.Canvas(crop_panel, bg="#161b22", height=118, highlightthickness=0)
        self.crop_canvas.pack(fill="x", padx=8, pady=(0, 8))

        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="x", padx=16, pady=(0, 10))
        ttk.Progressbar(bottom, variable=self.progress_var, maximum=100).pack(fill="x", side="top", pady=(0, 6))
        tk.Label(bottom, textvariable=self.status_var, bg=BG, fg=TEXT, anchor="w").pack(fill="x", side="left", expand=True)

    def choose_input(self):
        """One visible input button, two choices in a small menu."""
        menu = None
        try:
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Chọn ảnh / video", command=self.choose_file)
            menu.add_command(label="Chọn thư mục ảnh", command=self.choose_folder)
            x = self.input_button.winfo_rootx()
            y = self.input_button.winfo_rooty() + self.input_button.winfo_height()
            menu.tk_popup(x, y)
        finally:
            try:
                if menu is not None:
                    menu.grab_release()
            except Exception:
                pass

    def toggle_advanced(self):
        self.advanced_visible = not bool(getattr(self, "advanced_visible", False))
        if self.advanced_visible:
            self.advanced_panel.grid(row=3, column=0, columnspan=5, sticky="ew", padx=10, pady=(0, 8))
            try:
                self.advanced_button.configure(text="Advanced ▴")
            except Exception:
                pass
        else:
            self.advanced_panel.grid_remove()
            try:
                self.advanced_button.configure(text="Advanced ▾")
            except Exception:
                pass

    def set_running_ui(self, running: bool):
        try:
            if self.run_button is not None:
                self.run_button.configure(state="disabled" if running else "normal")
            if self.stop_button is not None:
                self.stop_button.configure(state="normal" if running else "disabled")
        except Exception:
            pass

    def stop_processing(self):
        """Stop long image-folder/video jobs. For video, also asks FFmpeg pipes to stop."""
        self.cancel_flag = True
        self.set_status("Đang dừng... video sẽ dừng sau vài frame.")
        for proc in (getattr(self, "dec_proc", None), getattr(self, "enc_proc", None)):
            try:
                if proc is not None and proc.poll() is None:
                    proc.terminate()
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        try:
            if getattr(self, "enc_proc", None) is not None and self.enc_proc.stdin:
                self.enc_proc.stdin.close()
        except Exception:
            pass

    def cfg(self):
        # Start with selected profile, then apply the GUI knobs.
        cfg = dict(PRESETS.get(self.preset_var.get(), PRESETS["Balanced"]))
        try:
            cfg["conf"] = float(self.det_conf_var.get())
            cfg["min_reliability"] = float(self.trust_var.get())
            cfg["max_show"] = int(self.max_show_var.get())
            cfg["imgsz"] = int(self.imgsz_var.get())
            cfg["crop_pad"] = float(self.crop_pad_var.get())
            cfg["only_valid_vn"] = bool(self.only_valid_var.get())
            cfg["hide_unknown"] = not bool(self.show_unknown_var.get())

            heavy = bool(self.heavy_scan_var.get())
            cfg["tile_fallback"] = heavy
            cfg["rotate_always"] = heavy or bool(cfg.get("rotate_always", False))
            cfg["gamma_fallback"] = True
            cfg["split_collage"] = True
            cfg["variant_stop_boxes"] = 99 if heavy else int(cfg.get("variant_stop_boxes", 2))
            cfg["classical_fallback"] = bool(self.classical_fallback_var.get())
            cfg["anti_sign_guard"] = bool(self.anti_sign_var.get())
            cfg["whole_scene_fallback"] = False

            # Heavy scan should not be over-aggressive at hiding candidates.
            if heavy and cfg["max_show"] < 8:
                cfg["max_show"] = 8
            if heavy and cfg["min_reliability"] > 0.45:
                cfg["min_reliability"] = 0.45
        except Exception:
            pass
        return cfg

    def find_default_model(self) -> str:
        candidates = [
            APP_DIR / "detector_used.pt",
            APP_DIR / "best.pt",
            APP_DIR / "best (1).pt",
            APP_DIR.parent / "best (1).pt",
            APP_DIR.parent / "best.pt",
            Path.home() / "Downloads" / "detector_used.pt",
            Path.home() / "Downloads" / "best.pt",
        ]
        for folder in [APP_DIR, APP_DIR / "results", APP_DIR / "outputs_clean"]:
            if folder.exists():
                candidates += list(folder.rglob("*.pt"))
        candidates = [p for p in candidates if p.exists()]
        priority = {"detector_used.pt": 0, "best.pt": 1, "yolo_best.pt": 2, "last.pt": 3}
        candidates = sorted(set(candidates), key=lambda p: (priority.get(p.name.lower(), 9), -p.stat().st_mtime))
        return str(candidates[0]) if candidates else ""

    def load_config(self):
        if not CONFIG_PATH.exists():
            self.apply_profile_to_controls()
            return
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            self.model_var.set(cfg.get("model", self.model_var.get()))
            self.input_var.set(cfg.get("input", self.input_var.get()))
            self.preset_var.set(cfg.get("preset", self.preset_var.get()))
            if self.preset_var.get() not in PRESETS:
                self.preset_var.set("Balanced")
            self.encoder_var.set(cfg.get("encoder", self.encoder_var.get()))
            self.ocr_backend_var.set(cfg.get("ocr_backend", self.ocr_backend_var.get()))

            # First load the profile, then override with saved manual knobs if they exist.
            self.apply_profile_to_controls()
            self.det_conf_var.set(float(cfg.get("det_conf", self.det_conf_var.get())))
            self.trust_var.set(float(cfg.get("min_reliability", self.trust_var.get())))
            self.max_show_var.set(int(cfg.get("max_show", self.max_show_var.get())))
            self.imgsz_var.set(int(cfg.get("imgsz", self.imgsz_var.get())))
            self.crop_pad_var.set(float(cfg.get("crop_pad", self.crop_pad_var.get())))
            self.only_valid_var.set(bool(cfg.get("only_valid_vn", self.only_valid_var.get())))
            self.show_unknown_var.set(bool(cfg.get("show_unknown", self.show_unknown_var.get())))
            self.heavy_scan_var.set(bool(cfg.get("heavy_scan", self.heavy_scan_var.get())))
            self.classical_fallback_var.set(bool(cfg.get("classical_fallback", self.classical_fallback_var.get())))
            self.anti_sign_var.set(bool(cfg.get("anti_sign_guard", self.anti_sign_var.get())))
            self.refresh_control_labels()
        except Exception:
            self.apply_profile_to_controls()

    def save_config(self):
        CONFIG_PATH.write_text(json.dumps({
            "model": self.model_var.get(),
            "input": self.input_var.get(),
            "preset": self.preset_var.get(),
            "encoder": self.encoder_var.get(),
            "ocr_backend": self.ocr_backend_var.get(),
            "det_conf": float(self.det_conf_var.get()),
            "min_reliability": float(self.trust_var.get()),
            "max_show": int(self.max_show_var.get()),
            "imgsz": int(self.imgsz_var.get()),
            "crop_pad": float(self.crop_pad_var.get()),
            "only_valid_vn": bool(self.only_valid_var.get()),
            "show_unknown": bool(self.show_unknown_var.get()),
            "heavy_scan": bool(self.heavy_scan_var.get()),
            "classical_fallback": bool(self.classical_fallback_var.get()),
            "anti_sign_guard": bool(self.anti_sign_var.get()),
        }, indent=2, ensure_ascii=False), encoding="utf-8")

    def choose_model(self):
        p = filedialog.askopenfilename(title="Choose YOLO .pt", filetypes=[("PyTorch model", "*.pt"), ("All files", "*.*")])
        if p:
            self.model_var.set(p)
            self.model = None
            self.loaded_model_path = ""
            self.save_config()

    def choose_file(self):
        p = filedialog.askopenfilename(
            title="Choose image or video",
            filetypes=[
                ("Image/Video", "*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff *.mp4 *.mkv *.webm *.mov *.avi *.m4v *.ts *.mts *.m2ts"),
                ("All files", "*.*"),
            ],
        )
        if p:
            self.input_var.set(p)
            ext = Path(p).suffix.lower()
            if ext in IMAGE_EXTS:
                self.preset_var.set("Image / Multi plates")
            elif ext in VIDEO_EXTS:
                self.preset_var.set("Slow video")
            else:
                self.preset_var.set("Balanced")
            self.apply_profile_to_controls()
            self.save_config()

    def choose_folder(self):
        p = filedialog.askdirectory(title="Choose image folder")
        if p:
            self.input_var.set(p)
            self.preset_var.set("Image / Multi plates")
            self.apply_profile_to_controls()
            self.save_config()

    def set_status(self, text):
        self.after(0, lambda: self.status_var.set(text))

    def set_summary(self, text):
        self.after(0, lambda: self.summary_var.set(text))

    def clear_table(self):
        self.row_by_iid.clear()
        for x in self.table.get_children():
            self.table.delete(x)
        try:
            self.crop_canvas.delete("all")
        except Exception:
            pass

    def add_row_ui(self, row):
        src = str(row.get("source", ""))
        src_short = src.split("|", 1)[0].replace("fastalpr:", "FA:").replace("fast_plate_ocr:", "FP:")[:40]
        iid = self.table.insert("", "end", values=(
            row.get("input", ""),
            row.get("time_s", ""),
            row.get("plate", ""),
            row.get("reliability", ""),
            row.get("det_conf", ""),
            row.get("ocr_conf", ""),
            src_short,
        ))
        self.row_by_iid[iid] = dict(row)
        children = self.table.get_children()
        if len(children) > 400:
            old = children[0]
            self.row_by_iid.pop(old, None)
            self.table.delete(old)

    def resolve_yolo_device(self):
        try:
            import torch
            return 0 if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def load_model(self):
        if YOLO is None:
            raise RuntimeError("ultralytics is not installed. Run: pip install ultralytics")
        p = Path(self.model_var.get())
        if not p.exists():
            raise FileNotFoundError(f"Model not found: {p}")
        if self.model is None or self.loaded_model_path != str(p):
            self.set_status(f"Loading YOLO: {p.name}")
            self.model = YOLO(str(p))
            self.loaded_model_path = str(p)
        return self.model

    def load_ocr(self):
        backend = self.ocr_backend_var.get().strip() or "Auto"

        # Auto: prefer FastALPR source-aligned OCR. If user only installed
        # fast_plate_ocr, fall back to your friend's backend automatically.
        if backend == "Auto":
            if DefaultOCR is not None:
                backend = "FastALPR DefaultOCR"
            elif LicensePlateRecognizer is not None:
                backend = "fast_plate_ocr"
            else:
                backend = "FastALPR DefaultOCR"

        key = backend
        if self.ocr is not None and self.loaded_ocr_key == key:
            return self.ocr

        if backend == "fast_plate_ocr":
            self.set_status("Loading fast_plate_ocr LicensePlateRecognizer...")
            self.ocr = FastPlateOCRWrapper("cct-s-v2-global-model", "cpu")
        else:
            self.set_status("Loading FastALPR DefaultOCR...")
            self.ocr = FastALPROCR("cct-s-v2-global-model", "auto")

        self.loaded_ocr_key = key
        return self.ocr

    def start(self):
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Running", "App đang chạy rồi.")
            return
        self.cancel_flag = False
        self.progress_var.set(0)
        self.clear_table()
        self.rows.clear()
        self.set_running_ui(True)
        self.worker = threading.Thread(target=self.run, daemon=True)
        self.worker.start()

    def run(self):
        try:
            self.save_config()
            input_path = Path(self.input_var.get())
            if not input_path.exists():
                raise FileNotFoundError(f"Input not found: {input_path}")

            model = self.load_model()
            ocr = self.load_ocr()

            if input_path.is_dir() or input_path.suffix.lower() in IMAGE_EXTS:
                self.run_images(model, ocr, input_path)
            elif input_path.suffix.lower() in VIDEO_EXTS:
                self.run_video(model, ocr, input_path)
            else:
                raise RuntimeError("Input không phải ảnh/folder ảnh/video hợp lệ.")

            if self.rows:
                pd.DataFrame(self.rows).to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
            if self.cancel_flag:
                self.set_summary("Stopped by user.")
            else:
                self.set_summary(f"Done • CSV: {CSV_PATH}")
        except Exception as e:
            if self.cancel_flag:
                self.set_status("Stopped.")
                self.set_summary("Stopped by user.")
            else:
                self.set_status("Run failed.")
                self.after(0, lambda msg=str(e): messagebox.showerror("Run failed", msg))
        finally:
            self.after(0, lambda: self.set_running_ui(False))

    def collect_images(self, input_path: Path):
        if input_path.is_file() and input_path.suffix.lower() in IMAGE_EXTS:
            return [input_path]
        if input_path.is_dir():
            return [p for p in sorted(input_path.rglob("*")) if p.suffix.lower() in IMAGE_EXTS]
        raise FileNotFoundError("Input không phải ảnh hoặc folder ảnh hợp lệ.")

    def run_images(self, model, ocr, input_path: Path):
        images = self.collect_images(input_path)
        if not images:
            raise RuntimeError("Không thấy ảnh trong folder.")
        cfg = self.cfg()
        device = self.resolve_yolo_device()
        self.set_summary(f"HCMUS Clean UI • Image mode • {len(images)} image(s) • preset={self.preset_var.get()}")

        for idx, img_path in enumerate(images, 1):
            if self.cancel_flag:
                break
            self.set_status(f"Image {idx}/{len(images)}: {img_path.name}")
            frame = cv2.imread(str(img_path))
            if frame is None:
                continue

            results = self.detect_frame(model, ocr, frame, img_path.name, "", "", cfg, device, log_rows=False)
            results = self.clean_display_results(results, cfg)
            annotated = self.draw(frame, results)
            out_img = IMG_ANNOT_DIR / f"annotated_{img_path.stem}.jpg"
            cv2.imwrite(str(out_img), annotated)
            self.latest_output = str(out_img)
            self.log_image_results(img_path.name, results, img_path, out_img)

            self.after(0, self.show_frame, annotated)
            self.after(0, lambda p=idx * 100.0 / len(images): self.progress_var.set(p))

        if self.cancel_flag:
            self.set_status("Stopped image mode.")
        else:
            self.set_status(f"Done image mode. Output: {IMG_ANNOT_DIR}")

    def ffmpeg_encoder_list(self, ffmpeg: str) -> set[str]:
        try:
            cp = subprocess.run(
                [ffmpeg, "-hide_banner", "-encoders"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=10,
            )
            txt = (cp.stdout or "") + "\n" + (cp.stderr or "")
            return {
                name for name in ["libx264", "h264_nvenc", "h264_amf", "h264_qsv"]
                if name in txt
            }
        except Exception:
            return {"libx264"}

    def choose_video_encoder(self, ffmpeg: str) -> tuple[str, list[str], str]:
        """Return encoder name, FFmpeg video args, user-facing label."""
        selected = self.encoder_var.get().strip()
        available = self.ffmpeg_encoder_list(ffmpeg)

        # Auto priority: NVENC -> QSV -> AMF -> CPU.
        requested = "libx264"
        label = "CPU x264"
        if selected == "Auto":
            if "h264_nvenc" in available:
                requested, label = "h264_nvenc", "Auto → NVIDIA NVENC"
            elif "h264_qsv" in available:
                requested, label = "h264_qsv", "Auto → Intel QuickSync"
            elif "h264_amf" in available:
                requested, label = "h264_amf", "Auto → AMD AMF"
            else:
                requested, label = "libx264", "Auto → CPU x264"
        elif selected == "NVIDIA NVENC":
            requested, label = "h264_nvenc", "NVIDIA NVENC"
        elif selected == "AMD AMF":
            requested, label = "h264_amf", "AMD AMF"
        elif selected == "Intel QuickSync":
            requested, label = "h264_qsv", "Intel QuickSync"
        else:
            requested, label = "libx264", "CPU x264"

        # Encoder not compiled into FFmpeg -> safe fallback.
        if requested not in available:
            self.set_summary(f"Encoder {label} không có trong FFmpeg này → fallback CPU x264.")
            requested, label = "libx264", "CPU x264 fallback"

        if requested == "h264_nvenc":
            args = [
                "-c:v", "h264_nvenc",
                "-preset", "p4",
                "-tune", "hq",
                "-rc", "vbr",
                "-cq", "23",
                "-b:v", "0",
                "-pix_fmt", "yuv420p",
            ]
        elif requested == "h264_amf":
            args = [
                "-c:v", "h264_amf",
                "-quality", "balanced",
                "-rc", "cqp",
                "-qp_i", "23",
                "-qp_p", "23",
                "-pix_fmt", "yuv420p",
            ]
        elif requested == "h264_qsv":
            # QSV availability also depends on Intel iGPU driver and FFmpeg build.
            args = [
                "-c:v", "h264_qsv",
                "-global_quality", "23",
                "-look_ahead", "0",
                "-pix_fmt", "nv12",
            ]
        else:
            args = [
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
            ]

        return requested, args, label


    def log_image_results(self, input_name: str, results: list[PlateResult], image_path: Path | None = None, annotated_path: Path | None = None):
        """Log only final cleaned image results, not raw OCR candidates."""
        for r in results:
            row = {
                "input": input_name,
                "time_s": "",
                "frame": "",
                "plate": clean_text(r.text),
                "reliability": reliability_text(r.text, r.det_conf, r.ocr_conf, r.bbox),
                "det_conf": round(float(r.det_conf), 4),
                "ocr_conf": round(float(r.ocr_conf), 4),
                "source": r.source,
                "bbox_xyxy": ",".join(str(round(x, 1)) for x in r.bbox),
                "crop_path": r.crop_path,
                "image_path": str(image_path or ""),
                "annotated_path": str(annotated_path or ""),
            }
            self.rows.append(row)
            self.after(0, self.add_row_ui, row)


    def run_video(self, model, ocr, video_path: Path):
        ffmpeg = bundled_exe("ffmpeg.exe")
        if not ffmpeg:
            raise FileNotFoundError("Không thấy ffmpeg.exe. Chạy download_ffmpeg_to_app_folder.bat trước.")
        ffprobe = ffprobe_from_ffmpeg(ffmpeg)
        if not ffprobe:
            raise FileNotFoundError("Không thấy ffprobe.exe. Chạy download_ffmpeg_to_app_folder.bat trước.")

        info = get_video_info(ffprobe, str(video_path))
        w, h, fps = info["width"], info["height"], info["fps"]
        total_frames = info["total_frames"]
        codec = info.get("codec", "")
        cfg = self.cfg()
        sample_fps = max(0.1, float(cfg["sample_fps"]))
        stride = max(1, int(round(fps / sample_fps)))
        effective_fps = fps / stride if stride else fps

        out_path = OUT_DIR / f"{video_path.stem}_annotated.mp4"
        temp_noaudio = out_path.with_name(out_path.stem + "_tmp_noaudio.mp4")
        device = self.resolve_yolo_device()

        dec_cmd = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
            "-i", str(video_path),
            "-map", "0:v:0",
            "-pix_fmt", "bgr24",
            "-f", "rawvideo",
            "-",
        ]
        encoder_name, encoder_args, encoder_label = self.choose_video_encoder(ffmpeg)
        self.set_summary(
            f"HCMUS Clean UI • Video {w}x{h} {fps:.2f}fps {codec} • "
            f"sample≈{effective_fps:.1f}fps • encoder={encoder_label} • giữ audio gốc • preset={self.preset_var.get()}"
        )

        enc_cmd = [
            ffmpeg, "-y",
            "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{w}x{h}",
            "-r", f"{fps:.6f}",
            "-i", "-",
            "-an",
            *encoder_args,
            str(temp_noaudio),
        ]

        dec = None
        enc = None
        try:
            dec = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            enc = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            self.dec_proc = dec
            self.enc_proc = enc

            frame_size = w * h * 3
            frame_idx = 0
            tracks: list[dict] = []
            next_track_id = 1
            hold_frames = max(1, int(round(fps * cfg["hold_s"])))
            last_results: list[PlateResult] = []
            started = time.time()
            last_preview = 0.0

            while True:
                if self.cancel_flag:
                    break
                raw = dec.stdout.read(frame_size)
                if not raw or len(raw) < frame_size:
                    break

                frame = np.frombuffer(raw, np.uint8).reshape((h, w, 3)).copy()
                now_s = frame_idx / fps if fps else 0.0

                if frame_idx % stride == 0:
                    raw_results = self.detect_frame(model, ocr, frame, video_path.name, frame_idx, round(now_s, 3), cfg, device, log_rows=False)
                    tracks, next_track_id = self.update_tracks(tracks, raw_results, next_track_id, frame_idx, round(now_s, 3), video_path.name, cfg, hold_frames)

                last_results = self.tracks_to_results(tracks, frame_idx, hold_frames, cfg)
                annotated = self.draw(frame, last_results)

                if enc.stdin:
                    try:
                        enc.stdin.write(annotated.tobytes())
                    except (BrokenPipeError, OSError):
                        if self.cancel_flag:
                            break
                        raise

                if frame_idx % max(1, int(fps)) == 0:
                    if total_frames:
                        self.after(0, lambda p=min(100.0, frame_idx * 100.0 / total_frames): self.progress_var.set(p))
                    elapsed = time.time() - started
                    speed = frame_idx / elapsed if elapsed > 0 else 0.0
                    self.set_status(f"Frame {frame_idx}/{total_frames or '?'} • speed={speed:.1f}fps • rows={len(self.rows)}")

                tnow = time.time()
                if tnow - last_preview > 0.5:
                    last_preview = tnow
                    self.after(0, self.show_frame, annotated)

                frame_idx += 1

            if dec and dec.stdout:
                dec.stdout.close()
            if enc and enc.stdin:
                enc.stdin.close()
            dec_rc = dec.wait(timeout=10) if dec else 0
            enc_rc = enc.wait(timeout=30) if enc else 0

            dec_err = dec.stderr.read().decode("utf-8", errors="ignore") if dec and dec.stderr else ""
            enc_err = enc.stderr.read().decode("utf-8", errors="ignore") if enc and enc.stderr else ""

            if enc_rc != 0 and not self.cancel_flag:
                raise RuntimeError("FFmpeg encoder error. Thử đổi Encoder về CPU x264 nếu NVENC/AMF/QSV không có driver/phần cứng.\n" + enc_err[:2500])
            if dec_rc != 0 and not self.cancel_flag:
                raise RuntimeError("FFmpeg decoder error:\n" + dec_err[:2500])

            if self.cancel_flag:
                self.latest_output = str(temp_noaudio)
                self.set_status("Cancelled.")
                return

            # Giữ lại tiếng gốc: mux audio từ video input vào video annotated.
            final_ok = self.mux_audio_from_source(ffmpeg, temp_noaudio, video_path, out_path)
            if not final_ok:
                # Nếu video gốc không có audio hoặc mux lỗi, vẫn xuất video không tiếng thay vì fail.
                shutil.move(str(temp_noaudio), str(out_path))

            self.latest_output = str(out_path)
            self.after(0, lambda: self.progress_var.set(100))
            self.set_status(f"Done video mode with audio. Output: {out_path}")
        finally:
            try:
                if dec and dec.poll() is None:
                    dec.kill()
            except Exception:
                pass
            try:
                if enc and enc.poll() is None:
                    enc.kill()
            except Exception:
                pass
            self.dec_proc = None
            self.enc_proc = None

    def make_inference_variants(self, frame, cfg):
        """Return (name, image_variant, inverse_bbox_mapper).

        V2 idea:
        - Full image first.
        - Gamma-brightened full image for dark parking-lot frames.
        - Optional 90-degree rotations for vertical / motorcycle plates.
        - Left/right split for collage-like or crowded frames.
        - Tile scan for images with many small plates. This is the key fix for
          cases where YOLO sees only one vehicle in a crowded frame.
        """
        h, w = frame.shape[:2]
        variants = []

        def ident_box(b):
            return b

        def add_variant(name, img, mapper):
            if img is not None and getattr(img, "size", 0) > 0:
                ih, iw = img.shape[:2]
                if ih >= 32 and iw >= 32:
                    variants.append((name, img, mapper))

        add_variant("orig", frame, ident_box)

        if cfg.get("gamma_fallback", True):
            try:
                gamma = 0.65
                table = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)]).astype("uint8")
                bright = cv2.LUT(frame, table)
                add_variant("gamma065", bright, ident_box)
            except Exception:
                pass

        def inv_cw(b):
            xr1, yr1, xr2, yr2 = map(float, b)
            pts = [(yr1, h - xr1), (yr2, h - xr1), (yr1, h - xr2), (yr2, h - xr2)]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            return [max(0, min(w - 1, min(xs))), max(0, min(h - 1, min(ys))), max(0, min(w - 1, max(xs))), max(0, min(h - 1, max(ys)))]

        def inv_ccw(b):
            xr1, yr1, xr2, yr2 = map(float, b)
            pts = [(w - yr1, xr1), (w - yr2, xr1), (w - yr1, xr2), (w - yr2, xr2)]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            return [max(0, min(w - 1, min(xs))), max(0, min(h - 1, min(ys))), max(0, min(w - 1, max(xs))), max(0, min(h - 1, max(ys)))]

        if cfg.get("rotate_fallback", True):
            add_variant("rot_cw90", cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE), inv_cw)
            add_variant("rot_ccw90", cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE), inv_ccw)

        # Split left/right/top/bottom when the image is wide OR when heavy scan is enabled.
        if cfg.get("split_collage", True):
            try:
                ratio = w / max(1, h)
                if ratio >= float(cfg.get("wide_ratio", 1.45)) or cfg.get("tile_fallback", False):
                    overlap_x = max(8, int(w * 0.06))
                    mid_x = w // 2

                    ranges_x = [
                        ("split_left", 0, min(w, mid_x + overlap_x)),
                        ("split_right", max(0, mid_x - overlap_x), w),
                    ]
                    for name, x0, x1 in ranges_x:
                        crop = frame[:, x0:x1].copy()
                        def make_inv_x(xoff):
                            return lambda b: [float(b[0]) + xoff, float(b[1]), float(b[2]) + xoff, float(b[3])]
                        add_variant(name, crop, make_inv_x(x0))

                    # Crowded motorbike images often have useful plates in lower half.
                    overlap_y = max(8, int(h * 0.06))
                    mid_y = h // 2
                    ranges_y = [
                        ("split_top", 0, min(h, mid_y + overlap_y)),
                        ("split_bottom", max(0, mid_y - overlap_y), h),
                    ]
                    for name, y0, y1 in ranges_y:
                        crop = frame[y0:y1, :].copy()
                        def make_inv_y(yoff):
                            return lambda b: [float(b[0]), float(b[1]) + yoff, float(b[2]), float(b[3]) + yoff]
                        add_variant(name, crop, make_inv_y(y0))
            except Exception:
                pass

        # Grid/tile scan: intentionally overlaps tiles so plates on borders are not lost.
        if cfg.get("tile_fallback", False):
            try:
                rows = max(1, int(cfg.get("tile_rows", 2)))
                cols = max(1, int(cfg.get("tile_cols", 2)))
                overlap = max(0.0, min(0.35, float(cfg.get("tile_overlap", 0.12))))

                tile_w = max(80, int(np.ceil(w / cols)))
                tile_h = max(80, int(np.ceil(h / rows)))
                step_x = max(40, int(tile_w * (1.0 - overlap)))
                step_y = max(40, int(tile_h * (1.0 - overlap)))

                y_starts = list(range(0, max(1, h - tile_h + 1), step_y))
                x_starts = list(range(0, max(1, w - tile_w + 1), step_x))
                if not y_starts or y_starts[-1] != max(0, h - tile_h):
                    y_starts.append(max(0, h - tile_h))
                if not x_starts or x_starts[-1] != max(0, w - tile_w):
                    x_starts.append(max(0, w - tile_w))

                for yi, y0 in enumerate(sorted(set(y_starts))):
                    for xi, x0 in enumerate(sorted(set(x_starts))):
                        x1 = min(w, x0 + tile_w)
                        y1 = min(h, y0 + tile_h)
                        crop = frame[y0:y1, x0:x1].copy()
                        def make_inv_xy(xoff, yoff):
                            return lambda b: [float(b[0]) + xoff, float(b[1]) + yoff, float(b[2]) + xoff, float(b[3]) + yoff]
                        add_variant(f"tile_{yi}_{xi}", crop, make_inv_xy(x0, y0))
            except Exception:
                pass

        return variants

    def predict_boxes_on_image(self, model, img, conf, imgsz, device):
        result = model.predict(img, imgsz=imgsz, conf=conf, iou=0.42, max_det=60, device=device, verbose=False)[0]
        found = []
        if result.boxes is None:
            return found
        hh, ww = img.shape[:2]
        for b in result.boxes:
            bbox = b.xyxy[0].detach().cpu().numpy().tolist()
            bbox = [
                max(0, min(ww - 1, float(bbox[0]))),
                max(0, min(hh - 1, float(bbox[1]))),
                max(0, min(ww - 1, float(bbox[2]))),
                max(0, min(hh - 1, float(bbox[3]))),
            ]
            found.append((bbox, float(b.conf[0].detach().cpu().numpy())))
        return found

    def dedup_detection_boxes(self, boxes, iou_thr=0.45):
        boxes = sorted(boxes, key=lambda x: x[1], reverse=True)
        kept = []
        for bbox, conf, variant in boxes:
            if all(bbox_iou(bbox, kb) < iou_thr for kb, _, _ in kept):
                kept.append((bbox, conf, variant))
        return kept

    def pass_geometry_filter(self, bbox, frame_w: int, frame_h: int) -> bool:
        x1, y1, x2, y2 = map(float, bbox)
        bw = max(1.0, x2 - x1)
        bh = max(1.0, y2 - y1)
        area_ratio = (bw * bh) / max(1.0, float(frame_w * frame_h))
        aspect = bw / bh
        # Keep loose enough for skewed/motorbike plates, but reject huge wall/column text regions.
        return 0.00008 <= area_ratio <= 0.12 and 0.55 <= aspect <= 8.50

    def visual_plate_score(self, crop_bgr: np.ndarray) -> float:
        """Simple CV guard against parking-column labels painted on walls/pillars."""
        try:
            if crop_bgr is None or crop_bgr.size == 0:
                return 0.0
            h, w = crop_bgr.shape[:2]
            if h < 14 or w < 24:
                return 0.0
            ar = w / max(1.0, h)
            if not (0.55 <= ar <= 8.50):
                return 0.0

            gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 55, 165)
            b = max(2, int(round(min(h, w) * 0.08)))
            border_mask = np.zeros((h, w), np.uint8)
            border_mask[:b, :] = 1
            border_mask[-b:, :] = 1
            border_mask[:, :b] = 1
            border_mask[:, -b:] = 1
            border_density = float(np.mean(edges[border_mask == 1] > 0)) if np.any(border_mask) else 0.0
            edge_density = float(np.mean(edges > 0))

            hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
            sat = hsv[:, :, 1]
            val = hsv[:, :, 2]
            white_ratio = float(np.mean((sat < 80) & (val > 130)))
            yellow_ratio = float(np.mean((hsv[:, :, 0] >= 15) & (hsv[:, :, 0] <= 45) & (sat > 70) & (val > 100)))
            dark_ratio = float(np.mean(gray < 95))

            score = 0.0
            score += min(0.35, border_density * 2.2)
            score += min(0.25, edge_density * 2.0)
            score += min(0.20, dark_ratio * 1.1)
            score += min(0.20, (white_ratio + yellow_ratio) * 0.35)
            if 1.05 <= ar <= 5.80:
                score += 0.10
            if 2.0 <= ar <= 5.5:
                score += 0.05
            return float(max(0.0, min(1.0, score)))
        except Exception:
            return 0.0

    def reject_by_anti_sign_guard(self, crop_bgr, bbox, frame_w, frame_h, text, source, det_conf, ocr_conf, cfg) -> bool:
        if not cfg.get("anti_sign_guard", True):
            return False

        t = clean_text(text)
        src = str(source or "")
        rel = reliability_score(t, det_conf, ocr_conf, bbox)
        visual = self.visual_plate_score(crop_bgr)

        if "fallback_whole" in src or "fallback_left" in src or "fallback_right" in src:
            return True

        raw = source_raw_text(src)

        # A tricky false positive is OCR turning a basement label D29/D28 into
        # something that superficially looks like 29D2828. If the crop does not
        # visually look like a physical plate, suppress it. A real plate with a
        # strong detector score or visible rectangular plate border still passes.
        if plausible_plate_text(t):
            if re.search(r"(^D\d{1,3}|D2\d|D3\d)", raw) and visual < 0.32 and det_conf < 0.70:
                return True
            if "classical" in src and visual < 0.28 and det_conf < 0.55:
                return True

        if looks_like_parking_area_code(t, src):
            return True

        if not plausible_plate_text(t):
            if not re.match(r"^\d{2}", t) or t[:2] not in VN_PROVINCE_CODES:
                return True
            if visual < 0.32 and det_conf < 0.45:
                return True
            if rel < 0.35 and visual < 0.45:
                return True

        if "classical_blue" in src and visual < 0.45:
            return True

        x1, y1, x2, y2 = map(float, bbox)
        bw, bh = max(1.0, x2 - x1), max(1.0, y2 - y1)
        area_ratio = (bw * bh) / max(1.0, float(frame_w * frame_h))
        y_center = (y1 + y2) * 0.5 / max(1.0, frame_h)
        if area_ratio > 0.020 and y_center < 0.42 and not plausible_plate_text(t):
            return True
        return False

    def classical_plate_fallback_boxes(self, frame, max_boxes=4):
        """Fallback when YOLO misses an obvious plate.

        Useful for blue/white long plates such as 36B1024 where the detector
        occasionally returns no box, so OCR never gets a crop.
        """
        try:
            h, w = frame.shape[:2]
            area_img = max(1.0, float(h * w))

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            blue = cv2.inRange(hsv, np.array([85, 40, 40]), np.array([135, 255, 255]))

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            bright = cv2.inRange(gray, 135, 255)

            edges = cv2.Canny(gray, 60, 160)
            edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

            # Do NOT use pure-blue mask by default: basement column labels
            # such as D28/D29 are blue and trigger false positives.
            masks = [
                ("bright", bright, 0.00035, 0.22),
                ("edge", edges, 0.00035, 0.22),
            ]

            kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 5))
            kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            boxes = []

            for tag, mask, min_area_ratio, max_area_ratio in masks:
                m = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)
                m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel_open, iterations=1)
                contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for cnt in contours:
                    x, y, bw, bh = cv2.boundingRect(cnt)
                    if bw <= 10 or bh <= 8:
                        continue

                    ar = bw / max(1.0, bh)
                    area_ratio = (bw * bh) / area_img

                    if not (1.15 <= ar <= 7.5):
                        continue
                    if not (min_area_ratio <= area_ratio <= max_area_ratio):
                        continue

                    extent = cv2.contourArea(cnt) / max(1.0, bw * bh)
                    if tag != "edge" and extent < 0.18:
                        continue

                    y_center = (y + bh * 0.5) / max(1.0, h)
                    score = 0.18 + (0.10 if y_center > 0.25 else 0.0)
                    score += min(0.35, area_ratio * 8.0)
                    if tag == "blue":
                        score += 0.18
                    if 2.0 <= ar <= 5.8:
                        score += 0.12
                    if 1.15 <= ar < 2.0:
                        score += 0.06

                    pad_x = int(max(3, bw * 0.04))
                    pad_y = int(max(3, bh * 0.08))
                    box = [
                        max(0, x - pad_x),
                        max(0, y - pad_y),
                        min(w - 1, x + bw + pad_x),
                        min(h - 1, y + bh + pad_y),
                    ]
                    boxes.append((box, float(min(0.65, score)), f"classical_{tag}"))

            boxes = sorted(boxes, key=lambda x: x[1], reverse=True)
            kept = []
            for b, s, tag in boxes:
                if all(bbox_iou(b, kb) < 0.35 for kb, _, _ in kept):
                    kept.append((b, s, tag))
                if len(kept) >= max_boxes:
                    break

            return kept
        except Exception:
            return []


    def detect_frame(self, model, ocr, frame, input_name, frame_idx, time_s, cfg, device, log_rows=True):
        h, w = frame.shape[:2]
        out: list[PlateResult] = []
        raw_boxes = []

        for vi, (variant_name, img_variant, inv_map) in enumerate(self.make_inference_variants(frame, cfg)):
            # Old app stopped after the first detected box; that caused missed plates
            # in crowded parking-lot images. Stop only after enough boxes, unless heavy scan is on.
            if vi > 0 and not cfg.get("rotate_always", False) and len(raw_boxes) >= int(cfg.get("variant_stop_boxes", 2)):
                break
            for vbbox, vconf in self.predict_boxes_on_image(model, img_variant, cfg.get("conf", 0.25), cfg.get("imgsz", 768), device):
                raw_boxes.append((inv_map(vbbox), vconf, variant_name))

        raw_boxes = self.dedup_detection_boxes(raw_boxes, iou_thr=0.45)

        # YOLO-miss fallback: in V2 we can also add these boxes during heavy image scan,
        # not only when YOLO returns zero boxes.
        if cfg.get("classical_fallback", True) and (not raw_boxes or cfg.get("tile_fallback", False)):
            raw_boxes.extend(self.classical_plate_fallback_boxes(frame, max_boxes=max(4, int(cfg.get("max_show", 8)))))
            raw_boxes = self.dedup_detection_boxes(raw_boxes, iou_thr=0.40)

        if not raw_boxes and cfg.get("whole_scene_fallback", False) and cfg["split_collage"]:
            # Disabled by default in V3 because OCR on a half/whole parking-lot
            # image tends to read pillar labels such as D28/D29.
            ratio = w / max(1, h)
            if ratio >= float(cfg["wide_ratio"]):
                mid = w // 2
                raw_boxes = [
                    ([0, 0, max(1, mid - 1), h - 1], 0.01, "fallback_left"),
                    ([mid, 0, w - 1, h - 1], 0.01, "fallback_right"),
                ]
            else:
                raw_boxes = [([0, 0, w - 1, h - 1], 0.01, "fallback_whole")]

        for plate_idx, (bbox, det_conf, variant_name) in enumerate(raw_boxes):
            if not (str(variant_name).startswith("fallback") or str(variant_name).startswith("classical")) and not self.pass_geometry_filter(bbox, w, h):
                continue

            crop = crop_box(frame, expand_box(bbox, w, h, pad=float(cfg.get("crop_pad", 0.08))))
            crop_path = ""
            if crop is not None and crop.size > 0:
                safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(str(input_name)).stem)
                frame_part = f"_frame_{frame_idx}" if frame_idx != "" else ""
                crop_path = str(CROP_DIR / f"{safe_stem}{frame_part}_plate_{plate_idx}.jpg")
                cv2.imwrite(crop_path, crop)

            if crop is not None and crop.size > 0:
                text, ocr_conf, source = ocr.read(crop)
                if not text:
                    text, display = "UNKNOWN", "UNKNOWN"
                else:
                    display = format_plate_smart(text, bbox)
            else:
                text, ocr_conf, source, display = "UNKNOWN", 0.0, "empty_crop", "UNKNOWN"

            source = f"{source}|{variant_name}"

            if self.reject_by_anti_sign_guard(crop, bbox, w, h, text, source, det_conf, ocr_conf, cfg):
                continue

            pr = PlateResult(bbox=bbox, det_conf=det_conf, text=text, display=display, ocr_conf=ocr_conf, source=source, crop_path=crop_path)
            out.append(pr)

            if log_rows:
                row = {
                    "input": input_name,
                    "time_s": time_s,
                    "frame": frame_idx,
                    "plate": text,
                    "reliability": reliability_text(text, det_conf, ocr_conf, bbox),
                    "det_conf": round(det_conf, 4),
                    "ocr_conf": round(float(ocr_conf), 4),
                    "source": source,
                    "bbox_xyxy": ",".join(str(round(x, 1)) for x in bbox),
                    "crop_path": crop_path,
                }
                self.rows.append(row)
                self.after(0, self.add_row_ui, row)

        return out

    def add_ocr_vote(self, tr: dict, text: str, ocr_conf: float):
        t = clean_text(text)
        if not t or t in {"UNKNOWN", "NOOCR", "NO_OCR"}:
            return
        votes = tr.setdefault("votes", {})
        weight = plate_vote_weight(t, ocr_conf)
        if weight <= 0:
            return
        if t not in votes:
            votes[t] = {"score": 0.0, "best_conf": 0.0, "count": 0}
        votes[t]["score"] += weight
        votes[t]["best_conf"] = max(float(votes[t]["best_conf"]), float(ocr_conf or 0.0))
        votes[t]["count"] += 1
        best_text, best_meta = max(votes.items(), key=lambda kv: (kv[1]["score"], kv[1]["best_conf"], 1 if valid_plate(kv[0]) else 0, kv[1]["count"]))
        tr["best_text"] = best_text
        tr["best_conf"] = float(best_meta["best_conf"])

    def update_tracks(self, tracks, detections, next_track_id, frame_idx, time_s, input_name, cfg, hold_frames):
        matched_tracks = set()
        matched_dets = set()
        det_order = sorted(range(len(detections)), key=lambda i: detections[i].det_conf, reverse=True)

        for di in det_order:
            det = detections[di]
            best_ti, best_iou = None, 0.0
            for ti, tr in enumerate(tracks):
                if ti in matched_tracks:
                    continue
                if frame_idx - int(tr.get("last_seen", -10**9)) > hold_frames:
                    continue
                score = bbox_iou(det.bbox, tr.get("smooth_bbox", tr.get("bbox", det.bbox)))
                if score > best_iou:
                    best_iou, best_ti = score, ti

            if best_ti is not None and best_iou >= 0.20:
                tr = tracks[best_ti]
                tr["bbox"] = list(det.bbox)
                tr["smooth_bbox"] = ema_box(tr.get("smooth_bbox", det.bbox), det.bbox, cfg["smooth"])
                tr["last_seen"] = frame_idx
                tr["hits"] = int(tr.get("hits", 0)) + 1
                tr["det_conf"] = float(tr.get("det_conf", det.det_conf)) * 0.70 + float(det.det_conf) * 0.30
                tr["source"] = det.source
                tr["crop_path"] = det.crop_path or tr.get("crop_path", "")
                self.add_ocr_vote(tr, det.text, det.ocr_conf)
                matched_tracks.add(best_ti)
                matched_dets.add(di)

        for di, det in enumerate(detections):
            if di in matched_dets:
                continue
            tr = {
                "id": next_track_id,
                "bbox": list(det.bbox),
                "smooth_bbox": list(det.bbox),
                "first_seen": frame_idx,
                "last_seen": frame_idx,
                "hits": 1,
                "det_conf": float(det.det_conf),
                "best_text": clean_text(det.text) if clean_text(det.text) else "UNKNOWN",
                "best_conf": float(det.ocr_conf or 0.0),
                "source": det.source,
                "crop_path": det.crop_path,
                "votes": {},
            }
            self.add_ocr_vote(tr, det.text, det.ocr_conf)
            tracks.append(tr)
            next_track_id += 1

        tracks = [tr for tr in tracks if frame_idx - int(tr.get("last_seen", frame_idx)) <= hold_frames]

        for tr in tracks:
            if int(tr.get("last_seen", -1)) != frame_idx:
                continue
            text = tr.get("best_text", "UNKNOWN") or "UNKNOWN"
            if cfg.get("hide_unknown", True) and text in {"UNKNOWN", "NO_OCR", "NOOCR"}:
                continue
            if cfg.get("only_valid_vn", False) and not valid_plate(text):
                continue
            if reliability_score(text, float(tr.get("det_conf", 0.0)), float(tr.get("best_conf", 0.0)), tr.get("smooth_bbox", tr.get("bbox", [0, 0, 1, 1]))) < float(cfg.get("min_reliability", 0.0)):
                continue
            row = {
                "input": input_name,
                "time_s": time_s,
                "frame": frame_idx,
                "track_id": tr.get("id", ""),
                "plate": text,
                "reliability": reliability_text(text, float(tr.get("det_conf", 0.0)), float(tr.get("best_conf", 0.0)), tr.get("smooth_bbox", tr.get("bbox", [0, 0, 1, 1]))),
                "det_conf": round(float(tr.get("det_conf", 0.0)), 4),
                "ocr_conf": round(float(tr.get("best_conf", 0.0)), 4),
                "source": "stable_track_vote",
                "bbox_xyxy": ",".join(str(round(x, 1)) for x in tr.get("smooth_bbox", [])),
                "crop_path": tr.get("crop_path", ""),
                "hits": tr.get("hits", 0),
            }
            self.rows.append(row)
            self.after(0, self.add_row_ui, row)

        return tracks, next_track_id

    def tracks_to_results(self, tracks, frame_idx, hold_frames, cfg):
        out = []
        for tr in tracks:
            age = frame_idx - int(tr.get("last_seen", frame_idx))
            if age > hold_frames:
                continue
            text = tr.get("best_text", "UNKNOWN") or "UNKNOWN"
            if cfg.get("hide_unknown", True) and text in {"UNKNOWN", "NO_OCR", "NOOCR"}:
                continue
            if cfg.get("only_valid_vn", False) and not valid_plate(text):
                continue
            if int(tr.get("hits", 0)) < int(cfg.get("min_hits", 1)):
                continue
            age_factor = max(0.25, 1.0 - age / max(1, hold_frames + 1))
            out.append(PlateResult(
                bbox=list(tr.get("smooth_bbox", tr.get("bbox", [0, 0, 1, 1]))),
                det_conf=float(tr.get("det_conf", 0.0)) * age_factor,
                text=text,
                display=format_plate_smart(text, tr.get("smooth_bbox", tr.get("bbox", [0, 0, 1, 1]))),
                ocr_conf=float(tr.get("best_conf", 0.0)),
                source=f"track#{tr.get('id', '?')} hits={tr.get('hits', 0)} age={age}",
                crop_path=tr.get("crop_path", ""),
            ))
        return self.clean_display_results(out, cfg)

    def center_inside_expanded(self, inner_bbox, outer_bbox, margin_ratio: float) -> bool:
        ix1, iy1, ix2, iy2 = map(float, inner_bbox)
        ox1, oy1, ox2, oy2 = map(float, outer_bbox)
        cx = (ix1 + ix2) * 0.5
        cy = (iy1 + iy2) * 0.5
        ow = max(1.0, ox2 - ox1)
        oh = max(1.0, oy2 - oy1)
        mx = ow * max(0.0, float(margin_ratio))
        my = oh * max(0.0, float(margin_ratio))
        return (ox1 - mx) <= cx <= (ox2 + mx) and (oy1 - my) <= cy <= (oy2 + my)

    def suppress_same_region(self, results, cfg):
        kept = []
        for r in results:
            conflict = False
            for k in kept:
                if bbox_iou(r.bbox, k.bbox) >= cfg["region_iou"]:
                    conflict = True
                    break
                if self.center_inside_expanded(r.bbox, k.bbox, cfg["center_margin"]) or self.center_inside_expanded(k.bbox, r.bbox, cfg["center_margin"]):
                    conflict = True
                    break
            if not conflict:
                kept.append(r)
        return kept

    def clean_display_results(self, results, cfg):
        def score(r: PlateResult):
            x1, y1, x2, y2 = map(float, r.bbox)
            area = max(1.0, (x2 - x1) * (y2 - y1))
            return (1 if valid_plate(clean_text(r.text)) else 0, float(r.ocr_conf), float(r.det_conf), area)

        good = []
        min_rel = float(cfg.get("min_reliability", 0.0))
        for r in results:
            t = clean_text(r.text)
            if cfg.get("hide_unknown", True) and (not t or t in {"UNKNOWN", "NOOCR", "NO_OCR"}):
                continue
            if cfg.get("anti_sign_guard", True) and looks_like_parking_area_code(t, r.source):
                continue
            if cfg.get("only_valid_vn", False) and not plausible_plate_text(t):
                continue
            # User-adjustable confidence requirement. Lower this when the model misses plates.
            rel = reliability_score(t, r.det_conf, r.ocr_conf, r.bbox)
            if rel < min_rel:
                continue
            good.append(r)

        good = sorted(good, key=score, reverse=True)
        good = self.suppress_same_region(good, cfg)
        return good[: max(1, int(cfg.get("max_show", 4)))]

    def draw(self, frame, results: list[PlateResult]):
        cfg = self.cfg()
        results = self.clean_display_results(results, cfg)
        vis = frame.copy()
        h, w = vis.shape[:2]
        font_scale = max(0.52, min(1.00, w / 1150))
        thickness = max(2, int(round(min(h, w) / 420)))

        for d in results:
            x1, y1, x2, y2 = map(int, d.bbox)
            label = cv2_ascii_label(clean_text(d.text) + " | " + reliability_text(d.text, d.det_conf, d.ocr_conf, d.bbox))
            box_color = (0, 210, 80)
            cv2.rectangle(vis, (x1, y1), (x2, y2), box_color, thickness)

            local_font = font_scale
            (tw, th), base = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, local_font, 2)
            max_label_w = max(80, min(w - 20, int((x2 - x1) * 1.8)))
            while tw > max_label_w and local_font > 0.42:
                local_font -= 0.04
                (tw, th), base = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, local_font, 2)
            tx = max(0, min(x1, w - tw - 12))
            ty = y1 - 8
            top_y = ty - th - base - 8

            if top_y < 0:
                ty = min(h - 6, y2 + th + base + 10)
                top_y = ty - th - base - 8

            # FastALPR-source-style text: black outline + white foreground.
            org = (tx + 5, min(h - 6, ty))
            text_thickness = 2
            outline_thickness = max(4, text_thickness + 3)
            cv2.putText(vis, label, org, cv2.FONT_HERSHEY_SIMPLEX, local_font, (0, 0, 0), outline_thickness, cv2.LINE_AA)
            cv2.putText(vis, label, org, cv2.FONT_HERSHEY_SIMPLEX, local_font, (255, 255, 255), text_thickness, cv2.LINE_AA)
        return vis

    def mux_audio_from_source(self, ffmpeg, video_noaudio: Path, source_video: Path, output_video: Path) -> bool:
        """Copy annotated video stream and mux original audio if available."""
        try:
            tmp_mux = output_video.with_name(output_video.stem + "_audio_mux_tmp.mp4")
            if tmp_mux.exists():
                tmp_mux.unlink()

            cmd = [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel", "error",
                "-i", str(video_noaudio),
                "-i", str(source_video),
                "-map", "0:v:0",
                "-map", "1:a?",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "160k",
                "-shortest",
                str(tmp_mux),
            ]
            cp = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=120,
            )

            if cp.returncode == 0 and tmp_mux.exists() and tmp_mux.stat().st_size > 0:
                if output_video.exists():
                    output_video.unlink()
                shutil.move(str(tmp_mux), str(output_video))
                try:
                    video_noaudio.unlink()
                except Exception:
                    pass
                return True

            # Có thể input không có audio. Không coi là lỗi nặng.
            try:
                if tmp_mux.exists():
                    tmp_mux.unlink()
            except Exception:
                pass
            return False
        except Exception:
            return False


    def show_frame(self, bgr):
        try:
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            cw = max(400, self.canvas.winfo_width())
            ch = max(300, self.canvas.winfo_height())
            img.thumbnail((cw, ch), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(cw // 2, ch // 2, image=self.photo, anchor="center")
        except Exception:
            pass


    def on_result_select(self, _event=None):
        try:
            selected = self.table.selection()
            if not selected:
                return
            row = self.row_by_iid.get(selected[0], {})
            self.show_result_preview(row)
            crop_path = row.get("crop_path", "")
            self.show_crop_preview(crop_path, row)
        except Exception:
            pass

    def show_result_preview(self, row: dict):
        preview_path = row.get("annotated_path") or row.get("image_path") or ""
        if not preview_path:
            return
        p = Path(str(preview_path))
        if not p.exists():
            return
        bgr = cv2.imread(str(p))
        if bgr is None:
            return
        self.show_frame(bgr)

    def show_crop_preview(self, crop_path: str, row: dict | None = None):
        try:
            self.crop_canvas.delete("all")
            cw = max(260, self.crop_canvas.winfo_width())
            ch = max(90, self.crop_canvas.winfo_height())
            label = ""
            if row:
                label = f"{row.get('plate','')} | trust={row.get('reliability','')} | det={row.get('det_conf','')} | ocr={row.get('ocr_conf','')}"
            p = Path(str(crop_path))
            if not crop_path or not p.exists():
                self.crop_canvas.create_text(cw // 2, ch // 2, text="Không có crop để xem", fill="white")
                return
            bgr = cv2.imread(str(p))
            if bgr is None:
                self.crop_canvas.create_text(cw // 2, ch // 2, text="Không đọc được crop", fill="white")
                return
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img.thumbnail((cw - 12, ch - 28), Image.LANCZOS)
            self.crop_photo = ImageTk.PhotoImage(img)
            self.crop_canvas.create_image(cw // 2, max(8, (ch - 22)//2), image=self.crop_photo, anchor="center")
            if label:
                self.crop_canvas.create_text(cw // 2, ch - 12, text=cv2_ascii_label(label)[:80], fill="white")
        except Exception:
            pass

    @staticmethod
    def open_path(path):
        try:
            os.startfile(str(path))
        except Exception:
            pass


if __name__ == "__main__":
    App().mainloop()

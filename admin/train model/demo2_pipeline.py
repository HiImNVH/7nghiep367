"""One video-to-tensor path for offline and future API callers."""

import hashlib
import json
import time
from contextlib import ExitStack
from pathlib import Path

import av
import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

ROOT = Path(__file__).resolve().parents[2] / "ai"


class PipelineError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def load_schema():
    return json.loads((ROOT / "configs/feature_schema.legacy-v0.2.json").read_text("utf-8"))


def decode_video(path, max_frames=900, max_seconds=30):
    """MP4 allowed for local references; WebM is the browser integration target."""
    path = Path(path)
    if not path.is_file():
        raise PipelineError("INVALID_REQUEST", "Video không tồn tại.")
    if path.stat().st_size > 100 * 1024 * 1024:
        raise PipelineError("CLIP_TOO_LARGE", "Demo giới hạn 100 MB.")
    with path.open("rb") as source:
        header = source.read(16)
    if not (header[:4] == b"\x1aE\xdf\xa3" or header[4:8] == b"ftyp"):
        raise PipelineError(
            "UNSUPPORTED_MEDIA_TYPE", "Cần video WebM hoặc MP4 thực sự."
        )
    frames, timestamps = [], []
    try:
        with av.open(str(path)) as container:
            if not container.streams.video:
                raise PipelineError("CLIP_DECODE_FAILED", "Không có video stream.")
            for frame in container.decode(video=0):
                if frame.pts is None or frame.time_base is None:
                    raise PipelineError("INVALID_TIMESTAMPS", "Frame không có PTS.")
                stamp = float(frame.pts * frame.time_base * 1000)
                if timestamps and stamp <= timestamps[-1]:
                    raise PipelineError(
                        "INVALID_TIMESTAMPS", "PTS không tăng nghiêm ngặt."
                    )
                if len(frames) >= max_frames or (
                    timestamps and stamp - timestamps[0] > max_seconds * 1000
                ):
                    raise PipelineError(
                        "CLIP_TOO_LONG", "Demo giới hạn 30 giây / 900 frame."
                    )
                if frame.width * frame.height > 3840 * 2160:
                    raise PipelineError(
                        "INVALID_REQUEST", "Độ phân giải vượt giới hạn demo 4K."
                    )
                rgb = frame.to_ndarray(format="rgb24")
                scale = min(1.0, 640 / rgb.shape[1])
                if scale < 1:
                    rgb = cv2.resize(rgb, (640, max(1, round(rgb.shape[0] * scale))))
                frames.append(rgb)
                timestamps.append(stamp)
    except PipelineError:
        raise
    except (av.error.FFmpegError, OSError, ValueError) as exc:
        raise PipelineError("CLIP_DECODE_FAILED", "Không giải mã được video.") from exc
    if not frames:
        raise PipelineError("CLIP_DECODE_FAILED", "Video không có frame đọc được.")
    timestamps = np.asarray(timestamps, dtype=np.float64)
    timestamps -= timestamps[0]
    integer_ms = np.rint(timestamps).astype(np.int64)
    if len(integer_ms) > 1 and np.any(np.diff(integer_ms) <= 0):
        raise PipelineError(
            "INVALID_TIMESTAMPS", "PTS quá gần để biểu diễn bằng mili giây nguyên."
        )
    return frames, timestamps, integer_ms


def extractor_identity(schema):
    assets = {}
    for filename in schema["modelFiles"].values():
        assets[filename] = hashlib.sha256(
            (ROOT / "models" / filename).read_bytes()
        ).hexdigest()
    expected = json.loads(
        (ROOT / "models/download-manifest.json").read_text("utf-8-sig")
    )
    for item in expected:
        if assets.get(item["name"]) != item["sha256"].lower():
            raise PipelineError(
                "MODEL_ASSET_MISMATCH", "Hash detector không khớp bản đã tải."
            )
    digest = hashlib.sha256(json.dumps(assets, sort_keys=True).encode()).hexdigest()[
        :16
    ]
    return {
        "version": f"tasks-hand-pose-face-{mp.__version__}-{digest}",
        "sha256": assets,
    }


def group_masks(valid):
    """Group pose flag means shoulders available, not all six arm points."""
    return np.column_stack(
        [
            valid[:, :21].all(axis=1),
            valid[:, 21:42].all(axis=1),
            valid[:, 42:44].all(axis=1),
            valid[:, 48:].all(axis=1),
        ]
    )


def extract(frames, timestamps, schema):
    n, count = len(frames), len(schema["landmarkOrder"])
    coords = np.full((n, count, 2), np.nan, dtype=np.float32)
    valid = np.zeros((n, count), dtype=bool)
    visibility = np.full((n, count), np.nan, np.float32)
    presence = np.full((n, count), np.nan, np.float32)
    hand_scores = np.full((n, 2), np.nan, np.float32)
    ambiguous = []
    with ExitStack() as stack:
        detectors = []
        for name, cls, opts in [
            ("hand", vision.HandLandmarker, vision.HandLandmarkerOptions),
            ("pose", vision.PoseLandmarker, vision.PoseLandmarkerOptions),
            ("face", vision.FaceLandmarker, vision.FaceLandmarkerOptions),
        ]:
            base = python.BaseOptions(
                model_asset_buffer=(
                    ROOT / "models" / schema["modelFiles"][name]
                ).read_bytes()
            )
            kwargs = {"num_hands": 2} if name == "hand" else {}
            options = opts(
                base_options=base, running_mode=vision.RunningMode.VIDEO, **kwargs
            )
            detectors.append(stack.enter_context(cls.create_from_options(options)))
        for i, rgb in enumerate(frames):
            image = mp.Image(
                image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb)
            )
            hand, pose, face = [
                d.detect_for_video(image, int(timestamps[i])) for d in detectors
            ]
            # Keep the highest-scoring candidate for each side; expose collisions explicitly.
            for landmarks, handedness in zip(hand.hand_landmarks, hand.handedness):
                label = handedness[0].category_name
                slot = 0 if label == "Left" else 1
                score = handedness[0].score
                if np.isfinite(hand_scores[i, slot]):
                    ambiguous.append(
                        {
                            "frame": i,
                            "side": label,
                            "reason": "duplicate side candidates",
                            "candidateXY": [[p.x, p.y] for p in landmarks],
                            "candidateScore": float(score),
                            "previousXY": coords[
                                i, slot * 21 : (slot + 1) * 21
                            ].tolist(),
                            "previousScore": float(hand_scores[i, slot]),
                        }
                    )
                    if score <= hand_scores[i, slot]:
                        continue
                hand_scores[i, slot] = score
                coords[i, slot * 21 : (slot + 1) * 21] = [(p.x, p.y) for p in landmarks]
                valid[i, slot * 21 : (slot + 1) * 21] = np.isfinite(
                    coords[i, slot * 21 : (slot + 1) * 21]
                ).all(axis=1)
            if pose.pose_landmarks:
                points = pose.pose_landmarks[0]
                for j, k in enumerate(schema["poseIndices"], start=42):
                    p = points[k]
                    coords[i, j] = [p.x, p.y]
                    visibility[i, j], presence[i, j] = p.visibility, p.presence
                    valid[i, j] = (
                        p.visibility >= schema["poseMinVisibility"]
                        and p.presence >= schema["poseMinPresence"]
                        and 0 <= p.x <= 1
                        and 0 <= p.y <= 1
                    )
            if face.face_landmarks:
                coords[i, 48:] = [
                    (face.face_landmarks[0][k].x, face.face_landmarks[0][k].y)
                    for k in schema["faceIndices"]
                ]
                valid[i, 48:] = np.isfinite(coords[i, 48:]).all(axis=1)
    return coords, valid, visibility, presence, hand_scores, ambiguous


def transform(coords, point_valid, timestamps, width, height, schema):
    """Only two reliable shoulders are needed for normalization; mask each point independently."""
    points = np.asarray(coords, dtype=np.float64).copy() * [width, height]
    valid = np.asarray(point_valid, dtype=bool).copy() & np.isfinite(points).all(axis=2)
    origin = (points[:, 42] + points[:, 43]) / 2
    scale = np.linalg.norm(points[:, 42] - points[:, 43], axis=1)
    anchor_ok = valid[:, 42] & valid[:, 43] & np.isfinite(scale) & (scale >= 1)
    valid &= anchor_ok[:, None]
    normalized = (points - origin[:, None]) / np.where(anchor_ok, scale, 1)[
        :, None, None
    ]
    normalized[~valid] = 0
    target = np.linspace(timestamps[0], timestamps[-1], schema["targetFrameCount"])
    output = np.zeros((len(target), points.shape[1], 2), np.float32)
    output_valid = np.zeros((len(target), points.shape[1]), bool)
    for i, stamp in enumerate(target):
        right = min(int(np.searchsorted(timestamps, stamp)), len(timestamps) - 1)
        left = right if timestamps[right] == stamp else max(0, right - 1)
        span = timestamps[right] - timestamps[left]
        weight = 0 if span == 0 else (stamp - timestamps[left]) / span
        ok = valid[left] & valid[right]
        output[i, ok] = (1 - weight) * normalized[left, ok] + weight * normalized[
            right, ok
        ]
        output_valid[i] = ok
    tensor = np.concatenate(
        [output.reshape(len(target), -1), output_valid.astype(np.float32)], axis=1
    )
    return tensor, output_valid, target


def process_video(path, expected_schema_version=None):
    schema = load_schema()
    if (
        expected_schema_version
        and expected_schema_version != schema["featureSchemaVersion"]
    ):
        raise PipelineError("FEATURE_SCHEMA_MISMATCH", "Schema không khớp bên gọi.")
    identity = extractor_identity(schema)
    if identity["version"] != schema["extractorVersion"]:
        raise PipelineError(
            "EXTRACTOR_VERSION_MISMATCH", "Extractor khác phiên bản schema đã khóa."
        )
    start = time.perf_counter()
    frames, timestamps, integer_ms = decode_video(path)
    decoded = time.perf_counter()
    if any(f.shape != frames[0].shape for f in frames):
        raise PipelineError("INVALID_REQUEST", "Kích thước frame thay đổi trong clip.")
    coords, valid, visibility, presence, hand_scores, ambiguous = extract(
        frames, integer_ms, schema
    )
    extracted = time.perf_counter()
    tensor, tensor_valid, target = transform(
        coords, valid, timestamps, frames[0].shape[1], frames[0].shape[0], schema
    )
    finished = time.perf_counter()
    groups = group_masks(valid)
    tensor_groups = group_masks(tensor_valid)
    usable = tensor_groups[:, 2] & tensor_groups[:, :2].any(axis=1)
    both = groups[:, 0] & groups[:, 1]
    report = {
        "demoReady": False,
        "stage": "preprocessing-only",
        "classificationAvailable": False,
        "featureSchemaVersion": schema["featureSchemaVersion"],
        "extractor": identity,
        "schemaSha256": hashlib.sha256(
            json.dumps(schema, sort_keys=True).encode()
        ).hexdigest(),
        "sourceName": Path(path).name,
        "frameCount": len(frames),
        "ptsSpanMs": float(timestamps[-1]),
        "durationNote": "First-to-last frame PTS span; not verified duration",
        "tensorShape": list(tensor.shape),
        "finiteTensor": bool(np.isfinite(tensor).all()),
        "nonzeroTensorValues": int(np.count_nonzero(tensor)),
        "detectionRatios": dict(
            zip(schema["missingMaskSchema"], groups.mean(axis=0).tolist())
        ),
        "pointValidRatios": dict(
            zip(schema["landmarkOrder"], valid.mean(axis=0).tolist())
        ),
        "bothHandsFrames": np.flatnonzero(both).tolist(),
        "bothHandsAndShouldersFrames": np.flatnonzero(both & groups[:, 2]).tolist(),
        "duplicateHandSideFrames": sorted({x["frame"] for x in ambiguous}),
        "usableTensorFrameRatio": float(usable.mean()),
        "inputStatus": "HAS_USABLE_FRAMES"
        if usable.any()
        else "INSUFFICIENT_LANDMARKS",
        "timingsMs": {
            "decode": round((decoded - start) * 1000, 2),
            "extractIncludingInit": round((extracted - decoded) * 1000, 2),
            "transform": round((finished - extracted) * 1000, 2),
            "total": round((finished - start) * 1000, 2),
        },
        "limitations": [
            "Draft schema, no sign classifier",
            "Hand side labels are detector outputs; mirrored input needs review",
            "Low-confidence pose estimates are retained but masked; not used for normalization",
            "No fabricated missing hand landmarks",
            "Not API parity, browser-camera or release-gate evidence",
        ],
    }
    return {
        "report": report,
        "schema": schema,
        "frames": frames,
        "coords": coords,
        "point_valid": valid,
        "visibility": visibility,
        "presence": presence,
        "hand_scores": hand_scores,
        "ambiguous": ambiguous,
        "masks": groups,
        "timestamps": timestamps,
        "tensor": tensor,
        "tensor_mask": tensor_valid,
        "target": target,
    }


HAND_EDGES = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
]
POSE_EDGES = [(42, 43), (42, 44), (44, 46), (43, 45), (45, 47)]


def draw_frame(result, index):
    image = cv2.cvtColor(result["frames"][index], cv2.COLOR_RGB2BGR)
    h, w = image.shape[:2]
    coords = result["coords"][index]
    valid = result["point_valid"][index]

    def pixel(k):
        return round(float(coords[k, 0]) * w), round(float(coords[k, 1]) * h)

    def color(k):
        return (
            (80, 240, 70)
            if k < 21
            else (
                (255, 170, 40)
                if k < 42
                else ((0, 215, 255) if k < 48 else (230, 140, 230))
            )
        )

    edges = HAND_EDGES + [(a + 21, b + 21) for a, b in HAND_EDGES] + POSE_EDGES
    for a, b in edges:
        if valid[a] and valid[b]:
            cv2.line(image, pixel(a), pixel(b), color(a), 2, cv2.LINE_AA)
    for k in range(len(coords)):
        if not np.isfinite(coords[k]).all():
            continue
        if valid[k]:
            cv2.circle(image, pixel(k), 3 if k < 48 else 1, color(k), -1)
        elif k >= 42 and k < 48 and np.all((coords[k] >= 0) & (coords[k] <= 1)):
            cv2.circle(image, pixel(k), 4, (155, 155, 155), 1)
    for k, label in [
        (0, "L hand"),
        (21, "R hand"),
        (42, "L shoulder"),
        (43, "R shoulder"),
    ]:
        if valid[k]:
            x, y = pixel(k)
            cv2.putText(
                image,
                label,
                (max(2, x - 30), max(40, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                color(k),
                1,
                cv2.LINE_AA,
            )
    for item in result["ambiguous"]:
        if item["frame"] != index:
            continue
        other = (
            item["previousXY"]
            if item["candidateScore"] > item["previousScore"]
            else item["candidateXY"]
        )
        other = np.asarray(other)
        for a, b in HAND_EDGES:
            pa = (round(float(other[a, 0]) * w), round(float(other[a, 1]) * h))
            pb = (round(float(other[b, 0]) * w), round(float(other[b, 1]) * h))
            cv2.line(image, pa, pb, (0, 140, 255), 1, cv2.LINE_AA)
        px, py = round(float(other[0, 0]) * w), round(float(other[0, 1]) * h)
        cv2.putText(
            image,
            "hand ? side ambiguous",
            (max(0, px - 60), max(45, py - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (0, 140, 255),
            1,
        )
    cv2.rectangle(image, (0, 0), (w, 34), (20, 25, 30), -1)
    g = result["masks"][index]
    caption = f"Frame {index}/{len(result['frames']) - 1}  {result['timestamps'][index]:.0f} ms | L:{int(g[0])} R:{int(g[1])} shoulders:{int(g[2])}"
    cv2.putText(
        image,
        caption,
        (5, 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (245, 245, 245),
        1,
        cv2.LINE_AA,
    )
    return image


def save_result(result, destination):
    """Explicit offline debugging: all frame images and readable numeric tables."""
    import csv

    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=False)
    (dest / "frames").mkdir()
    np.savez_compressed(
        dest / "features.npz",
        features=result["tensor"],
        missingPointMask=~result["tensor_mask"],
        missingMask=~group_masks(result["tensor_mask"]),
        timestampsMs=result["target"],
    )
    np.savez_compressed(
        dest / "raw-landmarks.npz",
        xy=result["coords"],
        pointValid=result["point_valid"],
        visibility=result["visibility"],
        presence=result["presence"],
        detected=result["masks"],
        handednessScores=result["hand_scores"],
        timestampsMs=result["timestamps"],
    )
    for filename, data in [
        ("report.json", result["report"]),
        ("feature_schema.json", result["schema"]),
        ("ambiguous-hands.json", result["ambiguous"]),
    ]:
        (dest / filename).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), "utf-8"
        )

    def value(v):
        return "" if not np.isfinite(v) else round(float(v), 6)

    with (dest / "landmarks.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "frame",
                "timestamp_ms",
                "landmark",
                "x_norm",
                "y_norm",
                "x_px",
                "y_px",
                "valid",
                "status",
                "pose_visibility",
                "pose_presence",
            ]
        )
        for i, points in enumerate(result["coords"]):
            h, w = result["frames"][i].shape[:2]
            for j, (x, y) in enumerate(points):
                ok = result["point_valid"][i, j]
                status = (
                    "VALID"
                    if ok
                    else (
                        "LOW_CONFIDENCE_OR_OUTSIDE"
                        if np.isfinite(x)
                        else "NOT_DETECTED"
                    )
                )
                writer.writerow(
                    [
                        i,
                        value(result["timestamps"][i]),
                        result["schema"]["landmarkOrder"][j],
                        value(x),
                        value(y),
                        value(x * w),
                        value(y * h),
                        int(ok),
                        status,
                        value(result["visibility"][i, j]),
                        value(result["presence"][i, j]),
                    ]
                )
    with (dest / "frames-summary.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "frame",
                "timestamp_ms",
                "left_hand_points",
                "right_hand_points",
                "left_shoulder",
                "right_shoulder",
                "pose_points",
                "face_points",
                "both_hands",
                "shoulders_valid",
            ]
        )
        for i, v in enumerate(result["point_valid"]):
            writer.writerow(
                [
                    i,
                    value(result["timestamps"][i]),
                    int(v[:21].sum()),
                    int(v[21:42].sum()),
                    int(v[42]),
                    int(v[43]),
                    int(v[42:48].sum()),
                    int(v[48:].sum()),
                    int(result["masks"][i, :2].all()),
                    int(result["masks"][i, 2]),
                ]
            )
    with (dest / "features.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        names = result["schema"]["landmarkOrder"]
        writer.writerow(
            ["step", "timestamp_ms"]
            + [f"{name}_{c}" for name in names for c in ["x", "y"]]
            + [f"{name}_valid" for name in names]
        )
        for i, row in enumerate(result["tensor"]):
            writer.writerow([i, value(result["target"][i])] + [value(v) for v in row])
    with (dest / "ambiguous-hand-points.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "frame",
                "detector_side",
                "candidate",
                "point",
                "x_norm",
                "y_norm",
                "handedness_score",
            ]
        )
        for item in result["ambiguous"]:
            for label, key, score in [
                ("previous", "previousXY", "previousScore"),
                ("candidate", "candidateXY", "candidateScore"),
            ]:
                for point, (x, y) in enumerate(item[key]):
                    writer.writerow(
                        [
                            item["frame"],
                            item["side"],
                            label,
                            point,
                            value(x),
                            value(y),
                            value(item[score]),
                        ]
                    )
    rendered = []
    for i in range(len(result["frames"])):
        image = draw_frame(result, i)
        ok, encoded = cv2.imencode(".png", image)
        if not ok:
            raise OSError("Cannot encode preview frame")
        (dest / "frames" / f"frame_{i:05}.png").write_bytes(encoded.tobytes())
        rendered.append(image)
    # Include an actual both-hand frame in the quick overview when available.
    indices = list(np.linspace(0, len(rendered) - 1, min(6, len(rendered)), dtype=int))
    both = (
        result["report"]["bothHandsAndShouldersFrames"]
        or result["report"]["bothHandsFrames"]
    )
    if both and not set(indices).intersection(both):
        indices[len(indices) // 2] = both[len(both) // 2]
        indices.sort()
    thumbs = []
    for i in indices:
        src = rendered[i]
        h, w = src.shape[:2]
        scale = min(400 / w, 320 / h)
        resized = cv2.resize(src, (round(w * scale), round(h * scale)))
        canvas = np.full((320, 400, 3), 25, np.uint8)
        hh, ww = resized.shape[:2]
        canvas[:hh, :ww] = resized
        thumbs.append(canvas)
    while len(thumbs) < 6:
        thumbs.append(np.full((320, 400, 3), 25, np.uint8))
    cv2.imencode(".png", np.vstack([np.hstack(thumbs[:3]), np.hstack(thumbs[3:])]))[
        1
    ].tofile(str(dest / "landmark-preview.png"))
    (dest / "READ-ME.txt").write_text(
        "Mở frames-summary.csv để xem từng frame. landmarks.csv chứa tọa độ tất cả điểm. Thư mục frames chứa mọi frame có vẽ xương và nhãn.\nVALID: đạt điều kiện; LOW_CONFIDENCE_OR_OUTSIDE: model có ước lượng nhưng không dùng cho tensor; NOT_DETECTED: không có điểm.\nL/R là nhãn của model, cần kiểm tra ảnh lật. Không có điểm không có nghĩa người đó không có tay/vai.\nSchema v0.2: 32 x 234 = 78 XY + 78 cờ hợp lệ, không tương thích tensor v0.1.\n",
        "utf-8",
    )
    return dest


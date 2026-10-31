import hashlib
import json
from pathlib import Path

import numpy as np

from .errors import PipelineError


def load_schema(path=None):
    default = Path(__file__).resolve().parents[3] / "configs/feature_schema.json"
    if not default.exists():
        default = Path(__file__).resolve().parents[1] / "configs/feature_schema.json"
    schema = json.loads(Path(path or default).read_text("utf-8-sig"))
    if len(schema["landmarkOrder"]) != 78 or len(set(schema["landmarkOrder"])) != 78:
        raise PipelineError(
            "FEATURE_SCHEMA_MISMATCH", "Expected ordered 78-point schema"
        )
    if schema["targetFrameCount"] < 1 or schema["velocityEnabled"]:
        raise PipelineError(
            "FEATURE_SCHEMA_MISMATCH", "Unsupported sequence configuration"
        )
    if schema.get("detectorExecution", "serial") not in ("serial", "parallel-by-group"):
        raise PipelineError(
            "FEATURE_SCHEMA_MISMATCH", "Unsupported detector execution policy"
        )
    policy = schema.get("preExtractionSampling")
    if policy is not None and (
        policy.get("method") != "uniform-pts-nearest"
        or type(policy.get("maxFrames")) is not int
        or policy["maxFrames"] < 2
    ):
        raise PipelineError(
            "FEATURE_SCHEMA_MISMATCH", "Unsupported extraction sampling policy"
        )
    return schema


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


def schema_digest(schema):
    semantic = {key: value for key, value in schema.items() if key != "status"}
    return hashlib.sha256(json.dumps(semantic, sort_keys=True).encode()).hexdigest()

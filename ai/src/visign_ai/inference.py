"""One production clip-to-tensor path shared by offline tools and the API adapter."""

import json
import time
from pathlib import Path

import numpy as np
import torch

from visign_ai.landmarks.pipeline import PipelineError, process_video
from visign_ai.landmarks.sequence_transform import load_schema, schema_digest
from visign_ai.training.gru_classifier import GRUClassifier


class GRUPredictor:
    def __init__(self, artifact, model_dir=None, device="cpu"):
        self.artifact = Path(artifact)
        self.metadata = json.loads(
            (self.artifact / "model_info.json").read_text("utf-8")
        )
        self.schema_path = self.artifact / "feature_schema.json"
        schema = load_schema(self.schema_path)
        for key in ("featureSchemaVersion", "extractorVersion"):
            if schema[key] != self.metadata[key]:
                raise ValueError(f"Artifact {key} mismatch")
        self.device = torch.device(device)
        checkpoint = torch.load(
            self.artifact / "model.pt", map_location=self.device, weights_only=True
        )
        expected_digest = checkpoint.get("schemaSha256")
        # Older draft checkpoints carried versions only. Accept their exact original schema.
        if expected_digest is None:
            expected_digest = (
                "367300e603b282a667c66083c1306e31a2c2a3625660bd337c0c1bd97d3327f6"
            )
        if schema_digest(schema) != expected_digest:
            raise ValueError("Checkpoint schema content mismatch")
        if checkpoint["modelConfig"]["num_classes"] != len(
            self.metadata["classLabels"]
        ):
            raise ValueError("Classifier output does not match label order")
        if checkpoint["modelConfig"]["input_size"] != len(schema["landmarkOrder"]) * 3:
            raise ValueError("Classifier input does not match schema")
        self.model = GRUClassifier(**checkpoint["modelConfig"]).to(self.device)
        self.model.load_state_dict(checkpoint["stateDict"], strict=True)
        self.model.eval()
        self.model_dir = model_dir

    def clip_to_tensor(self, clip, min_duration_ms=None, max_duration_ms=None):
        return process_video(
            clip,
            expected_schema_version=self.metadata["featureSchemaVersion"],
            schema_path=self.schema_path,
            model_dir=self.model_dir,
            min_duration_ms=min_duration_ms,
            max_duration_ms=max_duration_ms,
        )

    def predict(self, clip, min_duration_ms=300, max_duration_ms=6000):
        result = self.clip_to_tensor(
            clip, min_duration_ms=min_duration_ms, max_duration_ms=max_duration_ms
        )
        report = result["report"]
        if report["ptsSpanMs"] < min_duration_ms:
            raise PipelineError(
                "CLIP_TOO_SHORT", "Clip duration below configured minimum"
            )
        if report["ptsSpanMs"] > max_duration_ms:
            raise PipelineError(
                "CLIP_TOO_LONG", "Clip duration exceeds configured maximum"
            )
        if not result["point_valid"][:, 42:44].all(axis=1).any():
            raise PipelineError("NO_PERSON_DETECTED", "No reliable shoulder anchors")
        if report["inputStatus"] != "HAS_USABLE_FRAMES":
            raise PipelineError(
                "INSUFFICIENT_LANDMARKS", "No usable pose and hand frames"
            )
        start = time.perf_counter()
        features = torch.from_numpy(result["tensor"]).unsqueeze(0).to(self.device)
        with torch.inference_mode():
            probabilities = self.model(
                features, torch.tensor([features.shape[1]])
            ).softmax(-1)[0]
            confidence, index = probabilities.max(dim=0)
            confidence, index = float(confidence), int(index)
        label = self.metadata["classLabels"][index]
        timings = report["timingsMs"]
        return {
            "classLabel": label,
            "confidence": confidence,
            "text": self.metadata["displayTextMap"][self.metadata["meaningMap"][label]],
            "timingsMs": {
                "decode": round(timings["decode"]),
                "extract": round(
                    timings["extractIncludingInit"] + timings["transform"]
                ),
                "infer": round((time.perf_counter() - start) * 1000),
            },
            "qualityHints": {
                "handsDetectedRatio": float(
                    np.logical_or(result["masks"][:, 0], result["masks"][:, 1]).mean()
                ),
                "frameCount": report["frameCount"],
            },
        }

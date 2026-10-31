from types import SimpleNamespace

import numpy as np
import pytest
from visign_ai.landmarks.holistic_extractor import extract
from visign_ai.landmarks.sequence_transform import load_schema


@pytest.mark.parametrize("fail_hand", [False, True])
def test_parallel_detectors_have_fresh_ordered_state_and_always_close(
    tmp_path, monkeypatch, fail_hand
):
    schema = load_schema()
    schema["detectorExecution"] = "parallel-by-group"
    for filename in schema["modelFiles"].values():
        (tmp_path / filename).write_bytes(b"synthetic-detector-asset-for-test")
    instances = []

    class Detector:
        def __init__(self, kind):
            self.kind = kind
            self.stamps = []
            self.closed = False
            instances.append(self)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.closed = True

        def detect_for_video(self, image, stamp):
            assert not self.closed
            assert not self.stamps or stamp > self.stamps[-1]
            self.stamps.append(stamp)
            if fail_hand and self.kind == "hand" and stamp == 100:
                raise ValueError("synthetic detector failure")
            return SimpleNamespace(
                hand_landmarks=[], handedness=[], pose_landmarks=[], face_landmarks=[]
            )

    import visign_ai.landmarks.holistic_extractor as module

    monkeypatch.setattr(module.mp, "Image", lambda **kwargs: kwargs["data"])
    for kind, cls in [
        ("hand", module.vision.HandLandmarker),
        ("pose", module.vision.PoseLandmarker),
        ("face", module.vision.FaceLandmarker),
    ]:
        monkeypatch.setattr(
            cls, "create_from_options", lambda options, name=kind: Detector(name)
        )
    frames = [np.zeros((4, 4, 3), dtype=np.uint8) for _ in range(3)]
    for _ in range(2):
        if fail_hand:
            with pytest.raises(ValueError, match="synthetic detector failure"):
                extract(frames, [0, 100, 200], schema, tmp_path)
        else:
            coords, valid, *_ = extract(frames, [0, 100, 200], schema, tmp_path)
            assert coords.shape == (3, 78, 2) and not valid.any()
    assert len(instances) == 6
    assert all(instance.closed for instance in instances)
    assert all(instance.stamps[0] == 0 for instance in instances)
    assert all(
        instance.stamps == [0, 100, 200]
        for instance in instances
        if instance.kind != "hand" or not fail_hand
    )

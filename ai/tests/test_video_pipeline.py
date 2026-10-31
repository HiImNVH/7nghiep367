import numpy as np
import pytest
from visign_ai.landmarks.pipeline import (
    PipelineError,
    decode_video,
    load_schema,
    process_video,
    transform,
)


def fixture():
    schema = load_schema()
    p = np.zeros((3, 78, 2), dtype=float)
    p[:] = [0.5, 0.5]
    p[:, 42] = [0.25, 0.5]
    p[:, 43] = [0.75, 0.5]
    p[:, 0] = [0.75, 0.5]
    return schema, p, np.ones((3, 78), bool), np.array([0, 500, 1000])


def test_golden_coordinates():
    schema, p, m, t = fixture()
    x, mask, _ = transform(p, m, t, 640, 480, schema)
    assert x.shape == (32, 234)
    np.testing.assert_allclose(x[:, 0], 0.5)
    np.testing.assert_allclose(x[:, 1], 0)
    np.testing.assert_allclose(x[:, 84], -0.5)
    np.testing.assert_allclose(x[:, 86], 0.5)
    assert mask.all()


def test_translation_scale_invariance():
    s, p, m, t = fixture()
    a, _, _ = transform(p, m, t, 640, 480, s)
    b, _, _ = transform(p * 0.7 + 0.1, m, t, 640, 480, s)
    np.testing.assert_allclose(a, b, atol=1e-6)


def test_missing_shoulders_invalidates_all_groups():
    s, p, m, t = fixture()
    m[:, 42:44] = False
    x, mask, _ = transform(p, m, t, 640, 480, s)
    assert np.isfinite(x).all() and not x.any() and not mask.any()


def test_missing_hand_not_interpolated_through_gap():
    s, p, m, t = fixture()
    m[1, :21] = False
    x, mask, _ = transform(p, m, t, 640, 480, s)
    assert not mask[1:-1, :21].any()
    assert not x[1:-1, :42].any()
    assert mask[:, 21:].all()


def test_wrong_schema_rejected_before_file_access():
    with pytest.raises(PipelineError, match="Schema") as e:
        process_video("not-used.webm", expected_schema_version="wrong")
    assert e.value.code == "FEATURE_SCHEMA_MISMATCH"


@pytest.mark.parametrize(
    "content,code",
    [
        (b"not video", "UNSUPPORTED_MEDIA_TYPE"),
        (b"\x1aE\xdf\xa3broken", "CLIP_DECODE_FAILED"),
    ],
)
def test_invalid_clips(tmp_path, content, code):
    path = tmp_path / "bad.webm"
    path.write_bytes(content)
    with pytest.raises(PipelineError) as e:
        decode_video(path)
    assert e.value.code == code


def test_zero_shoulder_width():
    s, p, m, t = fixture()
    p[:, 43] = p[:, 42]
    x, mask, _ = transform(p, m, t, 640, 480, s)
    assert np.isfinite(x).all() and not mask.any()


def test_missing_elbow_and_wrist_do_not_hide_shoulders_or_hands():
    s, p, m, t = fixture()
    m[:, 44:48] = False
    x, mask, _ = transform(p, m, t, 640, 480, s)
    assert mask[:, :44].all()
    assert not mask[:, 44:48].any()
    assert mask[:, 48:].all()
    np.testing.assert_allclose(x[:, 0], 0.5)
    np.testing.assert_allclose(x[:, 84], -0.5)
    assert not x[:, 88:96].any()


def test_one_missing_shoulder_keeps_raw_but_invalidates_tensor():
    s, p, m, t = fixture()
    raw = p.copy()
    m[:, 42] = False
    x, mask, _ = transform(p, m, t, 640, 480, s)
    assert not mask.any() and not x.any()
    np.testing.assert_array_equal(p, raw)


def test_group_masks_need_only_shoulders_for_pose_flag():
    from visign_ai.landmarks.pipeline import group_masks

    v = np.ones((2, 78), bool)
    v[:, 44:48] = False
    v[0, :21] = False
    g = group_masks(v)
    assert g[:, 2].all() and not g[0, 0] and g[1, 0]

from pathlib import Path

import av
import cv2
import numpy as np

from .errors import PipelineError


def decode_video(path, max_frames=900, max_seconds=30):
    """MP4 allowed for local references; WebM is the browser integration target."""
    path = Path(path)
    if not path.is_file():
        raise PipelineError("INVALID_REQUEST", "Video không tồn tại.")
    if path.stat().st_size > 100 * 1024 * 1024:
        raise PipelineError("CLIP_TOO_LARGE", "Pipeline giới hạn 100 MB.")
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
                        "CLIP_TOO_LONG", "Pipeline giới hạn 30 giây / 900 frame."
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


class VideoDecoder:
    def decode(self, path):
        return decode_video(path)

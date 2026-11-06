"""Run Demo 2 with the repository's legacy schema and detector assets."""

import json
import sys
from pathlib import Path

from demo2_pipeline import PipelineError, process_video, save_result

if __name__ == "__main__":
    try:
        save_result(process_video(Path(sys.argv[1])), Path(sys.argv[2]))
    except PipelineError as exc:
        print(json.dumps({"detail": f"{exc.code}: {exc}"}, ensure_ascii=True))
        sys.exit(2)


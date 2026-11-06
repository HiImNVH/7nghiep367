"""Application configuration settings (T022)."""

import json
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = _SERVICE_ROOT.parents[1]


class Settings(BaseSettings):
    """Runtime configuration for ViSign Inference API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ViSign Inference API"
    environment: str = Field(default="development", alias="ENV")
    debug: bool = Field(default=False)

    # Artifact configuration.
    # Default is resolved from the package location so it works from any cwd;
    # a relative MODEL_ARTIFACT_PATH from the environment is resolved against cwd.
    model_artifact_path: str = Field(
        default=str(_SERVICE_ROOT / "tests" / "fixtures" / "model-artifacts" / "fixture"),
        alias="MODEL_ARTIFACT_PATH",
    )
    # Every loaded artifact must carry this featureSchemaVersion (T037 fail-closed check).
    # Source of truth is the shared schema file from visign_ai (T016); FEATURE_SCHEMA_VERSION
    # overrides it only when the file is not deployed next to the API.
    feature_schema_path: str = Field(
        default=str(REPO_ROOT / "ai" / "configs" / "feature_schema.json"),
        alias="FEATURE_SCHEMA_PATH",
    )
    feature_schema_version: str = Field(default="", alias="FEATURE_SCHEMA_VERSION")

    # Input clip constraints
    allowed_mime_types: List[str] = [
        "video/webm",
        "video/webm;codecs=vp8",
        "video/webm;codecs=vp9",
        "video/webm;codecs=vp8,opus",
        "video/webm;codecs=vp9,opus",
    ]
    max_clip_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    min_duration_ms: int = 300  # 0.3s
    max_duration_ms: int = 6000  # 6.0s

    # Inference execution limits
    inference_timeout_seconds: float = 3.0
    busy_retry_after_seconds: int = 3

    # CORS configuration: Vite dev/preview origins by default; override with
    # CORS_ORIGINS='["http://host:port"]'. No cookies/auth in MVP, so no credentials.
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]
    cors_allow_credentials: bool = False
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # Temporary directory for clip upload
    temp_dir: str = Field(default="", alias="TEMP_DIR")

    def serving_feature_schema_version(self) -> str:
        """Explicit FEATURE_SCHEMA_VERSION, else featureSchemaVersion from the shared schema file."""
        if self.feature_schema_version:
            return self.feature_schema_version
        path = Path(self.feature_schema_path)
        try:
            version = json.loads(path.read_text(encoding="utf-8-sig"))["featureSchemaVersion"]
        except (OSError, ValueError, KeyError, TypeError) as e:
            raise ValueError(f"cannot read featureSchemaVersion from {path}: {e}") from e
        if not isinstance(version, str) or not version:
            raise ValueError(f"featureSchemaVersion in {path} must be a non-empty string")
        return version


settings = Settings()

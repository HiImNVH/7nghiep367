"""Application configuration settings (T022)."""

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_SERVICE_ROOT = Path(__file__).resolve().parents[2]


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
    # Must equal featureSchemaVersion of every loaded artifact (T037 fail-closed check).
    # Replace with ai/configs/feature_schema.json once T016 ships the shared schema file.
    feature_schema_version: str = Field(default="vsl-feature-v1.0", alias="FEATURE_SCHEMA_VERSION")

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


settings = Settings()

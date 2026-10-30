"""Domain models and gate evaluation for ModelVersion (T019)."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ArtifactKind(str, Enum):
    FIXTURE = "fixture"
    PILOT = "pilot"
    FULL = "full"


class ModelMetadata(BaseModel):
    """Metadata describing a loaded model artifact."""

    modelVersion: str = Field(..., description="Unique immutable model version identifier")
    artifactKind: ArtifactKind = Field(..., description="Artifact kind: fixture, pilot, or full")
    datasetVersion: str = Field(..., description="Dataset manifest version or hash")
    featureSchemaVersion: str = Field(..., description="Feature schema version used by extractor/model")
    extractorVersion: str = Field(..., description="Extractor bundle and version identifier")
    meanings: List[str] = Field(..., min_length=1, max_length=10, description="List of supported meanings")
    classLabels: List[str] = Field(default_factory=list, description="Ordered distinct class labels")
    meaningMap: Dict[str, str] = Field(default_factory=dict, description="Mapping from classLabel to meaningId")
    acceptanceThreshold: float = Field(0.70, ge=0.0, le=1.0, description="Threshold for accepting prediction")
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall accuracy, nullable for fixture")
    macroF1: Optional[float] = Field(None, ge=0.0, le=1.0, description="Macro-F1, nullable for fixture")
    perMeaningPrecision: Optional[Dict[str, float]] = Field(None, description="Per-meaning precision")
    perMeaningRecall: Optional[Dict[str, float]] = Field(None, description="Per-meaning recall")
    evaluatedAt: Optional[datetime] = Field(None, description="Timestamp of evaluation, nullable for fixture")
    demoReady: bool = Field(False, description="True only for full models passing all quality gates")

    @model_validator(mode="after")
    def compute_and_validate_demo_ready(self) -> "ModelMetadata":
        """
        Validate demoReady status according to release gates:
        - fixture & pilot: MUST always be demoReady = False
        - full: MUST have exactly 10 meanings, macroF1 >= 0.80, and every perMeaningRecall >= 0.65 to be demoReady = True.
        """
        if self.artifactKind in (ArtifactKind.FIXTURE, ArtifactKind.PILOT):
            # Fixture and pilot can never be demoReady
            self.demoReady = False
            return self

        # ArtifactKind is FULL
        passes_gate = True

        if len(self.meanings) != 10:
            passes_gate = False

        if self.macroF1 is None or self.macroF1 < 0.80:
            passes_gate = False

        if not self.perMeaningRecall:
            passes_gate = False
        else:
            for meaning in self.meanings:
                recall = self.perMeaningRecall.get(meaning)
                if recall is None or recall < 0.65:
                    passes_gate = False
                    break

        self.demoReady = passes_gate
        return self


class ModelInfoResponse(BaseModel):
    """Response schema matching contracts/openapi.yaml #/components/schemas/ModelInfo."""

    modelVersion: str
    artifactKind: Literal["fixture", "pilot", "full"]
    datasetVersion: str
    featureSchemaVersion: str
    extractorVersion: str
    meanings: List[str] = Field(..., min_length=1, max_length=10)
    acceptanceThreshold: float = Field(..., ge=0.0, le=1.0)
    macroF1: Optional[float] = Field(None, ge=0.0, le=1.0)
    perMeaningRecall: Optional[Dict[str, float]] = None
    evaluatedAt: Optional[str] = None
    demoReady: bool

    @classmethod
    def from_metadata(cls, meta: ModelMetadata) -> "ModelInfoResponse":
        return cls(
            modelVersion=meta.modelVersion,
            artifactKind=meta.artifactKind.value,
            datasetVersion=meta.datasetVersion,
            featureSchemaVersion=meta.featureSchemaVersion,
            extractorVersion=meta.extractorVersion,
            meanings=meta.meanings,
            acceptanceThreshold=meta.acceptanceThreshold,
            macroF1=meta.macroF1,
            perMeaningRecall=meta.perMeaningRecall,
            evaluatedAt=meta.evaluatedAt.isoformat() if meta.evaluatedAt else None,
            demoReady=meta.demoReady,
        )

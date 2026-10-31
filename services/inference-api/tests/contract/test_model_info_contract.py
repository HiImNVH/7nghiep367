"""Contract tests for GET /api/v1/health and GET /api/v1/model-info (T055)."""

import uuid
from fastapi.testclient import TestClient
from visign_api.domain.model_version import ArtifactKind, ModelMetadata
from visign_api.inference.predictor import predictor_registry


def test_get_health_degraded_when_model_not_loaded(client: TestClient, monkeypatch):
    """Health stays HTTP 200 but reports degraded/modelReady=false when no artifact is loaded."""
    monkeypatch.setattr(predictor_registry, "_active_predictor", None)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "degraded", "modelReady": False, "modelVersion": None}


def test_get_model_info_not_ready_503(client: TestClient, monkeypatch):
    """Model-info returns 503 MODEL_NOT_READY with Retry-After when no artifact is loaded."""
    monkeypatch.setattr(predictor_registry, "_active_predictor", None)
    custom_id = str(uuid.uuid4())

    response = client.get("/api/v1/model-info", headers={"X-Request-ID": custom_id})

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert response.headers["X-Request-ID"] == custom_id
    data = response.json()
    assert data["code"] == "MODEL_NOT_READY"
    assert data["requestId"] == custom_id


def test_get_health_contract(client: TestClient):
    """Test health endpoint contract and request-id echoing."""
    custom_id = str(uuid.uuid4())
    response = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id

    data = response.json()
    assert data["status"] == "ok"
    assert data["modelReady"] is True
    assert data["modelVersion"] == "vsl-fixture-v0.1.0"


def test_get_model_info_fixture_contract(client: TestClient):
    """Test model-info endpoint contract under fixture mode."""
    custom_id = str(uuid.uuid4())
    response = client.get("/api/v1/model-info", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id

    data = response.json()
    assert data["modelVersion"] == "vsl-fixture-v0.1.0"
    assert data["artifactKind"] == "fixture"
    assert data["datasetVersion"] == "fixture-manifest-v1"
    assert data["featureSchemaVersion"] == "vsl-feature-v1.0"
    assert data["extractorVersion"] == "mediapipe-holistic-0.10.14"
    assert isinstance(data["meanings"], list)
    assert len(data["meanings"]) > 0
    assert data["acceptanceThreshold"] == 0.70
    assert data["macroF1"] is None
    assert data["perMeaningRecall"] is None
    # Fixture MUST always have demoReady = False
    assert data["demoReady"] is False


def test_model_metadata_demo_ready_gate_evaluation():
    """Verify gate rule: full && 10 meanings && macroF1 >= 0.80 && all perMeaningRecall >= 0.65."""
    ten_meanings = [
        "GIAY_TO", "DAU_BUNG", "THUOC", "SOT", "NHAN",
        "BAN", "XIN_CHAO", "CAM_ON", "CHO", "SAO_CHEP"
    ]
    good_recall = {m: 0.75 for m in ten_meanings}

    # 1. Full model passing all gates -> demoReady = True
    full_meta_pass = ModelMetadata(
        modelVersion="vsl-full-v1.0.0",
        artifactKind=ArtifactKind.FULL,
        datasetVersion="p0-manifest-hash",
        featureSchemaVersion="vsl-feature-v1.0",
        extractorVersion="mediapipe-holistic-0.10.14",
        meanings=ten_meanings,
        classLabels=ten_meanings,
        acceptanceThreshold=0.70,
        macroF1=0.84,
        perMeaningRecall=good_recall,
    )
    assert full_meta_pass.demoReady is True

    # 2. Pilot model with high metrics -> still demoReady = False
    pilot_meta = ModelMetadata(
        modelVersion="vsl-pilot-v0.2.0",
        artifactKind=ArtifactKind.PILOT,
        datasetVersion="pilot-manifest",
        featureSchemaVersion="vsl-feature-v1.0",
        extractorVersion="mediapipe-holistic-0.10.14",
        meanings=["XIN_CHAO", "CAM_ON", "THUOC"],
        classLabels=["XIN_CHAO", "CAM_ON", "THUOC"],
        acceptanceThreshold=0.70,
        macroF1=0.92,
        perMeaningRecall={"XIN_CHAO": 0.9, "CAM_ON": 0.9, "THUOC": 0.9},
    )
    assert pilot_meta.demoReady is False

    # 3. Full model with macroF1 < 0.80 -> demoReady = False
    full_low_f1 = ModelMetadata(
        modelVersion="vsl-full-low-f1",
        artifactKind=ArtifactKind.FULL,
        datasetVersion="p0-manifest",
        featureSchemaVersion="vsl-feature-v1.0",
        extractorVersion="mediapipe-holistic-0.10.14",
        meanings=ten_meanings,
        classLabels=ten_meanings,
        acceptanceThreshold=0.70,
        macroF1=0.78,
        perMeaningRecall=good_recall,
    )
    assert full_low_f1.demoReady is False

    # 4. Full model with one perMeaningRecall < 0.65 -> demoReady = False
    bad_recall = good_recall.copy()
    bad_recall["THUOC"] = 0.60
    full_low_recall = ModelMetadata(
        modelVersion="vsl-full-low-recall",
        artifactKind=ArtifactKind.FULL,
        datasetVersion="p0-manifest",
        featureSchemaVersion="vsl-feature-v1.0",
        extractorVersion="mediapipe-holistic-0.10.14",
        meanings=ten_meanings,
        classLabels=ten_meanings,
        acceptanceThreshold=0.70,
        macroF1=0.82,
        perMeaningRecall=bad_recall,
    )
    assert full_low_recall.demoReady is False

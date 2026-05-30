from __future__ import annotations

from fastapi.testclient import TestClient

from rdp.api import create_app
from rdp.storage import ResearchRunStore


def test_api_health_and_filtered_runs(tmp_path):
    store = ResearchRunStore(tmp_path)
    store.initialize(force=True)
    client = TestClient(create_app(store))

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json() == {"ok": True, "run_count": 8, "storage": "duckdb+parquet"}

    response = client.get("/api/runs", params={"status": "failed"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["run_id"] == "run_2026_05_30_004"


def test_api_run_detail_and_lineage(tmp_path):
    store = ResearchRunStore(tmp_path)
    store.initialize(force=True)
    client = TestClient(create_app(store))

    detail = client.get("/api/runs/run_2026_05_29_010")
    assert detail.status_code == 200
    body = detail.json()
    assert body["dataset"]["content_sha"] == "sha256:f19b-pubmed-v6"
    assert body["events"][0]["stage"] == "query"

    lineage = client.get("/api/runs/run_2026_05_29_010/lineage")
    assert lineage.status_code == 200
    assert lineage.json()["lineage"][0]["relation"] in {"parent_of", "used_by"}


def test_api_compare_and_not_found(tmp_path):
    store = ResearchRunStore(tmp_path)
    store.initialize(force=True)
    client = TestClient(create_app(store))

    comparison = client.get(
        "/api/compare",
        params={
            "base_run_id": "run_2026_05_30_001",
            "candidate_run_id": "run_2026_05_30_002",
        },
    )
    assert comparison.status_code == 200
    assert comparison.json()["verdict"] == "candidate_improved"

    missing = client.get("/api/runs/not_a_run")
    assert missing.status_code == 404

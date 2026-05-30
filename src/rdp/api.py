from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from rdp.models import MetricSummary, ResearchRun, RunComparison, RunDetail, RunFilter
from rdp.storage import ResearchRunStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
STATIC_DIR = PROJECT_ROOT / "static"


def default_store() -> ResearchRunStore:
    data_dir = Path(os.environ.get("RDP_DATA_DIR", DEFAULT_DATA_DIR))
    store = ResearchRunStore(data_dir)
    store.initialize()
    return store


def create_app(store: ResearchRunStore | None = None) -> FastAPI:
    app = FastAPI(
        title="Research Run Platform",
        version="0.1.0",
        description="Queryable research-run data, dataset provenance, metrics, and lightweight exploration APIs.",
    )
    app.state.store = store or default_store()
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    def get_store() -> ResearchRunStore:
        return app.state.store

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health")
    def health(store: ResearchRunStore = Depends(get_store)) -> dict[str, object]:
        return {
            "ok": True,
            "run_count": len(store.list_runs()),
            "storage": "duckdb+parquet",
        }

    @app.get("/api/runs", response_model=list[ResearchRun])
    def list_runs(
        model: str | None = None,
        dataset_id: str | None = None,
        status: str | None = None,
        min_accuracy: float | None = Query(default=None, ge=0, le=1),
        owner: str | None = None,
        store: ResearchRunStore = Depends(get_store),
    ) -> list[ResearchRun]:
        return store.list_runs(
            RunFilter(
                model=model,
                dataset_id=dataset_id,
                status=status,
                min_accuracy=min_accuracy,
                owner=owner,
            )
        )

    @app.get("/api/runs/{run_id}", response_model=RunDetail)
    def run_detail(run_id: str, store: ResearchRunStore = Depends(get_store)) -> RunDetail:
        try:
            return store.get_run_detail(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}") from exc

    @app.get("/api/runs/{run_id}/lineage")
    def run_lineage(run_id: str, store: ResearchRunStore = Depends(get_store)) -> dict[str, object]:
        try:
            detail = store.get_run_detail(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}") from exc
        return {
            "run_id": run_id,
            "dataset": detail.dataset,
            "lineage": detail.lineage,
        }

    @app.get("/api/metrics/summary", response_model=MetricSummary)
    def metrics_summary(store: ResearchRunStore = Depends(get_store)) -> MetricSummary:
        return store.metric_summary()

    @app.get("/api/compare", response_model=RunComparison)
    def compare_runs(
        base_run_id: str,
        candidate_run_id: str,
        store: ResearchRunStore = Depends(get_store),
    ) -> RunComparison:
        try:
            return store.compare_runs(base_run_id, candidate_run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="One or both runs were not found") from exc

    return app


app = create_app()


def run() -> None:
    uvicorn.run("rdp.api:app", host="127.0.0.1", port=8010, reload=True)

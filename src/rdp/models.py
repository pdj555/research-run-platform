from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RunFilter(BaseModel):
    model: str | None = None
    dataset_id: str | None = None
    status: str | None = None
    min_accuracy: float | None = Field(default=None, ge=0, le=1)
    owner: str | None = None


class ResearchRun(BaseModel):
    run_id: str
    model: str
    task: str
    dataset_id: str
    dataset_version: str
    status: str
    started_at: str
    duration_sec: int
    tokens: int
    eval_accuracy: float
    eval_helpfulness: float
    eval_harmlessness: float
    cost_usd: float
    owner: str
    notes: str


class DatasetVersion(BaseModel):
    dataset_id: str
    version: str
    source: str
    row_count: int
    created_at: str
    content_sha: str
    parent_dataset_id: str | None
    transform: str
    risk_level: str


class RunEvent(BaseModel):
    event_id: str
    run_id: str
    ts: str
    stage: str
    message: str
    metric_name: str | None
    metric_value: float | None


class LineageEdge(BaseModel):
    upstream: str
    downstream: str
    relation: str
    evidence: str


class RunDetail(BaseModel):
    run: ResearchRun
    dataset: DatasetVersion
    events: list[RunEvent]
    lineage: list[LineageEdge]


class MetricSummary(BaseModel):
    total_runs: int
    successful_runs: int
    avg_accuracy: float
    avg_helpfulness: float
    avg_harmlessness: float
    total_cost_usd: float
    by_model: list[dict[str, Any]]


class RunComparison(BaseModel):
    base_run_id: str
    candidate_run_id: str
    deltas: dict[str, float]
    verdict: str

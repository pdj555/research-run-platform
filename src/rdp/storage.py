from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from rdp.models import (
    DatasetVersion,
    LineageEdge,
    MetricSummary,
    ResearchRun,
    RunComparison,
    RunDetail,
    RunEvent,
    RunFilter,
)


RUN_ROWS = [
    (
        "run_2026_05_30_001",
        "claude-research-sim-v1",
        "summarize_training_trace",
        "frontier_eval_trace",
        "v3",
        "succeeded",
        "2026-05-30T08:10:00Z",
        842,
        1_240_000,
        0.912,
        0.884,
        0.973,
        184.22,
        "alignment-tools",
        "Baseline trace summarization over filtered RL events.",
    ),
    (
        "run_2026_05_30_002",
        "claude-research-sim-v1",
        "summarize_training_trace",
        "frontier_eval_trace",
        "v4",
        "succeeded",
        "2026-05-30T10:45:00Z",
        796,
        1_180_000,
        0.931,
        0.902,
        0.975,
        171.66,
        "alignment-tools",
        "Added deduped refusal-edge cases and provenance tags.",
    ),
    (
        "run_2026_05_30_003",
        "claude-research-sim-v2",
        "dataset_slice_regression",
        "harmlessness_challenges",
        "v2",
        "succeeded",
        "2026-05-30T12:20:00Z",
        522,
        820_000,
        0.887,
        0.846,
        0.991,
        122.41,
        "safety-evals",
        "Regression pass on harmful-compliance challenge slices.",
    ),
    (
        "run_2026_05_30_004",
        "claude-research-sim-v2",
        "dataset_slice_regression",
        "harmlessness_challenges",
        "v3",
        "failed",
        "2026-05-30T13:05:00Z",
        308,
        420_000,
        0.742,
        0.801,
        0.956,
        74.08,
        "safety-evals",
        "Stopped after drift detector flagged label-distribution mismatch.",
    ),
    (
        "run_2026_05_29_009",
        "retrieval-metrics-worker",
        "paper_context_retrieval",
        "pubmed_context_eval",
        "v5",
        "succeeded",
        "2026-05-29T22:14:00Z",
        454,
        610_000,
        0.901,
        0.872,
        0.968,
        91.77,
        "research-data",
        "Query engine benchmark for biomedical paper retrieval slices.",
    ),
    (
        "run_2026_05_29_010",
        "retrieval-metrics-worker",
        "paper_context_retrieval",
        "pubmed_context_eval",
        "v6",
        "succeeded",
        "2026-05-29T23:02:00Z",
        431,
        588_000,
        0.919,
        0.889,
        0.971,
        88.32,
        "research-data",
        "Added citation-window lineage and faster slice materialization.",
    ),
    (
        "run_2026_05_28_021",
        "run-metrics-indexer",
        "time_series_compaction",
        "rl_metrics_stream",
        "v1",
        "succeeded",
        "2026-05-28T17:30:00Z",
        192,
        210_000,
        0.864,
        0.811,
        0.964,
        38.45,
        "research-data",
        "Compacted high-volume run metrics into minute buckets.",
    ),
    (
        "run_2026_05_28_022",
        "run-metrics-indexer",
        "time_series_compaction",
        "rl_metrics_stream",
        "v2",
        "succeeded",
        "2026-05-28T18:18:00Z",
        188,
        205_000,
        0.879,
        0.824,
        0.969,
        36.91,
        "research-data",
        "Added late-arriving event handling and partition pruning.",
    ),
]


DATASET_ROWS = [
    (
        "frontier_eval_trace",
        "v3",
        "synthetic RL run event stream",
        120_000,
        "2026-05-28T09:00:00Z",
        "sha256:7f0c-frontier-v3",
        None,
        "filter invalid events; join policy tags",
        "medium",
    ),
    (
        "frontier_eval_trace",
        "v4",
        "synthetic RL run event stream",
        132_000,
        "2026-05-30T09:30:00Z",
        "sha256:9b1d-frontier-v4",
        "frontier_eval_trace:v3",
        "dedupe traces; attach provenance tags",
        "medium",
    ),
    (
        "harmlessness_challenges",
        "v2",
        "synthetic safety eval slices",
        42_000,
        "2026-05-27T14:10:00Z",
        "sha256:a12c-harmless-v2",
        None,
        "normalize labels; stratify by challenge family",
        "high",
    ),
    (
        "harmlessness_challenges",
        "v3",
        "synthetic safety eval slices",
        52_000,
        "2026-05-30T12:45:00Z",
        "sha256:e41e-harmless-v3",
        "harmlessness_challenges:v2",
        "append adversarial slice; rebalance labels",
        "high",
    ),
    (
        "pubmed_context_eval",
        "v5",
        "synthetic research paper retrieval benchmark",
        88_000,
        "2026-05-29T20:00:00Z",
        "sha256:d81a-pubmed-v5",
        None,
        "extract citation windows; chunk abstracts",
        "low",
    ),
    (
        "pubmed_context_eval",
        "v6",
        "synthetic research paper retrieval benchmark",
        91_500,
        "2026-05-29T22:30:00Z",
        "sha256:f19b-pubmed-v6",
        "pubmed_context_eval:v5",
        "materialize citation-window lineage",
        "low",
    ),
    (
        "rl_metrics_stream",
        "v1",
        "synthetic high-volume training metrics",
        9_600_000,
        "2026-05-28T16:00:00Z",
        "sha256:3aa1-rlstream-v1",
        None,
        "partition by run and minute",
        "medium",
    ),
    (
        "rl_metrics_stream",
        "v2",
        "synthetic high-volume training metrics",
        9_920_000,
        "2026-05-28T18:00:00Z",
        "sha256:4be2-rlstream-v2",
        "rl_metrics_stream:v1",
        "compact late events; add partition pruning",
        "medium",
    ),
]


EVENT_ROWS = [
    ("evt_001", "run_2026_05_30_001", "2026-05-30T08:12:00Z", "extract", "Read 120k raw trace events.", "rows_read", 120000.0),
    ("evt_002", "run_2026_05_30_001", "2026-05-30T08:18:00Z", "load", "Materialized run slices to Parquet.", "slice_count", 48.0),
    ("evt_003", "run_2026_05_30_002", "2026-05-30T10:50:00Z", "extract", "Read 132k raw trace events.", "rows_read", 132000.0),
    ("evt_004", "run_2026_05_30_002", "2026-05-30T10:58:00Z", "eval", "Accuracy improved on refusal-edge slices.", "accuracy", 0.931),
    ("evt_005", "run_2026_05_30_003", "2026-05-30T12:31:00Z", "eval", "Challenge set passed harmlessness gate.", "harmlessness", 0.991),
    ("evt_006", "run_2026_05_30_004", "2026-05-30T13:11:00Z", "gate", "Label distribution drift exceeded threshold.", "label_drift", 0.184),
    ("evt_007", "run_2026_05_29_009", "2026-05-29T22:22:00Z", "query", "Benchmarked retrieval query latency.", "p95_ms", 284.0),
    ("evt_008", "run_2026_05_29_010", "2026-05-29T23:11:00Z", "query", "Partition pruning reduced p95 latency.", "p95_ms", 219.0),
    ("evt_009", "run_2026_05_28_021", "2026-05-28T17:33:00Z", "compact", "Compacted metrics into minute buckets.", "buckets", 1440.0),
    ("evt_010", "run_2026_05_28_022", "2026-05-28T18:22:00Z", "compact", "Late event reconciliation completed.", "late_events", 912.0),
]


LINEAGE_ROWS = [
    ("frontier_eval_trace:v3", "run_2026_05_30_001", "used_by", "dataset version recorded at run start"),
    ("frontier_eval_trace:v3", "frontier_eval_trace:v4", "parent_of", "dedupe and provenance transform"),
    ("frontier_eval_trace:v4", "run_2026_05_30_002", "used_by", "dataset version recorded at run start"),
    ("harmlessness_challenges:v2", "run_2026_05_30_003", "used_by", "dataset version recorded at run start"),
    ("harmlessness_challenges:v2", "harmlessness_challenges:v3", "parent_of", "adversarial slice append"),
    ("harmlessness_challenges:v3", "run_2026_05_30_004", "used_by", "run failed on drift gate"),
    ("pubmed_context_eval:v5", "run_2026_05_29_009", "used_by", "retrieval benchmark source"),
    ("pubmed_context_eval:v5", "pubmed_context_eval:v6", "parent_of", "citation-window lineage materialized"),
    ("pubmed_context_eval:v6", "run_2026_05_29_010", "used_by", "retrieval benchmark source"),
    ("rl_metrics_stream:v1", "run_2026_05_28_021", "used_by", "metrics compaction benchmark"),
    ("rl_metrics_stream:v1", "rl_metrics_stream:v2", "parent_of", "late event handling transform"),
    ("rl_metrics_stream:v2", "run_2026_05_28_022", "used_by", "metrics compaction benchmark"),
]


class ResearchRunStore:
    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / "research_runs.duckdb"

    def initialize(self, force: bool = False) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if force:
            for path in self.data_dir.glob("*.parquet"):
                path.unlink()
            if self.db_path.exists():
                self.db_path.unlink()

        if not (self.data_dir / "runs.parquet").exists():
            self._write_seed_parquet()

        with self._connect() as con:
            self._create_views(con)

    def list_runs(self, filters: RunFilter | None = None) -> list[ResearchRun]:
        filters = filters or RunFilter()
        clauses: list[str] = []
        params: list[Any] = []

        if filters.model:
            clauses.append("model = ?")
            params.append(filters.model)
        if filters.dataset_id:
            clauses.append("dataset_id = ?")
            params.append(filters.dataset_id)
        if filters.status:
            clauses.append("status = ?")
            params.append(filters.status)
        if filters.min_accuracy is not None:
            clauses.append("eval_accuracy >= ?")
            params.append(filters.min_accuracy)
        if filters.owner:
            clauses.append("owner = ?")
            params.append(filters.owner)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"""
            SELECT *
            FROM runs
            {where}
            ORDER BY started_at DESC, run_id DESC
        """
        with self._connect() as con:
            return [ResearchRun(**row) for row in self._fetch_dicts(con, query, params)]

    def get_run_detail(self, run_id: str) -> RunDetail:
        with self._connect() as con:
            run_rows = self._fetch_dicts(con, "SELECT * FROM runs WHERE run_id = ?", [run_id])
            if not run_rows:
                raise KeyError(run_id)
            run = ResearchRun(**run_rows[0])

            dataset_rows = self._fetch_dicts(
                con,
                """
                SELECT *
                FROM datasets
                WHERE dataset_id = ? AND version = ?
                """,
                [run.dataset_id, run.dataset_version],
            )
            events = [
                RunEvent(**row)
                for row in self._fetch_dicts(
                    con,
                    "SELECT * FROM events WHERE run_id = ? ORDER BY ts ASC",
                    [run_id],
                )
            ]
            lineage = self._lineage_for_run(con, run_id, run.dataset_id, run.dataset_version)
            return RunDetail(
                run=run,
                dataset=DatasetVersion(**dataset_rows[0]),
                events=events,
                lineage=lineage,
            )

    def metric_summary(self) -> MetricSummary:
        with self._connect() as con:
            summary = self._fetch_dicts(
                con,
                """
                SELECT
                    count(*)::INTEGER AS total_runs,
                    sum(CASE WHEN status = 'succeeded' THEN 1 ELSE 0 END)::INTEGER AS successful_runs,
                    round(avg(eval_accuracy), 4) AS avg_accuracy,
                    round(avg(eval_helpfulness), 4) AS avg_helpfulness,
                    round(avg(eval_harmlessness), 4) AS avg_harmlessness,
                    round(sum(cost_usd), 2) AS total_cost_usd
                FROM runs
                """,
            )[0]
            by_model = self._fetch_dicts(
                con,
                """
                SELECT
                    model,
                    count(*)::INTEGER AS runs,
                    round(avg(eval_accuracy), 4) AS avg_accuracy,
                    round(sum(cost_usd), 2) AS cost_usd
                FROM runs
                GROUP BY model
                ORDER BY avg_accuracy DESC
                """,
            )
            return MetricSummary(by_model=by_model, **summary)

    def compare_runs(self, base_run_id: str, candidate_run_id: str) -> RunComparison:
        with self._connect() as con:
            rows = self._fetch_dicts(
                con,
                """
                SELECT
                    base.run_id AS base_run_id,
                    candidate.run_id AS candidate_run_id,
                    candidate.eval_accuracy - base.eval_accuracy AS accuracy,
                    candidate.eval_helpfulness - base.eval_helpfulness AS helpfulness,
                    candidate.eval_harmlessness - base.eval_harmlessness AS harmlessness,
                    candidate.cost_usd - base.cost_usd AS cost_usd,
                    candidate.duration_sec - base.duration_sec AS duration_sec
                FROM runs base
                CROSS JOIN runs candidate
                WHERE base.run_id = ? AND candidate.run_id = ?
                """,
                [base_run_id, candidate_run_id],
            )
        if not rows:
            raise KeyError(f"{base_run_id} or {candidate_run_id}")

        row = rows[0]
        deltas = {
            "accuracy": round(row["accuracy"], 4),
            "helpfulness": round(row["helpfulness"], 4),
            "harmlessness": round(row["harmlessness"], 4),
            "cost_usd": round(row["cost_usd"], 2),
            "duration_sec": int(row["duration_sec"]),
        }
        verdict = "candidate_improved" if deltas["accuracy"] > 0 and deltas["helpfulness"] > 0 else "needs_review"
        return RunComparison(
            base_run_id=base_run_id,
            candidate_run_id=candidate_run_id,
            deltas=deltas,
            verdict=verdict,
        )

    def _write_seed_parquet(self) -> None:
        with self._connect() as con:
            con.execute("DROP TABLE IF EXISTS seed_runs")
            con.execute(
                """
                CREATE TABLE seed_runs (
                    run_id VARCHAR,
                    model VARCHAR,
                    task VARCHAR,
                    dataset_id VARCHAR,
                    dataset_version VARCHAR,
                    status VARCHAR,
                    started_at VARCHAR,
                    duration_sec INTEGER,
                    tokens INTEGER,
                    eval_accuracy DOUBLE,
                    eval_helpfulness DOUBLE,
                    eval_harmlessness DOUBLE,
                    cost_usd DOUBLE,
                    owner VARCHAR,
                    notes VARCHAR
                )
                """
            )
            con.executemany("INSERT INTO seed_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", RUN_ROWS)

            con.execute("DROP TABLE IF EXISTS seed_datasets")
            con.execute(
                """
                CREATE TABLE seed_datasets (
                    dataset_id VARCHAR,
                    version VARCHAR,
                    source VARCHAR,
                    row_count INTEGER,
                    created_at VARCHAR,
                    content_sha VARCHAR,
                    parent_dataset_id VARCHAR,
                    transform VARCHAR,
                    risk_level VARCHAR
                )
                """
            )
            con.executemany("INSERT INTO seed_datasets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", DATASET_ROWS)

            con.execute("DROP TABLE IF EXISTS seed_events")
            con.execute(
                """
                CREATE TABLE seed_events (
                    event_id VARCHAR,
                    run_id VARCHAR,
                    ts VARCHAR,
                    stage VARCHAR,
                    message VARCHAR,
                    metric_name VARCHAR,
                    metric_value DOUBLE
                )
                """
            )
            con.executemany("INSERT INTO seed_events VALUES (?, ?, ?, ?, ?, ?, ?)", EVENT_ROWS)

            con.execute("DROP TABLE IF EXISTS seed_lineage")
            con.execute(
                """
                CREATE TABLE seed_lineage (
                    upstream VARCHAR,
                    downstream VARCHAR,
                    relation VARCHAR,
                    evidence VARCHAR
                )
                """
            )
            con.executemany("INSERT INTO seed_lineage VALUES (?, ?, ?, ?)", LINEAGE_ROWS)

            for table in ("runs", "datasets", "events", "lineage"):
                target = self.data_dir / f"{table}.parquet"
                con.execute(
                    f"COPY seed_{table} TO '{self._sql_path(target)}' (FORMAT PARQUET)"
                )

    def _lineage_for_run(
        self,
        con: duckdb.DuckDBPyConnection,
        run_id: str,
        dataset_id: str,
        dataset_version: str,
    ) -> list[LineageEdge]:
        dataset_key = f"{dataset_id}:{dataset_version}"
        rows = self._fetch_dicts(
            con,
            """
            SELECT *
            FROM lineage
            WHERE downstream = ?
               OR upstream = ?
               OR downstream = ?
            ORDER BY relation, upstream, downstream
            """,
            [run_id, dataset_key, dataset_key],
        )
        return [LineageEdge(**row) for row in rows]

    def _connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path))

    def _create_views(self, con: duckdb.DuckDBPyConnection) -> None:
        for table in ("runs", "datasets", "events", "lineage"):
            parquet_path = self.data_dir / f"{table}.parquet"
            con.execute(
                f"CREATE OR REPLACE VIEW {table} AS SELECT * FROM read_parquet('{self._sql_path(parquet_path)}')"
            )

    @staticmethod
    def _fetch_dicts(
        con: duckdb.DuckDBPyConnection,
        query: str,
        params: list[Any] | None = None,
    ) -> list[dict[str, Any]]:
        result = con.execute(query, params or [])
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]

    @staticmethod
    def _sql_path(path: Path) -> str:
        return str(path).replace("'", "''")

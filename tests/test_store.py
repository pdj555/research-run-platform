from __future__ import annotations

from rdp.models import RunFilter
from rdp.storage import ResearchRunStore


def test_store_seeds_and_filters_runs(tmp_path):
    store = ResearchRunStore(tmp_path)
    store.initialize(force=True)

    all_runs = store.list_runs()
    assert len(all_runs) == 8
    assert all_runs[0].started_at >= all_runs[-1].started_at

    high_accuracy = store.list_runs(RunFilter(status="succeeded", min_accuracy=0.90))
    assert {run.run_id for run in high_accuracy} == {
        "run_2026_05_30_001",
        "run_2026_05_30_002",
        "run_2026_05_29_009",
        "run_2026_05_29_010",
    }

    research_data_runs = store.list_runs(RunFilter(owner="research-data"))
    assert len(research_data_runs) == 4


def test_run_detail_includes_dataset_events_and_lineage(tmp_path):
    store = ResearchRunStore(tmp_path)
    store.initialize(force=True)

    detail = store.get_run_detail("run_2026_05_30_002")

    assert detail.run.dataset_id == "frontier_eval_trace"
    assert detail.dataset.version == "v4"
    assert detail.dataset.parent_dataset_id == "frontier_eval_trace:v3"
    assert len(detail.events) == 2
    assert any(edge.upstream == "frontier_eval_trace:v4" for edge in detail.lineage)


def test_compare_runs_returns_metric_deltas(tmp_path):
    store = ResearchRunStore(tmp_path)
    store.initialize(force=True)

    comparison = store.compare_runs("run_2026_05_30_001", "run_2026_05_30_002")

    assert comparison.verdict == "candidate_improved"
    assert comparison.deltas["accuracy"] == 0.019
    assert comparison.deltas["helpfulness"] == 0.018
    assert comparison.deltas["cost_usd"] == -12.56


def test_metric_summary_groups_by_model(tmp_path):
    store = ResearchRunStore(tmp_path)
    store.initialize(force=True)

    summary = store.metric_summary()

    assert summary.total_runs == 8
    assert summary.successful_runs == 7
    assert summary.total_cost_usd > 800
    assert {row["model"] for row in summary.by_model} == {
        "claude-research-sim-v1",
        "claude-research-sim-v2",
        "retrieval-metrics-worker",
        "run-metrics-indexer",
    }

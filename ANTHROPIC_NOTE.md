# Anthropic Research Data Platform Note

This repo is a focused proof asset for the Software Engineer, Research Data Platform role.

It demonstrates the kind of platform layer described in the role:

- Experiment/run data extracted into queryable storage.
- Dataset versions with parentage, transforms, content hashes, and risk metadata.
- Lineage edges connecting datasets and runs.
- FastAPI endpoints for run search, detail inspection, lineage, summary metrics, and run comparison.
- A compact browser explorer for researchers to inspect runs without needing SQL.
- Tests that cover storage, filtering, API behavior, lineage, and comparison logic.

The data is synthetic, but the system shape is real: Parquet files, DuckDB query views, typed API contracts, and a UI designed around the questions researchers ask when they need to understand experiment results.

The point is not to mimic Anthropic internals. The point is to show that I understand the job's product surface: make research data easier to trust, query, inspect, and act on.

## Short Outreach Add-on

I also put together a small proof repo shaped around this role: a research-run platform using Parquet/DuckDB, FastAPI, dataset provenance, run comparison, and a lightweight explorer. The data is synthetic, but it shows the system shape I would expect in researcher-facing tooling: queryable run data, lineage, metrics, and APIs that help technical users inspect experiments quickly.

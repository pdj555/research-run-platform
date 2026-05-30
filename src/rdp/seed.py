from __future__ import annotations

import argparse
from pathlib import Path

from rdp.storage import ResearchRunStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed deterministic research-run Parquet data.")
    parser.add_argument("--data-dir", default="data", help="Directory for DuckDB and Parquet files.")
    parser.add_argument("--force", action="store_true", help="Rewrite existing seed data.")
    args = parser.parse_args()

    store = ResearchRunStore(Path(args.data_dir))
    store.initialize(force=args.force)
    print(f"Seeded research-run platform data in {Path(args.data_dir).resolve()}")

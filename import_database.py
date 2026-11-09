"""Create/import the GeoHazard SQLite database (stage 2)."""

import argparse
import json
import sys
from pathlib import Path

from geohazard_pipeline.baseline_import import build_baseline_rows
from geohazard_pipeline.db import (
    DEFAULT_DB_PATH,
    import_baseline,
    import_run_dir,
    initialize_database,
)
from geohazard_pipeline.util import ROOT


def _latest_run_dirs(root):
    root = Path(root)
    if not root.exists():
        return []
    candidates = []
    for path in root.iterdir():
        if path.is_dir() and (path / "tables").is_dir():
            manifest = path / "manifest.json"
            if manifest.is_file():
                candidates.append(path)
    return sorted(candidates, key=lambda path: path.name, reverse=True)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Create SQLite schema and import baseline plus pipeline runs."
    )
    parser.add_argument(
        "--database",
        default=str(DEFAULT_DB_PATH),
        help=f"SQLite database path (default {DEFAULT_DB_PATH}).",
    )
    parser.add_argument(
        "--run-dir",
        action="append",
        default=None,
        help="Pipeline run directory to import; repeatable. Default: latest run.",
    )
    parser.add_argument(
        "--pipeline-root",
        default=str(ROOT / "data" / "pipeline"),
        help="Root used to find the latest run when --run-dir is omitted.",
    )
    parser.add_argument(
        "--baseline",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Import the preserved 787-row baseline as legacy rows (default yes).",
    )
    parser.add_argument(
        "--baseline-only",
        action="store_true",
        help="Import only the baseline, do not import a pipeline run.",
    )
    parser.add_argument(
        "--no-initialize",
        action="store_true",
        help="Do not execute database/schema.sql before importing.",
    )
    args = parser.parse_args(argv)

    database = Path(args.database)
    initialize = not args.no_initialize
    if initialize:
        initialize_database(database)

    result = {"database": str(database), "baseline": None, "runs": []}
    if args.baseline:
        tables = build_baseline_rows()
        result["baseline"] = import_baseline(
            database, tables, initialize=False
        )

    if not args.baseline_only:
        run_dirs = args.run_dir
        if not run_dirs:
            run_dirs = [str(path) for path in _latest_run_dirs(args.pipeline_root)]
        if not run_dirs:
            result["message"] = (
                "Tidak ada run pipeline ditemukan; hanya baseline yang diimpor."
            )
        for run_dir in run_dirs:
            result["runs"].append(
                import_run_dir(database, run_dir, initialize=False)
            )

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

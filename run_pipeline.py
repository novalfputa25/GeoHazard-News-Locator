"""Run the unified GeoHazard pipeline (stage 1)."""

import argparse
import json
import sys

from geohazard_pipeline.db import DEFAULT_DB_PATH, import_run_dir
from geohazard_pipeline.runner import run_pipeline
from geohazard_pipeline.util import ROOT


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fetch, parse, normalize, and export GeoHazard provenance tables."
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Replay raw payloads instead of live HTTP fetch.",
    )
    parser.add_argument(
        "--raw-dir",
        default=None,
        help="Directory containing <source_id>.(xml|atom|json) for offline replay.",
    )
    parser.add_argument(
        "--output-root",
        default=str(ROOT / "data" / "pipeline"),
        help="Root directory for run output (default: data/pipeline).",
    )
    parser.add_argument("--run-id", default=None, help="Explicit run id.")
    parser.add_argument(
        "--sources",
        nargs="*",
        default=None,
        help="Subset of active source ids; default all active feeds.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help=(
            "Fallback maximum selected items per source (default: all items). "
            "Per-feed max_items or --source-max-items takes precedence."
        ),
    )
    parser.add_argument(
        "--source-max-items",
        action="append",
        default=[],
        metavar="SOURCE=LIMIT",
        help=(
            "Per-source selected-item limit, e.g. mongabay_indonesia=50. "
            "May be repeated."
        ),
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between live source/page requests in seconds (default 1.0).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds (default 30).",
    )
    parser.add_argument(
        "--database",
        default=None,
        help=f"Optional SQLite path to import this run (default {DEFAULT_DB_PATH}).",
    )
    args = parser.parse_args(argv)

    if args.offline and not args.raw_dir:
        parser.error("--offline membutuhkan --raw-dir")

    max_items_by_source = {}
    for value in args.source_max_items:
        if "=" not in value:
            parser.error(f"--source-max-items harus SOURCE=LIMIT: {value}")
        source_id, limit = value.split("=", 1)
        source_id = source_id.strip()
        try:
            max_items_by_source[source_id] = int(limit)
        except ValueError:
            parser.error(f"LIMIT bukan angka: {value}")

    manifest = run_pipeline(
        output_root=args.output_root,
        raw_dir=args.raw_dir,
        sources=args.sources,
        max_items=args.max_items,
        run_id=args.run_id,
        fetch_timeout=args.timeout,
        fetch_delay=args.delay,
        max_items_by_source=max_items_by_source or None,
    )
    result = {"run": manifest}
    if args.database:
        result["database"] = import_run_dir(
            args.database, manifest["run_dir"], initialize=True
        )
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

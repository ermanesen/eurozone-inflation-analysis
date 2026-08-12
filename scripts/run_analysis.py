"""Run the complete Eurozone inflation analysis."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurozone_inflation.pipeline import run_pipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Download a fresh, configuration-pinned snapshot from Eurostat.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    try:
        output = run_pipeline(ROOT, refresh=args.refresh)
    except Exception:
        logging.getLogger(__name__).exception("Analysis pipeline failed.")
        return 1

    quality = output["quality"]
    logging.getLogger(__name__).info(
        "Analysis complete: %d panel rows, %d model rows, %d countries.",
        quality["complete_rows"],
        quality["model_rows"],
        quality["countries"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate all LaTeX table row fragments."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis import economic_tables, functional_tables, perception_tables, process_tables

Generator = tuple[str, Callable[[list[str] | None], int]]

GENERATORS: tuple[Generator, ...] = (
    ("economic", economic_tables.main),
    ("process", process_tables.main),
    ("functional", functional_tables.main),
    ("perception", perception_tables.main),
)


def main(argv: list[str] | None = None) -> int:
    """Run every table generator.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code, zero when every generator succeeds.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)

    generator_args = ["--config", str(args.config), "--output-dir", str(args.output_dir)]
    for name, run in GENERATORS:
        exit_code = run(generator_args)
        if exit_code != 0:
            print(
                f"error: {name} table generator failed with exit code {exit_code}",
                file=sys.stderr,
            )
            return exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

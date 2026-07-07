#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate LaTeX row fragments for functional result tables."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.cohort import (
    ParticipantPair,
    SessionArtefacts,
    load_sessions,
    model_band,
    pair_by_participant,
)
from analysis.config import ConfigError, load_records
from analysis.latex import level_row, paired_row, write_fragment
from analysis.stats import level_summary, paired_summary


def main(argv: list[str] | None = None) -> int:
    """Run the functional table generator.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code (0 on success, 1 on a config or data error).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        pairs = pair_by_participant(load_sessions(load_records(args.config)))
        _write_outputs(pairs, args.output_dir)
    except (ConfigError, KeyError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


def _write_outputs(pairs: list[ParticipantPair], output_dir: Path) -> None:
    """Write all functional row fragments to ``output_dir``.

    Args:
        pairs: Cohort participant pairs.
        output_dir: Destination directory for the row-fragment files.
    """
    write_fragment(output_dir / "func-score-levels.tex", _score_levels(pairs))
    write_fragment(output_dir / "func-score-paired.tex", _score_paired(pairs))
    write_fragment(output_dir / "func-score-paired-by-model.tex", _score_paired_by_model(pairs))
    write_fragment(output_dir / "func-score-paired-by-section.tex", _score_paired_by_section(pairs))


def _score_levels(pairs: list[ParticipantPair]) -> list[str]:
    """Return cohort and model-split score level rows.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per scope and framework.
    """
    rows: list[str] = []
    for label, subset in [
        ("Cohort", pairs),
        ("Opus", [pair for pair in pairs if model_band(pair.apm) == "opus"]),
        ("Sonnet", [pair for pair in pairs if model_band(pair.apm) == "sonnet"]),
    ]:
        for framework in ("apm", "speckit"):
            values = [_score(getattr(pair, framework), "total") for pair in subset]
            rows.append(
                level_row(
                    [label, "APM" if framework == "apm" else "Spec-kit"], level_summary(values), 1
                )
            )
    return rows


def _score_paired(pairs: list[ParticipantPair]) -> list[str]:
    """Return pooled paired total-score row.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        A single-row list with the pooled paired summary.
    """
    return [
        paired_row(
            [],
            paired_summary(
                [_score(pair.apm, "total") for pair in pairs],
                [_score(pair.speckit, "total") for pair in pairs],
            ),
            1,
            include_zero=True,
        )
    ]


def _score_paired_by_model(pairs: list[ParticipantPair]) -> list[str]:
    """Return model-split paired total-score rows.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per model.
    """
    rows: list[str] = []
    for model in ("opus", "sonnet"):
        subset = [pair for pair in pairs if model_band(pair.apm) == model]
        rows.append(
            paired_row(
                [model.title()],
                paired_summary(
                    [_score(pair.apm, "total") for pair in subset],
                    [_score(pair.speckit, "total") for pair in subset],
                ),
                1,
                include_zero=True,
            )
        )
    return rows


def _score_paired_by_section(pairs: list[ParticipantPair]) -> list[str]:
    """Return paired score rows for the Python and C rubric sections.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per rubric section.
    """
    rows: list[str] = []
    for key, label in (("python", "Python extension"), ("c", "C replica")):
        rows.append(
            paired_row(
                [label],
                paired_summary(
                    [_score(pair.apm, key) for pair in pairs],
                    [_score(pair.speckit, key) for pair in pairs],
                ),
                1,
                include_zero=True,
            )
        )
    return rows


def _score(session: SessionArtefacts, key: str) -> float:
    """Return a grader score value.

    Args:
        session: One session's loaded artefacts.
        key: ``"total"`` for the overall score, or a rubric section key.

    Returns:
        The requested score value.
    """
    scores = session.grader_results["scores"]
    if key == "total":
        return float(scores["total"])
    return float(scores[key]["total"])


if __name__ == "__main__":
    raise SystemExit(main())

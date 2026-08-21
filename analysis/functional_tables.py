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
    order_label,
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
    write_fragment(output_dir / "func-score-paired-by-section.tex", _score_paired_by_section(pairs))
    write_fragment(output_dir / "func-score-sessions.tex", _score_sessions(pairs))
    write_fragment(output_dir / "func-score-paired-by-order.tex", _score_paired_by_order(pairs))
    write_fragment(output_dir / "disc-learning-by-participant.tex", _learning_by_participant(pairs))
    write_fragment(output_dir / "disc-compact-regrade.tex", _compact_regrade_sessions(pairs))
    write_fragment(output_dir / "disc-compact-regrade-paired.tex", _compact_regrade_paired(pairs))


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
        if rows:
            rows.append(r"\midrule")
        for framework in ("apm", "speckit"):
            values = [_score(getattr(pair, framework), "total") for pair in subset]
            group_cell = label if framework == "apm" else ""
            rows.append(
                level_row(
                    [group_cell, "APM" if framework == "apm" else "Spec-kit"],
                    level_summary(values),
                    1,
                )
            )
    return rows


def _score_paired(pairs: list[ParticipantPair]) -> list[str]:
    """Return cohort and model-group paired total-score rows.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per participant group.
    """
    rows: list[str] = []
    for label, subset in [
        ("Cohort", pairs),
        ("Opus", [pair for pair in pairs if model_band(pair.apm) == "opus"]),
        ("Sonnet", [pair for pair in pairs if model_band(pair.apm) == "sonnet"]),
    ]:
        if rows:
            rows.append(r"\midrule")
        rows.append(
            paired_row(
                [label],
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
    """Return paired score rows by participant group and rubric section.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per participant group and rubric section.
    """
    rows: list[str] = []
    for group_label, subset in [
        ("Cohort", pairs),
        ("Opus", [pair for pair in pairs if model_band(pair.apm) == "opus"]),
        ("Sonnet", [pair for pair in pairs if model_band(pair.apm) == "sonnet"]),
    ]:
        if rows:
            rows.append(r"\midrule")
        for index, (key, section_label) in enumerate(
            (("python", "Python extension"), ("c", "C replica"))
        ):
            rows.append(
                paired_row(
                    [group_label if index == 0 else "", section_label],
                    paired_summary(
                        [_score(pair.apm, key) for pair in subset],
                        [_score(pair.speckit, key) for pair in subset],
                    ),
                    1,
                    include_zero=True,
                )
            )
    return rows


def _score_sessions(pairs: list[ParticipantPair]) -> list[str]:
    """Return per-session functional score rows."""
    rows: list[str] = []
    for pair in pairs:
        for framework in ("apm", "speckit"):
            session = getattr(pair, framework)
            scores = session.grader_results["scores"]
            rows.append(
                " & ".join(
                    [
                        pair.pid if framework == "apm" else "",
                        "APM" if framework == "apm" else "Spec-kit",
                        _points(float(scores["total_strict"])),
                        _points(float(scores["total_partial"])),
                        _points(float(scores["total"])),
                        _points(float(scores["python"]["total"])),
                        _points(float(scores["c"]["total"])),
                    ]
                )
                + r" \\"
            )
    return rows


def _score_paired_by_order(pairs: list[ParticipantPair]) -> list[str]:
    """Return total-score paired rows by realized order."""
    rows: list[str] = []
    for order in ("APM first", "APM second"):
        subset = [pair for pair in pairs if order_label(pair) == order]
        rows.append(
            paired_row(
                [order],
                paired_summary(
                    [_score(pair.apm, "total") for pair in subset],
                    [_score(pair.speckit, "total") for pair in subset],
                ),
                1,
                include_zero=True,
            )
        )
    return rows


def _learning_by_participant(pairs: list[ParticipantPair]) -> list[str]:
    """Return first-to-second total-score change rows for Learning Effects.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One row per participant in participant-id order.
    """
    rows: list[str] = []
    for pair in sorted(pairs, key=lambda item: item.pid):
        first, second = _ordered_sessions(pair)
        change = _score(second, "total") - _score(first, "total")
        change_text = _points(change) if change == 0.0 else _signed_points(change)
        rows.append(
            f"{pair.pid} & {model_band(pair.apm).title()} & "
            f"{_framework_label(second)} & {change_text} \\\\"
        )
    return rows


def _compact_regrade_sessions(pairs: list[ParticipantPair]) -> list[str]:
    """Return compact-input diagnostic rows for sessions whose scores changed.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per Sonnet session with a changed diagnostic score.

    Raises:
        ValueError: If a Sonnet session omits compact-input grading results.
    """
    rows: list[str] = []
    for pair in pairs:
        for session in (pair.apm, pair.speckit):
            if model_band(session) != "sonnet":
                continue
            standard_score = _score(session, "total")
            diagnostic_score = _compact_score(session)
            if abs(diagnostic_score - standard_score) <= 0.01:
                continue
            rows.append(
                " & ".join(
                    [
                        f"{pair.pid} {session.record.session} ({_framework_label(session)})",
                        _points(standard_score),
                        _points(diagnostic_score),
                    ]
                )
                + r" \\"
            )
    return rows


def _compact_regrade_paired(pairs: list[ParticipantPair]) -> list[str]:
    """Return the paired compact-input diagnostic row within the Sonnet group.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        The Sonnet paired diagnostic-score summary.
    """
    sonnet_pairs = [pair for pair in pairs if model_band(pair.apm) == "sonnet"]
    return [
        paired_row(
            ["Sonnet"],
            paired_summary(
                [_compact_score(pair.apm) for pair in sonnet_pairs],
                [_compact_score(pair.speckit) for pair in sonnet_pairs],
            ),
            1,
        )
    ]


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


def _compact_score(session: SessionArtefacts) -> float:
    """Return one session's compact-input diagnostic score.

    Args:
        session: One Sonnet session with compact-input grading results.

    Returns:
        The compact-input total score.

    Raises:
        ValueError: If the session omits compact-input grading results.
    """
    compact = session.compact_grader_results
    if compact is None:
        raise ValueError(
            f"{session.record.pid} {session.record.session} {session.record.framework}: "
            "missing compact_grader_results in config"
        )
    return float(compact["scores"]["total"])


def _ordered_sessions(pair: ParticipantPair) -> tuple[SessionArtefacts, SessionArtefacts]:
    """Return sessions in realized first, second order."""
    return (pair.apm, pair.speckit) if pair.apm.record.session == "S1" else (pair.speckit, pair.apm)


def _framework_label(session: SessionArtefacts) -> str:
    """Return display label for one session's framework."""
    return "APM" if session.record.framework == "apm" else "Spec-kit"


def _points(value: float) -> str:
    """Format a score value."""
    return f"${value:.1f}$"


def _signed_points(value: float) -> str:
    """Format a signed score value."""
    return f"${value:+.1f}$"


if __name__ == "__main__":
    raise SystemExit(main())

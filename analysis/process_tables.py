#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate LaTeX row fragments for process result tables."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.cohort import (
    ParticipantPair,
    SessionArtefacts,
    load_sessions,
    pair_by_participant,
    phase_scope,
    role_scopes,
    session_scope,
)
from analysis.config import ConfigError, load_records
from analysis.latex import level_row, paired_row, write_fragment
from analysis.stats import level_summary, paired_summary

PHASES = {"planning": "Planning", "implementation": "Implementation"}
TIME_MEASURES = {
    "duration": "Duration",
    "turn_time": "Turn time",
    "inter_turn_time": "Inter-turn idle",
}


def main(argv: list[str] | None = None) -> int:
    """Run the process table generator.

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
    """Write all process row fragments to ``output_dir``.

    Args:
        pairs: Cohort participant pairs.
        output_dir: Destination directory for the row-fragment files.
    """
    write_fragment(output_dir / "proc-duration-levels.tex", _duration_levels(pairs))
    write_fragment(output_dir / "proc-time-paired.tex", _time_paired(pairs))
    write_fragment(output_dir / "proc-phase-paired.tex", _phase_time_paired(pairs))
    write_fragment(output_dir / "proc-turns-levels.tex", _turn_levels(pairs))
    write_fragment(output_dir / "proc-turns-paired.tex", _turn_paired(pairs))
    write_fragment(output_dir / "proc-turns-levels-by-role.tex", _turn_levels_by_role(pairs))


def _duration_levels(pairs: list[ParticipantPair]) -> list[str]:
    """Return rows for per-framework session and phase duration levels.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per scope and framework.
    """
    rows: list[str] = []
    rows.extend(
        _level_rows_for_scope(
            pairs, "Session", lambda session: session_scope(session, "metrics")["duration"]
        )
    )
    for phase_key, phase_label in PHASES.items():
        rows.extend(
            _level_rows_for_scope(
                pairs,
                phase_label,
                lambda session, phase=phase_key: phase_scope(session, "metrics", phase)["duration"],
            )
        )
    return rows


def _turn_levels(pairs: list[ParticipantPair]) -> list[str]:
    """Return rows for per-framework turn-prompt count levels.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per scope and framework.
    """
    rows: list[str] = []
    rows.extend(
        _level_rows_for_scope(
            pairs, "Session", lambda session: session_scope(session, "data")["turn_prompt_count"]
        )
    )
    for phase_key, phase_label in PHASES.items():
        rows.extend(
            _level_rows_for_scope(
                pairs,
                phase_label,
                lambda session, phase=phase_key: phase_scope(session, "data", phase)[
                    "turn_prompt_count"
                ],
            )
        )
    return rows


def _level_rows_for_scope(
    pairs: list[ParticipantPair],
    scope_label: str,
    value_fn: Callable[[SessionArtefacts], float],
) -> list[str]:
    """Return APM and Spec-kit level rows for one scope.

    Args:
        pairs: Cohort participant pairs.
        scope_label: Row label for the scope (e.g. ``"Session"``).
        value_fn: Extracts the measured value from one session's artefacts.

    Returns:
        One LaTeX row per framework.
    """
    rows: list[str] = []
    for framework in ("apm", "speckit"):
        values = [float(value_fn(getattr(pair, framework))) for pair in pairs]
        rows.append(
            level_row(
                [scope_label, "APM" if framework == "apm" else "Spec-kit"], level_summary(values), 1
            )
        )
    return rows


def _time_paired(pairs: list[ParticipantPair]) -> list[str]:
    """Return pooled paired session-time rows.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per time measure.
    """
    rows: list[str] = []
    for key, label in TIME_MEASURES.items():
        apm = [session_scope(pair.apm, "metrics")[key] for pair in pairs]
        speckit = [session_scope(pair.speckit, "metrics")[key] for pair in pairs]
        rows.append(paired_row([label], paired_summary(apm, speckit), 1))
    return rows


def _phase_time_paired(pairs: list[ParticipantPair]) -> list[str]:
    """Return pooled paired phase-time rows.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per phase and time measure.
    """
    rows: list[str] = []
    for phase_key, phase_label in PHASES.items():
        for key, label in TIME_MEASURES.items():
            apm = [phase_scope(pair.apm, "metrics", phase_key)[key] for pair in pairs]
            speckit = [phase_scope(pair.speckit, "metrics", phase_key)[key] for pair in pairs]
            rows.append(paired_row([phase_label, label], paired_summary(apm, speckit), 1))
    return rows


def _turn_paired(pairs: list[ParticipantPair]) -> list[str]:
    """Return pooled paired turn-prompt count rows.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per scope.
    """
    rows: list[str] = []
    apm = [session_scope(pair.apm, "data")["turn_prompt_count"] for pair in pairs]
    speckit = [session_scope(pair.speckit, "data")["turn_prompt_count"] for pair in pairs]
    rows.append(paired_row(["Session"], paired_summary(apm, speckit), 1, include_zero=True))
    for phase_key, phase_label in PHASES.items():
        apm = [phase_scope(pair.apm, "data", phase_key)["turn_prompt_count"] for pair in pairs]
        speckit = [
            phase_scope(pair.speckit, "data", phase_key)["turn_prompt_count"] for pair in pairs
        ]
        rows.append(paired_row([phase_label], paired_summary(apm, speckit), 1, include_zero=True))
    return rows


def _turn_levels_by_role(pairs: list[ParticipantPair]) -> list[str]:
    """Return APM-only per-role turn count rows.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per role.
    """
    rows: list[str] = []
    for prefix, label in (("planner-", "Planner"), ("manager-", "Manager"), ("worker-", "Worker")):
        values: list[float] = []
        for pair in pairs:
            total = 0.0
            for role, block in role_scopes(pair.apm, "data").items():
                if role.startswith(prefix):
                    total += float(block["turn_prompt_count"])
            values.append(total)
        rows.append(level_row([label], level_summary(values), 1))
    return rows


if __name__ == "__main__":
    raise SystemExit(main())

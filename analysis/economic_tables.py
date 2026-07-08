#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate LaTeX row fragments for economic result tables."""

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
    phase_scope,
    role_scopes,
    session_scope,
)
from analysis.config import ConfigError, load_records
from analysis.latex import level_row, paired_row, write_fragment
from analysis.stats import level_summary, paired_summary

PHASES = {"planning": "Planning", "implementation": "Implementation"}
TOKEN_KEYS = {
    "input": "Input",
    "output": "Output",
    "cache_read": "Cache read",
    "cache_5m": "Cache write (5-minute)",
    "cache_1h": "Cache write (1-hour)",
}


def main(argv: list[str] | None = None) -> int:
    """Run the economic table generator.

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
        sessions = load_sessions(load_records(args.config))
        pairs = pair_by_participant(sessions)
        _write_outputs(pairs, args.output_dir)
    except (ConfigError, KeyError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


def _write_outputs(pairs: list[ParticipantPair], output_dir: Path) -> None:
    """Write all economic row fragments to ``output_dir``.

    Args:
        pairs: Cohort participant pairs.
        output_dir: Destination directory for the row-fragment files.
    """
    write_fragment(output_dir / "cost-session-levels-by-model.tex", _cost_session_levels(pairs))
    write_fragment(output_dir / "cost-session-paired.tex", _cost_session_paired(pairs))
    write_fragment(
        output_dir / "cost-session-paired-by-model.tex", _cost_session_paired_by_model(pairs)
    )
    write_fragment(output_dir / "cost-session-levels-by-role.tex", _cost_levels_by_role(pairs))
    write_fragment(output_dir / "cost-phase-paired.tex", _cost_phase_paired(pairs))
    write_fragment(
        output_dir / "cost-phase-paired-by-model.tex", _cost_phase_paired_by_model(pairs)
    )
    write_fragment(
        output_dir / "cost-session-paired-by-order.tex", _cost_session_paired_by_order(pairs)
    )
    write_fragment(
        output_dir / "cost-token-composition-by-model.tex",
        _cost_token_composition_by_model(pairs),
    )
    write_fragment(output_dir / "cost-token-paired.tex", _cost_token_paired(pairs))
    write_fragment(
        output_dir / "cost-token-paired-by-model.tex", _cost_token_paired_by_model(pairs)
    )


def _cost_session_levels(pairs: list[ParticipantPair]) -> list[str]:
    """Return rows for session and phase cost levels by model.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        Rows for session, planning, and implementation levels, grouped by model.
    """
    rows: list[str] = []
    for model in ("opus", "sonnet"):
        if rows:
            rows.append(r"\midrule")
        subset = [pair for pair in pairs if model_band(pair.apm) == model]
        model_label = model.title()
        for scope_key, scope_label in (
            ("session", "Session"),
            ("planning", "Planning"),
            ("implementation", "Implementation"),
        ):
            for framework in ("apm", "speckit"):
                label_model = model_label if scope_key == "session" and framework == "apm" else ""
                label_scope = scope_label if framework == "apm" else ""
                framework_label = "APM" if framework == "apm" else "Spec-kit"
                if model == "opus" and scope_key == "session" and framework == "apm":
                    framework_label += r"\tnote{a}"
                values = [_scope_cost(getattr(pair, framework), scope_key) for pair in subset]
                rows.append(
                    level_row([label_model, label_scope, framework_label], level_summary(values), 2)
                )
    return rows


def _cost_session_paired(pairs: list[ParticipantPair]) -> list[str]:
    """Return rows for pooled session cost paired differences.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        A single-row list with the pooled paired summary.
    """
    apm = [session_scope(pair.apm, "metrics")["cost_usd"] for pair in pairs]
    speckit = [session_scope(pair.speckit, "metrics")["cost_usd"] for pair in pairs]
    return [paired_row([], paired_summary(apm, speckit), 2)]


def _cost_session_paired_by_model(pairs: list[ParticipantPair]) -> list[str]:
    """Return rows for session cost paired differences by model.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per model.
    """
    rows: list[str] = []
    for model in ("opus", "sonnet"):
        subset = [pair for pair in pairs if model_band(pair.apm) == model]
        apm = [session_scope(pair.apm, "metrics")["cost_usd"] for pair in subset]
        speckit = [session_scope(pair.speckit, "metrics")["cost_usd"] for pair in subset]
        rows.append(paired_row([model.title()], paired_summary(apm, speckit), 2))
    return rows


def _cost_phase_paired(pairs: list[ParticipantPair]) -> list[str]:
    """Return rows for pooled phase cost paired differences.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per phase.
    """
    rows: list[str] = []
    for key, label in PHASES.items():
        note = r"\tnote{a}" if key == "planning" else r"\tnote{b,c}"
        apm = [phase_scope(pair.apm, "metrics", key)["cost_usd"] for pair in pairs]
        speckit = [phase_scope(pair.speckit, "metrics", key)["cost_usd"] for pair in pairs]
        rows.append(paired_row([label + note], paired_summary(apm, speckit), 2))
    return rows


def _cost_phase_paired_by_model(pairs: list[ParticipantPair]) -> list[str]:
    """Return phase cost paired differences by model."""
    rows: list[str] = []
    for model in ("opus", "sonnet"):
        if rows:
            rows.append(r"\midrule")
        subset = [pair for pair in pairs if model_band(pair.apm) == model]
        for key, label in PHASES.items():
            model_cell = model.title() if key == "planning" else ""
            note = _phase_model_note(model, key)
            rows.append(
                paired_row(
                    [model_cell, label + note],
                    paired_summary(
                        [phase_scope(pair.apm, "metrics", key)["cost_usd"] for pair in subset],
                        [phase_scope(pair.speckit, "metrics", key)["cost_usd"] for pair in subset],
                    ),
                    2,
                )
            )
    return rows


def _cost_session_paired_by_order(pairs: list[ParticipantPair]) -> list[str]:
    """Return session cost paired differences by realized order."""
    rows: list[str] = []
    for order in ("APM first", "APM second"):
        subset = [pair for pair in pairs if order_label(pair) == order]
        rows.append(
            paired_row(
                [order],
                paired_summary(
                    [session_scope(pair.apm, "metrics")["cost_usd"] for pair in subset],
                    [session_scope(pair.speckit, "metrics")["cost_usd"] for pair in subset],
                ),
                2,
            )
        )
    return rows


def _cost_levels_by_role(pairs: list[ParticipantPair]) -> list[str]:
    """Return APM cost levels by model and agent role."""
    rows: list[str] = []
    for model in ("opus", "sonnet"):
        if rows:
            rows.append(r"\midrule")
        subset = [pair for pair in pairs if model_band(pair.apm) == model]
        for prefix, role in (
            ("planner-", "Planner"),
            ("manager-", "Manager"),
            ("worker-", "Worker"),
        ):
            values = [_role_cost(pair.apm, prefix) for pair in subset]
            note = r"\tnote{a}" if model == "opus" and role in {"Planner", "Manager"} else ""
            label = role + note
            rows.append(level_row([model.title(), label], level_summary(values), 2))
    return rows


def _cost_token_composition_by_model(pairs: list[ParticipantPair]) -> list[str]:
    """Return per-framework token-category cost levels by model."""
    rows: list[str] = []
    categories = (
        ("output", "Output"),
        ("cache_read", "Cache read"),
        ("cache_1h", "Cache write (1-hour)"),
    )
    for model in ("opus", "sonnet"):
        if rows:
            rows.append(r"\midrule")
        subset = [pair for pair in pairs if model_band(pair.apm) == model]
        for framework in ("apm", "speckit"):
            for key, label in categories:
                framework_cell = "APM" if framework == "apm" else "Spec-kit"
                values = [_category_cost(getattr(pair, framework), key) for pair in subset]
                rows.append(
                    level_row(
                        [
                            model.title() if framework == "apm" and key == "output" else "",
                            framework_cell if key == "output" else "",
                            label,
                        ],
                        level_summary(values),
                        2,
                    )
                )
    return rows


def _scope_cost(session: SessionArtefacts, scope_key: str) -> float:
    """Return session or phase cost from parser metrics.

    Args:
        session: The loaded session artefacts.
        scope_key: ``"session"`` or a phase key.

    Returns:
        Cost in US dollars.
    """
    if scope_key == "session":
        return float(session_scope(session, "metrics")["cost_usd"])
    return float(phase_scope(session, "metrics", scope_key)["cost_usd"])


def _role_cost(session: SessionArtefacts, role_prefix: str) -> float:
    """Return total APM cost for all role scopes matching ``role_prefix``."""
    return sum(
        float(block["cost_usd"])
        for role, block in role_scopes(session, "metrics").items()
        if role.startswith(role_prefix)
    )


def _cost_token_paired(pairs: list[ParticipantPair]) -> list[str]:
    """Return rows for pooled token-category cost differences.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per token category.
    """
    rows: list[str] = []
    for key, label in TOKEN_KEYS.items():
        apm = [_category_cost(pair.apm, key) for pair in pairs]
        speckit = [_category_cost(pair.speckit, key) for pair in pairs]
        rows.append(paired_row([label], paired_summary(apm, speckit), 2))
    return rows


def _cost_token_paired_by_model(pairs: list[ParticipantPair]) -> list[str]:
    """Return token-category cost paired differences by model."""
    rows: list[str] = []
    for model in ("opus", "sonnet"):
        if rows:
            rows.append(r"\midrule")
        subset = [pair for pair in pairs if model_band(pair.apm) == model]
        for key, label in TOKEN_KEYS.items():
            rows.append(
                paired_row(
                    [model.title() if key == "input" else "", label],
                    paired_summary(
                        [_category_cost(pair.apm, key) for pair in subset],
                        [_category_cost(pair.speckit, key) for pair in subset],
                    ),
                    2,
                )
            )
    return rows


def _category_cost(session: SessionArtefacts, category: str) -> float:
    """Return USD cost for one token category, including delegated dispatches.

    Sums the parser's own pre-priced ``<category>_cost_usd`` field across
    every ``calls[]`` row and every ``dispatch_calls[]`` row. ``calls[]``
    carries only main-conversation usage; folding in ``dispatch_calls[]``
    is what makes this total include subagent-dispatch spend, notably the
    five-minute ephemeral cache, which only a dispatch ever writes to.

    Args:
        session: The session whose parser data is read.
        category: One of the five token categories (e.g. ``"cache_5m"``).

    Returns:
        The summed USD cost for ``category`` across the session.
    """
    key = f"{category}_cost_usd"
    total = 0.0
    for call in session.parser_data["calls"]:
        total += float(call[key])
    for dispatch in session.parser_data["dispatch_calls"]:
        total += float(dispatch[key])
    return total


def _phase_model_note(model: str, phase: str) -> str:
    """Return note marker for a model-split phase-cost row."""
    if model == "opus" and phase == "planning":
        return r"\tnote{a}"
    if model == "opus" and phase == "implementation":
        return r"\tnote{c}"
    if model == "sonnet" and phase == "implementation":
        return r"\tnote{b}"
    return ""


if __name__ == "__main__":
    raise SystemExit(main())

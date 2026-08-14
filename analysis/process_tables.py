#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate LaTeX row fragments for process result tables."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

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
from analysis.latex import level_row, number, paired_row, percent, write_fragment
from analysis.stats import level_summary, paired_summary

PHASES = {"planning": "Planning", "implementation": "Implementation"}
TIME_SCOPES = {"session": "Session", **PHASES}
TIME_MEASURES = {
    "duration": "Duration",
    "turn_time": "Turn time",
    "inter_turn_time": "Inter-turn idle",
}
BUCKETS = {"protocol": "Protocol", "short": "Short", "standard": "Standard"}
PLANNING_BEHAVIOUR_MEASURES = {
    "request_count": "Requests",
    "tool_result_count": "Main tool calls",
    "subagent_request_count": "Subagent requests",
    "subagent_tool_count": "Subagent tool calls",
}
IMPLEMENTATION_BEHAVIOUR_MEASURES = {
    "request_count": "Requests",
    "tool_result_count": "Main tool calls",
}
PLANNING_BEHAVIOUR_NOTES = {
    "request_count": r"\tnote{a}",
    "tool_result_count": r"\tnote{a}",
    "subagent_request_count": r"\tnote{b}",
}
SUBAGENT_REQUEST_MEASURE = "subagent_request_count"
# A subagent's request count is only readable from that subagent's own transcript. One
# participant's APM submission shipped none, so its dispatches there contribute nothing and
# the pair is dropped from that measure rather than read as zero.
UNRECOVERABLE_SUBAGENT_REQUESTS = frozenset({("P001", "apm")})


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
    write_fragment(output_dir / "proc-time-paired-by-scope.tex", _time_paired_by_scope(pairs))
    write_fragment(output_dir / "proc-time-paired-by-model.tex", _time_paired_by_model(pairs))
    write_fragment(output_dir / "proc-paired-by-order.tex", _paired_by_order(pairs))
    write_fragment(output_dir / "proc-concurrency-sessions.tex", _concurrency_sessions(pairs))
    write_fragment(output_dir / "proc-turns-levels.tex", _turn_levels(pairs))
    write_fragment(output_dir / "proc-turns-paired.tex", _turn_paired(pairs))
    write_fragment(output_dir / "proc-turns-paired-by-model.tex", _turn_paired_by_model(pairs))
    write_fragment(output_dir / "proc-buckets-composition.tex", _bucket_composition(pairs))
    write_fragment(
        output_dir / "proc-planning-buckets-by-participant.tex",
        _bucket_sessions(pairs, "planning"),
    )
    write_fragment(
        output_dir / "proc-implementation-buckets-by-participant.tex",
        _bucket_sessions(pairs, "implementation"),
    )
    write_fragment(
        output_dir / "proc-buckets-composition-by-model.tex", _bucket_composition_by_model(pairs)
    )
    write_fragment(
        output_dir / "proc-bucket-magnitudes-by-model.tex", _bucket_magnitudes_by_model(pairs)
    )
    write_fragment(
        output_dir / "proc-buckets-composition-by-role.tex", _bucket_composition_by_role(pairs)
    )
    write_fragment(output_dir / "proc-steers-by-participant.tex", _steers_by_participant(pairs))
    write_fragment(output_dir / "proc-turns-levels-by-role.tex", _turn_levels_by_role(pairs))
    write_fragment(
        output_dir / "disc-planning-behaviour-paired.tex", _planning_behaviour_paired(pairs)
    )
    write_fragment(
        output_dir / "disc-implementation-behaviour-paired.tex",
        _implementation_behaviour_paired(pairs),
    )
    write_fragment(
        output_dir / "disc-compaction-incidence-by-model.tex",
        _compaction_incidence_by_model(pairs),
    )


def _duration_levels(pairs: list[ParticipantPair]) -> list[str]:
    """Return rows for per-framework session and phase duration levels.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per scope and framework.
    """
    rows: list[str] = []
    for scope_key, scope_label in (
        ("session", "Session"),
        ("planning", "Planning"),
        ("implementation", "Implementation"),
    ):
        if rows:
            rows.append(r"\midrule")
        rows.extend(
            _level_rows_for_scope(
                pairs,
                scope_label,
                lambda session, scope=scope_key: _duration_value(session, scope),
                notes=_duration_notes(scope_key),
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
    for scope_key, scope_label in (
        ("session", "Session"),
        ("planning", "Planning"),
        ("implementation", "Implementation"),
    ):
        if rows:
            rows.append(r"\midrule")
        rows.extend(
            _level_rows_for_scope(
                pairs,
                scope_label,
                lambda session, scope=scope_key: _turn_value(session, scope),
                notes=_turn_notes(scope_key),
            )
        )
    return rows


def _level_rows_for_scope(
    pairs: list[ParticipantPair],
    scope_label: str,
    value_fn: Callable[[SessionArtefacts], float],
    notes: dict[str, str] | None = None,
) -> list[str]:
    """Return APM and Spec-kit level rows for one scope.

    Args:
        pairs: Cohort participant pairs.
        scope_label: Row label for the scope (e.g. ``"Session"``).
        value_fn: Extracts the measured value from one session's artefacts.
        notes: Optional LaTeX note markers keyed by framework.

    Returns:
        One LaTeX row per framework.
    """
    rows: list[str] = []
    notes = notes or {}
    for framework in ("apm", "speckit"):
        values = [float(value_fn(getattr(pair, framework))) for pair in pairs]
        framework_label = "APM" if framework == "apm" else "Spec-kit"
        framework_label += notes.get(framework, "")
        first_cell = scope_label if framework == "apm" else ""
        rows.append(
            level_row(
                [first_cell, framework_label],
                level_summary(values),
                1,
            )
        )
    return rows


def _time_paired_by_scope(pairs: list[ParticipantPair]) -> list[str]:
    """Return pooled paired time rows at session and phase scope.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per time measure and scope.
    """
    return _time_rows(pairs)


def _time_paired_by_model(pairs: list[ParticipantPair]) -> list[str]:
    """Return paired time rows at session and phase scope by model group."""
    rows: list[str] = []
    for model in ("opus", "sonnet"):
        if rows:
            rows.append(r"\midrule")
        subset = [pair for pair in pairs if model_band(pair.apm) == model]
        rows.extend(_time_rows(subset, group_label=model.title()))
    return rows


def _time_rows(pairs: list[ParticipantPair], group_label: str | None = None) -> list[str]:
    """Return paired time rows at every scope for one participant group.

    Args:
        pairs: Participant pairs in the group to summarise.
        group_label: Optional label for the first row of a model-group block.

    Returns:
        One LaTeX row per scope and time measure.
    """
    rows: list[str] = []
    for scope_key, scope_label in TIME_SCOPES.items():
        if rows:
            start_column = 2 if group_label is not None else 1
            end_column = 9 if group_label is not None else 8
            rows.append(rf"\cmidrule(lr){{{start_column}-{end_column}}}")
        for key, label in TIME_MEASURES.items():
            cells = [scope_label if key == "duration" else "", label]
            if group_label is not None:
                cells.insert(0, group_label if not rows else "")
            rows.append(
                paired_row(
                    cells,
                    paired_summary(
                        [_time_value(pair.apm, scope_key, key) for pair in pairs],
                        [_time_value(pair.speckit, scope_key, key) for pair in pairs],
                    ),
                    1,
                )
            )
    return rows


def _paired_by_order(pairs: list[ParticipantPair]) -> list[str]:
    """Return paired session duration and turn-prompt rows by realized order."""
    rows: list[str] = []
    measures = (
        (
            "Duration",
            lambda pair: float(session_scope(pair.apm, "metrics")["duration"]),
            lambda pair: float(session_scope(pair.speckit, "metrics")["duration"]),
            False,
        ),
        (
            "Turn prompts",
            lambda pair: _turn_value(pair.apm, "session"),
            lambda pair: _turn_value(pair.speckit, "session"),
            True,
        ),
    )
    for measure, apm_value, speckit_value, include_zero in measures:
        if rows:
            rows.append(r"\midrule")
        for order in ("APM first", "APM second"):
            subset = [pair for pair in pairs if order_label(pair) == order]
            rows.append(
                paired_row(
                    [measure if order == "APM first" else "", f"{order}~"],
                    paired_summary(
                        [apm_value(pair) for pair in subset],
                        [speckit_value(pair) for pair in subset],
                    ),
                    1,
                    include_zero=include_zero,
                )
            )
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


def _turn_paired_by_model(pairs: list[ParticipantPair]) -> list[str]:
    """Return turn-prompt paired rows by model and scope."""
    rows: list[str] = []
    for model in ("opus", "sonnet"):
        if rows:
            rows.append(r"\midrule")
        subset = [pair for pair in pairs if model_band(pair.apm) == model]
        for scope, label in (
            ("session", "Session"),
            ("planning", "Planning"),
            ("implementation", "Implementation"),
        ):
            rows.append(
                paired_row(
                    [model.title() if scope == "session" else "", label],
                    paired_summary(
                        [_turn_value(pair.apm, scope) for pair in subset],
                        [_turn_value(pair.speckit, scope) for pair in subset],
                    ),
                    1,
                    include_zero=True,
                )
            )
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


def _concurrency_sessions(pairs: list[ParticipantPair]) -> list[str]:
    """Return APM session solo/concurrent active-time rows."""
    rows: list[str] = []
    for pair in pairs:
        scope = session_scope(pair.apm, "metrics")
        solo = float(scope["turn_time_solo"])
        concurrent = float(scope["turn_time_concurrent"])
        share = concurrent / float(scope["turn_time"]) if float(scope["turn_time"]) else 0.0
        rows.append(f"{pair.pid} & {solo:.0f} & {concurrent:.0f} & {percent(share)} \\\\")
    return rows


def _bucket_composition(pairs: list[ParticipantPair]) -> list[str]:
    """Return bucket share and magnitude summaries by phase and framework."""
    rows: list[str] = []
    for phase_key, phase_label in PHASES.items():
        if rows:
            rows.append(r"\midrule")
        for framework in ("apm", "speckit"):
            if framework == "speckit":
                rows.append(r"\cmidrule(lr){2-9}")
            for bucket, label in BUCKETS.items():
                sessions = [getattr(pair, framework) for pair in pairs]
                note = (
                    r"\tnote{b}"
                    if phase_key == "implementation" and framework == "apm" and bucket == "standard"
                    else ""
                )
                row_label = label + note
                framework_label = _framework_cell(framework, bucket)
                rows.append(
                    _bucket_summary_row(
                        [
                            phase_label if framework == "apm" and bucket == "protocol" else "",
                            framework_label,
                            row_label,
                        ],
                        [_bucket_share(session, phase_key, bucket) for session in sessions],
                        [_bucket_magnitude(session, phase_key, bucket) for session in sessions],
                    )
                )
    return rows


def _bucket_sessions(pairs: list[ParticipantPair], phase: str, measure: str = "both") -> list[str]:
    """Return per-participant bucket values and counts for one phase and measure."""
    rows: list[str] = []
    for pair in pairs:
        for framework in ("apm", "speckit"):
            session = getattr(pair, framework)
            label = pair.pid if framework == "apm" else ""
            if (
                phase == "implementation"
                and measure in ("both", "magnitudes")
                and framework == "apm"
                and pair.pid == "P002"
            ):
                label += r"\tnote{a}"
            if (
                phase == "implementation"
                and measure in ("both", "shares")
                and framework == "apm"
                and pair.pid == "P006"
            ):
                label += r"\tnote{b}"
            count = int(_turn_value(session, phase))
            shares = (
                ["--", "--", "--"]
                if count == 0
                else [
                    f"{_bucket_share(session, phase, bucket):.2f}"
                    for bucket in ("protocol", "short", "standard")
                ]
            )
            cells = [label, "APM" if framework == "apm" else "Spec-kit"]
            if measure in ("both", "shares"):
                cells.extend(shares)
            if measure in ("both", "magnitudes"):
                cells.extend(
                    _plain_intish(_bucket_magnitude(session, phase, bucket))
                    for bucket in ("protocol", "short", "standard")
                )
            cells.append(str(count))
            rows.append(" & ".join(cells) + r" \\")
    return rows


def _bucket_composition_by_model(pairs: list[ParticipantPair]) -> list[str]:
    """Return bucket-share summaries by model, phase, and framework."""
    rows: list[str] = []
    for model in ("opus", "sonnet"):
        if rows:
            rows.append(r"\midrule")
        subset = [pair for pair in pairs if model_band(pair.apm) == model]
        for phase_key, phase_label in PHASES.items():
            if phase_key == "implementation":
                rows.append(r"\cmidrule(lr){2-7}")
            for framework in ("apm", "speckit"):
                sessions = [getattr(pair, framework) for pair in subset]
                for bucket, label in BUCKETS.items():
                    model_cell = (
                        model.title()
                        if phase_key == "planning" and framework == "apm" and bucket == "protocol"
                        else ""
                    )
                    phase_cell = phase_label if framework == "apm" and bucket == "protocol" else ""
                    rows.append(
                        level_row(
                            [
                                model_cell,
                                phase_cell,
                                _framework_cell(framework, bucket),
                                label,
                            ],
                            level_summary(
                                [_bucket_share(session, phase_key, bucket) for session in sessions]
                            ),
                            2,
                        )
                    )
    return rows


def _bucket_magnitudes_by_model(pairs: list[ParticipantPair]) -> list[str]:
    """Return bucket character-count summaries by model, phase, and framework."""
    rows: list[str] = []
    for model in ("opus", "sonnet"):
        if rows:
            rows.append(r"\midrule")
        subset = [pair for pair in pairs if model_band(pair.apm) == model]
        for phase_key, phase_label in PHASES.items():
            if phase_key == "implementation":
                rows.append(r"\cmidrule(lr){2-7}")
            for framework in ("apm", "speckit"):
                sessions = [getattr(pair, framework) for pair in subset]
                for bucket, label in BUCKETS.items():
                    model_cell = (
                        model.title()
                        if phase_key == "planning" and framework == "apm" and bucket == "protocol"
                        else ""
                    )
                    phase_cell = phase_label if framework == "apm" and bucket == "protocol" else ""
                    note = (
                        r"\tnote{a}"
                        if model == "sonnet"
                        and phase_key == "implementation"
                        and framework == "apm"
                        and bucket == "standard"
                        else ""
                    )
                    magnitudes = [
                        _bucket_magnitude(session, phase_key, bucket) for session in sessions
                    ]
                    observed = [value for value in magnitudes if value > 0]
                    summary = level_summary(observed or magnitudes)
                    cells = [
                        model_cell,
                        phase_cell,
                        _framework_cell(framework, bucket),
                        label + note,
                        _math_intish(summary.median),
                        _math_intish(summary.hl),
                        _math_intish(summary.mean),
                    ]
                    rows.append(" & ".join(cells) + r" \\")
    return rows


def _bucket_composition_by_role(pairs: list[ParticipantPair]) -> list[str]:
    """Return APM bucket summaries by agent role."""
    rows: list[str] = []
    for prefix, role_label in (
        ("planner-", "Planner"),
        ("manager-", "Manager"),
        ("worker-", "Worker"),
    ):
        if rows:
            rows.append(r"\midrule")
        for bucket, bucket_label in BUCKETS.items():
            shares = [_role_bucket(pair.apm, prefix, bucket)[0] for pair in pairs]
            magnitudes = [_role_bucket(pair.apm, prefix, bucket)[1] for pair in pairs]
            note = r"\tnote{a}" if prefix == "worker-" and bucket == "standard" else ""
            label = bucket_label + note
            rows.append(
                _bucket_summary_row(
                    [role_label if bucket == "protocol" else "", label],
                    shares,
                    magnitudes,
                )
            )
    return rows


def _steers_by_participant(pairs: list[ParticipantPair]) -> list[str]:
    """Return per-participant steer outcomes for both frameworks.

    Steers are too few to summarise, so every session's own counts are listed at
    session scope, the only scope at which the events are numerous enough to read.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per participant, plus a cohort total row.
    """
    rows: list[str] = []
    totals = [0, 0, 0, 0]
    for pair in pairs:
        counts: list[int] = []
        for framework in ("apm", "speckit"):
            scope = session_scope(getattr(pair, framework), "data")
            counts.append(int(scope["steer_delivered_count"]))
            counts.append(int(scope["steer_abandoned_count"]))
        totals = [total + count for total, count in zip(totals, counts, strict=True)]
        rows.append(f"{pair.pid} & " + " & ".join(str(count) for count in counts) + r" \\")
    rows.append(r"\midrule")
    rows.append("Cohort & " + " & ".join(str(total) for total in totals) + r" \\")
    return rows


def _planning_behaviour_paired(pairs: list[ParticipantPair]) -> list[str]:
    """Return paired planning-phase behaviour rows for Discussions.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per behaviour measure.
    """
    return _behaviour_paired(
        pairs, "planning", PLANNING_BEHAVIOUR_MEASURES, notes=PLANNING_BEHAVIOUR_NOTES
    )


def _implementation_behaviour_paired(pairs: list[ParticipantPair]) -> list[str]:
    """Return paired implementation-phase behaviour rows for Discussions.

    Args:
        pairs: Cohort participant pairs.

    Returns:
        One LaTeX row per behaviour measure.
    """
    return _behaviour_paired(pairs, "implementation", IMPLEMENTATION_BEHAVIOUR_MEASURES)


def _behaviour_paired(
    pairs: list[ParticipantPair],
    phase: str,
    measures: dict[str, str],
    notes: dict[str, str] | None = None,
) -> list[str]:
    """Return paired behaviour rows for one phase.

    Args:
        pairs: Cohort participant pairs.
        phase: Phase scope key, ``"planning"`` or ``"implementation"``.
        measures: Parser data field names mapped to their row labels.
        notes: Optional LaTeX note markers keyed by measure.

    Returns:
        One LaTeX row per measure, in the order ``measures`` gives them.
    """
    rows: list[str] = []
    notes = notes or {}
    for measure, label in measures.items():
        subset = _recoverable_pairs(pairs, measure)
        rows.append(
            paired_row(
                [label + notes.get(measure, "")],
                paired_summary(
                    [_behaviour_value(pair.apm, phase, measure) for pair in subset],
                    [_behaviour_value(pair.speckit, phase, measure) for pair in subset],
                ),
                1,
            )
        )
    return rows


def _recoverable_pairs(pairs: list[ParticipantPair], measure: str) -> list[ParticipantPair]:
    """Return the pairs one behaviour measure is recoverable for in both frameworks.

    A paired difference needs both sessions, so a pair is dropped when either
    session is missing the measure.

    Args:
        pairs: Cohort participant pairs.
        measure: Parser data field name.

    Returns:
        ``pairs`` unchanged, less any pair with an unrecoverable session.
    """
    if measure != SUBAGENT_REQUEST_MEASURE:
        return pairs
    return [
        pair
        for pair in pairs
        if not any(
            (pair.pid, framework) in UNRECOVERABLE_SUBAGENT_REQUESTS
            for framework in ("apm", "speckit")
        )
    ]


def _behaviour_value(session: SessionArtefacts, phase: str, measure: str) -> float:
    """Return one behaviour count from a session's phase scope."""
    return float(phase_scope(session, "data", phase)[measure])


def _compaction_incidence_by_model(pairs: list[ParticipantPair]) -> list[str]:
    """Return compaction incidence rows by model and framework."""
    rows: list[str] = []
    for model in ("opus", "sonnet"):
        for framework in ("apm", "speckit"):
            sessions = [getattr(pair, framework) for pair in pairs if model_band(pair.apm) == model]
            counts = [_compaction_count(session) for session in sessions]
            rows.append(
                f"{model.title() if framework == 'apm' else ''} & "
                f"{'APM' if framework == 'apm' else 'Spec-kit'} & "
                f"{len(sessions)} & {sum(count > 0 for count in counts)} & "
                f"{sum(count > 1 for count in counts)} \\\\"
            )
    return rows


def _duration_value(session: SessionArtefacts, scope: str) -> float:
    """Return duration for a session or phase scope."""
    if scope == "session":
        return float(session_scope(session, "metrics")["duration"])
    return float(phase_scope(session, "metrics", scope)["duration"])


def _time_value(session: SessionArtefacts, scope: str, measure: str) -> float:
    """Return one time measure at session or phase scope.

    Args:
        session: Session artefacts containing the recorded measurements.
        scope: Session, planning, or implementation scope.
        measure: Duration, turn-time, or inter-turn-time metric key.

    Returns:
        Recorded time in seconds.
    """
    if scope == "session":
        return float(session_scope(session, "metrics")[measure])
    return float(phase_scope(session, "metrics", scope)[measure])


def _turn_value(session: SessionArtefacts, scope: str) -> float:
    """Return turn-prompt count for a session or phase scope."""
    if scope == "session":
        return float(session_scope(session, "data")["turn_prompt_count"])
    return float(phase_scope(session, "data", scope)["turn_prompt_count"])


def _duration_notes(scope: str) -> dict[str, str]:
    """Return existing table note markers for duration rows.

    Markers run in row order, so the session row takes the first letter.
    """
    if scope == "session":
        return {"apm": r"\tnote{a}"}
    if scope == "planning":
        return {"apm": r"\tnote{b}"}
    if scope == "implementation":
        return {"speckit": r"\tnote{c}"}
    return {}


def _bucket_share(session: SessionArtefacts, scope: str, bucket: str) -> float:
    """Return one turn-prompt bucket share."""
    block = _metric_scope(session, scope)
    return float(block["turn_prompts_bucket_shares"][bucket])


def _bucket_magnitude(session: SessionArtefacts, scope: str, bucket: str) -> float:
    """Return one turn-prompt bucket magnitude."""
    block = _metric_scope(session, scope)
    return float(block["turn_prompts_magnitude_by_bucket"][bucket])


def _metric_scope(session: SessionArtefacts, scope: str) -> dict[str, Any]:
    """Return a session or phase metric scope."""
    if scope == "session":
        return session_scope(session, "metrics")
    return phase_scope(session, "metrics", scope)


def _framework_cell(framework: str, first_row_key: str) -> str:
    """Return framework label for the first row of a grouped block."""
    if first_row_key not in {"protocol", "planning"}:
        return ""
    return "APM" if framework == "apm" else "Spec-kit"


def _bucket_summary_row(
    label_cells: list[str], shares: list[float], magnitudes: list[float]
) -> str:
    """Return a row with share and magnitude level summaries."""
    share = level_summary(shares)
    observed_magnitudes = [value for value in magnitudes if value > 0]
    magnitude = level_summary(observed_magnitudes or magnitudes)
    cells = [
        *label_cells,
        number(share.median, 2),
        number(share.hl, 2),
        number(share.mean, 2),
        _math_intish(magnitude.median),
        _math_intish(magnitude.hl),
        _math_intish(magnitude.mean),
    ]
    return " & ".join(cells) + r" \\"


def _role_bucket(session: SessionArtefacts, role_prefix: str, bucket: str) -> tuple[float, float]:
    """Return aggregate turn-prompt share and magnitude for one role prefix and bucket."""
    prompt_count_total = 0.0
    prompt_bucket_count = 0.0
    prompt_bucket_chars = 0.0
    for role, data in role_scopes(session, "data").items():
        if not role.startswith(role_prefix):
            continue
        metrics = role_scopes(session, "metrics")[role]
        prompt_count = float(data["turn_prompt_count"])
        prompt_share = float(metrics["turn_prompts_bucket_shares"][bucket])
        magnitude = float(metrics["turn_prompts_magnitude_by_bucket"][bucket])
        prompt_count_total += prompt_count
        role_prompt_bucket_count = prompt_count * prompt_share
        prompt_bucket_count += role_prompt_bucket_count
        prompt_bucket_chars += role_prompt_bucket_count * magnitude
    if prompt_count_total == 0 or prompt_bucket_count == 0:
        return 0.0, 0.0
    return prompt_bucket_count / prompt_count_total, prompt_bucket_chars / prompt_bucket_count


def _compaction_count(session: SessionArtefacts) -> int:
    """Return the number of parser context segments closed by compaction."""
    if "context_segments" not in session.parser_data:
        raise ValueError(f"{session.record.parser_data}: missing context_segments[]")
    return sum(
        1 for segment in session.parser_data["context_segments"] if segment["closed_by_compaction"]
    )


def _math_intish(value: float) -> str:
    """Format a table value as a math integer unless a decimal is needed."""
    return f"${_plain_intish(value)}$"


def _plain_intish(value: float) -> str:
    """Format a plain integer-like value with no needless decimal."""
    return str(round(value))


def _turn_notes(scope: str) -> dict[str, str]:
    """Return existing table note markers for turn-count rows."""
    if scope == "planning":
        return {"apm": r"\tnote{a}"}
    if scope == "implementation":
        return {"speckit": r"\tnote{b,c}"}
    return {}


if __name__ == "__main__":
    raise SystemExit(main())

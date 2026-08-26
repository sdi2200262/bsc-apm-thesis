#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate the LaTeX row fragment pricing context held above the compaction ceiling.

A conversation that is not reset carries its whole context into every later call,
and the platform charges those tokens as cache reads. This module prices the part
of that context standing above the auto-compaction ceiling, for the sessions whose
conversation was served past the context window stated for its model.

The selection is derived from the data rather than named in the config: a session
qualifies when any of its context segments peaks above the window stated for its
model. Thresholds are declared per model band, and a session whose band the config
does not declare is not considered, since the condition is only meaningful where a
band's window is within reach of what a session accumulates. The generator takes
its own config because the sessions it reports are not a partition of the cohort
and cannot be produced by splitting a cohort-wide table.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.cohort import (
    SessionArtefacts,
    load_sessions,
    model_band,
    model_band_from_parser_data,
    pair_by_participant,
    session_scope,
)
from analysis.config import ConfigError, load_records
from analysis.latex import money, write_fragment
from analysis.stats import PairedSummary, paired_summary

FRAGMENT_NAME = "disc-above-ceiling-cost.tex"


@dataclass(frozen=True)
class BandThresholds:
    """The token thresholds declared for one model band.

    Attributes:
        ceiling_tokens: Context size above which accumulation counts as excess.
        window_tokens: Peak a context segment must exceed for a session of this
            band to be reported.
    """

    ceiling_tokens: int
    window_tokens: int


@dataclass(frozen=True)
class SessionInput:
    """One configured session the generator may report.

    Attributes:
        pid: Participant id, e.g. ``P003``.
        session: Session label, ``S1`` or ``S2``.
        parser_data: Path to the session's ``parser_data.json``.
    """

    pid: str
    session: str
    parser_data: Path


@dataclass(frozen=True)
class AboveCeiling:
    """The above-ceiling accumulation of one session.

    Attributes:
        pid: Participant id.
        cache_read_tokens: All tokens the session read from the prompt cache,
            the population the above-ceiling reads are drawn from. Covers the
            whole session, including any segment that never reached the ceiling.
        excess_tokens: Tokens read above the ceiling across the session, summed
            over every call that sat above it.
        excess_cost: Dollar cost of those reads at their own cache-read rate.
        session_cost: The session's total dollar cost.
    """

    pid: str
    cache_read_tokens: int
    excess_tokens: int
    excess_cost: float
    session_cost: float


def main(argv: list[str] | None = None) -> int:
    """Generate the above-ceiling cost fragment.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code (0 on success, 1 on a config or data error).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path, help="common asset root")
    parser.add_argument("--cohort-config", type=Path)
    args = parser.parse_args(argv)
    try:
        sessions, bands = load_inputs(args.config)
        summaries = [
            summary
            for summary in (measure(session, bands) for session in sessions)
            if summary is not None
        ]
        if not summaries:
            raise ConfigError("no configured session peaks above its band's window")
        summaries.sort(key=lambda summary: summary.pid)
        write_fragment(args.output_dir / "tables" / FRAGMENT_NAME, rows(summaries))
        if args.cohort_config is not None:
            report_sensitivity(summaries, args.cohort_config)
    except (ConfigError, KeyError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


def load_inputs(config_path: Path) -> tuple[list[SessionInput], dict[str, BandThresholds]]:
    """Load the generator's config.

    Args:
        config_path: JSON config path. Relative session paths resolve against
            the config file's own directory.

    Returns:
        The configured sessions and the thresholds declared per model band.

    Raises:
        ConfigError: When the config is malformed.
    """
    path = config_path.resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ConfigError(f"cannot read config {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"invalid JSON in config {path}: {error}") from error
    bands = _bands_from_payload(payload, path)
    raw = payload.get("sessions")
    if not isinstance(raw, list) or not raw:
        raise ConfigError(f"{path}: expected non-empty sessions array")
    base = path.parent
    sessions = [_session_from_payload(item, base, path, index) for index, item in enumerate(raw)]
    return sessions, bands


def measure(session: SessionInput, bands: dict[str, BandThresholds]) -> AboveCeiling | None:
    """Price one session's above-ceiling accumulation.

    A call's above-ceiling part is capped at the cache reads it actually made, so
    the figure never counts tokens the call did not read from cache, and it is
    priced at that call's own realised cache-read rate rather than a rate table
    restated here.

    Args:
        session: The configured session to measure.
        bands: Thresholds by model band, as declared in the config.

    Returns:
        The session's summary, or ``None`` when its band is not declared or no
        segment peaks above that band's window.

    Raises:
        ConfigError: When the session's parser artefact cannot be read or is
            missing a field this computation needs.
    """
    try:
        data = json.loads(session.parser_data.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigError(f"cannot read {session.parser_data}: {error}") from error
    try:
        thresholds = bands.get(model_band_from_parser_data(data))
        if thresholds is None:
            return None
        ceiling = thresholds.ceiling_tokens
        peaks = [segment["peak_context_tokens"] for segment in data["context_segments"]]
        peak = max(peaks, default=0)
        if peak <= thresholds.window_tokens:
            return None
        cache_read_tokens = 0
        excess_tokens = 0
        excess_cost = 0.0
        session_cost = 0.0
        for call in data["calls"]:
            session_cost += _call_cost(call)
            cache_read_tokens += call["cache_read"]
            seen = _occupancy(call)
            if seen <= ceiling or call["cache_read"] == 0:
                continue
            excess = min(seen - ceiling, call["cache_read"])
            excess_tokens += excess
            excess_cost += call["cache_read_cost_usd"] * excess / call["cache_read"]
        # Subagent dispatches are billed to the session but run in their own context,
        # so they belong to the session's cost and carry no occupancy of their own.
        for dispatch in data.get("dispatch_calls") or []:
            session_cost += _call_cost(dispatch)
    except KeyError as error:
        raise ConfigError(f"{session.parser_data}: missing field {error}") from error
    return AboveCeiling(
        pid=session.pid,
        cache_read_tokens=cache_read_tokens,
        excess_tokens=excess_tokens,
        excess_cost=excess_cost,
        session_cost=session_cost,
    )


def rows(summaries: list[AboveCeiling]) -> list[str]:
    """Return the LaTeX row lines for the fragment.

    Args:
        summaries: Per-session summaries, in the order they should appear.

    Returns:
        One row string per session.
    """
    return [
        " & ".join(
            [
                summary.pid,
                f"${summary.cache_read_tokens / 1000:.1f}$",
                f"${summary.excess_tokens / 1000:.1f}$",
                money(summary.excess_cost),
                money(summary.session_cost),
            ]
        )
        + r" \\"
        for summary in summaries
    ]


def report_sensitivity(summaries: list[AboveCeiling], cohort_config: Path) -> None:
    """Print the Sonnet paired cost summary with each session's excess removed.

    The excess sits on the Spec-kit side of a Sonnet pair, and no config edit can
    express a cost reduction, so the counterfactual is computed and printed here.

    Args:
        summaries: The measured sessions.
        cohort_config: Path to the cohort config.

    Raises:
        ConfigError: When a measured session has no Sonnet pair in the cohort.
    """
    excess = {summary.pid: summary.excess_cost for summary in summaries}
    pairs = [
        pair
        for pair in pair_by_participant(load_sessions(load_records(cohort_config)))
        if model_band(pair.apm) == "sonnet"
    ]
    missing = sorted(excess.keys() - {pair.pid for pair in pairs})
    if missing:
        raise ConfigError(f"{cohort_config}: no Sonnet pair for {', '.join(missing)}")
    apm = [_session_cost(pair.apm) for pair in pairs]
    speckit = [_session_cost(pair.speckit) for pair in pairs]
    adjusted = [cost - excess.get(pair.pid, 0.0) for cost, pair in zip(speckit, pairs, strict=True)]
    _print_summary("observed", paired_summary(apm, speckit))
    _print_summary("excess removed", paired_summary(apm, adjusted))


def _print_summary(label: str, summary: PairedSummary) -> None:
    """Print one paired summary at the precision the cost tables carry."""
    print(
        f"sonnet session cost, {label}: "
        f"sign=+{summary.positive}/-{summary.negative} "
        f"median={summary.median:+.2f} hl={summary.hl:+.2f} mean={summary.mean:+.2f} "
        f"ci=[{summary.ci_low:+.2f}, {summary.ci_high:+.2f}]"
    )


def _session_cost(session: SessionArtefacts) -> float:
    """Return one session's total dollar cost from its parser metrics."""
    return float(session_scope(session, "metrics")["cost_usd"])


def _bands_from_payload(payload: Any, config_path: Path) -> dict[str, BandThresholds]:
    """Build the per-band threshold map from the config object."""
    raw = payload.get("bands") if isinstance(payload, dict) else None
    if not isinstance(raw, dict) or not raw:
        raise ConfigError(f"{config_path}: expected non-empty bands object")
    bands: dict[str, BandThresholds] = {}
    for name, item in raw.items():
        ceiling = _required_int(item, "ceiling_tokens", config_path, name)
        window = _required_int(item, "window_tokens", config_path, name)
        if ceiling > window:
            raise ConfigError(f"{config_path}: band '{name}' ceiling exceeds its window")
        bands[str(name)] = BandThresholds(ceiling_tokens=ceiling, window_tokens=window)
    return bands


def _required_int(payload: Any, key: str, config_path: Path, band: str) -> int:
    """Return a required positive integer field of one band's config object."""
    value = payload.get(key) if isinstance(payload, dict) else None
    if not isinstance(value, int) or value <= 0:
        raise ConfigError(f"{config_path}: band '{band}' needs a positive '{key}'")
    return value


def _session_from_payload(
    item: Any,
    base: Path,
    config_path: Path,
    index: int,
) -> SessionInput:
    """Build one ``SessionInput`` from a JSON object."""
    if not isinstance(item, dict):
        raise ConfigError(f"{config_path}: sessions[{index}] must be an object")
    missing = [key for key in ("pid", "session", "parser_data") if not item.get(key)]
    if missing:
        raise ConfigError(f"{config_path}: sessions[{index}] missing {', '.join(missing)}")
    parser_data = Path(str(item["parser_data"]))
    if not parser_data.is_absolute():
        parser_data = base / parser_data
    return SessionInput(
        pid=str(item["pid"]),
        session=str(item["session"]),
        parser_data=parser_data,
    )


def _occupancy(call: dict[str, Any]) -> int:
    """Return the prompt-side token total the model saw on one call."""
    return call["input"] + call["cache_read"] + call["cache_5m"] + call["cache_1h"]


def _call_cost(call: dict[str, Any]) -> float:
    """Return the parser's total dollar cost for one call or dispatch."""
    return (
        call["input_cost_usd"]
        + call["output_cost_usd"]
        + call["cache_read_cost_usd"]
        + call["cache_5m_cost_usd"]
        + call["cache_1h_cost_usd"]
    )


if __name__ == "__main__":
    sys.exit(main())

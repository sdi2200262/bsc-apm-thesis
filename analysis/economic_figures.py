#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate economic result PDF figures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt

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
from analysis.style import APM_COLOR, APM_MARKER, apply_grid, label_axis_end_right, new_figure

MORE_FILL = "#e6e6e6"
LESS_FILL = "#ffffff"


def main(argv: list[str] | None = None) -> int:
    """Run the economic figure generator.

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
        render_all(pairs, args.output_dir)
    except (ConfigError, KeyError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


def render_all(pairs: list[ParticipantPair], output_dir: Path) -> None:
    """Render all economic figures.

    Args:
        pairs: Cohort participant pairs.
        output_dir: Destination directory.
    """
    render_cost_differences(pairs, output_dir / "cost_overall.pdf", width_in=6.8)
    render_cost_differences(
        _model_pairs(pairs, "opus"),
        output_dir / "cost_opus.pdf",
        width_in=3.3,
        y_limits=_common_ylim(pairs),
        x_label="Opus",
    )
    render_cost_differences(
        _model_pairs(pairs, "sonnet"),
        output_dir / "cost_sonnet.pdf",
        width_in=3.3,
        y_limits=_common_ylim(pairs),
        x_label="Sonnet",
    )


def render_cost_differences(
    pairs: list[ParticipantPair],
    output: Path,
    *,
    width_in: float,
    y_limits: tuple[float, float] | None = None,
    x_label: str | None = None,
) -> None:
    """Render one per-participant cost-difference panel.

    Args:
        pairs: Participant pairs to plot.
        output: Destination PDF path.
        width_in: Figure width in inches.
        y_limits: Optional shared y-axis limits.
        x_label: Optional x-axis label.
    """
    diffs = [_cost(pair.apm) - _cost(pair.speckit) for pair in pairs]
    y_bot, y_top = y_limits if y_limits is not None else _limits_for_values(diffs)
    fig, ax = new_figure(width_in=width_in, height_in=4.0)
    ax.set_ylim(y_bot, y_top)
    ax.axhspan(0, y_top, facecolor=MORE_FILL, edgecolor="none", zorder=0)
    ax.axhspan(y_bot, 0, facecolor=LESS_FILL, edgecolor="none", zorder=0)
    ax.axhline(y=0, color="#333333", linewidth=0.9, linestyle="--", zorder=2)
    xs = list(range(len(pairs)))
    ax.scatter(xs, diffs, s=28, color=APM_COLOR, marker=APM_MARKER, linewidths=0, zorder=3)
    ax.set_xticks(xs)
    ax.set_xticklabels([pair.pid for pair in pairs], fontsize=8, rotation=45, ha="right")
    ax.set_xlim(-0.6, len(pairs) - 0.4)
    ax.set_ylabel("Cost difference (USD)", fontsize=9)
    if x_label is not None:
        ax.set_xlabel(x_label, fontsize=9, labelpad=8)
    apply_grid(ax, axis="y")
    label_axis_end_right(ax, y_data=y_top * 0.78, text="APM costs more", fontsize=7.5)
    label_axis_end_right(ax, y_data=y_bot * 0.78, text="APM costs less", fontsize=7.5)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def _model_pairs(pairs: list[ParticipantPair], model: str) -> list[ParticipantPair]:
    """Return participant pairs for one model band."""
    return [pair for pair in pairs if model_band(pair.apm) == model]


def _common_ylim(pairs: list[ParticipantPair]) -> tuple[float, float]:
    """Return y-axis limits from the full-cohort cost range."""
    return _limits_for_values([_cost(pair.apm) - _cost(pair.speckit) for pair in pairs])


def _limits_for_values(values: list[float]) -> tuple[float, float]:
    """Return padded y-axis limits for ``values``."""
    span = max(values) - min(values)
    pad = 0.10 * span if span else 1.0
    return min(values) - pad, max(values) + pad


def _cost(session: SessionArtefacts) -> float:
    """Return the parser session cost for one loaded session."""
    return float(session.parser_metrics["scopes"]["session"]["cost_usd"])


if __name__ == "__main__":
    raise SystemExit(main())

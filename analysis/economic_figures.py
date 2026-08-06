#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate economic result PDF figures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.lines import Line2D

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
from analysis.style import (
    APM_COLOR,
    APM_LABEL,
    APM_MARKER,
    SPECKIT_FACECOLOR,
    SPECKIT_LABEL,
    SPECKIT_MARKER,
    apply_grid,
    new_figure,
    report_extremes,
)


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
    render_cost_levels(
        _model_pairs(pairs, "opus"),
        output_dir / "cost_levels_opus.pdf",
        width_in=3.3,
        x_label="Opus",
    )
    render_cost_levels(
        _model_pairs(pairs, "sonnet"),
        output_dir / "cost_levels_sonnet.pdf",
        width_in=3.3,
        x_label="Sonnet",
    )


def render_cost_levels(
    pairs: list[ParticipantPair],
    output: Path,
    *,
    width_in: float,
    x_label: str,
) -> None:
    """Render one per-participant session-cost panel for a model group.

    Each panel carries its own y-axis scale, since the two models price a session
    at different orders and a shared scale would flatten the Sonnet group's own
    spread, which is what this figure exists to show.

    Args:
        pairs: Participant pairs to plot.
        output: Destination PDF path.
        width_in: Figure width in inches.
        x_label: Model name for the x-axis.
    """
    panel = output.stem
    report_extremes(f"{panel} APM", [_cost(pair.apm) for pair in pairs], 2)
    report_extremes(f"{panel} Spec-kit", [_cost(pair.speckit) for pair in pairs], 2)
    fig, ax = new_figure(width_in=width_in, height_in=4.0)
    _draw_levels(ax, pairs)
    # The model name sits below the form key, so it clears the tick labels and the
    # key both.
    ax.set_xlabel(x_label, fontsize=9, labelpad=34)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def _draw_levels(ax: Axes, pairs: list[ParticipantPair]) -> None:
    """Draw each participant's two session costs onto ``ax``.

    Args:
        ax: Axes to draw on.
        pairs: Participant pairs.
    """
    xs = list(range(len(pairs)))
    values: list[float] = []
    for x, pair in zip(xs, pairs, strict=True):
        apm = _cost(pair.apm)
        speckit = _cost(pair.speckit)
        values.extend((apm, speckit))
        ax.plot([x, x], [speckit, apm], color="#000000", linewidth=0.8, zorder=1)
        ax.plot(
            x,
            apm,
            marker=APM_MARKER,
            markerfacecolor=APM_COLOR,
            markeredgecolor="#000000",
            markersize=6,
            zorder=3,
        )
        ax.plot(
            x,
            speckit,
            marker=SPECKIT_MARKER,
            markerfacecolor=SPECKIT_FACECOLOR,
            markeredgecolor="#000000",
            markersize=6,
            zorder=3,
        )
    ax.set_xticks(xs)
    ax.set_xticklabels([pair.pid for pair in pairs], fontsize=8, rotation=45, ha="right")
    ax.set_xlim(-0.6, len(pairs) - 0.4)
    ax.set_ylabel("Session cost (USD)", fontsize=9)
    ax.set_ylim(0, max(values) * 1.10)
    apply_grid(ax, axis="y")
    _form_key(ax)


def _form_key(ax: Axes) -> None:
    """Place a frameless APM/Spec-kit marker key below the axes."""
    apm_key = Line2D(
        [],
        [],
        marker=APM_MARKER,
        linestyle="none",
        markerfacecolor=APM_COLOR,
        markeredgecolor="#000000",
        markersize=6,
        label=APM_LABEL,
    )
    speckit_key = Line2D(
        [],
        [],
        marker=SPECKIT_MARKER,
        linestyle="none",
        markerfacecolor=SPECKIT_FACECOLOR,
        markeredgecolor="#000000",
        markersize=6,
        label=SPECKIT_LABEL,
    )
    ax.legend(
        handles=[apm_key, speckit_key],
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
        ncol=2,
        fontsize=8,
    )


def _model_pairs(pairs: list[ParticipantPair], model: str) -> list[ParticipantPair]:
    """Return participant pairs for one model band."""
    return [pair for pair in pairs if model_band(pair.apm) == model]


def _cost(session: SessionArtefacts) -> float:
    """Return the parser session cost for one loaded session."""
    return float(session.parser_metrics["scopes"]["session"]["cost_usd"])


if __name__ == "__main__":
    raise SystemExit(main())

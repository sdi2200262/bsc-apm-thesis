#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate the cost-versus-score discussion figure."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
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
from analysis.style import APM_COLOR, SPECKIT_FACECOLOR, apply_grid, new_figure

LABELLED = {"P001", "P002", "P004", "P009", "P012"}


@dataclass(frozen=True)
class Point:
    """One participant's paired cost and score difference."""

    pid: str
    model: str
    cost_difference: float
    score_difference: float


def main(argv: list[str] | None = None) -> int:
    """Run the cost-versus-score figure generator.

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
        render(_points(pairs), args.output_dir / "cost_score.pdf")
    except (ConfigError, KeyError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


def render(points: list[Point], output: Path) -> None:
    """Render the cost-versus-score scatter.

    Args:
        points: Participant difference points.
        output: Destination PDF path.
    """
    fig, ax = new_figure(width_in=6.9, height_in=4.2)
    ax.axhline(0, color="#888888", linewidth=0.7, zorder=0)
    ax.axvline(0, color="#888888", linewidth=0.7, zorder=0)
    for point in points:
        _plot_model_marker(ax, point.cost_difference, point.score_difference, point.model)
        if point.pid in LABELLED:
            ax.annotate(
                point.pid,
                xy=(point.cost_difference, point.score_difference),
                xytext=(5, 2),
                textcoords="offset points",
                ha="left",
                va="bottom",
                fontsize=7,
            )
    ax.set_xlabel("Cost difference (USD)", fontsize=9)
    ax.set_ylabel("Score difference (points)", fontsize=9)
    apply_grid(ax, axis="both")
    _form_key(ax)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def _points(pairs: list[ParticipantPair]) -> list[Point]:
    """Return cost-versus-score points for participant pairs."""
    return [
        Point(
            pid=pair.pid,
            model=model_band(pair.apm),
            cost_difference=_cost(pair.apm) - _cost(pair.speckit),
            score_difference=_score(pair.apm) - _score(pair.speckit),
        )
        for pair in pairs
    ]


def _plot_model_marker(ax: Axes, x: float, y: float, model: str) -> None:
    """Plot one point using the marker for ``model``.

    Args:
        ax: Axes to draw on.
        x: Cost-difference coordinate.
        y: Score-difference coordinate.
        model: ``"opus"`` or ``"sonnet"``.
    """
    if model == "opus":
        ax.plot(
            x,
            y,
            marker="o",
            markerfacecolor=APM_COLOR,
            markeredgecolor="#000000",
            markersize=6,
            linestyle="none",
            zorder=3,
        )
        return
    ax.plot(
        x,
        y,
        marker="D",
        markerfacecolor=SPECKIT_FACECOLOR,
        markeredgecolor="#000000",
        markersize=6,
        linestyle="none",
        zorder=3,
    )


def _form_key(ax: Axes) -> None:
    """Place a frameless model marker key below the axes."""
    opus = Line2D(
        [],
        [],
        marker="o",
        linestyle="none",
        markerfacecolor=APM_COLOR,
        markeredgecolor="#000000",
        markersize=6,
        label="Opus",
    )
    sonnet = Line2D(
        [],
        [],
        marker="D",
        linestyle="none",
        markerfacecolor=SPECKIT_FACECOLOR,
        markeredgecolor="#000000",
        markersize=6,
        label="Sonnet",
    )
    ax.legend(
        handles=[opus, sonnet],
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=2,
        fontsize=8,
    )


def _cost(session: SessionArtefacts) -> float:
    """Return a session cost in USD."""
    return float(session.parser_metrics["scopes"]["session"]["cost_usd"])


def _score(session: SessionArtefacts) -> float:
    """Return a session total score."""
    return float(session.grader_results["scores"]["total"])


if __name__ == "__main__":
    raise SystemExit(main())

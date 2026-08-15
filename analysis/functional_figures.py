#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate functional score PDF figures."""

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
)

LABEL_BELOW = 88.0


def main(argv: list[str] | None = None) -> int:
    """Run the functional figure generator.

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
    """Render model-split score figures.

    Args:
        pairs: Cohort participant pairs.
        output_dir: Destination directory.
    """
    render_dumbbell(
        [pair for pair in pairs if model_band(pair.apm) == "opus"],
        output_dir / "functional_dumbbell_opus.pdf",
        width_in=3.35,
    )
    render_dumbbell(
        [pair for pair in pairs if model_band(pair.apm) == "sonnet"],
        output_dir / "functional_dumbbell_sonnet.pdf",
        width_in=3.35,
    )


def render_dumbbell(pairs: list[ParticipantPair], output: Path, *, width_in: float) -> None:
    """Render one paired score dumbbell figure.

    Args:
        pairs: Participant pairs to plot.
        output: Destination PDF path.
        width_in: Figure width in inches.
    """
    fig, ax = new_figure(width_in=width_in, height_in=4.0)
    _draw(ax, pairs)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def _draw(ax: Axes, pairs: list[ParticipantPair]) -> None:
    """Draw paired score markers onto ``ax``.

    Args:
        ax: Axes to draw on.
        pairs: Participant pairs.
    """
    xs = list(range(len(pairs)))
    for x, pair in zip(xs, pairs, strict=True):
        apm = _score(pair.apm)
        speckit = _score(pair.speckit)
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
        low = min(apm, speckit)
        if low < LABEL_BELOW:
            ax.annotate(
                pair.pid,
                xy=(x, low),
                xytext=(5, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=7,
            )
    ax.set_xticks(xs)
    ax.set_xticklabels([pair.pid for pair in pairs], fontsize=8, rotation=45, ha="right")
    ax.set_xlim(-0.6, len(pairs) - 0.4)
    ax.set_ylabel("Total score (points)", fontsize=9)
    ax.set_ylim(0, 104)
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


def _score(session: SessionArtefacts) -> float:
    """Return a session's total score."""
    return float(session.grader_results["scores"]["total"])


if __name__ == "__main__":
    raise SystemExit(main())

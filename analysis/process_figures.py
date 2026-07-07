#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate process result PDF figures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.patches import Patch

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.cohort import (
    ParticipantPair,
    SessionArtefacts,
    load_sessions,
    pair_by_participant,
    session_scope,
)
from analysis.config import ConfigError, load_records
from analysis.style import (
    APM_COLOR,
    APM_LABEL,
    SPECKIT_FACECOLOR,
    SPECKIT_HATCH,
    SPECKIT_LABEL,
    apply_grid,
    new_figure,
)

IDLE_FILL = "#ffffff"
BAR_WIDTH = 0.40


def main(argv: list[str] | None = None) -> int:
    """Run the process figure generator.

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
        render_temporal(pairs, args.output_dir / "temporal.pdf")
    except (ConfigError, KeyError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


def render_temporal(pairs: list[ParticipantPair], output: Path) -> None:
    """Render the per-participant temporal decomposition figure.

    Args:
        pairs: Cohort participant pairs.
        output: Destination PDF path.
    """
    fig, ax = new_figure(width_in=6.8, height_in=4.0)
    centres = list(range(len(pairs)))
    for centre, pair in zip(centres, pairs, strict=True):
        _draw_bar(ax, centre - BAR_WIDTH / 2 - 0.02, pair.apm, hatch=None)
        _draw_bar(ax, centre + BAR_WIDTH / 2 + 0.02, pair.speckit, hatch=SPECKIT_HATCH)
    ax.set_xticks(centres)
    ax.set_xticklabels([pair.pid for pair in pairs], fontsize=8, rotation=45, ha="right")
    ax.set_xlim(-0.7, len(pairs) - 0.3)
    ax.set_ylabel("Session duration (thousand seconds)", fontsize=9)
    ax.set_ylim(0, None)
    apply_grid(ax, axis="y")
    _form_key(ax)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def _draw_bar(ax: Axes, x: float, session: SessionArtefacts, *, hatch: str | None) -> None:
    """Draw one active-plus-idle session bar.

    Args:
        ax: Axes to draw on.
        x: Centre x position.
        session: Session artefacts.
        hatch: Hatch for Spec-kit active time, or ``None`` for APM.
    """
    scope = session_scope(session, "metrics")
    active = float(scope["turn_time"]) / 1000.0
    idle = float(scope["inter_turn_time"]) / 1000.0
    face = APM_COLOR if hatch is None else SPECKIT_FACECOLOR
    ax.bar(
        x,
        active,
        width=BAR_WIDTH,
        facecolor=face,
        edgecolor="#000000",
        linewidth=0.9,
        hatch=hatch,
        zorder=2,
    )
    ax.bar(
        x,
        idle,
        width=BAR_WIDTH,
        bottom=active,
        facecolor=IDLE_FILL,
        edgecolor="#000000",
        linewidth=0.7,
        zorder=2,
    )


def _form_key(ax: Axes) -> None:
    """Place a frameless APM/Spec-kit bar key below the axes."""
    apm_key = Patch(facecolor=APM_COLOR, edgecolor="#000000", linewidth=0.9, label=APM_LABEL)
    speckit_key = Patch(
        facecolor=SPECKIT_FACECOLOR,
        edgecolor="#000000",
        linewidth=0.9,
        hatch=SPECKIT_HATCH,
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


if __name__ == "__main__":
    raise SystemExit(main())

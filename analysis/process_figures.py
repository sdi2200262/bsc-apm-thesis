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
    phase_scope,
    session_scope,
)
from analysis.config import ConfigError, load_records
from analysis.style import (
    APM_COLOR,
    APM_LABEL,
    FILLED,
    OPEN,
    SPECKIT_FACECOLOR,
    SPECKIT_HATCH,
    SPECKIT_LABEL,
    apply_grid,
    new_figure,
    report_extremes,
)

IDLE_FILL = "#ffffff"
BAR_WIDTH = 0.40

BUCKET_ORDER = ("protocol", "short", "standard")
BUCKET_LABELS = {"protocol": "Protocol", "short": "Short", "standard": "Standard"}
# The stacked segments take the fill channel, so the framework is carried by position alone. The
# ramp runs between the same black and white the mark pairs use, with one grey between them.
BUCKET_FILL = {"protocol": FILLED, "short": "#8c8c8c", "standard": OPEN}
SHARE_BAR_WIDTH = 0.30
SHARE_BAR_GAP = 0.02
# Left and right panels are reserved for the model groups, so a phase split stacks vertically.
PHASE_PANELS = (("planning", "Planning"), ("implementation", "Implementation"))


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
        render_bucket_shares(pairs, args.output_dir / "bucket_shares.pdf")
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


def render_bucket_shares(pairs: list[ParticipantPair], output: Path) -> None:
    """Render the per-session turn-prompt bucket-share figure, one panel per phase.

    Args:
        pairs: Cohort participant pairs.
        output: Destination PDF path.
    """
    fig, axes = plt.subplots(nrows=len(PHASE_PANELS), figsize=(7.2, 5.4), sharex=True)
    centres = list(range(len(pairs)))
    for ax, (phase, phase_label) in zip(axes, PHASE_PANELS, strict=True):
        for centre, pair in zip(centres, pairs, strict=True):
            offset = SHARE_BAR_WIDTH / 2 + SHARE_BAR_GAP
            _draw_share_bar(ax, centre - offset, pair.apm, phase)
            _draw_share_bar(ax, centre + offset, pair.speckit, phase)
        ax.set_ylabel(f"{phase_label} bucket share", fontsize=9)
        ax.set_ylim(0, 1)
        ax.set_xlim(-0.7, len(pairs) - 0.3)
        apply_grid(ax, axis="y")
        _report_share_extremes(pairs, phase)
    axes[-1].set_xticks(centres)
    axes[-1].set_xticklabels([pair.pid for pair in pairs], fontsize=8, rotation=45, ha="right")
    _bucket_key(axes[-1])
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


def _draw_share_bar(ax: Axes, x: float, session: SessionArtefacts, phase: str) -> None:
    """Draw one session's stacked bucket shares for one phase.

    Args:
        ax: Axes to draw on.
        x: Centre x position.
        session: Session artefacts.
        phase: Phase key, ``planning`` or ``implementation``.
    """
    shares = _bucket_shares(session, phase)
    if shares is None:
        # The empty footprint marks a recorded absence rather than a bar that failed to render.
        ax.bar(
            x,
            1.0,
            width=SHARE_BAR_WIDTH,
            facecolor="none",
            edgecolor="#999999",
            linewidth=0.7,
            linestyle="--",
            zorder=2,
        )
        return
    bottom = 0.0
    for bucket in BUCKET_ORDER:
        height = shares[bucket]
        ax.bar(
            x,
            height,
            width=SHARE_BAR_WIDTH,
            bottom=bottom,
            facecolor=BUCKET_FILL[bucket],
            edgecolor="#000000",
            linewidth=0.7,
            zorder=2,
        )
        bottom += height


def _bucket_shares(session: SessionArtefacts, phase: str) -> dict[str, float] | None:
    """Return one session's bucket shares for a phase.

    Args:
        session: Session artefacts.
        phase: Phase key, ``planning`` or ``implementation``.

    Returns:
        The share of each bucket, or ``None`` where the phase carried no turn prompt.
    """
    if float(phase_scope(session, "data", phase)["turn_prompt_count"]) == 0:
        return None
    block = phase_scope(session, "metrics", phase)["turn_prompts_bucket_shares"]
    return {bucket: float(block[bucket]) for bucket in BUCKET_ORDER}


def _report_share_extremes(pairs: list[ParticipantPair], phase: str) -> None:
    """Print the reach of each framework's bucket shares in one phase.

    Args:
        pairs: Cohort participant pairs.
        phase: Phase key, ``planning`` or ``implementation``.
    """
    for framework in ("apm", "speckit"):
        drawn = [_bucket_shares(getattr(pair, framework), phase) for pair in pairs]
        for bucket in BUCKET_ORDER:
            values = [shares[bucket] for shares in drawn if shares is not None]
            report_extremes(f"{phase}/{framework}/{bucket}", values, precision=2)


def _bucket_key(ax: Axes) -> None:
    """Place a frameless bucket key below the lower panel."""
    handles = [
        Patch(
            facecolor=BUCKET_FILL[bucket],
            edgecolor="#000000",
            linewidth=0.7,
            label=BUCKET_LABELS[bucket],
        )
        for bucket in BUCKET_ORDER
    ]
    ax.legend(
        handles=handles,
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.22),
        ncol=len(BUCKET_ORDER),
        fontsize=8,
    )


if __name__ == "__main__":
    raise SystemExit(main())

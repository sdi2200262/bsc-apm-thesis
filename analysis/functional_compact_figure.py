#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate the compact-serialization diagnostic PDF figure."""

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
from analysis.style import CONTRAST_MARKER, FILLED, OPEN, apply_grid, new_figure


@dataclass(frozen=True)
class CompactSession:
    """One Sonnet session's standard and compact-serialization scores."""

    label: str
    standard: float
    compact: float


def main(argv: list[str] | None = None) -> int:
    """Run the compact-serialization figure generator.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code (0 on success, 1 on a config or data error).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path, help="common asset root")
    args = parser.parse_args(argv)
    try:
        pairs = pair_by_participant(load_sessions(load_records(args.config)))
        render(
            _sonnet_sessions(pairs),
            args.output_dir / "figures" / "discussions" / "functional_compact.pdf",
        )
    except (ConfigError, KeyError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


def render(sessions: list[CompactSession], output: Path) -> None:
    """Render the standard-to-compact score diagnostic.

    Args:
        sessions: Sonnet sessions in display order.
        output: Destination PDF path.
    """
    fig, ax = new_figure(width_in=6.8, height_in=4.0)
    xs = list(range(len(sessions)))
    for x, session in zip(xs, sessions, strict=True):
        if session.compact - session.standard > 0.01:
            ax.plot(
                [x, x],
                [session.standard, session.compact],
                color="#000000",
                linewidth=0.8,
                zorder=1,
            )
            ax.plot(
                x,
                session.compact,
                marker=CONTRAST_MARKER,
                markerfacecolor=OPEN,
                markeredgecolor="#000000",
                markersize=6,
                zorder=3,
            )
        ax.plot(
            x,
            session.standard,
            marker=CONTRAST_MARKER,
            markerfacecolor=FILLED,
            markeredgecolor="#000000",
            markersize=6,
            zorder=3,
        )
    ax.set_xticks(xs)
    ax.set_xticklabels(
        [session.label for session in sessions], fontsize=7.5, rotation=45, ha="right"
    )
    ax.set_xlim(-0.6, len(sessions) - 0.4)
    ax.set_ylabel("Total score (points)", fontsize=9)
    ax.set_ylim(0, 104)
    apply_grid(ax, axis="y")
    _form_key(ax)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def _sonnet_sessions(pairs: list[ParticipantPair]) -> list[CompactSession]:
    """Return the Sonnet sessions used by the diagnostic figure."""
    sessions: list[CompactSession] = []
    for pair in pairs:
        if model_band(pair.apm) != "sonnet":
            continue
        sessions.append(_compact_session(f"{pair.pid} APM", pair.apm))
        sessions.append(_compact_session(f"{pair.pid} SK", pair.speckit))
    return sessions


def _compact_session(label: str, session: SessionArtefacts) -> CompactSession:
    """Return standard and compact scores for one configured session.

    Args:
        label: Display label.
        session: Session artefacts.

    Returns:
        The plotted score pair.

    Raises:
        ValueError: If the config omits compact-serialization grader results.
    """
    if session.compact_grader_results is None:
        raise ValueError(
            f"{session.record.pid} {session.record.session} {session.record.framework}: "
            "missing compact_grader_results in config"
        )
    return CompactSession(
        label=label,
        standard=float(session.grader_results["scores"]["total"]),
        compact=float(session.compact_grader_results["scores"]["total"]),
    )


def _form_key(ax: Axes) -> None:
    """Place a frameless standard/compact marker key below the axes."""
    standard = Line2D(
        [],
        [],
        marker=CONTRAST_MARKER,
        linestyle="none",
        markerfacecolor=FILLED,
        markeredgecolor="#000000",
        markersize=6,
        label="Standard JSON total",
    )
    compact = Line2D(
        [],
        [],
        marker=CONTRAST_MARKER,
        linestyle="none",
        markerfacecolor=OPEN,
        markeredgecolor="#000000",
        markersize=6,
        label="Compact JSON total",
    )
    ax.legend(
        handles=[standard, compact],
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        fontsize=8,
    )


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate context-occupancy PDF figures from parser artefacts.

Renders three panels (pooled, Opus-only, Sonnet-only) from the ``context_segments[]``
field the parser writes per session. Each participant occupies one column carrying
every context-segment peak from both frameworks (APM solid circles, Spec-kit open
diamonds) bound by a faint stem, with reference lines for the nominal 200k Sonnet
context window and the ~167k auto-compaction ceiling it empirically reaches. The
visual register (Latin Modern serif, faint grid, black-ink markers) mirrors the
house style used by every other Evaluation-chapter figure in this thesis.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.transforms import Bbox

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
    SPECKIT_COLOR,
    SPECKIT_FACECOLOR,
    SPECKIT_LABEL,
    SPECKIT_MARKER,
    new_figure,
    report_extremes,
)

SONNET_WINDOW = 200_000
SONNET_CEILING = 167_000


def main(argv: list[str] | None = None) -> int:
    """Run the occupancy figure generator.

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
        opus_pairs = [pair for pair in pairs if model_band(pair.apm) == "opus"]
        sonnet_pairs = [pair for pair in pairs if model_band(pair.apm) == "sonnet"]
        render(pairs, args.output_dir / "occupancy_pooled.pdf", plot_w_in=6.07)
        render(
            opus_pairs,
            args.output_dir / "occupancy_opus.pdf",
            plot_w_in=5.87,
            show_window=False,
            show_ceiling=False,
        )
        render(sonnet_pairs, args.output_dir / "occupancy_sonnet.pdf", plot_w_in=5.87)
    except (ConfigError, KeyError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


def render(
    pairs: list[ParticipantPair],
    output: Path,
    *,
    plot_w_in: float,
    show_window: bool = True,
    show_ceiling: bool = True,
) -> None:
    """Render one paired occupancy panel and save it to ``output``.

    Each participant occupies one column carrying every context-segment peak from
    both frameworks (APM solid circles, Spec-kit open diamonds), bound by a faint
    stem so the values read as one cluster.

    Args:
        pairs: Participant pairs to plot, already filtered to the panel's cohort
            slice, in display order.
        output: Destination PDF path (parent directories created if absent).
        plot_w_in: Width of the plotting area (the Axes box) in inches; the two
            model-split panels share one value so their plot areas are pixel-identical.
        show_window: Whether to draw the 200k Sonnet context-window reference line.
        show_ceiling: Whether to draw the ~167k auto-compaction ceiling reference line.

    Raises:
        ValueError: If no participant pair has any context-segment peak.
    """
    columns = [(pair.pid, _segments(pair.apm), _segments(pair.speckit)) for pair in pairs]
    if not any(apm_peaks or speckit_peaks for _, apm_peaks, speckit_peaks in columns):
        raise ValueError("no context segment peaks to plot")

    panel = output.stem
    report_extremes(f"{panel} APM", [p for _, apm, _ in columns for p in apm], 0)
    report_extremes(f"{panel} Spec-kit", [p for _, _, speckit in columns for p in speckit], 0)

    plot_h_in = 3.2
    left_in, top_in, bottom_in, right_in = 0.55, 0.18, 0.82, 0.08
    fig_w = left_in + plot_w_in + right_in
    fig_h = top_in + plot_h_in + bottom_in
    fig, ax = _new_figure(fig_w, fig_h)

    step = 1.35  # column spacing: wider than 1 so each participant's markers stand clear
    xs = [i * step for i in range(len(columns))]
    for x, (_, apm_peaks, speckit_peaks) in zip(xs, columns, strict=True):
        all_peaks = apm_peaks + speckit_peaks
        if all_peaks:
            ax.plot(
                [x, x],
                [min(all_peaks) / 1000, max(all_peaks) / 1000],
                color="#000000",
                linewidth=0.6,
                alpha=0.3,
                zorder=1,
            )
        # Both frameworks share the participant's column; the marker form tells them apart.
        for peaks, marker, face in (
            (apm_peaks, APM_MARKER, APM_COLOR),
            (speckit_peaks, SPECKIT_MARKER, SPECKIT_FACECOLOR),
        ):
            ys = [peak / 1000 for peak in peaks]
            if ys:
                ax.plot(
                    [x] * len(ys),
                    ys,
                    linestyle="none",
                    marker=marker,
                    markersize=5.5,
                    markerfacecolor=face,
                    markeredgecolor="#000000",
                    markeredgewidth=0.9,
                    zorder=2,
                )

    if show_window:
        ax.axhline(
            SONNET_WINDOW / 1000, color="#000000", linewidth=0.8, alpha=0.5, linestyle=(0, (5, 3))
        )
    if show_ceiling:
        ax.axhline(
            SONNET_CEILING / 1000,
            color="#000000",
            linewidth=0.8,
            alpha=0.5,
            linestyle=(0, (1, 1.5)),
        )

    ax.set_xticks(xs)
    ax.set_xticklabels([pid.replace("P0", "P") for pid, _, _ in columns], fontsize=7.5)
    ax.set_ylabel("Peak context occupancy (thousand tokens)")
    ax.set_xlim(-step * 0.7, xs[-1] + step * 0.7)
    panel_max = max(
        peak for _, apm_peaks, speckit_peaks in columns for peak in apm_peaks + speckit_peaks
    )
    ax.set_ylim(0, max(panel_max, SONNET_WINDOW if show_window else 0) / 1000 * 1.08)
    ax.grid(True, axis="y", color="#cccccc", linewidth=0.5, linestyle="-", alpha=0.4)
    ax.set_axisbelow(True)

    apm_key = Line2D(
        [],
        [],
        marker=APM_MARKER,
        color=APM_COLOR,
        linewidth=0,
        markerfacecolor=APM_COLOR,
        markeredgecolor="#000000",
        markersize=5.5,
        label=APM_LABEL,
    )
    skt_key = Line2D(
        [],
        [],
        marker=SPECKIT_MARKER,
        color=SPECKIT_COLOR,
        linewidth=0,
        markerfacecolor=SPECKIT_FACECOLOR,
        markeredgecolor="#000000",
        markersize=5.5,
        label=SPECKIT_LABEL,
    )
    ax.legend(
        handles=[apm_key, skt_key],
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.13),
        ncol=2,
        fontsize=8,
    )

    # Place the axes from the inch margins, and save the full canvas (overriding the
    # rcParams tight bbox default for this call) so the plot area is exactly
    # plot_w_in by plot_h_in on every panel.
    ax.set_position((left_in / fig_w, bottom_in / fig_h, plot_w_in / fig_w, plot_h_in / fig_h))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches=Bbox([[0, 0], [fig_w, fig_h]]), pad_inches=0)
    plt.close(fig)


def _new_figure(width_in: float, height_in: float) -> tuple[Figure, Axes]:
    """Create a new Figure/Axes pair with the house rcParams already applied.

    Args:
        width_in: Figure width in inches.
        height_in: Figure height in inches.

    Returns:
        A (Figure, Axes) pair ready for data.
    """
    return new_figure(width_in, height_in)


def _segments(session: SessionArtefacts) -> list[int]:
    """Return context-segment peaks from one parser data artefact.

    Args:
        session: The session artefacts to read.

    Returns:
        The positive ``peak_context_tokens`` values from ``context_segments[]``.

    Raises:
        ValueError: If the session's parser data lacks ``context_segments[]``.
    """
    if "context_segments" not in session.parser_data:
        raise ValueError(
            f"{session.record.parser_data}: missing context_segments[]; re-run parser first"
        )
    return [
        int(segment["peak_context_tokens"])
        for segment in session.parser_data["context_segments"]
        if int(segment["peak_context_tokens"]) > 0
    ]


if __name__ == "__main__":
    raise SystemExit(main())

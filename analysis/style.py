# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Shared matplotlib style and reporting for thesis analysis figures."""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Literal, NoReturn

import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

_LM_DIR_ENV = "THESIS_LM_FONT_DIR"
_LM_FACES = (
    ("lmroman10-regular.otf", "normal", "normal"),
    ("lmroman10-italic.otf", "italic", "normal"),
    ("lmroman10-bold.otf", "normal", "bold"),
    ("lmroman10-bolditalic.otf", "italic", "bold"),
)
# A private family name, since the faces' own "Latin Modern Roman" is shared by
# every optical size a full TeX installation ships and matplotlib resolves a
# family to whichever tying face it scanned first.
_LM_FAMILY = "LM Roman 10 (thesis figures)"

APM_COLOR = "#000000"
APM_LABEL = "APM"
APM_MARKER = "o"

SPECKIT_COLOR = "#000000"
SPECKIT_FACECOLOR = "#ffffff"
SPECKIT_HATCH = "///"
SPECKIT_LABEL = "Spec-kit"
SPECKIT_MARKER = "D"

GRID_ALPHA = 0.4


def _fail(message: str) -> NoReturn:
    """Exit with one actionable stderr line.

    This runs at import, ahead of any script's own error handling, so it exits
    rather than unwinding a traceback through the caller.

    Args:
        message: The line to emit.

    Raises:
        SystemExit: Always, with status 1.
    """
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def _register_lm_fonts() -> str:
    """Register the ten-point Latin Modern faces the figures are set in.

    The faces are entered ahead of the scanned system fonts, so a host carrying
    the whole family cannot pull in another optical size.

    Returns:
        The family name to select in the rcParams.

    Raises:
        SystemExit: When ``THESIS_LM_FONT_DIR`` is unset, does not name a
            directory, or the directory lacks one of the four faces.
    """
    configured = os.environ.get(_LM_DIR_ENV)
    if not configured:
        _fail(
            f"{_LM_DIR_ENV} is unset; set it to the directory holding the Latin Modern "
            "OpenType faces (locate one with: kpsewhich lmroman10-regular.otf)"
        )
    directory = Path(configured)
    if not directory.is_dir():
        _fail(f"{_LM_DIR_ENV} does not name a directory: {directory}")
    for face, style, weight in _LM_FACES:
        path = directory / face
        if not path.is_file():
            _fail(f"{_LM_DIR_ENV} directory is missing {face}: {directory}")
        fm.fontManager.ttflist.insert(
            0, fm.FontEntry(fname=str(path), name=_LM_FAMILY, style=style, weight=weight)
        )
    return _LM_FAMILY


_SERIF_FAMILY = _register_lm_fonts()

mpl.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": [_SERIF_FAMILY],
        "font.size": 10,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.grid": True,
        "grid.color": "#cccccc",
        "grid.linewidth": 0.5,
        "grid.linestyle": "-",
        "axes.axisbelow": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#333333",
        "axes.labelcolor": "#000000",
        "xtick.color": "#333333",
        "ytick.color": "#333333",
        "text.color": "#000000",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
    }
)


def new_figure(width_in: float, height_in: float) -> tuple[Figure, Axes]:
    """Create a matplotlib figure with one axes.

    Args:
        width_in: Figure width in inches.
        height_in: Figure height in inches.

    Returns:
        A ``(Figure, Axes)`` pair.
    """
    return plt.subplots(figsize=(width_in, height_in))


def apply_grid(ax: Axes, axis: Literal["both", "x", "y"] = "both") -> None:
    """Apply the shared faint grid to an axes.

    Args:
        ax: Axes to update.
        axis: Axis or axes that should carry the grid.
    """
    ax.grid(True, axis=axis, color="#cccccc", linewidth=0.5, linestyle="-", alpha=GRID_ALPHA)
    ax.set_axisbelow(True)


def report_extremes(series: str, values: Sequence[float], precision: int) -> None:
    """Print the smallest and largest value of one plotted series.

    A data plot shows how far its values reach, and prose that states that reach
    needs the numbers behind it. The plot is the reader's evidence; this is where
    the writer's numbers come from, so a range in prose is never measured off a
    rendered figure. Every figure module calls this for each series and panel it
    draws, whether or not prose currently names a value.

    Args:
        series: Identifier of the panel and series, as the figure draws it.
        values: The values plotted for that series.
        precision: Decimal places, matching the dimension's table precision so a
            prose value and its table read the same.

    Raises:
        ValueError: If ``values`` is empty, since an empty series has no reach
            and a figure module asking for one has drawn nothing.
    """
    if not values:
        raise ValueError(f"no values plotted for series {series}")
    low = f"{min(values):.{precision}f}"
    high = f"{max(values):.{precision}f}"
    print(f"{series}: min={low} max={high} n={len(values)}")


def label_axis_end_right(
    ax: Axes,
    y_data: float,
    text: str,
    *,
    va: str = "center",
    offset_pts: float = 6.0,
    italic: bool = False,
    fontsize: float | None = None,
) -> None:
    """Place a label just outside the right edge of an axes.

    Args:
        ax: Axes on which to place the label.
        y_data: Data-coordinate y value.
        text: Label text.
        va: Vertical alignment.
        offset_pts: Horizontal offset from the axes edge, in points.
        italic: Whether to render the label in italic.
        fontsize: Optional font size override.
    """
    ax.annotate(
        text,
        xy=(1.0, y_data),
        xycoords=("axes fraction", "data"),
        xytext=(offset_pts, 0),
        textcoords="offset points",
        ha="left",
        va=va,
        fontstyle="italic" if italic else "normal",
        fontsize=fontsize,
        annotation_clip=False,
    )

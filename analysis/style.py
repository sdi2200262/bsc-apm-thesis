# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Shared matplotlib style for thesis analysis figures."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

_LM_OTF_DIR = Path("/usr/local/texlive/2025/texmf-dist/fonts/opentype/public/lm")
_LM_FACES = (
    "lmroman10-regular.otf",
    "lmroman10-italic.otf",
    "lmroman10-bold.otf",
    "lmroman10-bolditalic.otf",
)
_LM_FAMILY = "Latin Modern Roman"

APM_COLOR = "#000000"
APM_LABEL = "APM"
APM_MARKER = "o"

SPECKIT_COLOR = "#000000"
SPECKIT_FACECOLOR = "#ffffff"
SPECKIT_HATCH = "///"
SPECKIT_LABEL = "Spec-kit"
SPECKIT_MARKER = "D"

GRID_ALPHA = 0.4


def _register_lm_fonts() -> str:
    """Register TeX Latin Modern faces when available.

    Returns:
        The preferred serif family for matplotlib rcParams.
    """
    if not _LM_OTF_DIR.is_dir():
        return "DejaVu Serif"
    for face in _LM_FACES:
        path = _LM_OTF_DIR / face
        if not path.is_file():
            return "DejaVu Serif"
        fm.fontManager.addfont(str(path))
    return _LM_FAMILY


_SERIF_FAMILY = _register_lm_fonts()

mpl.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": [_SERIF_FAMILY, "DejaVu Serif"],
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

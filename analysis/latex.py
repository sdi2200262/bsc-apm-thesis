# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""LaTeX row formatting helpers."""

from __future__ import annotations

from pathlib import Path

from .stats import LevelSummary, PairedSummary


def money(value: float) -> str:
    """Format a dollar value for a table cell."""
    return f"${signed(value, 2)}$" if value < 0 else f"${value:.2f}$"


def number(value: float, digits: int = 1, signed_value: bool = False) -> str:
    """Format a plain numeric value for a table cell."""
    text = signed(value, digits) if signed_value else f"{value:.{digits}f}"
    return f"${text}$"


def signed(value: float, digits: int = 1) -> str:
    """Format ``value`` with an explicit sign."""
    return f"{value:+.{digits}f}"


def percent(value: float, digits: int = 1) -> str:
    """Format a proportion as a percent."""
    return f"{100 * value:.{digits}f}\\%"


def level_row(label_cells: list[str], summary: LevelSummary, digits: int = 1) -> str:
    """Return one level-summary LaTeX row."""
    cells = [
        *label_cells,
        number(summary.median, digits),
        number(summary.hl, digits),
        number(summary.mean, digits),
    ]
    return " & ".join(cells) + r" \\"


def paired_row(
    label_cells: list[str],
    summary: PairedSummary,
    digits: int = 1,
    include_zero: bool = False,
) -> str:
    """Return one paired-summary LaTeX row."""
    sign = (
        f"{summary.positive} / {summary.negative} / {summary.zero}"
        if include_zero
        else f"{summary.positive} / {summary.negative}"
    )
    ci = f"$[{signed(summary.ci_low, digits)}, {signed(summary.ci_high, digits)}]$"
    cells = [
        *label_cells,
        str(summary.n),
        sign,
        number(summary.median, digits, signed_value=True),
        number(summary.hl, digits, signed_value=True),
        number(summary.mean, digits, signed_value=True),
        ci,
    ]
    return " & ".join(cells) + r" \\"


def write_fragment(path: Path, rows: list[str]) -> None:
    """Write a LaTeX row fragment to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")

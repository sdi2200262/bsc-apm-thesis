#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate LaTeX row fragments for perception result tables."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.config import ConfigError, InputRecord, load_records
from analysis.latex import write_fragment

# Item order follows the questionnaire, so a table row sits where the participant met it.
ITEMS: tuple[tuple[str, str, str], ...] = (
    ("Familiarity", "context", "How familiar were you with this framework before this study?"),
    ("Confidence", "higher", "How confident are you in your submitted solution?"),
    (
        "Effectiveness",
        "higher",
        "How effective was the framework in helping you complete the task?",
    ),
    ("Mental demand", "lower", "How mentally demanding was the session?"),
    ("Frustration", "lower", "How frustrated did you feel during the session?"),
    ("Effort", "lower", "How much effort did you have to invest?"),
    (
        "Verification effort",
        "lower",
        "How much effort went into checking what the AI in this framework produced?",
    ),
    (
        "Steering effort",
        "lower",
        "How much effort went into instructing and steering the AI in this framework?",
    ),
)
COMPARATIVE_COLUMN = (
    "Compared to the framework you used in your first session, completing the task with this "
    "framework felt..."
)
COMPARATIVE_VALUES = ("Much harder", "Harder", "About the same", "Easier", "Much easier")
COMPLETION_COLUMN = "Completion state"
COMPLETION_VALUES = (
    "Completed the task comfortably within the three-hour cap",
    "Completed the task near the three-hour cap",
    "Hit the three-hour cap without completing",
    "Stopped early without completing",
)


@dataclass(frozen=True)
class QuestionnaireRow:
    """One parsed questionnaire response."""

    pid: str
    framework: str
    session_number: str
    comparative: str
    completion: str
    values: dict[str, int]


def main(argv: list[str] | None = None) -> int:
    """Run the perception table generator."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path, help="common asset root")
    args = parser.parse_args(argv)
    try:
        records = load_records(args.config)
        csv_paths = {record.questionnaire_csv for record in records if record.questionnaire_csv}
        if len(csv_paths) != 1:
            raise ConfigError("perception config must point every record at one questionnaire_csv")
        rows = _read_questionnaire(next(iter(csv_paths)))
        output_dir = args.output_dir / "tables"
        write_fragment(output_dir / "perc-ratings-paired.tex", _rating_direction_rows(rows))
        write_fragment(
            output_dir / "perc-ratings-distribution.tex", _rating_distribution_rows(rows)
        )
        write_fragment(output_dir / "perc-completion-state.tex", _completion_state_rows(rows))
        write_fragment(
            output_dir / "perc-comparative-distribution.tex",
            _comparative_distribution_rows(rows, records),
        )
    except (ConfigError, OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


def _read_questionnaire(path: Path) -> list[QuestionnaireRow]:
    """Read questionnaire responses from ``path``."""
    rows: list[QuestionnaireRow] = []
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        for raw in reader:
            framework = _framework(raw["Framework used in this session"])
            values = {label: _rating(raw[column]) for label, _better, column in ITEMS}
            rows.append(
                QuestionnaireRow(
                    pid=raw["Participant ID"],
                    framework=framework,
                    session_number=raw["Session number"],
                    comparative=raw[COMPARATIVE_COLUMN],
                    completion=raw[COMPLETION_COLUMN],
                    values=values,
                )
            )
    return rows


def _rating_direction_rows(rows: list[QuestionnaireRow]) -> list[str]:
    """Return paired direction rows for the eight rating items."""
    by_pid = _by_pid(rows)
    out: list[str] = []
    for label, better, _column in ITEMS:
        positive = negative = equal = 0
        for pair in by_pid.values():
            diff = pair["apm"].values[label] - pair["speckit"].values[label]
            positive += diff > 0
            negative += diff < 0
            equal += diff == 0
        out.append(f"{label} & {better} & {positive} / {negative} / {equal} \\\\")
    return out


def _rating_distribution_rows(rows: list[QuestionnaireRow]) -> list[str]:
    """Return per-framework rating distribution rows."""
    out: list[str] = []
    for label, _better, _column in ITEMS:
        if out:
            out.append(r"\midrule")
        for framework in ("apm", "speckit"):
            counts = [0, 0, 0, 0, 0]
            for row in rows:
                if row.framework == framework:
                    counts[row.values[label] - 1] += 1
            label_cell = label if framework == "apm" else ""
            out.append(
                f"{label_cell} & {'APM' if framework == 'apm' else 'Spec-kit'} & "
                + " & ".join(str(count) for count in counts)
                + r" \\"
            )
    return out


def _completion_state_rows(rows: list[QuestionnaireRow]) -> list[str]:
    """Return per-framework completion-state counts against the session cap.

    Args:
        rows: Parsed questionnaire responses.

    Returns:
        One LaTeX row per framework, counting the sessions in each state.

    Raises:
        ValueError: When a response records a state the instrument does not offer.
    """
    out: list[str] = []
    for framework, label in (("apm", "APM"), ("speckit", "Spec-kit")):
        counts = [0] * len(COMPLETION_VALUES)
        for row in rows:
            if row.framework != framework:
                continue
            if row.completion not in COMPLETION_VALUES:
                raise ValueError(f"unrecognised completion state: {row.completion}")
            counts[COMPLETION_VALUES.index(row.completion)] += 1
        out.append(f"{label} & " + " & ".join(str(count) for count in counts) + r" \\")
    return out


def _by_pid(rows: list[QuestionnaireRow]) -> dict[str, dict[str, QuestionnaireRow]]:
    """Group questionnaire rows by participant and framework."""
    grouped: dict[str, dict[str, QuestionnaireRow]] = {}
    for row in rows:
        grouped.setdefault(row.pid, {})[row.framework] = row
    for pid, pair in grouped.items():
        if set(pair) != {"apm", "speckit"}:
            raise ValueError(f"{pid}: expected one apm and one speckit questionnaire response")
    return grouped


def _comparative_distribution_rows(
    rows: list[QuestionnaireRow], records: list[InputRecord]
) -> list[str]:
    """Return comparison-question response counts by realized second framework."""
    record_sessions = {(record.pid, record.framework): record.session for record in records}
    out: list[str] = []
    for framework in ("apm", "speckit"):
        counts = {value: 0 for value in COMPARATIVE_VALUES}
        for row in rows:
            if row.framework != framework:
                continue
            if record_sessions[(row.pid, row.framework)] != "S2":
                continue
            if row.session_number != "Second Session" or not row.comparative:
                continue
            if row.comparative not in counts:
                raise ValueError(f"unknown comparative value {row.comparative!r}")
            counts[row.comparative] += 1
        label = r"APM\tnote{a}" if framework == "apm" else "Spec-kit"
        out.append(
            f"{label} & " + " & ".join(str(counts[value]) for value in COMPARATIVE_VALUES) + r" \\"
        )
    return out


def _framework(value: str) -> str:
    """Normalise the questionnaire framework label."""
    if value.startswith("APM"):
        return "apm"
    if value.startswith("Spec-kit") or value.startswith("GitHub Spec-kit"):
        return "speckit"
    raise ValueError(f"unknown questionnaire framework {value!r}")


def _rating(value: str) -> int:
    """Parse a one-to-five rating cell."""
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"invalid rating {value!r}") from error
    if parsed < 1 or parsed > 5:
        raise ValueError(f"rating out of range: {parsed}")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())

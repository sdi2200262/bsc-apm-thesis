# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Load explicit thesis analysis input configs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FRAMEWORKS = {"apm", "speckit"}
SESSIONS = {"S1", "S2"}


class ConfigError(RuntimeError):
    """Raised when an analysis config is malformed or inconsistent."""


@dataclass(frozen=True)
class InputRecord:
    """One configured session input record.

    Attributes:
        pid: Participant id, e.g. ``P001``.
        session: Session label, ``S1`` or ``S2``.
        framework: Framework label, ``apm`` or ``speckit``.
        parser_data: Path to ``parser_data.json``.
        parser_metrics: Path to ``parser_metrics.json``.
        grader_results: Path to ``grader_results.json``.
        compact_grader_results: Optional compact-serialization grader results path.
        questionnaire_csv: Optional questionnaire CSV path for perception outputs.
    """

    pid: str
    session: str
    framework: str
    parser_data: Path
    parser_metrics: Path
    grader_results: Path
    compact_grader_results: Path | None = None
    questionnaire_csv: Path | None = None


def load_records(config_path: Path) -> list[InputRecord]:
    """Load and validate input records from ``config_path``.

    Relative artefact paths are resolved against the config file's directory.

    Args:
        config_path: JSON config path.

    Returns:
        The configured input records.

    Raises:
        ConfigError: When the config is malformed or points at inconsistent artefacts.
    """
    path = config_path.resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ConfigError(f"cannot read config {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"invalid JSON in config {path}: {error}") from error
    raw_records = payload.get("records")
    if not isinstance(raw_records, list) or not raw_records:
        raise ConfigError(f"{path}: expected non-empty records array")
    base = path.parent
    records = [
        _record_from_payload(item, base, path, index) for index, item in enumerate(raw_records)
    ]
    _validate_pairs(records, path)
    for record in records:
        _validate_metadata(record)
    return records


def _record_from_payload(
    item: Any,
    base: Path,
    config_path: Path,
    index: int,
) -> InputRecord:
    """Build one :class:`InputRecord` from a JSON object."""
    if not isinstance(item, dict):
        raise ConfigError(f"{config_path}: records[{index}] must be an object")
    pid = _required_str(item, "pid", config_path, index)
    session = _required_str(item, "session", config_path, index)
    framework = _required_str(item, "framework", config_path, index)
    if session not in SESSIONS:
        raise ConfigError(f"{config_path}: records[{index}].session must be S1 or S2")
    if framework not in FRAMEWORKS:
        raise ConfigError(f"{config_path}: records[{index}].framework must be apm or speckit")
    compact_grader = item.get("compact_grader_results")
    questionnaire = item.get("questionnaire_csv")
    return InputRecord(
        pid=pid,
        session=session,
        framework=framework,
        parser_data=_resolve_existing(base, item, "parser_data", config_path, index),
        parser_metrics=_resolve_existing(base, item, "parser_metrics", config_path, index),
        grader_results=_resolve_existing(base, item, "grader_results", config_path, index),
        compact_grader_results=(
            _resolve_existing(base, item, "compact_grader_results", config_path, index)
            if compact_grader is not None
            else None
        ),
        questionnaire_csv=(
            _resolve_existing(base, item, "questionnaire_csv", config_path, index)
            if questionnaire is not None
            else None
        ),
    )


def _required_str(item: dict[str, Any], key: str, config_path: Path, index: int) -> str:
    """Return one required string field."""
    value = item.get(key)
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{config_path}: records[{index}].{key} must be a non-empty string")
    return value


def _resolve_existing(
    base: Path,
    item: dict[str, Any],
    key: str,
    config_path: Path,
    index: int,
) -> Path:
    """Resolve one required path field relative to ``base``."""
    raw = _required_str(item, key, config_path, index)
    path = Path(raw)
    if not path.is_absolute():
        path = base / path
    path = path.resolve()
    if not path.is_file():
        raise ConfigError(f"{config_path}: records[{index}].{key} not found: {path}")
    return path


def _validate_pairs(records: list[InputRecord], config_path: Path) -> None:
    """Validate that each participant has one APM and one Spec-kit record."""
    by_pid: dict[str, set[str]] = {}
    for record in records:
        by_pid.setdefault(record.pid, set()).add(record.framework)
    bad = {pid: frameworks for pid, frameworks in by_pid.items() if frameworks != FRAMEWORKS}
    if bad:
        raise ConfigError(
            f"{config_path}: each pid must have one apm and one speckit record: {bad}"
        )


def _validate_metadata(record: InputRecord) -> None:
    """Check configured metadata against parser artefacts."""
    parser_data = _read_json(record.parser_data)
    parser_metrics = _read_json(record.parser_metrics)
    data_framework = parser_data.get("metadata", {}).get("framework")
    metrics_framework = parser_metrics.get("metadata", {}).get("framework")
    if data_framework != record.framework:
        raise ConfigError(f"{record.parser_data}: metadata.framework is {data_framework!r}")
    if metrics_framework != record.framework:
        raise ConfigError(f"{record.parser_metrics}: metadata.framework is {metrics_framework!r}")


def _read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from ``path``."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigError(f"cannot read JSON artefact {path}: {error}") from error
    if not isinstance(payload, dict):
        raise ConfigError(f"{path}: top-level JSON value must be an object")
    return payload

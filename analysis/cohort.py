# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Cohort loading utilities for thesis analysis scripts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import InputRecord


@dataclass(frozen=True)
class SessionArtefacts:
    """Loaded artefacts for one configured session."""

    record: InputRecord
    parser_data: dict[str, Any]
    parser_metrics: dict[str, Any]
    grader_results: dict[str, Any]


@dataclass(frozen=True)
class ParticipantPair:
    """A participant's paired APM and Spec-kit sessions."""

    pid: str
    apm: SessionArtefacts
    speckit: SessionArtefacts


def load_sessions(records: list[InputRecord]) -> list[SessionArtefacts]:
    """Load every configured session artefact."""
    return [
        SessionArtefacts(
            record=record,
            parser_data=_read_json(record.parser_data),
            parser_metrics=_read_json(record.parser_metrics),
            grader_results=_read_json(record.grader_results),
        )
        for record in records
    ]


def pair_by_participant(sessions: list[SessionArtefacts]) -> list[ParticipantPair]:
    """Return participant pairs in PID order."""
    grouped: dict[str, dict[str, SessionArtefacts]] = {}
    for session in sessions:
        grouped.setdefault(session.record.pid, {})[session.record.framework] = session
    pairs: list[ParticipantPair] = []
    for pid in sorted(grouped):
        frameworks = grouped[pid]
        pairs.append(ParticipantPair(pid=pid, apm=frameworks["apm"], speckit=frameworks["speckit"]))
    return pairs


def model_band(session: SessionArtefacts) -> str:
    """Return ``opus`` or ``sonnet`` from the parser model distribution."""
    distribution = session.parser_data["scopes"]["session"]["model_token_distribution"]
    study = {k: v for k, v in distribution.items() if "opus" in k or "sonnet" in k}
    if not study:
        return "unknown"
    model = max(study, key=lambda key: study[key])
    return "opus" if "opus" in model else "sonnet"


def order_label(pair: ParticipantPair) -> str:
    """Return whether APM was first or second for ``pair``."""
    return "APM first" if pair.apm.record.session == "S1" else "APM second"


def session_scope(session: SessionArtefacts, source: str) -> dict[str, Any]:
    """Return a session-scope block from parser data or metrics."""
    artefact = session.parser_data if source == "data" else session.parser_metrics
    return artefact["scopes"]["session"]


def phase_scope(session: SessionArtefacts, source: str, phase: str) -> dict[str, Any]:
    """Return one phase-scope block from parser data or metrics."""
    artefact = session.parser_data if source == "data" else session.parser_metrics
    return artefact["scopes"]["phases"][phase]


def role_scopes(session: SessionArtefacts, source: str) -> dict[str, dict[str, Any]]:
    """Return role-scope blocks keyed by role for an APM session."""
    artefact = session.parser_data if source == "data" else session.parser_metrics
    return artefact["scopes"].get("roles", {})


def _read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from ``path``."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return payload

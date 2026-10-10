#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Generate draw.io concept diagrams and export cropped thesis PDF figures.

This script programmatically generates the draw.io XML definitions for the thesis
concept diagrams under ``diagrams/framework-design/``, using Lucide icon assets and
clean orthogonal routing. It then exports cropped vector PDFs into
``assets/figures/framework-design/`` via the ``drawio`` CLI.

Usage:
    python3 diagrams/build.py
    python3 diagrams/build.py --drawio-only
    python3 diagrams/build.py --figures message-bus state-compression
"""

from __future__ import annotations

import argparse
import base64
import html
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = REPO_ROOT / "diagrams" / "framework-design" / "icons" / "lucide"
DEFAULT_DRAWIO_DIR = REPO_ROOT / "diagrams" / "framework-design"
DEFAULT_PDF_DIR = REPO_ROOT / "assets" / "figures" / "framework-design"

THEMES: dict[str, dict[str, str]] = {
    "mono": {"ink": "#000000", "paper": "#ffffff"},
    "gruvbox-light": {"ink": "#3C3836", "paper": "#FBF1C7"},
    "gruvbox-dark": {"ink": "#EBDBB2", "paper": "#282828"},
}
FADE = "opacity=20;textOpacity=20;"


def thin(svg: str, size: float) -> str:
    """Adjust Lucide icon stroke-width for balanced visual weight with 1px edges."""
    return re.sub(
        r'stroke-width="[^"]*"', f'stroke-width="{36 / size:.3g}"', svg, count=1
    )


class DrawioWriter:
    """Minimal programmatic draw.io XML generator.

    Coordinates represent cell centres; draw.io routes orthogonal edges between cells.
    """

    def __init__(
        self,
        width: int,
        height: int,
        theme: dict[str, str],
        font_size: int,
        icon_size: int = 30,
        font_family: str = "Helvetica",
    ) -> None:
        self.cells: list[str] = []
        self.counter = 2
        self.width = width
        self.height = height
        self.theme = theme
        self.icon_size = icon_size
        self.font_family = font_family
        self.base_style = (
            f"fontFamily={font_family};fontSize={font_size};"
            f"fontColor={theme['ink']};strokeColor={theme['ink']};"
        )

    def next_id(self) -> str:
        self.counter += 1
        return f"c{self.counter}"

    def add(self, label: str, style: str, geometry: str, **attrs: str | int) -> str:
        cid = self.next_id()
        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        escaped_label = html.escape(label).replace("\n", "&#xa;")
        self.cells.append(
            f'<mxCell id="{cid}" value="{escaped_label}" '
            f'style="{self.base_style}{style}" {attr_str} parent="1">{geometry}</mxCell>'
        )
        return cid

    def icon(
        self, name: str, x: float, y: float, label: str, fade: bool = False
    ) -> str:
        size = self.icon_size
        icon_path = ICONS_DIR / f"{name}.svg"
        if not icon_path.exists():
            raise FileNotFoundError(f"Icon not found: {icon_path}")
        raw_svg = icon_path.read_text(encoding="utf-8").replace(
            "currentColor", self.theme["ink"]
        )
        svg_content = thin(raw_svg, size)
        b64_img = base64.b64encode(svg_content.encode("utf-8")).decode("ascii")
        style = (
            "shape=image;verticalLabelPosition=bottom;verticalAlign=top;"
            f"imageAspect=0;image=data:image/svg+xml,{b64_img};"
            + (FADE if fade else "")
        )
        geometry = (
            f'<mxGeometry x="{x - size / 2}" y="{y - size / 2}" '
            f'width="{size}" height="{size}" as="geometry"/>'
        )
        return self.add(label, style, geometry, vertex=1)

    def text(
        self,
        x: float,
        y: float,
        width: float,
        label: str,
        fade: bool = False,
        italic: bool = True,
    ) -> str:
        font_style = 2 if italic else 0
        style = (
            f"text;html=0;align=center;verticalAlign=middle;fontStyle={font_style};"
            + (FADE if fade else "")
        )
        geometry = (
            f'<mxGeometry x="{x - width / 2}" y="{y - 10}" '
            f'width="{width}" height="20" as="geometry"/>'
        )
        return self.add(label, style, geometry, vertex=1)

    def shape(
        self, kind: str, x: float, y: float, width: float, height: float, label: str
    ) -> str:
        if kind not in ("rhombus", "ellipse"):
            raise ValueError(f"Unsupported shape: {kind}")
        style = f"{kind};html=0;align=center;verticalAlign=middle;fillColor=none;"
        geometry = (
            f'<mxGeometry x="{x - width / 2}" y="{y - height / 2}" '
            f'width="{width}" height="{height}" as="geometry"/>'
        )
        return self.add(label, style, geometry, vertex=1)

    def point(self, x: float, y: float) -> str:
        return self.add(
            "",
            "text;html=0;",
            f'<mxGeometry x="{x}" y="{y}" width="0" height="0" as="geometry"/>',
            vertex=1,
        )

    def edge(
        self,
        source: str,
        target: str,
        ex: tuple[float, float] | None = None,
        en: tuple[float, float] | None = None,
        line: bool = False,
        dashed: bool = False,
        both: bool = False,
        fade: bool = False,
        wp: Sequence[tuple[float, float]] = (),
    ) -> str:
        style = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;endSize=5;startSize=5;"
        if ex:
            style += f"exitX={ex[0]};exitY={ex[1]};exitDx=0;exitDy=0;"
        if en:
            style += f"entryX={en[0]};entryY={en[1]};entryDx=0;entryDy=0;"
        if dashed:
            style += "dashed=1;dashPattern=8 8;"
        if line:
            style += "endArrow=none;"
        if both:
            style += "startArrow=classic;startFill=1;"
        if fade:
            style += FADE
        pts = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in wp)
        geometry = (
            '<mxGeometry relative="1" as="geometry">'
            + (f'<Array as="points">{pts}</Array>' if pts else "")
            + "</mxGeometry>"
        )
        return self.add("", style, geometry, edge=1, source=source, target=target)

    def xml(self) -> str:
        return (
            f'<mxfile><diagram name="p" id="p">'
            f'<mxGraphModel pageWidth="{self.width}" pageHeight="{self.height}">'
            '<root><mxCell id="0"/><mxCell id="1" parent="0"/>'
            + "".join(self.cells)
            + "</root></mxGraphModel></diagram></mxfile>"
        )


def note(
    writer: DrawioWriter, x: float, y: float, label: str, width: float = 120
) -> str:
    return writer.text(x, y, width, label, italic=False)


def planning_phase_overview(
    theme: dict[str, str], font_family: str = "Helvetica"
) -> DrawioWriter:
    d = DrawioWriter(720, 420, theme, font_size=9, font_family=font_family)
    lb = 38
    s_col, initiate_col, g_col, u_col, p_col, a_col = 45, 165, 285, 405, 525, 675
    lane, write_col, review_col, check_col, end_col = 45, 165, 320, 470, 610
    top_row, mid_row, lower_row, file_row = 80, 160, 255, 365
    loop1_y, loop2_y = 22, 205

    start = d.shape("ellipse", s_col, top_row, 54, 54, "Project\nbegins")
    initiate = d.icon("user", initiate_col, top_row, "User initiates\nPlanner")
    gather = d.icon(
        "bot", g_col, top_row, "Planner gathers\ncontext and elicits\nrequirements"
    )
    requirements = d.icon("user", u_col, top_row, "User articulates\nrequirements")
    propose = d.icon(
        "bot", p_col, top_row, "Planner consolidates\nand proposes\napproaches"
    )
    aligned = d.shape("rhombus", a_col, top_row, 64, 50, "Aligned?")
    write = d.icon("bot", write_col, lower_row, "Planner creates\nplanning documents")
    review = d.icon("user", review_col, lower_row, "User reviews\nfor completeness")
    checked = d.shape("rhombus", check_col, lower_row, 64, 50, "Aligned?")
    done = d.shape("ellipse", end_col, lower_row, 60, 60, "Planning\ncomplete")
    specs = d.icon("file-cog", write_col, file_row, "Spec, Plan, Rules")

    for src, dst in (
        (start, initiate),
        (initiate, gather),
        (gather, requirements),
    ):
        d.edge(src, dst, (1, 0.5), (0, 0.5))
    d.edge(requirements, propose, (1, 0.25), (0, 0.25))
    d.edge(propose, requirements, (0, 0.75), (1, 0.75))
    d.edge(propose, aligned, (1, 0.5), (0, 0.5))
    note(d, (p_col + 15 + a_col - 32) / 2, top_row - 22, "Presents\nunderstanding", 90)
    d.edge(
        aligned,
        requirements,
        (0.5, 0),
        (0.5, 0),
        wp=[(a_col, loop1_y), (u_col, loop1_y)],
    )
    note(d, (u_col + a_col) / 2, loop1_y - 10, "No, understanding gap: clarify", 170)
    d.edge(
        aligned,
        write,
        (0.5, 1),
        (0, 0.5),
        wp=[(a_col, mid_row), (lane, mid_row), (lane, lower_row)],
    )
    note(d, a_col + 14, top_row + 34, "Yes", 30)

    d.edge(write, review, (1, 0.5), (0, 0.5))
    d.edge(review, checked, (1, 0.5), (0, 0.5))
    d.edge(
        checked,
        write,
        (0.5, 0),
        (0.5, 0),
        wp=[(check_col, loop2_y), (write_col, loop2_y)],
    )
    note(
        d, (write_col + check_col) / 2, loop2_y - 10, "No, document issue: revise", 170
    )
    d.edge(checked, done, (1, 0.5), (0, 0.5))
    note(d, (check_col + 32 + end_col - 30) / 2, lower_row - 12, "Yes", 30)
    d.edge(
        d.point(write_col, lower_row + lb + 6),
        specs,
        en=(0.5, 0),
        line=True,
        dashed=True,
    )
    return d


def implementation_phase_overview(
    theme: dict[str, str], font_family: str = "Helvetica"
) -> DrawioWriter:
    d = DrawioWriter(770, 920, theme, font_size=9, font_family=font_family)
    l_col, m_col, r_col, e_col = 100, 380, 535, 630
    loop_x, lane_x = 742, 58
    tr_col, pl_col = m_col - 120, m_col + 120
    init_y, assign_y, work_y, report_y = 100, 290, 545, 790
    doc_y, state_y, loop1_y = 460, 665, 205
    s_offset = 9

    start = d.shape("ellipse", 48 + s_offset, init_y, 86, 86, "Implementation\nbegins")
    initiate_manager = d.icon("user", 148 + s_offset, init_y, "User initiates\nManager")
    review_plan = d.icon(
        "bot", 255 + s_offset, init_y, "Manager reviews\nplanning documents"
    )
    first_aligned = d.shape("rhombus", m_col + s_offset, init_y, 64, 58, "Aligned?")
    update = d.icon(
        "bot",
        m_col,
        assign_y,
        "Manager updates Tracker,\nmaintains planning documents\nand writes assignments",
    )
    new_worker = d.shape("rhombus", r_col, assign_y, 74, 58, "New Worker?")
    initiate_worker = d.icon("user", r_col, loop1_y, "")
    note(d, r_col, loop1_y - 29, "User initiates\nnew Worker", 100)
    notify_workers = d.icon("user", e_col, assign_y, "User notifies\nWorkers")
    tracker = d.icon("file-chart-column-increasing", tr_col, doc_y, "Tracker")
    plan = d.icon("file-cog", pl_col, doc_y, "Spec, Plan, Rules")
    second_aligned = d.shape("rhombus", l_col, assign_y, 64, 58, "Aligned?")
    complete = d.shape("ellipse", lane_x, 420, 64, 64, "Project\ncomplete")
    review_logs = d.icon("bot", l_col, work_y, "Manager reviews\nlogs and reports")
    bus = d.icon("inbox", m_col, work_y, "Message Bus")
    read_assignments = d.icon(
        "bot", e_col, work_y, "Workers read and\nexecute assignments"
    )
    memory = d.icon("folder-tree", tr_col, state_y, "Memory")
    deliverables = d.icon("boxes", pl_col, state_y, "Deliverables")
    notify_manager = d.icon("user", l_col, report_y, "User notifies\nManager")
    write_reports = d.icon("bot", m_col, report_y, "Workers write\nlogs and reports")
    success = d.shape("rhombus", e_col, report_y, 72, 58, "Success?")

    d.edge(start, initiate_manager, (1, 0.5), (0, 0.5))
    d.edge(initiate_manager, review_plan, (1, 0.5), (0, 0.5))
    d.edge(review_plan, first_aligned, (1, 0.5), (0, 0.5))
    note(
        d,
        (255 + 15 + m_col - 32) / 2 + s_offset,
        init_y - 27,
        "Presents\nunderstanding",
        112,
    )
    d.edge(
        first_aligned,
        review_plan,
        (0.5, 0),
        (0.5, 0),
        wp=[(m_col + s_offset, 35), (255 + s_offset, 35)],
    )
    note(d, (255 + m_col) / 2 + s_offset, 26, "No, understanding gap: clarify", 180)
    d.edge(first_aligned, update, (0.5, 1), (0.8, 0))
    note(d, m_col + s_offset + 16, 160, "Yes", 30)

    d.edge(update, new_worker, (1, 0.5), (0, 0.5))
    d.edge(new_worker, initiate_worker, (0.5, 0), (0.5, 1))
    note(d, r_col + 16, assign_y - 49, "Yes", 30)
    d.edge(new_worker, notify_workers, (1, 0.5), (0, 0.5))
    note(d, (r_col + 37 + e_col - 15) / 2, assign_y - 13, "No", 30)
    d.edge(initiate_worker, notify_workers, (1, 0.5), (0.5, 0), wp=[(e_col, loop1_y)])
    d.edge(d.point(e_col, assign_y + 50), read_assignments, en=(0.5, 0))

    d.edge(d.point(m_col, assign_y + 69), bus, en=(0.5, 0), line=True, dashed=True)
    d.edge(d.point(m_col, doc_y), tracker, en=(1, 0.5), line=True, dashed=True)
    d.edge(d.point(m_col, doc_y), plan, en=(0, 0.5), line=True, dashed=True)
    d.edge(review_logs, bus, (1, 0.5), (0, 0.5), line=True, dashed=True)
    d.edge(read_assignments, bus, (0, 0.5), (1, 0.5), line=True, dashed=True)
    d.edge(d.point(tr_col, work_y), memory, en=(0.5, 0), line=True, dashed=True)
    d.edge(d.point(m_col, state_y), memory, en=(1, 0.5), line=True, dashed=True)
    d.edge(d.point(pl_col, work_y), deliverables, en=(0.5, 0), line=True, dashed=True)
    d.edge(d.point(m_col, state_y), deliverables, en=(0, 0.5), line=True, dashed=True)
    d.edge(write_reports, d.point(m_col, work_y + 48), (0.5, 0), line=True, dashed=True)

    d.edge(d.point(e_col, work_y + 54), success, en=(0.5, 0))
    d.edge(
        success,
        read_assignments,
        (1, 0.5),
        (1, 0.5),
        wp=[(loop_x, report_y), (loop_x, work_y)],
    )
    note(d, (e_col + 15 + loop_x) / 2, work_y - 22, "No, recoverable:\niterate", 90)
    d.edge(success, write_reports, (0, 0.5), (1, 0.5))
    note(d, e_col - 52, report_y - 12, "Yes", 30)
    d.edge(
        success,
        d.point(m_col, report_y + 49),
        (0.5, 1),
        wp=[(e_col, 870), (m_col, 870)],
    )
    note(d, (e_col + m_col) / 2, 882, "No, blocker: escalate", 130)
    d.edge(write_reports, notify_manager, (0, 0.5), (1, 0.5))
    d.edge(notify_manager, d.point(l_col, work_y + 54), (0.5, 0))
    d.edge(review_logs, second_aligned, (0.5, 0), (0.5, 1))
    d.edge(
        second_aligned,
        complete,
        (0, 0.5),
        (0.5, 0),
        wp=[(lane_x, assign_y), (lane_x, 380)],
    )
    note(d, lane_x - 33, 335, "Yes,\nno work\nremains", 48)
    d.edge(second_aligned, update, (1, 0.5), (0, 0.5))
    note(d, (l_col + 32 + m_col - 15) / 2, assign_y - 20, "Yes, work remains", 135)
    d.edge(
        second_aligned,
        update,
        (0.5, 0),
        (0.2, 0),
        wp=[(l_col, loop1_y), (m_col - 9, loop1_y)],
    )
    note(
        d,
        (l_col + m_col) / 2,
        loop1_y - 12,
        "No, planning or contained issue: revise or retry",
        230,
    )
    return d


def message_bus(theme: dict[str, str], font_family: str = "Helvetica") -> DrawioWriter:
    d = DrawioWriter(600, 230, theme, font_size=9, font_family=font_family)
    lb = 34
    l_col, m_col, r_col = 40, 300, 560
    e1, e2 = (l_col + m_col) / 2, (m_col + r_col) / 2
    top_y, mid_y, bot_y = 30, 110, 190

    manager = d.icon("bot", l_col, mid_y, "Manager")
    user = d.icon("user", m_col, mid_y, "User")
    worker = d.icon("bot", r_col, mid_y, "Worker")
    task_bus = d.icon("file-input", m_col, top_y, "Task Bus")
    report_bus = d.icon("file-output", m_col, bot_y, "Report Bus")

    d.edge(manager, task_bus, (1, 0.2), (0, 0.5), wp=[(e1, mid_y - 9), (e1, top_y)])
    d.edge(task_bus, worker, (1, 0.5), (0, 0.2), wp=[(e2, top_y), (e2, mid_y - 9)])
    d.edge(worker, report_bus, (0, 0.8), (1, 0.5), wp=[(e2, mid_y + 9), (e2, bot_y)])
    d.edge(report_bus, manager, (0, 0.5), (1, 0.8), wp=[(e1, bot_y), (e1, mid_y + 9)])
    d.edge(manager, user, (1, 0.5), (0, 0.5), line=True, dashed=True)
    d.edge(user, worker, (1, 0.5), (0, 0.5), line=True, dashed=True)
    d.edge(d.point(m_col, top_y + lb), user, en=(0.5, 0), line=True, dashed=True)
    d.edge(d.point(m_col, mid_y + lb), report_bus, en=(0.5, 0), line=True, dashed=True)
    for x, a, b in (
        (e1 + m_col - 15, "Writes to", "Read by"),
        (e2 + m_col + 15, "Read by", "Writes to"),
    ):
        note(d, x / 2, top_y - 8, a)
        note(d, x / 2, bot_y + 8, b)
    return d


def state_compression(
    theme: dict[str, str], font_family: str = "Helvetica"
) -> DrawioWriter:
    d = DrawioWriter(640, 200, theme, font_size=9, font_family=font_family)
    x0, x1, e_col, xi, xm = 40, 200, 420, 520, 600
    top_y, mid_y, bot_y = 30, 100, 170

    exec_detail = d.icon("boxes", x0, top_y, "Execution detail")
    coord_detail = d.icon("network", x0, bot_y, "Coordination detail")
    task_log = d.icon("file-box", x1, top_y, "Task Log")
    tracker = d.icon("file-chart-column-increasing", x1, bot_y, "Tracker")
    idx = d.icon("file-search", xi, mid_y, "Index")
    memory = d.icon("folder-tree", xm, mid_y, "Memory")

    d.edge(exec_detail, task_log, (1, 0.5), (0, 0.5))
    d.edge(coord_detail, tracker, (1, 0.5), (0, 0.5))
    d.edge(
        task_log, idx, (1, 0.5), (0, 0.25), wp=[(e_col, top_y), (e_col, mid_y - 7.5)]
    )
    d.edge(tracker, idx, (1, 0.5), (0, 0.75), wp=[(e_col, bot_y), (e_col, mid_y + 7.5)])
    d.edge(idx, memory, (1, 0.5), (0, 0.5), line=True, dashed=True)
    note(d, (x0 + x1) / 2, top_y - 8, "Recorded in")
    note(d, (x0 + x1) / 2, bot_y + 8, "Recorded in")
    note(
        d,
        (x1 + 15 + e_col) / 2,
        top_y - 8,
        "Condensed into completed-work summaries",
        200,
    )
    note(
        d, (x1 + 15 + e_col) / 2, bot_y + 8, "Distilled into durable observations", 200
    )
    return d


def handoff(theme: dict[str, str], font_family: str = "Helvetica") -> DrawioWriter:
    d = DrawioWriter(620, 310, theme, font_size=9, font_family=font_family)
    lb = 34
    l_col, m_col, r_col = 40, 300, 560
    e1, e2 = (l_col + m_col) / 2, (m_col + r_col) / 2
    top_y, mid_y, bot_y, p_y = 30, 110, 190, 260

    outgoing = d.icon("bot", l_col, mid_y, "Outgoing agent with\naccumulated context")
    incoming = d.icon("bot", r_col, mid_y, "Incoming agent with\nfresh context")
    handoff_log = d.icon("file-box", m_col, top_y, "Handoff Log")
    user = d.icon("user", m_col, mid_y, "User")
    handoff_bus = d.icon("file-input", m_col, bot_y, "Handoff Bus")
    project_state = d.icon("boxes", m_col, p_y, "Other relevant\nproject state")

    d.edge(outgoing, handoff_log, (1, 0.2), (0, 0.5), wp=[(e1, mid_y - 9), (e1, top_y)])
    d.edge(handoff_log, incoming, (1, 0.5), (0, 0.2), wp=[(e2, top_y), (e2, mid_y - 9)])
    d.edge(outgoing, user, (1, 0.5), (0, 0.5), line=True, dashed=True)
    d.edge(user, incoming, (1, 0.5), (0, 0.5), line=True, dashed=True)
    d.edge(outgoing, handoff_bus, (1, 0.8), (0, 0.5), wp=[(e1, mid_y + 9), (e1, bot_y)])
    d.edge(handoff_bus, incoming, (1, 0.5), (0, 0.8), wp=[(e2, bot_y), (e2, mid_y + 9)])
    d.edge(project_state, incoming, (1, 0.5), (0, 0.8), wp=[(e2, p_y), (e2, mid_y + 9)])
    d.edge(d.point(m_col, top_y + lb), user, en=(0.5, 0), line=True, dashed=True)
    d.edge(d.point(m_col, mid_y + lb), handoff_bus, en=(0.5, 0), line=True, dashed=True)
    note(d, (e1 + m_col - 15) / 2, top_y - 8, "Writes")
    note(d, (e2 + m_col + 15) / 2, top_y - 8, "Read by")
    note(d, (e1 + m_col - 15) / 2, bot_y + 8, "Writes to")
    note(d, (e2 + m_col + 15) / 2, bot_y + 8, "Read by")
    note(d, (e2 + m_col + 15) / 2, p_y + 8, "Read by")
    return d


def overview(
    theme: dict[str, str],
    hl: str | None = None,
    font_family: str = "Helvetica",
) -> DrawioWriter:
    """Landscape overview diagram of the full APM workflow."""
    fade_p = hl not in (None, "planning")
    fade_i = hl not in (None, "manager", "workers")
    fade_m = hl not in (None, "manager")
    fade_w = hl not in (None, "workers")
    fade_ps = hl not in (None, "planning", "state")
    fade_is = hl not in (None, "state", "manager", "workers")
    fade_ms = hl not in (None, "state", "manager")
    fade_ws = hl not in (None, "state", "workers")
    fade_u = hl not in (None, "user")
    fade_h = hl is not None and hl != "user"

    d = DrawioWriter(720, 260, theme, font_size=9, font_family=font_family)
    step = 150
    cols = [60 + step * k for k in range(5)]
    by_row, agent_row = 50, 140
    ly_row, file_row = agent_row + 34, agent_row + 95

    d.text((cols[0] + cols[1]) / 2, 0, 200, "Planning Phase", fade=fade_p)
    d.text(cols[3], 0, 200, "Implementation Phase", fade=fade_i)
    pl = d.icon("bot", cols[0], agent_row, "Planner", fade=fade_p)
    u1 = d.icon("user", cols[1], agent_row, "User", fade=fade_p and fade_u)
    ma = d.icon("bot", cols[2], agent_row, "Manager", fade=fade_m)
    u2 = d.icon("user", cols[3], agent_row, "User", fade=fade_i and fade_u)
    wo = d.icon("bot", cols[4], agent_row, "Workers", fade=fade_w)

    d.edge(pl, u1, (1, 0.5), (0, 0.5), both=True, fade=fade_p and fade_u)
    d.edge(u1, ma, (1, 0.5), (0, 0.5), dashed=True, fade=fade_h)
    d.edge(ma, u2, (1, 0.5), (0, 0.5), both=True, fade=fade_m and fade_u)
    d.edge(u2, wo, (1, 0.5), (0, 0.5), both=True, fade=fade_w and fade_u)

    sp = d.icon(
        "file-cog", (cols[0] + cols[1]) / 2, file_row, "Spec, Plan, Rules", fade=fade_ps
    )
    d.edge(
        d.point(cols[0], ly_row),
        sp,
        en=(0, 0.5),
        line=True,
        dashed=True,
        fade=fade_ps,
        wp=[(cols[0], file_row)],
    )
    d.edge(
        d.point(cols[1], ly_row),
        sp,
        en=(1, 0.5),
        line=True,
        dashed=True,
        fade=fade_ps,
        wp=[(cols[1], file_row)],
    )

    bus = d.icon("inbox", cols[3], by_row, "Message Bus", fade=fade_is and fade_u)
    d.edge(ma, bus, (0.5, 0), (0, 0.5), line=True, dashed=True, fade=fade_ms)
    d.edge(wo, bus, (0.5, 0), (1, 0.5), line=True, dashed=True, fade=fade_ws)
    d.edge(
        u2,
        d.point(cols[3], by_row + 34),
        (0.5, 0),
        line=True,
        dashed=True,
        fade=fade_is and fade_u,
    )

    tr = d.icon(
        "file-chart-column-increasing",
        (cols[2] + cols[3]) / 2,
        file_row,
        "Tracker",
        fade=fade_ms,
    )
    me = d.icon(
        "folder-tree", (cols[3] + cols[4]) / 2, file_row, "Memory", fade=fade_is
    )
    d.edge(
        d.point(cols[2], ly_row),
        tr,
        en=(0, 0.5),
        line=True,
        dashed=True,
        fade=fade_ms,
        wp=[(cols[2], file_row)],
    )
    d.edge(tr, me, (1, 0.5), (0, 0.5), line=True, dashed=True, fade=fade_ms)
    d.edge(
        d.point(cols[4], ly_row),
        me,
        en=(1, 0.5),
        line=True,
        dashed=True,
        fade=fade_ws,
        wp=[(cols[4], file_row)],
    )
    return d


THESIS_FIGURES: dict[str, callable] = {
    "planning-phase-overview": planning_phase_overview,
    "implementation-phase-overview": implementation_phase_overview,
    "message-bus": message_bus,
    "state-compression": state_compression,
    "handoff": handoff,
}

ALL_FIGURES: dict[str, callable] = {
    **THESIS_FIGURES,
    "overview": overview,
}


def build_diagrams(
    figures: list[str],
    drawio_dir: Path,
    pdf_dir: Path | None,
    theme_name: str,
    font_family: str,
) -> None:
    theme = THEMES.get(theme_name, THEMES["mono"])
    drawio_dir.mkdir(parents=True, exist_ok=True)
    if pdf_dir:
        pdf_dir.mkdir(parents=True, exist_ok=True)

    drawio_bin = shutil.which("drawio")
    if pdf_dir and not drawio_bin:
        print(
            "Warning: drawio CLI not found on PATH; skipping PDF export.",
            file=sys.stderr,
        )
        pdf_dir = None

    for name in figures:
        fn = ALL_FIGURES.get(name)
        if fn is None:
            raise KeyError(f"Unknown figure name: {name}")

        writer = fn(theme, font_family=font_family)
        drawio_file = drawio_dir / f"{name}.drawio"
        drawio_file.write_text(writer.xml(), encoding="utf-8")
        print(f"Generated draw.io: {drawio_file.relative_to(REPO_ROOT)}")

        if pdf_dir and drawio_bin:
            pdf_file = pdf_dir / f"{name}.pdf"
            cmd = [
                drawio_bin,
                "--export",
                "--format",
                "pdf",
                "--crop",
                "--output",
                str(pdf_file),
                str(drawio_file),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                print(f"Error exporting {pdf_file}: {res.stderr}", file=sys.stderr)
                sys.exit(res.returncode)
            print(f"Exported PDF:     {pdf_file.relative_to(REPO_ROOT)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate draw.io concept diagrams and export thesis PDF figures."
    )
    parser.add_argument(
        "--figures",
        nargs="+",
        default=list(THESIS_FIGURES.keys()),
        help=f"Figures to build (default: {list(THESIS_FIGURES.keys())})",
    )
    parser.add_argument(
        "--drawio-dir",
        type=Path,
        default=DEFAULT_DRAWIO_DIR,
        help=f"Directory for generated .drawio files (default: {DEFAULT_DRAWIO_DIR})",
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=DEFAULT_PDF_DIR,
        help=f"Directory for exported .pdf files (default: {DEFAULT_PDF_DIR})",
    )
    parser.add_argument(
        "--drawio-only",
        action="store_true",
        help="Only generate .drawio files, skip PDF export",
    )
    parser.add_argument(
        "--theme",
        choices=list(THEMES.keys()),
        default="mono",
        help="Color theme for strokes and ink (default: mono)",
    )
    parser.add_argument(
        "--font",
        default="Helvetica",
        help="Base font family for cells and labels (default: Helvetica)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_out = None if args.drawio_only else args.pdf_dir
    build_diagrams(
        figures=args.figures,
        drawio_dir=args.drawio_dir,
        pdf_dir=pdf_out,
        theme_name=args.theme,
        font_family=args.font,
    )


if __name__ == "__main__":
    main()

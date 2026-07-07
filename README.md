# BSc APM Thesis

BSc thesis evaluating [Agentic Project Management (APM)](https://github.com/sdi2200262/agentic-project-management) against [GitHub Spec-kit](https://github.github.io/spec-kit/) on the Claude Code CLI, for AI-assisted software development.

## Overview

This thesis investigates whether user-mediated coordination between several agents provides tangible benefits over a workflow carried by one agent on complex software development tasks. The case study compares two open-source spec-driven frameworks running on the same coding agent, so the comparison isolates APM's coordination design from platform or tooling differences:

- **APM** (v1.0): spec-driven, with a Planner, a Manager, and Workers coordinated through the user over file-based protocols.
- **GitHub Spec-kit**: spec-driven, with one agent driven by slash commands (`/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-implement`).

The evaluation compares the two along four dimensions, defined as research questions in the Evaluation chapter:

- **Economic**: the dollar cost of completing a task, priced against the platform's per-token rate card.
- **Process**: the time a task takes and the effort it demands of the user.
- **Functional**: how much of the task each framework completes, and how it fails when it falls short.
- **Perception**: participants' self-reported experience, read against the behaviour measured from their sessions.

## Evaluation Methodology

The study is a within-subjects experiment on Claude Code. Each participant completes the case-study task twice, once with APM and once with Spec-kit, with the framework order counterbalanced across the cohort to control for task-familiarity effects. One Claude model, Opus 4.7 or Sonnet 4.6, is held fixed across a participant's two sessions. Sessions are time-boxed to three hours.

Transcript-derived metrics are extracted programmatically from the per-session Claude Code JSONL transcripts; the functional outcome is scored by an automated grader against a fixed 100-point rubric, and a post-session questionnaire captures self-report. The measures are organised by the four research questions (economic, process, functional, perception), alongside a small set of supplementary descriptors. Each session's submission bundles the solution patch, the transcripts, and the questionnaire response, anonymised and encrypted before storage.

The methodology is set out in [`chapters/evaluation/`](chapters/evaluation/); the findings are reported in [`chapters/results/`](chapters/results/) and interpreted in [`chapters/discussions/`](chapters/discussions/). The grader, parser, and grading environment live in the infrastructure repository linked below.

## Building

The thesis is one source of truth: `thesis.tex` sets the class and metadata and
assembles one body file per chapter under `chapters/`, with the three appendix
bodies gathered at the end. The `apmthesis` class implements the mandatory DIT
BSc submission layout; it is an LPPL Derived Work of the community `dithesis`
class. The body font defaults to the vendored, freely redistributable Arimo so
the build is reproducible with no system font installed.

The build uses XeLaTeX and is automated via the `Makefile`. The finished
`thesis.pdf` is written to the repository root; auxiliary files stay in
`build/`. **Always run from the repository root** so `latexmkrc` and the
`Makefile` are picked up and the class's relative font path resolves.

```bash
cd /path/to/bsc-apm-thesis

# Build the full thesis (default: vendored Arimo, fully reproducible)
make pdf

# Build with a system-installed Arial instead (requires Arial on the host)
make arial

# Continuous rebuild on source changes
make watch

# Clean auxiliary and output files
make clean
```

If you prefer running `latexmk` manually:

```bash
# Build the full thesis
latexmk thesis.tex

# Build with a system-installed Arial
THESIS_ARIAL=1 latexmk thesis.tex

# Clean auxiliary files
latexmk -c
```

Running from a subdirectory will miss `latexmkrc` and fail to resolve the font path.

## Result Generation

The thesis keeps table and figure environments in the chapter files. Analysis
scripts under `analysis/` generate only table rows and figure PDFs, run
against a config that lists each session's identity, framework, model, and
the paths to its parser and grader artefacts.

```bash
python3 analysis/process_tables.py --config analysis/config/cohort.json --output-dir analysis/generated-local/tables
```

## Related

- [bsc-apm-case-study-task](https://github.com/sdi2200262/bsc-apm-case-study-task): task specification, participant package, and testing environment.
- [bsc-apm-case-study-infra](https://github.com/sdi2200262/bsc-apm-case-study-infra): grader, transcript parser, and grading environment.
- [bsc-apm-case-study-data](https://github.com/sdi2200262/bsc-apm-case-study-data): participant submissions (restricted access).
- [eclass-mcp-server](https://github.com/sdi2200262/eclass-mcp-server): reference MCP client for the openeclass platform.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).

---

*BSc thesis, Department of Informatics and Telecommunications, University of Athens.*

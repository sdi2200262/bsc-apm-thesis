# BSc APM Thesis

BSc thesis evaluating Agentic Project Management (APM v1) against GitHub Spec-kit on the Claude Code CLI platform.

**Status:** Work in Progress

## Overview

This thesis investigates whether multi-agent coordination structures provide tangible benefits over single-agent workflows when applied to complex software development tasks. The case study compares two spec-driven frameworks on a shared AI coding platform:

- **APM v1**: Multi-agent, spec-driven (Planner, Manager, Workers; file-based Message Bus)
- **GitHub Spec-kit**: Single-agent, spec-driven (`/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-implement`)

Both frameworks are open-source and run on the same AI coding CLI, so the evaluation isolates the effect of multi-agent coordination overhead from platform or tooling differences.

The research evaluates three dimensions:

- **Economic Efficiency**: Dollar cost of a session, computed against the platform's per-token rate card
- **Process Efficiency**: Human coordination and verification burden across a session
- **Functional Efficacy**: Ability to complete non-trivial tasks that stress single-context-window workflows

## Repository Structure

```
bsc-apm-thesis/
├── Makefile                 # Build automation (wraps latexmk)
├── README.md                # This file
├── LICENSE                  # GPL-3.0-or-later (thesis content)
├── thesis.tex               # Master: class, metadata, chapter assembly
├── apmthesis.cls            # Thesis document class (DIT BSc, Pergamos layout)
├── latexmkrc                # XeLaTeX build configuration
├── references.bib           # Bibliography database (filled in the grounding pass)
├── fonts/arimo/             # Vendored Arimo font (OFL) + its license
├── emblems/                 # NKUA Athena emblem (title page)
├── chapters/
│   ├── introduction/introduction.tex
│   ├── background/background.tex
│   ├── framework-design/framework-design.tex
│   ├── evaluation/evaluation.tex            # Evaluation chapter body
│   ├── evaluation/evaluation-appendix.tex   # Evaluation appendix body
│   └── conclusion/conclusion.tex
├── assets/                  # Images and figures
└── build/                   # XeLaTeX auxiliary files, git-ignored
                             # (thesis.pdf is written to the repo root)
```

The thesis is one source of truth: `thesis.tex` sets the class and metadata and
assembles one body file per chapter under `chapters/`. The `apmthesis` class
implements the mandatory DIT BSc submission layout (A4, Arial-metric font,
bilingual front matter) accepted by the Pergamos repository; it is an LPPL
Derived Work of the community `dithesis` class (provenance and change notice in
the class header). The body font defaults to the vendored, freely
redistributable Arimo (metric-identical to Arial) so the build is reproducible
with no system font installed.

## Evaluation Methodology

The study is a within-subjects experiment on Claude Code. Each participant completes the case study task twice, once with APM v1 and once with Spec-kit, with the order counterbalanced across the cohort to control for task-familiarity effects. Sessions are time-boxed to three hours.

Metrics are extracted programmatically from the per-session Claude Code JSONL transcripts and organised into three measurement dimensions (economic, process, functional) plus a consolidated analysis plan. Each session's submission bundles the patch, the transcripts, and a post-session questionnaire response, packaged as a single zip and submitted alongside the questionnaire through one per-session web form. Transcripts are anonymised and encrypted with an HMAC-SHA256 XOR cipher before storage, protecting participant privacy while preserving reproducibility.

Full methodology, including the testbed, the 100-point grading rubric, and infrastructure details, lives in [`chapters/evaluation/`](chapters/evaluation/).

## Building

The build uses XeLaTeX and is automated via the `Makefile`. Output (PDF and
auxiliary files) goes to `build/`. **Always run from the repository root** so
`latexmkrc` and the `Makefile` are picked up and the class's relative font path
resolves.

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

The finished PDF is `thesis.pdf` at the repository root (auxiliary files
stay in `build/`). If you prefer running `latexmk` manually:

```bash
# Build the full thesis
latexmk thesis.tex

# Build with a system-installed Arial
THESIS_ARIAL=1 latexmk thesis.tex

# Clean auxiliary files
latexmk -c
```

Running from a subdirectory will miss `latexmkrc` and fail to resolve the font path.

## Related Repositories

- [bsc-apm-case-study-task](https://github.com/sdi2200262/bsc-apm-case-study-task): Participant package and containerised testing environment
- [bsc-apm-case-study-infra](https://github.com/sdi2200262/bsc-apm-case-study-infra): Grading suite, transcript parser, and submission processing pipeline (private)
- [bsc-apm-case-study-data](https://github.com/sdi2200262/bsc-apm-case-study-data): Participant submissions (restricted access)

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).

---

*BSc thesis, Department of Informatics and Telecommunications, University of Athens*

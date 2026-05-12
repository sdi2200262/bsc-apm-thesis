# BSc APM Thesis

BSc thesis evaluating Agentic Project Management (APM v1) against GitHub Spec-kit on the Claude Code CLI platform.

**Status:** Work in Progress

## Overview

This thesis investigates whether multi-agent coordination structures provide tangible benefits over single-agent workflows when applied to complex software development tasks. The case study compares two spec-driven frameworks on a shared AI coding platform:

- **APM v1** - Multi-agent, spec-driven (Planner, Manager, Workers; file-based Message Bus)
- **GitHub Spec-kit** - Single-agent, spec-driven (`/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-implement`)

Both frameworks are open-source and run on the same AI coding CLI, so the evaluation isolates the effect of multi-agent coordination overhead from platform or tooling differences.

The research evaluates three dimensions:

- **Economic Efficiency** - Dollar cost of a session, computed against the platform's per-token rate card
- **Process Efficiency** - Human coordination and verification burden across a session
- **Functional Efficacy** - Ability to complete non-trivial tasks that stress single-context-window workflows

## Repository Structure

```
bsc-apm-thesis/
├── README.md                # This file
├── LICENSE                  # GPL-3.0-or-later
├── latexmkrc                # LaTeX build configuration
├── chapters/
│   └── evaluation/
│       ├── evaluation.tex         # Evaluation methodology section
│       ├── evaluation.pdf         # Compiled PDF
│       ├── evaluation-appendix.tex # Infrastructure and implementation details
│       └── evaluation-appendix.pdf # Compiled appendix PDF
├── assets/                  # Images and figures
└── build/                   # LaTeX auxiliary files
```

## Evaluation Methodology

The study is a within-subjects experiment on Claude Code. Each participant completes the case study task twice, once with APM v1 and once with Spec-kit, with the order counterbalanced across the cohort to control for task-familiarity effects. Sessions are time-boxed to three hours.

Metrics are extracted programmatically from the per-session Claude Code JSONL transcripts and organised into three measurement dimensions (economic, process, functional) plus a consolidated analysis plan. Each session's submission bundles the patch, the transcripts, and a post-session questionnaire response, packaged as a single zip and submitted alongside the questionnaire through one per-session web form. Transcripts are anonymised and encrypted with an HMAC-SHA256 XOR cipher before storage, protecting participant privacy while preserving reproducibility.

Full methodology, including the testbed, the 100-point grading rubric, and infrastructure details, lives in [`chapters/evaluation/`](chapters/evaluation/).

## Building

Auxiliary files are output to `build/` to keep the root directory clean. **Always run latexmk from the repository root** to ensure the `latexmkrc` configuration is found.

```bash
# Build a specific chapter (run from repo root)
cd /path/to/bsc-apm-thesis
latexmk -pdf chapters/evaluation/evaluation.tex

# Build the evaluation appendix (run from repo root)
latexmk -pdf chapters/evaluation/evaluation-appendix.tex

# Clean auxiliary files (run from repo root)
latexmk -c
```

**Note:** If you run latexmk from a subdirectory, it may not find the `latexmkrc` configuration file and auxiliary files will be placed in the subdirectory instead of `build/`.

## Related Repositories

- [bsc-apm-case-study-task](https://github.com/sdi2200262/bsc-apm-case-study-task) - Participant package and containerised testing environment
- [bsc-apm-case-study-infra](https://github.com/sdi2200262/bsc-apm-case-study-infra) - Grading suite, transcript parser, and submission processing pipeline (private)
- [bsc-apm-case-study-data](https://github.com/sdi2200262/bsc-apm-case-study-data) - Participant submissions (restricted access)

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).

---

*BSc thesis - Department of Informatics and Telecommunications, University of Athens*

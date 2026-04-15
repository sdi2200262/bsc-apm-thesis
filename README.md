# BSc APM Thesis

BSc thesis evaluating Agentic Project Management (APM v1) against GitHub Spec-kit on the GitHub Copilot platform.

**Status:** Work in Progress

## Overview

This thesis investigates whether multi-agent coordination structures (like APM) provide tangible benefits over single-agent workflows when applied to complex software development tasks. The case study compares two spec-driven frameworks on a shared IDE platform:

- **APM v1** - Multi-agent, spec-driven (Planner, Manager, Workers; file-based Message Bus)
- **GitHub Spec-kit** - Single-agent, spec-driven (`specify`, `plan`, `tasks`)

Both frameworks are open-source and run on GitHub Copilot, so the evaluation isolates the effect of multi-agent coordination overhead rather than platform or tooling differences.

The research evaluates three dimensions:

- **Economic Efficiency** - Request consumption as a proxy for enterprise budget impact
- **Process Efficiency** - Human cognitive load and interaction burden
- **Functional Efficacy** - Ability to complete non-trivial tasks without "Agentic Handoff Failures"

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

The study is a within-subjects experiment on GitHub Copilot. Each participant completes the case study task twice — once with APM v1, once with Spec-kit — with the order counterbalanced across the cohort to control for task-familiarity effects.

Metrics are extracted programmatically from the Copilot JSON chat exports and organized into five categories: session metadata, cost, reliability, process, and functional. Chat exports are sanitized with HMAC-XOR encryption before storage to protect participant privacy while preserving reproducibility.

Full methodology, including the testbed, grading rubric (48 points), and infrastructure details, lives in [`chapters/evaluation/`](chapters/evaluation/).

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

- [bsc-apm-case-study-task](https://github.com/sdi2200262/bsc-apm-case-study-task) - Task specification and grading suite
- [bsc-apm-case-study-data](https://github.com/sdi2200262/bsc-apm-case-study-data) - Participant submissions (private)

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).

---

*BSc thesis - Department of Informatics and Telecommunications, University of Athens*

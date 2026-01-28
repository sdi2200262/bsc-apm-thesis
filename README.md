# BSc APM Thesis

BSc thesis evaluating Agentic Project Management (APM) frameworks against single-agent workflows in AI-assisted software development.

**Status:** Work in Progress

## Overview

This thesis investigates whether multi-agent coordination structures (like APM) provide tangible benefits over single-agent or double-agent workflows when applied to complex software development tasks.

The research evaluates three key dimensions:

- **Economic Efficiency** - Token consumption and financial cost comparison
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

The evaluation consists of two complementary sub-studies:

1. **Sub-Study A (Cursor)** - Quantitative Economic Analysis
   - Controlled group using Cursor with standardized model (Composer 1)
   - Measures token consumption, cost, and cache efficiency

2. **Sub-Study B (GitHub Copilot)** - Qualitative Process Analysis
   - University students using GitHub Copilot (via GitHub Education)
   - Metrics extracted from chat exports across 3 tiers
   - Data sanitized using HMAC-XOR encryption for participant privacy

### Sub-Study B Metrics

Process efficiency is measured via automatically extracted metrics from GitHub Copilot chat exports:

- **Session Metadata:** Session ID (SHA256), Model ID
- **Core Metrics:** Request counts, tool invocations, success rates, user interventions, session duration
- **Supporting Metrics:** Execution rounds, retry patterns, tool diversity  
- **Agentic Activity:** File modifications, read/write operations, modification strategy

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

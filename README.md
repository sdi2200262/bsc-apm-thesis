# BSc APM Thesis

This thesis presents [Agentic Project Management (APM)](https://github.com/sdi2200262/agentic-project-management), which coordinates several agents through the user, and evaluates it against [Spec-kit](https://github.github.io/spec-kit/) in a comparative case study with Claude Code.

## Overview

Both open-source frameworks operate on the same coding agent:

- **APM v1** coordinates a Planner, a Manager, and Workers through a spec-driven workflow mediated by the user over file-based protocols.
- **Spec-kit** takes one agent through a spec-driven workflow using slash commands.

The evaluation covers four dimensions:

- **Economic:** dollar-equivalent cost under the platform's per-token rate card.
- **Process:** session duration and recorded user interaction.
- **Functional:** task completion and failure.
- **Perception:** participants' reported experience alongside their measured behaviour.

Each participant attempts the same task once with each framework. The assigned model remains fixed across the pair, and framework order is counterbalanced across the cohort. Each attempt has a three-hour cap. A transcript parser computes the economic and process measures from the participants' transcripts, an automated grader scores their submitted solution patch against a fixed rubric, and a questionnaire supplies the perception measures.

The methodology is in [`chapters/evaluation/`](chapters/evaluation/), the findings in [`chapters/results/`](chapters/results/), and their interpretation in [`chapters/discussions/`](chapters/discussions/). The related repositories hold the task, study infrastructure, and participant data.

## Building

`thesis.tex` configures the document and assembles one source file per chapter. The `apmthesis` class implements the DIT BSc submission layout and derives from the community `dithesis` class. The default build uses the vendored Arimo font.

Run every build from the repository root so `latexmkrc` and the class's font path resolve. XeLaTeX writes the finished `thesis.pdf` to the root and keeps auxiliary files under `build/`.

```bash
make pdf
make arial
make watch
make clean
```

`make arial` selects a system-installed Arial. The equivalent direct commands are:

```bash
latexmk thesis.tex
THESIS_ARIAL=1 latexmk thesis.tex
latexmk -c
```

## Result Generation

The `analysis/` package generates the table rows and figure PDFs imported by the chapters. Its config locates each session's data. Every generator receives `assets/` as its output root. Table fragments go to `assets/tables/`, and figures go to their dimension under `assets/figures/`.

Figure generation requires matplotlib and the Latin Modern OpenType faces:

```bash
export THESIS_LM_FONT_DIR="$(dirname "$(kpsewhich lmroman10-regular.otf)")"
COHORT_CONFIG=/path/to/cohort.json
python3 analysis/generate_tables.py --config "$COHORT_CONFIG" --output-dir assets
python3 analysis/economic_figures.py --config "$COHORT_CONFIG" --output-dir assets
python3 analysis/process_figures.py --config "$COHORT_CONFIG" --output-dir assets
python3 analysis/functional_figures.py --config "$COHORT_CONFIG" --output-dir assets
python3 analysis/occupancy_figures.py --config "$COHORT_CONFIG" --output-dir assets
python3 analysis/functional_compact_figure.py --config "$COHORT_CONFIG" --output-dir assets
python3 analysis/cost_score_figure.py --config "$COHORT_CONFIG" --output-dir assets
```

`COHORT_CONFIG` names a JSON file with one `records` entry per session. Each entry gives `pid`, `session` (`S1` or `S2`), `framework` (`apm` or `speckit`), and the paths to that session's `parser_data.json`, `parser_metrics.json`, and `grader_results.json`. The optional `compact_grader_results` and `questionnaire_csv` paths feed the compact re-grade and the perception outputs. Relative paths resolve against the config file's directory.

```json
{
  "records": [
    {
      "pid": "P001",
      "session": "S1",
      "framework": "apm",
      "parser_data": "my-submissions/P001/S1_apm_opus/parser_data.json",
      "parser_metrics": "my-submissions/P001/S1_apm_opus/parser_metrics.json",
      "grader_results": "my-submissions/P001/S1_apm_opus/grader_results.json",
      "compact_grader_results": "my-submissions/P001/S1_apm_opus/grader_results_compact_serialization.json",
      "questionnaire_csv": "my-submissions/questionnaire/raw/responses.csv"
    }
  ]
}
```

## Concept Diagrams

Concept-diagram sources live under `diagrams/`, and their rendered PDFs live under `assets/figures/`.

Render D2 sources through SVG so the thesis receives a vector PDF:

```bash
d2 --elk-nodeNodeBetweenLayers 40 --elk-padding "[top=40,left=20,bottom=20,right=20]" \
  diagrams/framework-design/stage-progression.d2 /tmp/stage-progression.svg
rsvg-convert -b "#FDFCFA" -f pdf \
  -o assets/figures/framework-design/stage-progression.pdf /tmp/stage-progression.svg
```

The D2 sources pin ELK as their layout engine and carry the chapter's shared visual styles.

Programmatically generate all draw.io diagram sources and export cropped vector PDFs:

```bash
make diagrams
# or directly:
python3 diagrams/build.py
```

Individual draw.io sources can also be exported directly:

```bash
drawio --export --format pdf --crop \
  --output assets/figures/framework-design/planning-phase-overview.pdf \
  diagrams/framework-design/planning-phase-overview.drawio
```

## Spec-kit Release Audit

The study sessions used several Spec-kit releases. `spec-kit-audit/` compares the installed instructions of each release with its predecessor. The committed output contains one unified diff per release step and a manifest hashing every installed file. The audit requires `git`, [`uv`](https://docs.astral.sh/uv/), and network access to GitHub.

```bash
python3 spec-kit-audit/audit.py
python3 spec-kit-audit/audit.py --check
```

## Related Repositories

- [bsc-apm-case-study-task](https://github.com/sdi2200262/bsc-apm-case-study-task): task, participant package, and testing environment.
- [bsc-apm-case-study-infra](https://github.com/sdi2200262/bsc-apm-case-study-infra): transcript parser, grader, rubric, and grading environment.
- [bsc-apm-case-study-data](https://github.com/sdi2200262/bsc-apm-case-study-data): encrypted study dataset.
- [agentic-project-management](https://github.com/sdi2200262/agentic-project-management): the APM framework.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).

---

*BSc thesis "Agentic Project Management: A Spec-Driven Multi-Agent Framework for
AI-Assisted Software Engineering" by Konstantinos Chaidemenos, supervised by Thanassis Avgerinos,
Department of Informatics and Telecommunications, National and Kapodistrian University of Athens,
2026.*

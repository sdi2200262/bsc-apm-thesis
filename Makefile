# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) BSc APM Case Study 2025-2026
#
# Convenience wrapper around latexmk for the BSc APM thesis. All targets run
# from the repository root (required: latexmkrc and the class's relative font
# path resolve there). The finished PDF is thesis.pdf at the repository root
# (auxiliary files stay in build/).

MAIN := thesis.tex
PDF  := thesis.pdf

.PHONY: all pdf diagrams arial watch clean help

# Default: build with the vendored Arimo font (reproducible, no system font).
all: pdf

pdf:
	latexmk $(MAIN)

# Programmatically generate concept diagrams and export PDF figures.
diagrams:
	python3 diagrams/build.py

# Build with a system-installed Arial instead (requires Arial on the host).
arial:
	THESIS_ARIAL=1 latexmk $(MAIN)

# Continuous rebuild on source changes.
watch:
	latexmk -pvc $(MAIN)

# Remove auxiliary and output files, including the root PDF copy.
clean:
	latexmk -C $(MAIN)
	rm -f $(PDF)

help:
	@echo "make pdf      - build $(PDF) with the vendored Arimo font (default)"
	@echo "make diagrams - regenerate draw.io diagrams and export PDF figures"
	@echo "make arial    - build with a system-installed Arial"
	@echo "make watch  - rebuild continuously on changes"
	@echo "make clean  - remove build artifacts"

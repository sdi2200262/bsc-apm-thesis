# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) BSc APM Case Study 2025-2026
#
# latexmk configuration for the BSc APM thesis.
#
# Build with XeLaTeX (the apmthesis class needs it for the OpenType Arial /
# Arimo font stack and the Greek front matter). Invoke from the repository
# root so the class's relative font path (fonts/arimo/) resolves:
#
#   latexmk thesis.tex
#
# Auxiliary files stay in build/; the finished PDF is copied to thesis.pdf at
# the repository root for convenient viewing (see $success_cmd below). The
# default build uses the vendored Arimo font, so it is reproducible with no
# system font installed. Set THESIS_ARIAL=1 to build with a system-installed
# Arial instead:
#
#   THESIS_ARIAL=1 latexmk thesis.tex

$pdf_mode = 5;            # 5 = produce PDF directly with xelatex
$postscript_mode = 0;
$dvi_mode = 0;

# %P (not %S) so latexmk prepends $pre_tex_code ahead of the document;
# $jobname keeps the output named thesis.pdf under that invocation form.
$xelatex = 'xelatex -interaction=nonstopmode -file-line-error -synctex=1 %O %P';
$jobname = 'thesis';

$out_dir = 'build';
$aux_dir = 'build';

$recorder = 1;
$max_repeat = 5;

# Font source switch. With THESIS_ARIAL set, pass the class's `arial' option
# ahead of the document so the build uses a system-installed Arial; otherwise
# the class default (vendored Arimo) applies.
if ($ENV{'THESIS_ARIAL'}) {
    $pre_tex_code = '\PassOptionsToClass{arial}{apmthesis}';
}

$clean_ext = 'aux bbl blg fls fdb_latexmk out synctex.gz toc lof lot';

# After a successful build, copy the PDF from build/ to thesis.pdf at the
# repository root. %D is the generated PDF; $success_cmd runs from the root.
$success_cmd = 'cp %D thesis.pdf';

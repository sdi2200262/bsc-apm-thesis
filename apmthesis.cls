% apmthesis.cls
%
% A LaTeX2e document class for a BSc thesis submitted to the Department of
% Informatics and Telecommunications (DIT) of the National and Kapodistrian
% University of Athens (NKUA), formatted to the department's mandatory
% submission template and accepted by the Pergamos digital repository.
%
% -----------------------------------------------------------------------------
% Provenance and licensing (LaTeX Project Public License)
% -----------------------------------------------------------------------------
% This class is a Derived Work, in the sense of the LaTeX Project Public
% License (LPPL) v1.3c, of the community class `dithesis.cls':
%
%   Copyright (c) 2014, 2015 Charalampos S. Nikolaou <charnik@di.uoa.gr>
%                       2017 Ergys Dona <errikosd@gmail.com>
%                       2020 Giorgos Katsogiannis <geo.katsogiannis@gmail.com>
%
% The original Work is distributed under the LPPL; the latest version of that
% license is at http://www.latex-project.org/lppl.txt. This Derived Work is
% likewise distributed under the LPPL.
%
% A complete, unmodified copy of the original Work can be obtained from
% https://github.com/errikos/dithesis at commit
% 8ffc7d3a71ff1f111ec66363505a9bc57012edde (LPPL 1.3c clause 6.d.2).
%
% Nature of the changes in this Derived Work (LPPL 1.3c clause 6.b):
%   - Renamed from `dithesis' to `apmthesis' so it identifies itself as a
%     modified version and is not a drop-in replacement for the original
%     (LPPL 1.3c clause 6.a).
%   - Reorganized into banner-delimited regions with intent-level comments to
%     match the maintaining project's source conventions. The formatting
%     behavior, page builders, and the department layout it produces are
%     preserved.
%   - The body font stack is parameterized. By default the class loads a
%     vendored, freely redistributable, metric-compatible Arial substitute
%     (Arimo) by path, so the build is reproducible on any host with no
%     system font dependency. Passing the `arial' class option instead loads
%     a system-installed Arial by family name (requires Arial on the build
%     host).
%   - The legacy `xunicode' and `xltxtra' shims and the `CMU Bright' math
%     font overrides were dropped; the modern fontspec + polyglossia stack
%     and the default math fonts are used instead, for reproducibility.
%
% The original authors do not provide, and are not implied to provide, any
% support for this Derived Work (LPPL 1.3c clause 6.c).
%
% Maintained for the BSc APM Case Study 2025-2026.
%
% -----------------------------------------------------------------------------
% Class options
% -----------------------------------------------------------------------------
%   inscr     Print a dedication (inscription) page; content via \inscriptionEn.
%   ack       Print an acknowledgements page; content via \acksEn.
%   preface   Print a preface page before the first chapter; content via
%             \prefaceEn.
%   lop       Print a list-of-publications page (PhD only; unused for BSc).
%   dualpage  Centre the page number in the footer for double-sided printing.
%   arial     Use a system-installed Arial instead of the vendored Arimo.

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{apmthesis}[2026/05/15 v1.0 BSc thesis class for the Department
of Informatics and Telecommunications, NKUA; LPPL Derived Work of dithesis]

% =============================================================================
% Option declarations
% =============================================================================

% Optional front-matter pages, toggled by class options.
\newif\ifinscriptionpage   \inscriptionpagefalse
\newif\ifackpage           \ackpagefalse
\newif\ifloppage           \loppagefalse
\newif\ifprefacepage       \prefacepagefalse

% Footer layout: centred page number for double-sided printing.
\newif\ifdualpage          \dualpagefalse

% Body font source: vendored Arimo (default) versus system Arial.
\newif\ifsystemarial       \systemarialfalse

% Internal flags (not driven by options): which language a shared page builder
% is currently rendering, and whether the appendix region has started.
\newif\ifenglishfrontpage      \englishfrontpagefalse
\newif\ifenglishcommitteepage  \englishcommitteepagefalse
\newif\ifappendixstarted       \appendixstartedfalse

\DeclareOption{inscr}{\inscriptionpagetrue}
\DeclareOption{ack}{\ackpagetrue}
\DeclareOption{preface}{\prefacepagetrue}
\DeclareOption{lop}{\loppagetrue}
\DeclareOption{dualpage}{\dualpagetrue}
\DeclareOption{arial}{\systemarialtrue}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{book}}
\ProcessOptions\relax

\LoadClass[12pt,oneside]{book}

% =============================================================================
% Page geometry and required packages
% =============================================================================
%
% Margins, header, and footer follow the department template: A4, 2 cm on
% every side, 0.5 cm binding offset, header and footer band 1.25 cm from the
% trim. Add showframe=true to the geometry options when debugging the frame.
\RequirePackage[a4paper,
  top=2cm,bottom=2cm,bindingoffset=0.5cm,left=2cm,right=2cm,
  headsep=0.5cm,footskip=0.75cm]{geometry}
\RequirePackage{fancyhdr}
\RequirePackage[final]{graphicx}
\RequirePackage{sectsty}              % chapter / section heading fonts
\RequirePackage{textcase}             % case-correct uppercasing in headings
\RequirePackage[resetlabels]{multibib}
\RequirePackage{etoolbox}
\RequirePackage{tabularx}
\RequirePackage{longtable}            % abbreviations table spanning pages
\RequirePackage{xifthen}
\RequirePackage[caption=false]{subfig}
\RequirePackage[%
  font={footnotesize,bf},
  justification=centering,
  labelsep=colon,
  figureposition=bottom,
  tableposition=top]{caption}

% =============================================================================
% Font stack: Latin and Greek, with the Arimo / Arial switch
% =============================================================================
%
% The class is bilingual (English body, Greek front matter), so the same font
% family must carry Latin and Greek glyphs. Arimo and Arial both do. The
% department template mandates the Arial typeface; Arimo is metric-identical
% to Arial, so the rendered page (line breaks, page count, layout) is the same
% whichever source is used, and the Pergamos check sees an equivalent result.
%
% Default: the vendored Arimo TrueType files under fonts/arimo/, loaded by
% path so no font need be installed on the build host. The build must be
% invoked from the repository root so this relative path resolves.
%
% With the `arial' option: a system-installed Arial, resolved by family name.
\RequirePackage{fontspec}
\RequirePackage{polyglossia}
\defaultfontfeatures{Mapping=tex-text,Scale=MatchLowercase}

\ifsystemarial
  \setmainfont[Ligatures={Common,TeX}]{Arial}
  \setsansfont{Arial}
  \newfontfamily\greekfont[Script=Greek]{Arial}
  \newfontfamily\greekfontsf[Script=Greek]{Arial}
  \newfontfamily\greekfonttt[Script=Greek]{Arial}
\else
  \setmainfont[
    Path=fonts/arimo/,Extension=.ttf,
    UprightFont=Arimo-Regular,BoldFont=Arimo-Bold,
    ItalicFont=Arimo-Italic,BoldItalicFont=Arimo-BoldItalic,
    Ligatures={Common,TeX}]{Arimo}
  \setsansfont[
    Path=fonts/arimo/,Extension=.ttf,
    UprightFont=Arimo-Regular,BoldFont=Arimo-Bold,
    ItalicFont=Arimo-Italic,BoldItalicFont=Arimo-BoldItalic]{Arimo}
  \newfontfamily\greekfont[
    Path=fonts/arimo/,Extension=.ttf,
    UprightFont=Arimo-Regular,BoldFont=Arimo-Bold,
    ItalicFont=Arimo-Italic,BoldItalicFont=Arimo-BoldItalic,
    Script=Greek]{Arimo}
  \newfontfamily\greekfontsf[
    Path=fonts/arimo/,Extension=.ttf,
    UprightFont=Arimo-Regular,BoldFont=Arimo-Bold,
    ItalicFont=Arimo-Italic,BoldItalicFont=Arimo-BoldItalic,
    Script=Greek]{Arimo}
  \newfontfamily\greekfonttt[
    Path=fonts/arimo/,Extension=.ttf,
    UprightFont=Arimo-Regular,BoldFont=Arimo-Bold,
    ItalicFont=Arimo-Italic,BoldItalicFont=Arimo-BoldItalic,
    Script=Greek]{Arimo}
\fi

\setdefaultlanguage[variant=uk]{english}
\setotherlanguage{greek}

% Ordinal superscripts used on the Greek inner-cover descriptions (1ο, 2η).
% The superscript letters are literal Greek glyphs, rendered by the Greek
% font family under XeLaTeX.
\providecommand{\grnumm}[1]{#1\textsuperscript{ο}}
\providecommand{\grnumf}[1]{#1\textsuperscript{η}}

% =============================================================================
% Document metadata commands
% =============================================================================
%
% Each command stores a value the front matter reads back. Greek and English
% variants are kept separate because the title page and inner cover are
% rendered once per language.

% Author name parts and student registry number.
\providecommand{\authorFirstGr}[1]{\gdef\@authorFirstGr{#1}}
\providecommand{\authorFirstAbrGr}[1]{\gdef\@authorFirstAbrGr{#1}}
\providecommand{\authorMiddleGr}[1]{\gdef\@authorMiddleGr{#1}}
\providecommand{\authorLastGr}[1]{\gdef\@authorLastGr{#1}}
\providecommand{\authorFirstEn}[1]{\gdef\@authorFirstEn{#1}}
\providecommand{\authorFirstAbrEn}[1]{\gdef\@authorFirstAbrEn{#1}}
\providecommand{\authorMiddleEn}[1]{\gdef\@authorMiddleEn{#1}}
\providecommand{\authorLastEn}[1]{\gdef\@authorLastEn{#1}}
\providecommand{\authorSn}[1]{\gdef\@authorSn{#1}}

% Thesis title.
\providecommand{\titleGr}[1]{\gdef\@titleGr{#1}}
\providecommand{\titleEn}[1]{\gdef\@titleEn{#1}}

% Examination date (month followed by year).
\providecommand{\dateGr}[1]{\gdef\@dateGr{#1}}
\providecommand{\dateEn}[1]{\gdef\@dateEn{#1}}

% Supervisor(s). Calling the command twice records a second supervisor and
% switches the printed label to its plural form in both languages.
\gdef\@supervisorLabelSuffixGr{ων}
\gdef\@supervisorLabelSuffixEn{}
\providecommand{\supervisorGr}[2]{%
  \ifthenelse{\isundefined{\@thesupervisorslistGr}}{%
    \def\@thesupervisorslistGr{\textbf{#1,} #2}%
  }{%
    \g@addto@macro\@thesupervisorslistGr{\\&\textbf{#1,} #2}%
    \def\@supervisorLabelSuffixGr{οντες}%
  }%
}
\providecommand{\supervisorEn}[2]{%
  \ifthenelse{\isundefined{\@thesupervisorslistEn}}{%
    \def\@thesupervisorslistEn{\textbf{#1,} #2}%
  }{%
    \g@addto@macro\@thesupervisorslistEn{\\&\textbf{#1,} #2}%
    \def\@supervisorLabelSuffixEn{s}%
  }%
}

% Abstract, Greek synopsis, acknowledgements, dedication, and preface bodies.
\providecommand{\abstractEn}[1]{\gdef\@abstractEn{#1}}
\providecommand{\abstractGr}[1]{\gdef\@abstractGr{#1}}
\providecommand{\synopsisGr}[1]{\gdef\@synopsisGr{#1}}
\providecommand{\acksEn}[1]{\gdef\@acksEn{#1}}
\providecommand{\inscriptionEn}[1]{\gdef\@inscriptionEn{%
  \vspace*{0.2\textheight}%
  \begin{flushright}#1\end{flushright}%
}}
\providecommand{\prefaceEn}[1]{\gdef\@prefaceEn{#1}}

% Subject area and keywords (printed under each abstract).
\providecommand{\subjectAreaGr}[1]{\gdef\@subjectAreaGr{#1}}
\providecommand{\subjectAreaEn}[1]{\gdef\@subjectAreaEn{#1}}
\providecommand{\keywordsGr}[1]{\gdef\@keywordsGr{#1}}
\providecommand{\keywordsEn}[1]{\gdef\@keywordsEn{#1}}

% List-of-publications source file (PhD only; unused for BSc).
\providecommand{\lopfile}[1]{%
  \newcites{lop}{List of publications}\gdef\@lopfileinternal{#1}}

% Unnumbered, ToC-listed chapter that holds the abbreviations table. The user
% supplies the table body after calling \abbreviations.
\providecommand{\abbreviations}{%
  \chapter*{ABBREVIATIONS - ACRONYMS}%
  \addcontentsline{toc}{chapter}{ABBREVIATIONS - ACRONYMS}%
}

% =============================================================================
% Title page and approval (inner-cover) page
% =============================================================================
%
% One builder renders both language variants; \ifenglishfrontpage and
% \ifenglishcommitteepage select which language the current pass emits.

\def\@frontpage{%
  \begin{center}
    \includegraphics[scale=0.85]{emblems/athena-black}
  \end{center}
  \begin{minipage}[t]{\textwidth}
    \begin{center}
      {\large \bfseries
        \ifenglishfrontpage
          NATIONAL AND KAPODISTRIAN UNIVERSITY OF ATHENS
        \else
          ΕΘΝΙΚΟ ΚΑΙ ΚΑΠΟΔΙΣΤΡΙΑΚΟ ΠΑΝΕΠΙΣΤΗΜΙΟ ΑΘΗΝΩΝ
        \fi}
      \linebreak

      {\bfseries
        \ifenglishfrontpage
          SCHOOL OF SCIENCES \\ DEPARTMENT OF INFORMATICS AND TELECOMMUNICATIONS
        \else
          ΣΧΟΛΗ ΘΕΤΙΚΩΝ ΕΠΙΣΤΗΜΩΝ \\ ΤΜΗΜΑ ΠΛΗΡΟΦΟΡΙΚΗΣ ΚΑΙ ΤΗΛΕΠΙΚΟΙΝΩΝΙΩΝ
        \fi}
      \linebreak\linebreak\linebreak\linebreak\linebreak

      {\bfseries
        \ifenglishfrontpage BSc THESIS \else ΠΤΥΧΙΑΚΗ ΕΡΓΑΣΙΑ \fi}
      \linebreak\linebreak

      {\Large \bfseries
        \ifenglishfrontpage \@titleEn \else \@titleGr \fi}
      \linebreak\linebreak\linebreak

      {\bfseries
        \ifenglishfrontpage
          \@authorFirstEn{} \@authorMiddleEn{} \@authorLastEn
        \else
          \@authorFirstGr{} \@authorMiddleGr{} \@authorLastGr
        \fi}
      \linebreak\linebreak\linebreak
      \linebreak\linebreak\linebreak
      \linebreak\linebreak
    \end{center}
    {%
      \ifenglishfrontpage
        \begin{tabular}{l l}
          \textbf{Supervisor\@supervisorLabelSuffixEn:} & \@thesupervisorslistEn \\
        \end{tabular}
      \else
        \begin{tabular}{l l}
          \textbf{Επιβλέπ\@supervisorLabelSuffixGr:} & \@thesupervisorslistGr \\
        \end{tabular}
      \fi}
  \end{minipage}
  \vfill
  \begin{center}
    {\bfseries \ifenglishfrontpage ATHENS \else ΑΘΗΝΑ \fi}
    \\\vspace*{4mm}
    {\bfseries \ifenglishfrontpage \@dateEn \else \@dateGr \fi}
  \end{center}
  \clearpage
}

\def\@committeepage{%
  \begin{center}
    \vspace*{1.5cm}
    {\bfseries
      \ifenglishcommitteepage BSc THESIS \else ΠΤΥΧΙΑΚΗ ΕΡΓΑΣΙΑ \fi}
    \linebreak

    {\ifenglishcommitteepage \@titleEn \else \@titleGr \fi}
    \linebreak\linebreak\linebreak

    {\bfseries
      \ifenglishcommitteepage
        \@authorFirstEn{} \@authorMiddleEn{} \@authorLastEn
      \else
        \@authorFirstGr{} \@authorMiddleGr{} \@authorLastGr
      \fi
      \vspace{2mm}}
    \linebreak
    {\ifenglishcommitteepage
        {\bfseries S.N.:} \@authorSn
      \else
        {\bfseries Α.Μ.:} \@authorSn
      \fi}
    \linebreak\linebreak\linebreak
    \linebreak\linebreak\linebreak
    \linebreak\linebreak\linebreak
    \linebreak\linebreak\linebreak
    \linebreak\linebreak
  \end{center}
  {%
    \ifenglishcommitteepage
      \begin{tabular}{l l}
        \textbf{SUPERVISOR\MakeUppercase{\@supervisorLabelSuffixEn:}} & \@thesupervisorslistEn \\
      \end{tabular}
    \else
      \begin{tabular}{l l}
        \textbf{ΕΠΙΒΛΕΠ\MakeUppercase{\@supervisorLabelSuffixGr:}} & \@thesupervisorslistGr \\
      \end{tabular}
    \fi}
  \clearpage
}

% =============================================================================
% Abstract, synopsis, dedication, acknowledgements, preface, publications
% =============================================================================

\def\@absEn{%
  \chapter*{Abstract}
  \thispagestyle{empty}
  \@abstractEn{}
  \vfill
  \begin{tabularx}{\textwidth}{l X}
    {\bfseries SUBJECT AREA:} & \@subjectAreaEn
  \end{tabularx}
  \begin{tabularx}{\textwidth}{l X}
    {\bfseries KEYWORDS:} & \@keywordsEn
  \end{tabularx}
}

\def\@absGr{%
  \chapter*{ΠΕΡΙΛΗΨΗ}
  \thispagestyle{empty}
  \begin{greek}\@abstractGr{}\end{greek}
  \vfill
  \begin{tabularx}{\textwidth}{l X}
    {\bfseries ΘΕΜΑΤΙΚΗ ΠΕΡΙΟΧΗ:} & \@subjectAreaGr
  \end{tabularx}
  \begin{tabularx}{\textwidth}{l X}
    {\bfseries ΛΕΞΕΙΣ ΚΛΕΙΔΙΑ:} & \@keywordsGr
  \end{tabularx}
}

\def\@synopsis{%
  \chapter*{ΣΥΝΟΠΤΙΚΗ ΠΑΡΟΥΣΙΑΣΗ}
  \thispagestyle{empty}
  \@synopsisGr{}
  \clearpage
}

\def\@inscr{%
  \cleardoublepage
  \@inscriptionEn{}
  \clearpage
}

\def\@acks{%
  \chapter*{Acknowledgements}
  \thispagestyle{empty}
  \@acksEn{}
  \clearpage
}

\def\@preface{%
  \chapter*{Preface}
  \thispagestyle{empty}
  \@prefaceEn{}
  \clearpage
}

\def\@listofpubs{%
  \bibliographystylelop{unsrt}
  \bibliographylop{\@lopfileinternal}
  \thispagestyle{empty}
  \clearpage
}

% =============================================================================
% Table of contents, list of figures, list of tables
% =============================================================================
\RequirePackage{titletoc}
\RequirePackage[subfigure,titles]{tocloft}

% The table of contents always opens on an empty-styled page, then restores
% the running header and footer.
\let\oldtableofcontents\tableofcontents
\DeclareRobustCommand{\tableofcontents}{%
  \newpage
  \pagestyle{empty}
  \oldtableofcontents
  \clearpage
  \pagestyle{fancy}%
}

% Dotted leaders for section and subsection entries.
\renewcommand{\cftsecleader}{\bfseries\cftdotfill{\cftdotsep}}
\renewcommand{\cftsubsecleader}{\bfseries\cftdotfill{\cftdotsep}}
% A dot after each chapter number.
\renewcommand{\cftchapaftersnum}{.}
% Section entries bold, all entries 10 pt.
\renewcommand{\cftsecfont}{\fontsize{10pt}{12pt}\selectfont\bfseries}
\renewcommand{\cftsubsecfont}{\fontsize{10pt}{12pt}\selectfont}
\renewcommand{\cftsubsubsecfont}{\fontsize{10pt}{12pt}\selectfont}
% Sections flush left; subsections and subsubsections indented under them.
\setlength\cftsubsubsecindent\cftsubsecindent
\setlength\cftsubsecindent\cftsecindent
\setlength{\cftsecindent}{0pt}
% Sections get the same vertical lead-in as chapters.
\setlength\cftbeforesecskip\cftbeforechapskip
% Extra room between a chapter number and its title for double-digit numbers.
\newlength{\tocbinnumwidth}
\settowidth{\tocbinnumwidth}{9}
\addtolength{\cftchapnumwidth}{\tocbinnumwidth}

% =============================================================================
% Front, main, and back matter sequencing
% =============================================================================
%
% \frontmatter renders the mandated department order: title page and its Greek
% translation, approval page and its Greek translation, English then Greek
% abstract, optional dedication and acknowledgements, contents, list of
% figures, list of tables, optional preface.
\renewcommand{\frontmatter}{%
  \pagestyle{empty}

  \englishfrontpagetrue  \@frontpage
  \englishfrontpagefalse \@frontpage

  \englishcommitteepagetrue  \@committeepage
  \englishcommitteepagefalse \@committeepage

  \@absEn
  \@absGr

  \ifinscriptionpage \@inscr \fi
  \ifackpage \@acks \fi

  \addtocontents{toc}{\protect{\pdfbookmark[0]{CONTENTS}{toc}}}
  \tableofcontents

  \cleardoublepage
  \begingroup
    \makeatletter
    \let\ps@plain\ps@empty
    \makeatother
    \pagestyle{empty}
    \listoffigures
    \cleardoublepage
  \endgroup

  \listoftables
  \thispagestyle{empty}

  \ifprefacepage \@preface \fi

  \clearpage
  \thispagestyle{empty}%
}

% Main and back matter run with the fancy page style (running header/footer).
\renewcommand{\mainmatter}{\pagestyle{fancy}}
\renewcommand{\backmatter}{\pagestyle{fancy}}

% =============================================================================
% Chapter and section heading style
% =============================================================================
%
% Chapter titles are centred, bold, all caps, and prefixed with the chapter
% number, or "APPENDIX <n>." once the appendix region has started.
\def\@makechapterhead#1{%
  {\parindent \z@ \raggedright \normalfont
    \interlinepenalty\@M
    \ifappendixstarted
      \large \centering \bfseries APPENDIX \thechapter. \MakeTextUppercase{#1}
    \else
      \large \centering \bfseries \thechapter. \MakeTextUppercase{#1}
    \fi
    \par\nobreak
    \vskip 20\p@}%
}
\chaptertitlefont{\vspace*{-2.38cm} \large \centering \MakeTextUppercase}
\sectionfont{\normalsize}
\subsectionfont{\normalsize}
\subsubsectionfont{\normalsize}
\paragraphfont{\normalsize}
\subparagraphfont{\normalsize}

% =============================================================================
% Bibliography, depth, and paragraph layout
% =============================================================================
\renewcommand{\bibname}{REFERENCES}
% Number headings down to subsection only. A subsubsection therefore carries
% no number (no four-component chapter.section.subsection.subsubsection label)
% but keeps its heading and its place in the table of contents, so the visual
% hierarchy below a subsection is preserved without the deep numbering.
\setcounter{tocdepth}{4}
\setcounter{secnumdepth}{2}

% Paragraphs are separated by vertical space, not indentation; single line
% spacing; 6 pt after each paragraph (department template).
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\linespread{1}

% =============================================================================
% Running header and footer
% =============================================================================
%
% Header: thesis title (left). Footer: author short name (left) and page
% number (right, or centred under the dualpage option). No header rule. The
% plain page style (set automatically by \chapter) is redefined to match so
% chapter-opening pages carry the same header and footer.
\fancyhf{}
\fancyhead[LEO]{{\scriptsize \@titleEn{}}}
\ifdualpage
  \fancyfoot[C]{{\fontsize{10pt}{10pt}\selectfont \thepage}}
\else
  \fancyfoot[R]{{\fontsize{10pt}{10pt}\selectfont \thepage}}
\fi
\fancyfoot[LE,LO]{{\scriptsize \@authorFirstAbrEn{} \@authorLastEn{}}}

\fancypagestyle{plain}{%
  \fancyhf{}
  \fancyhead[LO]{{\scriptsize \@titleEn{}}}
  \ifdualpage
    \fancyfoot[C]{{\fontsize{10pt}{10pt}\selectfont \thepage}}
  \else
    \fancyfoot[R]{{\fontsize{10pt}{10pt}\selectfont \thepage}}
  \fi
  \fancyfoot[LE,LO]{{\scriptsize \@authorFirstAbrEn{} \@authorLastEn{}}}%
}
\renewcommand{\headrulewidth}{0pt}

% The first contents page must carry the empty page style.
\AtBeginDocument{\addtocontents{toc}{\protect\thispagestyle{empty}}}

\endinput

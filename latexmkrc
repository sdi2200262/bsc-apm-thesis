#!/usr/bin/env perl
##
## LaTeX Makefile Configuration for latexmk
##
## This configuration file defines compilation settings for LaTeX documents
## in the BSc APM Thesis repository. It ensures that:
## - Auxiliary files are stored in a dedicated build/ directory
## - PDF outputs are placed alongside their source .tex files
## - The configuration works regardless of the current working directory
##

use strict;
use warnings;
use Cwd qw(abs_path getcwd);
use File::Spec;
use File::Basename;

# Disable strict vars for latexmk configuration variables
# These are global variables expected by latexmk, not regular Perl variables
no strict 'vars';

# Suppress 'once' warnings for latexmk configuration variables
# These variables are set once and then used by latexmk's runtime, not by our code
no warnings 'once';

# ============================================================================
# Compilation Mode Configuration
# ============================================================================

$pdf_mode = 1;      # Generate PDF output
$postscript_mode = 0;
$dvi_mode = 0;

# ============================================================================
# Repository Root Detection
# ============================================================================

sub find_repository_root {
    ##
    ## Locates the repository root by searching upward from the current directory
    ## for the latexmkrc file. This ensures the build directory is always relative
    ## to the repository root, regardless of the current working directory.
    ##
    ## Returns:
    ##     Absolute path to the repository root directory
    ##
    my $current_dir = getcwd();
    my $search_dir = $current_dir;
    
    while (1) {
        my $latexmkrc_path = File::Spec->catfile($search_dir, 'latexmkrc');
        if (-f $latexmkrc_path) {
            return abs_path($search_dir);
        }
        
        my $parent_dir = File::Spec->catdir($search_dir, File::Spec->updir());
        last if $parent_dir eq $search_dir;  # Reached filesystem root
        $search_dir = $parent_dir;
    }
    
    # Fallback: use current directory if latexmkrc not found
    # This should not occur in normal operation
    return abs_path($current_dir);
}

my $repo_root = find_repository_root();

# ============================================================================
# Build Directory Configuration
# ============================================================================

sub ensure_build_directory {
    ##
    ## Creates the build directory if it does not exist.
    ##
    ## Parameters:
    ##     $build_path - Absolute path to the build directory
    ##
    ## Dies if the directory cannot be created.
    ##
    my ($build_path) = @_;
    
    unless (-d $build_path) {
        unless (mkdir $build_path) {
            die "Error: Cannot create build directory: $build_path\n";
        }
    }
    
    return $build_path;
}

my $build_dir = File::Spec->catdir($repo_root, 'build');
ensure_build_directory($build_dir);

# ============================================================================
# Bibliography Input Path Configuration
# ============================================================================
#
# bibtex runs from the aux_dir (build/) and searches for .bib files via the
# BIBINPUTS environment variable. Because references.bib lives alongside its
# .tex file in chapters/<chapter>/ rather than at the repo root, we extend
# BIBINPUTS to include the evaluation chapter directory so bibtex can resolve
# \bibliography{references} during compilation.

my $eval_chapter_dir = File::Spec->catdir($repo_root, 'chapters', 'evaluation');
my $existing_bibinputs = $ENV{BIBINPUTS} // '';
$ENV{BIBINPUTS} = join(':', $eval_chapter_dir, $existing_bibinputs, '');

# ============================================================================
# Output Directory Configuration
# ============================================================================

# Auxiliary files (.aux, .log, .out, etc.) are stored in the build directory
$aux_dir = $build_dir;

# PDF files are initially compiled to the build directory, then moved to
# the source directory via the success command hook
$out_dir = $build_dir;

# ============================================================================
# PDF Post-Processing Hook
# ============================================================================

sub create_pdf_relocation_command {
    ##
    ## Generates a command string that relocates the compiled PDF from the build
    ## directory to the source directory (alongside the .tex file).
    ##
    ## The command searches for the source .tex file in common locations and
    ## copies the PDF to that directory upon successful compilation.
    ##
    ## Returns:
    ##     Command string for latexmk's $success_cmd variable
    ##
    # Embedded Perl script that will be executed by latexmk's success command
    # Uses single-quoted heredoc to prevent variable interpolation
    my $script = <<'ENDPERL';
use strict;
use warnings;
use File::Spec;
use File::Basename;
use File::Copy;

my $pdf_path = shift;
unless (defined $pdf_path && -f $pdf_path) {
    exit 1;
}

my $pdf_name = basename($pdf_path, '.pdf');
my $repo_root = shift;

unless (defined $repo_root && -d $repo_root) {
    exit 1;
}

# Search directories in order of preference
my @search_dirs = (
    File::Spec->catdir($repo_root, 'chapters', 'evaluation'),
    File::Spec->catdir($repo_root, 'chapters'),
    $repo_root
);

for my $search_dir (@search_dirs) {
    my $tex_file = File::Spec->catfile($search_dir, "$pdf_name.tex");
    
    if (-f $tex_file) {
        my $target_pdf = File::Spec->catfile($search_dir, "$pdf_name.pdf");
        
        # Only copy if source and target differ
        if ($pdf_path ne $target_pdf) {
            if (copy($pdf_path, $target_pdf)) {
                exit 0;
            }
        } else {
            exit 0;  # Already in correct location
        }
    }
}

exit 1;  # Source .tex file not found
ENDPERL

    # Escape single quotes for safe embedding in shell command
    # This allows the script to be passed as a single argument to perl -e
    $script =~ s/'/'\\''/g;
    
    # Return command string: %D will be replaced by latexmk with the PDF path
    return "perl -e '$script' %D '$repo_root'";
}

$success_cmd = create_pdf_relocation_command();

# ============================================================================
# PDF Viewer Configuration
# ============================================================================

# Configure PDF viewer for macOS (Preview.app)
# Alternative: Uncomment the following line to use Skim instead
# $pdf_previewer = 'open -a Skim %O %S';
$pdf_previewer = 'open -a Preview %O %S';

# ============================================================================
# Compilation Behavior Configuration
# ============================================================================

# Enable file change tracking for automatic recompilation
$recorder = 1;

# Maximum number of LaTeX compilation passes
# LaTeX may require multiple passes to resolve cross-references
$max_repeat = 5;

# ============================================================================
# File Management Configuration
# ============================================================================

# Additional file extensions to track as generated files
push @generated_exts, 'synctex.gz';

# File extensions to remove when running 'latexmk -c' (clean mode)
@clean_ext = qw(aux out bbl blg fls fdb_latexmk);

# ============================================================================
# Output Verbosity
# ============================================================================

# Set to 1 for verbose output during compilation
$verbose = 0;

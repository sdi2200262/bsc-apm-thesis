#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Audit consecutive Spec-kit releases for changes to the instructions reaching the agent.

The study's Spec-kit sessions ran a span of releases rather than one pinned version, so
each release is compared against the one before it. What is compared is the project
tree that ``specify init`` installs under the study's own configuration, since the CLI
renders the command templates as it installs them and that rendering layer changed
within the span. The audited surface is what the coding agent reads: the command
bundles, the templates they fill, the scripts they run, and the agent context file. The
files the command-line tool keeps for itself are held aside, and the rest are compared
byte for byte.

Two things are written under ``generated/``. The diffs are one unified diff per release
step, empty where a release leaves the files identical, and they carry the substance of
what changed, which only reading them establishes. The manifest records each release
with its tag date, its commit, and the SHA-256 of every file it installs, which ties
the diffs to the releases they are drawn from and lets a later reader confirm that the
tree they install is the tree that was audited.

Both outputs are free of timestamps, so ``--check`` can re-derive them and compare byte
for byte against the committed copy.
"""

from __future__ import annotations

import argparse
import difflib
import filecmp
import hashlib
import itertools
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPOSITORY = "https://github.com/github/spec-kit"

# Files the command-line tool keeps for itself: the record of what was installed and
# when, and the workflow definition its runner follows to drive the commands from a
# terminal. The coding agent reads none of them.
CLI_ONLY_FILES = (
    ".specify/init-options.json",
    ".specify/integration.json",
    ".specify/integrations/claude.manifest.json",
    ".specify/integrations/speckit.manifest.json",
    ".specify/workflows/speckit/workflow.yml",
    ".specify/workflows/workflow-registry.json",
)

MANIFEST_NAME = "manifest.json"
DIFF_DIR_NAME = "diffs"


@dataclass(frozen=True)
class Release:
    """One audited Spec-kit release and the tree it installs.

    Attributes:
        tag: Release tag, e.g. ``v0.8.5``.
        date: Tag date as ``YYYY-MM-DD``.
        commit: Full commit hash the tag points at.
        files: Installed file path, relative to the project root, to its SHA-256.
        contents: Installed file path to its decoded text.
    """

    tag: str
    date: str
    commit: str
    files: dict[str, str]
    contents: dict[str, str]


def run(command: list[str], cwd: Path | None = None) -> str:
    """Run ``command`` and return its standard output.

    Args:
        command: Argument vector to execute.
        cwd: Working directory, defaulting to the current one.

    Returns:
        The command's standard output, with trailing newlines stripped.

    Raises:
        SystemExit: If the command is unavailable or exits non-zero.
    """
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        raise SystemExit(f"required command not found: {command[0]}") from None
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"{' '.join(command)} failed:\n{error.stderr}") from None
    return result.stdout.rstrip("\n")


def clone_metadata(work: Path) -> Path:
    """Clone the Spec-kit repository without blobs, for tag enumeration and dating.

    Args:
        work: Directory to clone into.

    Returns:
        Path to the bare clone.
    """
    bare = work / "spec-kit.git"
    run(["git", "clone", "--bare", "--quiet", "--filter=blob:none", REPOSITORY, str(bare)])
    return bare


def span_tags(bare: Path, first: str, last: str) -> list[tuple[str, str, str]]:
    """Return every release tag from ``first`` to ``last`` inclusive, in release order.

    Args:
        bare: Path to the bare clone.
        first: Earliest tag in the span.
        last: Latest tag in the span.

    Returns:
        One ``(tag, date, commit)`` triple per release, ordered by version.

    Raises:
        SystemExit: If either bound is absent from the repository.
    """
    ordered = run(["git", "tag", "--sort=version:refname"], cwd=bare).splitlines()
    for bound in (first, last):
        if bound not in ordered:
            raise SystemExit(f"tag not found in {REPOSITORY}: {bound}")
    tags = ordered[ordered.index(first) : ordered.index(last) + 1]
    return [
        (
            tag,
            run(["git", "log", "-1", "--format=%cs", tag], cwd=bare),
            run(["git", "rev-list", "-1", tag], cwd=bare),
        )
        for tag in tags
    ]


def install(tag: str, destination: Path, integration: str, script: str) -> Path:
    """Install a Spec-kit release into a fresh project directory.

    Args:
        tag: Release tag to install.
        destination: Directory to create the project under.
        integration: Coding agent to install for, as ``specify init --ai`` names it.
        script: Script flavour to install, as ``specify init --script`` names it.

    Returns:
        Path to the installed project root.
    """
    destination.mkdir(parents=True, exist_ok=True)
    run(
        [
            "uvx",
            "--from",
            f"git+{REPOSITORY}.git@{tag}",
            "specify",
            "init",
            "project",
            "--ai",
            integration,
            "--script",
            script,
            "--no-git",
            "--force",
        ],
        cwd=destination,
    )
    return destination / "project"


def read_tree(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Hash and read every installed file the coding agent reads.

    Args:
        root: Installed project root.

    Returns:
        A ``(hashes, contents)`` pair, both keyed by path relative to ``root``.
    """
    hashes: dict[str, str] = {}
    contents: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in CLI_ONLY_FILES:
            continue
        payload = path.read_bytes()
        hashes[relative] = hashlib.sha256(payload).hexdigest()
        contents[relative] = payload.decode("utf-8")
    return hashes, contents


def compare(previous: Release, release: Release) -> str:
    """Diff one release against the one before it.

    Args:
        previous: The earlier release.
        release: The later release.

    Returns:
        A unified diff across every installed file that differs, empty where the two
        installations match.
    """
    diff: list[str] = []
    for path in sorted(set(previous.contents) | set(release.contents)):
        before = previous.contents.get(path, "").splitlines()
        after = release.contents.get(path, "").splitlines()
        if before == after:
            continue
        diff.extend(
            difflib.unified_diff(
                before, after, fromfile=f"a/{path}", tofile=f"b/{path}", lineterm=""
            )
        )
    return "\n".join(diff) + "\n" if diff else ""


def write_outputs(output_dir: Path, releases: list[Release], integration: str, script: str) -> None:
    """Write the manifest and one diff per release step.

    Args:
        output_dir: Directory to write under, created if absent.
        releases: Every audited release, in release order.
        integration: Coding agent the audit installed for.
        script: Script flavour the audit installed.
    """
    diff_dir = output_dir / DIFF_DIR_NAME
    if diff_dir.exists():
        shutil.rmtree(diff_dir)
    diff_dir.mkdir(parents=True)

    manifest = {
        "repository": REPOSITORY,
        "installed_with": {"integration": integration, "script": script},
        "excluded": list(CLI_ONLY_FILES),
        "releases": [
            {
                "tag": release.tag,
                "date": release.date,
                "commit": release.commit,
                "files": release.files,
            }
            for release in releases
        ],
    }
    (output_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    for previous, release in itertools.pairwise(releases):
        name = f"{previous.tag}..{release.tag}.diff"
        (diff_dir / name).write_text(compare(previous, release), encoding="utf-8")


def differences(left: Path, right: Path) -> list[str]:
    """Return the paths that differ between two generated directories.

    Args:
        left: The committed directory.
        right: The freshly derived directory.

    Returns:
        Relative paths that are missing on either side or differ in content.
    """
    names = {p.relative_to(left).as_posix() for p in left.rglob("*") if p.is_file()}
    names |= {p.relative_to(right).as_posix() for p in right.rglob("*") if p.is_file()}
    return sorted(
        name
        for name in names
        if not (left / name).is_file()
        or not (right / name).is_file()
        or not filecmp.cmp(left / name, right / name, shallow=False)
    )


def main(argv: list[str] | None = None) -> int:
    """Audit the span and write or verify the generated outputs.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code, zero when the audit succeeds and, under ``--check``,
        when the committed outputs match what the audit derives.
    """
    default_output = Path(__file__).resolve().parent / "generated"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", default="v0.8.5", help="earliest release in the span")
    parser.add_argument("--last", default="v0.8.13", help="latest release in the span")
    parser.add_argument("--integration", default="claude", help="coding agent to install for")
    parser.add_argument("--script", default="sh", help="script flavour to install")
    parser.add_argument("--output-dir", type=Path, default=default_output)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed outputs instead of rewriting them",
    )
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as name:
        work = Path(name)
        bare = clone_metadata(work)
        releases = []
        for tag, date, commit in span_tags(bare, args.first, args.last):
            print(f"installing {tag}", file=sys.stderr)
            root = install(tag, work / tag, args.integration, args.script)
            files, contents = read_tree(root)
            releases.append(Release(tag, date, commit, files, contents))

        if not args.check:
            write_outputs(args.output_dir, releases, args.integration, args.script)
            print(f"wrote {len(releases) - 1} release steps to {args.output_dir}", file=sys.stderr)
            return 0

        derived = work / "generated"
        write_outputs(derived, releases, args.integration, args.script)
        if changed := differences(args.output_dir, derived):
            print("committed audit outputs differ:", file=sys.stderr)
            for name in changed:
                print(f"  {name}", file=sys.stderr)
            return 1
        print("committed audit outputs match", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

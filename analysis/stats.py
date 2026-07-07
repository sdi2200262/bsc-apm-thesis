# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) BSc APM Case Study 2025-2026
"""Small exact statistics used by thesis table generators."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median


@dataclass(frozen=True)
class LevelSummary:
    """Median, Hodges-Lehmann estimate, and mean for one sample."""

    median: float
    hl: float
    mean: float


@dataclass(frozen=True)
class PairedSummary:
    """Paired difference summary for one measure."""

    n: int
    positive: int
    negative: int
    zero: int
    median: float
    hl: float
    mean: float
    ci_low: float
    ci_high: float
    coverage: float


def level_summary(values: list[float]) -> LevelSummary:
    """Return the three descriptive summaries for ``values``."""
    if not values:
        raise ValueError("cannot summarise an empty sample")
    return LevelSummary(
        median=float(median(values)),
        hl=hodges_lehmann(values),
        mean=float(mean(values)),
    )


def paired_summary(apm: list[float], speckit: list[float]) -> PairedSummary:
    """Return an exact paired APM-minus-Spec-kit summary."""
    if len(apm) != len(speckit):
        raise ValueError("paired samples must have the same length")
    differences = [a - s for a, s in zip(apm, speckit, strict=True)]
    positives = sum(1 for value in differences if value > 0)
    negatives = sum(1 for value in differences if value < 0)
    zeros = sum(1 for value in differences if value == 0)
    low, high, coverage = wilcoxon_shift_interval(differences)
    return PairedSummary(
        n=len(differences),
        positive=positives,
        negative=negatives,
        zero=zeros,
        median=float(median(differences)),
        hl=hodges_lehmann(differences),
        mean=float(mean(differences)),
        ci_low=low,
        ci_high=high,
        coverage=coverage,
    )


def hodges_lehmann(values: list[float]) -> float:
    """Return the one-sample Hodges-Lehmann estimate."""
    if not values:
        raise ValueError("cannot compute Hodges-Lehmann estimate for an empty sample")
    walsh = sorted((a + b) / 2 for index, a in enumerate(values) for b in values[index:])
    return float(median(walsh))


def wilcoxon_shift_interval(differences: list[float]) -> tuple[float, float, float]:
    """Return an exact signed-rank shift interval from Walsh averages.

    Uses the exact Hollander-Wolfe interval over the sorted Walsh averages
    (d_i + d_j) / 2 for i <= j, computed over the full sample (zero-valued
    differences are not filtered out). The interval is bounded by the
    largest signed-rank critical index whose per-tail probability does not
    exceed 2.5%, so the returned coverage is the exact two-sided coverage
    that search achieves; it varies with ``n`` rather than being fixed.

    Args:
        differences: Paired difference values (APM minus Spec-kit).

    Returns:
        Tuple of ``(low, high, coverage)``: the interval bounds and the
        exact coverage achieved by the critical-index search.
    """
    if not differences:
        return 0.0, 0.0, 1.0
    n = len(differences)
    walsh = sorted((a + b) / 2 for index, a in enumerate(differences) for b in differences[index:])
    m = len(walsh)
    critical, tail_count = _signed_rank_critical(n, target=0.025)
    low_index = min(critical, m - 1)
    high_index = max(0, m - critical - 1)
    total = 2**n
    coverage = 1.0 - (2 * tail_count / total)
    return float(walsh[low_index]), float(walsh[high_index]), coverage


def _signed_rank_critical(n: int, target: float) -> tuple[int, int]:
    """Return the largest signed-rank critical index whose tail stays within target.

    Finds the largest integer C such that the exact null cumulative count
    P(W+ <= C) does not exceed ``target`` (expressed as a fraction of the
    ``2**n`` equally likely sign assignments). This is the monotonic
    threshold search behind the exact Hollander-Wolfe Wilcoxon signed-rank
    confidence interval; it never selects a C whose tail exceeds ``target``.

    Args:
        n: Sample size underlying the signed-rank null distribution.
        target: Maximum per-tail probability, e.g. 0.025.

    Returns:
        Tuple of ``(critical_index, cumulative_count)`` where
        ``cumulative_count`` is the integer count of sign assignments with
        W+ <= ``critical_index``. Falls back to index 0 (with its own
        cumulative count) when even that index's tail exceeds ``target``.
    """
    total = 2**n
    target_count = target * total
    distribution = _rank_sum_distribution(n)
    cumulative = 0
    critical = 0
    critical_count = distribution[0]
    for index, count in enumerate(distribution):
        cumulative += count
        if cumulative > target_count:
            break
        critical = index
        critical_count = cumulative
    return critical, critical_count


def _rank_sum_distribution(n: int) -> list[int]:
    """Return signed-rank statistic counts for ranks 1..``n``."""
    max_sum = n * (n + 1) // 2
    counts = [0] * (max_sum + 1)
    counts[0] = 1
    for rank in range(1, n + 1):
        for value in range(max_sum, rank - 1, -1):
            counts[value] += counts[value - rank]
    expected = 2**n
    if sum(counts) != expected:
        raise AssertionError(f"signed-rank distribution should have {expected} outcomes")
    return counts

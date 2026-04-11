"""
Total score — weighted combination of component scores.

Momentum 40% + Revisions 20% + Valuation 40%
Normalizes weights if a component is missing.
"""

from config import MOMENTUM_WEIGHT, REVISIONS_WEIGHT, VALUATION_WEIGHT


def calculate_total(momentum: float | None, revisions: float | None,
                    valuation: float | None) -> float | None:
    """Calculate weighted total score. Returns None if no components available."""
    parts = []
    weights = []

    if momentum is not None:
        parts.append(momentum * MOMENTUM_WEIGHT)
        weights.append(MOMENTUM_WEIGHT)
    if revisions is not None:
        parts.append(revisions * REVISIONS_WEIGHT)
        weights.append(REVISIONS_WEIGHT)
    if valuation is not None:
        parts.append(valuation * VALUATION_WEIGHT)
        weights.append(VALUATION_WEIGHT)

    if not weights:
        return None

    return round(sum(parts) / sum(weights), 1)

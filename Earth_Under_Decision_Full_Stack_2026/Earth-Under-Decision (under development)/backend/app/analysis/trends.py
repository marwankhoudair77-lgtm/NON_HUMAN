from datetime import datetime
from math import isfinite
from typing import Sequence
import numpy as np
from scipy.stats import kendalltau, theilslopes


class InsufficientTrendData(ValueError):
    pass


def summarize_monotonic_trend(
    dates: Sequence[datetime],
    values: Sequence[float | None],
    *,
    minimum_observations: int = 8,
    assumptions_reviewed: bool = False,
) -> dict:
    """Compute a Theil-Sen slope summary for an already quality-screened series.

    This helper is deliberately not wired to public analysis endpoints yet. A caller
    must establish product QA, temporal semantics, seasonal handling, and autocorrelation
    suitability before treating the result inferentially.
    """
    if len(dates) != len(values):
        raise ValueError("dates and values must have the same length")

    pairs = []
    for date_value, value in zip(dates, values):
        if value is None:
            continue
        numeric = float(value)
        if isfinite(numeric):
            pairs.append((date_value, numeric))
    pairs.sort(key=lambda item: item[0])
    if len(pairs) < minimum_observations:
        raise InsufficientTrendData(
            f"At least {minimum_observations} valid observations are required; found {len(pairs)}."
        )
    if len({item[0] for item in pairs}) != len(pairs):
        raise ValueError("duplicate observation timestamps must be resolved before trend analysis")

    origin = pairs[0][0]
    years = np.array([(date_value - origin).total_seconds() / (365.2425 * 86400) for date_value, _ in pairs])
    data = np.array([value for _, value in pairs], dtype=float)
    if np.ptp(years) <= 0:
        raise ValueError("observations must span a non-zero time interval")

    slope, intercept, low_slope, high_slope = theilslopes(data, years, alpha=0.95)
    tau, p_value = kendalltau(years, data, nan_policy="omit")
    warnings = []
    if not assumptions_reviewed:
        warnings.append("Descriptive result only: seasonality and temporal autocorrelation have not been reviewed by this helper.")
    return {
        "method": "Theil-Sen slope with Kendall tau association statistic",
        "sample_size": int(len(data)),
        "time_span_years": float(years[-1] - years[0]),
        "sen_slope_per_year": float(slope),
        "sen_slope_ci_95": [float(low_slope), float(high_slope)],
        "kendall_tau": float(tau) if np.isfinite(tau) else None,
        "p_value": float(p_value) if assumptions_reviewed and np.isfinite(p_value) else None,
        "inferential_status": "eligible_for_review" if assumptions_reviewed else "descriptive_only",
        "warnings": warnings,
        "note": "Statistical significance does not by itself establish environmental importance or causality.",
    }

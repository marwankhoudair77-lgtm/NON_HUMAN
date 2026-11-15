from datetime import datetime, timedelta, timezone
import pytest
from app.analysis.trends import InsufficientTrendData, summarize_monotonic_trend


def test_trend_helper_is_descriptive_only_without_review():
    dates = [datetime(2015, 1, 1, tzinfo=timezone.utc) + timedelta(days=365 * i) for i in range(10)]
    values = [float(i * 2) for i in range(10)]
    result = summarize_monotonic_trend(dates, values)
    assert result["sample_size"] == 10
    assert result["sen_slope_per_year"] == pytest.approx(2.0, rel=0.02)
    assert result["p_value"] is None
    assert result["inferential_status"] == "descriptive_only"


def test_trend_helper_rejects_small_samples():
    dates = [datetime(2020, 1, 1, tzinfo=timezone.utc) + timedelta(days=i) for i in range(4)]
    with pytest.raises(InsufficientTrendData):
        summarize_monotonic_trend(dates, [1, 2, 3, 4])

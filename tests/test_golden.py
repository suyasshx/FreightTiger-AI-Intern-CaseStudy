"""
RouteGuard AI - Golden Evaluation Tests
Tests pipeline output against the authoritative sample examples in sample_output_format_v2.csv.
Validates numerical rounding, percentage comparisons, flagged verdicts, matched note IDs, and reason text.
"""

import pytest
import pandas as pd
from backend.app.services.pipeline import run_pipeline


@pytest.fixture(scope="module")
def pipeline_results():
    output_df, records, summary = run_pipeline()
    return output_df


def test_golden_delhi_jaipur(pipeline_results):
    """
    Sample row 1: Delhi-Jaipur, week 2024-11-11
    Cost: 4.17
    vs_own_history: +35.5% vs this route's past average
    vs_similar_routes: +21.0% vs similar-length routes this week
    flagged: Yes
    matched_note_id: blank
    """
    row = pipeline_results[
        (pipeline_results["route"] == "Delhi-Jaipur") &
        (pipeline_results["week_of"] == "2024-11-11")
    ]
    assert len(row) == 1
    r = row.iloc[0]

    assert r["cost_per_tonne_km"] == "4.17" or float(r["cost_per_tonne_km"]) == 4.17
    assert r["vs_own_history"] == "+35.5% vs this route's past average"
    assert r["vs_similar_routes"] == "+21.0% vs similar-length routes this week"
    assert r["flagged"] == "Yes"
    assert pd.isna(r["matched_note_id"]) or r["matched_note_id"] == ""
    assert "No matching note found for this route or date range" in r["reason"]


def test_golden_ahmedabad_mumbai(pipeline_results):
    """
    Sample row 2: Ahmedabad-Mumbai, week 2025-01-20
    Cost: 3.29
    vs_own_history: +29.5% vs this route's past average
    vs_similar_routes: +22.5% vs similar-length routes this week
    flagged: No (justified)
    matched_note_id: N002
    """
    row = pipeline_results[
        (pipeline_results["route"] == "Ahmedabad-Mumbai") &
        (pipeline_results["week_of"] == "2025-01-20")
    ]
    assert len(row) == 1
    r = row.iloc[0]

    assert r["cost_per_tonne_km"] == "3.29" or float(r["cost_per_tonne_km"]) == 3.29
    assert r["vs_own_history"] == "+29.5% vs this route's past average"
    assert r["vs_similar_routes"] == "+22.5% vs similar-length routes this week"
    assert r["flagged"] == "No (justified)"
    assert str(r["matched_note_id"]).strip() == "N002"
    assert "Matches note N002 dated 2025-01-20" in r["reason"]


def test_golden_mumbai_pune(pipeline_results):
    """
    Sample row 3: Mumbai-Pune, week 2025-09-15
    Cost: 3.98
    vs_own_history: +9.2% vs this route's past average
    vs_similar_routes: +23.6% vs similar-length routes this week
    flagged: Yes
    matched_note_id: blank
    """
    row = pipeline_results[
        (pipeline_results["route"] == "Mumbai-Pune") &
        (pipeline_results["week_of"] == "2025-09-15")
    ]
    assert len(row) == 1
    r = row.iloc[0]

    assert r["cost_per_tonne_km"] == "3.98" or float(r["cost_per_tonne_km"]) == 3.98
    assert r["vs_own_history"] == "+9.2% vs this route's past average"
    assert r["vs_similar_routes"] == "+23.6% vs similar-length routes this week"
    assert r["flagged"] == "Yes"
    assert pd.isna(r["matched_note_id"]) or r["matched_note_id"] == ""
    assert "The closest note (N006, 2025-09-22)" in r["reason"]

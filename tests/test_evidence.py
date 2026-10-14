"""
RouteGuard AI - Contextual Evidence Gating Unit Tests
Tests each note (N001 through N010) against the 6 hard validation gates:
Route applicability, temporal overlap, causal mechanism, negative disqualifiers,
and magnitude consistency.
"""

import pytest
import pandas as pd
from backend.app.services.evidence_validation import evaluate_note_evidence


def test_n001_chennai_bangalore_flooding():
    """N001 justifies Chennai-Bangalore flooding only during Feb 24 - Mar 8, 2025."""
    note = {
        "note_id": "N001",
        "date": "2025-02-24",
        "applies_to": "Chennai-Bangalore",
        "note": "Heavy flooding on the Chennai-Bangalore highway disrupted normal truck movement from Feb 24 to Mar 8, forcing longer detours and higher trip costs. Roads were passable again by Mar 9."
    }

    # Week 1: 2025-02-24 -> MUST PASS
    res1 = evaluate_note_evidence(note, route="Chennai-Bangalore", week_start=pd.Timestamp("2025-02-24"))
    assert res1.passed_all_gates is True
    assert res1.route_gate.passed is True
    assert res1.temporal_gate.passed is True
    assert res1.causal_gate.passed is True

    # Week 2: 2025-03-03 (overlaps Mar 3 - Mar 8) -> MUST PASS
    res2 = evaluate_note_evidence(note, route="Chennai-Bangalore", week_start=pd.Timestamp("2025-03-03"))
    assert res2.passed_all_gates is True

    # Week 3: 2025-03-10 (roads passable Mar 9) -> MUST FAIL (Temporal gate)
    res3 = evaluate_note_evidence(note, route="Chennai-Bangalore", week_start=pd.Timestamp("2025-03-10"))
    assert res3.passed_all_gates is False
    assert res3.temporal_gate.passed is False

    # Route Mismatch: Mumbai-Pune during flood week -> MUST FAIL (Route gate)
    res4 = evaluate_note_evidence(note, route="Mumbai-Pune", week_start=pd.Timestamp("2025-02-24"))
    assert res4.passed_all_gates is False
    assert res4.route_gate.passed is False


def test_n002_ahmedabad_mumbai_festival_surcharge():
    """N002 justifies Ahmedabad-Mumbai festival surcharge only for week of 2025-01-20."""
    note = {
        "note_id": "N002",
        "date": "2025-01-20",
        "applies_to": "Ahmedabad-Mumbai",
        "note": "A regional festival week saw a temporary surcharge applied by transporters on the Ahmedabad-Mumbai corridor due to high demand and limited truck availability."
    }

    # Week of festival -> PASS
    res = evaluate_note_evidence(note, route="Ahmedabad-Mumbai", week_start=pd.Timestamp("2025-01-20"))
    assert res.passed_all_gates is True

    # Later week in February -> FAIL
    res_late = evaluate_note_evidence(note, route="Ahmedabad-Mumbai", week_start=pd.Timestamp("2025-02-17"))
    assert res_late.passed_all_gates is False
    assert res_late.temporal_gate.passed is False


def test_n003_diesel_price_magnitude_gate():
    """N003 applies nationwide to May 5, 2025, but cannot justify massive 35% spikes alone."""
    note = {
        "note_id": "N003",
        "date": "2025-05-05",
        "applies_to": "All Routes",
        "note": "Diesel prices rose nationwide starting this week, pushing up transportation costs across all routes by roughly 5-7%."
    }

    # Route with consistent ~6% rise -> PASS
    res_modest = evaluate_note_evidence(
        note, route="Delhi-Jaipur", week_start=pd.Timestamp("2025-05-05"), observed_hist_pct=6.5
    )
    assert res_modest.passed_all_gates is True

    # Route with massive 35% spike -> FAIL magnitude consistency
    res_extreme = evaluate_note_evidence(
        note, route="Delhi-Jaipur", week_start=pd.Timestamp("2025-05-05"), observed_hist_pct=35.0
    )
    assert res_extreme.passed_all_gates is False
    assert res_extreme.magnitude_gate.passed is False


def test_n004_unincluded_routes_rejected():
    """N004 must NEVER justify any route because the highway stretch is not part of this dataset."""
    note = {
        "note_id": "N004",
        "date": "2024-03-11",
        "applies_to": "All Routes",
        "note": "A new toll plaza was commissioned on a national highway stretch, but the affected routes are not part of this dataset."
    }
    res = evaluate_note_evidence(note, route="Delhi-Jaipur", week_start=pd.Timestamp("2024-03-11"))
    assert res.passed_all_gates is False
    assert res.route_gate.passed is False


def test_n005_costs_unaffected_rejected():
    """N005 must NEVER justify an increase because costs were not significantly affected."""
    note = {
        "note_id": "N005",
        "date": "2024-07-29",
        "applies_to": "Mumbai-Delhi",
        "note": "Scheduled highway maintenance work between Mumbai and Delhi caused minor delays for about a week; costs were not significantly affected."
    }
    res = evaluate_note_evidence(note, route="Mumbai-Delhi", week_start=pd.Timestamp("2024-07-29"))
    assert res.passed_all_gates is False
    assert res.negative_filter_gate.passed is False


def test_n006_and_n008_normal_conditions_rejected():
    """N006 and N008 report stable demand and normal movement; must NEVER justify a price increase."""
    n006 = {
        "note_id": "N006",
        "date": "2025-09-22",
        "applies_to": "All Routes",
        "note": "A logistics industry report noted overall demand for freight capacity remained stable this quarter with no major disruptions reported."
    }
    res6 = evaluate_note_evidence(n006, route="Mumbai-Pune", week_start=pd.Timestamp("2025-09-22"))
    assert res6.passed_all_gates is False
    assert res6.negative_filter_gate.passed is False

    n008 = {
        "note_id": "N008",
        "date": "2025-06-09",
        "applies_to": "Kolkata-Bhubaneswar",
        "note": "No significant disruptions were reported on the Kolkata-Bhubaneswar corridor this quarter; freight movement remained normal."
    }
    res8 = evaluate_note_evidence(n008, route="Kolkata-Bhubaneswar", week_start=pd.Timestamp("2025-06-09"))
    assert res8.passed_all_gates is False
    assert res8.negative_filter_gate.passed is False


def test_n007_and_n009_improvements_and_recovery_rejected():
    """N007 (road resurfacing improvement) and N009 (post-flood repair recovery) do NOT justify increases."""
    n007 = {
        "note_id": "N007",
        "date": "2024-05-20",
        "applies_to": "Delhi-Jaipur",
        "note": "Local authorities announced improved road conditions on the Delhi-Jaipur stretch after resurfacing work was completed."
    }
    res7 = evaluate_note_evidence(n007, route="Delhi-Jaipur", week_start=pd.Timestamp("2024-05-20"))
    assert res7.passed_all_gates is False
    assert res7.negative_filter_gate.passed is False

    n009 = {
        "note_id": "N009",
        "date": "2025-03-17",
        "applies_to": "Chennai-Bangalore",
        "note": "Highway authorities confirmed the Chennai-Bangalore route returned to normal conditions after flood-related repairs were completed."
    }
    res9 = evaluate_note_evidence(n009, route="Chennai-Bangalore", week_start=pd.Timestamp("2025-03-17"))
    assert res9.passed_all_gates is False
    assert res9.negative_filter_gate.passed is False


def test_n010_costs_absorbed_rejected():
    """N010 states fleet compliance costs were absorbed without rate change; must NEVER justify rate increase."""
    n010 = {
        "note_id": "N010",
        "date": "2025-10-27",
        "applies_to": "All Routes",
        "note": "A new vehicle tracking mandate was introduced for commercial fleets; compliance costs were absorbed by transporters without a rate change."
    }
    res10 = evaluate_note_evidence(n010, route="Mumbai-Pune", week_start=pd.Timestamp("2025-10-27"))
    assert res10.passed_all_gates is False
    assert res10.negative_filter_gate.passed is False

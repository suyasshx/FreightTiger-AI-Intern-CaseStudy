"""
RouteGuard AI - API Endpoints Integration Tests
Tests REST endpoints using FastAPI TestClient to ensure end-to-end API correctness.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["shipments_file_exists"] is True
    assert data["notes_file_exists"] is True


def test_api_overview():
    response = client.get("/api/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_route_weeks"] == 728
    assert data["unexplained_anomalies"] == 24
    assert data["justified_anomalies"] == 3
    assert data["normal_route_weeks"] == 701
    assert "route_breakdown" in data
    assert "weekly_trend" in data


def test_api_routes_pagination_and_filtering():
    # Filter by route
    res = client.get("/api/routes?route=Ahmedabad-Mumbai")
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] == 104  # 104 weeks of data

    # Filter by verdict = 'No (justified)'
    res_justified = client.get("/api/routes?flagged=No (justified)")
    assert res_justified.status_code == 200
    data_j = res_justified.json()
    assert data_j["total_records"] == 3
    for item in data_j["items"]:
        assert item["flagged"] == "No (justified)"
        assert item["matched_note_id"] in ["N001", "N002"]


def test_api_route_timeseries():
    res = client.get("/api/routes/timeseries/Chennai-Bangalore")
    assert res.status_code == 200
    data = res.json()
    assert data["route"] == "Chennai-Bangalore"
    assert data["total_weeks"] == 104
    assert len(data["data"]) == 104


def test_api_notes():
    res = client.get("/api/notes")
    assert res.status_code == 200
    notes = res.json()
    assert len(notes) == 10
    note_ids = {n["note_id"] for n in notes}
    assert "N001" in note_ids
    assert "N010" in note_ids


def test_api_evidence_detail():
    res = client.get("/api/evidence/Ahmedabad-Mumbai/2025-01-20")
    assert res.status_code == 200
    data = res.json()
    assert data["route"] == "Ahmedabad-Mumbai"
    assert data["week_of"] == "2025-01-20"
    assert data["flagged"] == "No (justified)"
    assert data["matched_note_id"] == "N002"
    assert len(data["candidates_evaluated"]) > 0


def test_api_chat_assistant():
    payload = {"question": "Why did Ahmedabad-Mumbai cost increase in January 2025?"}
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "Ahmedabad-Mumbai" in data["answer"]
    assert "N002" in data["evidence_notes"] or "N002" in data["answer"]
    assert data["grounded_in_computation"] is True


def test_api_cost_log():
    res = client.get("/api/cost-log")
    assert res.status_code == 200
    data = res.json()
    assert data["dataset_records_count"] == 2940
    assert data["total_route_weeks"] == 728
    assert data["estimated_api_cost"] == 0.0


def test_api_export_csv():
    res = client.get("/api/export/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    content = res.text
    assert "route,week_of,cost_per_tonne_km,vs_own_history,vs_similar_routes,flagged,matched_note_id,reason" in content

"""
RouteGuard AI - Data Ingestion and Validation Service
Loads shipment records and contextual notes, enforces strict schema integrity,
parses ISO Monday calendar weeks, and audits data quality.
"""

from pathlib import Path
from typing import Dict, Tuple, Any
import pandas as pd
import numpy as np


REQUIRED_SHIPMENT_COLUMNS = {
    "shipment_id", "origin", "destination", "route_type", "material",
    "quantity_tonnes", "distance_km", "freight_cost_inr", "shipment_date", "transporter"
}

REQUIRED_NOTE_COLUMNS = {"note_id", "date", "applies_to", "note"}


def format_route_name(origin: str, destination: str) -> str:
    """Format canonical directional route string: 'Origin-Destination'."""
    return f"{str(origin).strip()}-{str(destination).strip()}"


def compute_monday_week(dt: pd.Series) -> pd.Series:
    """
    Compute Monday start date for any calendar date.
    Weeks run Monday through Sunday; week_of is the Monday in YYYY-MM-DD.
    """
    # weekday(): Monday is 0, Sunday is 6
    deltas = pd.to_timedelta(dt.dt.weekday, unit="D")
    return (dt - deltas).dt.normalize()


def load_and_validate_datasets(
    shipments_path: str | Path,
    notes_path: str | Path
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Ingest, clean, and validate shipment records and context notes.
    Returns:
        shipments_clean: pd.DataFrame
        notes_clean: pd.DataFrame
        quality_report: Dict with auditing diagnostics
    """
    s_path = Path(shipments_path)
    n_path = Path(notes_path)

    if not s_path.exists():
        raise FileNotFoundError(f"Shipment records file not found at: {s_path}")
    if not n_path.exists():
        raise FileNotFoundError(f"Context notes file not found at: {n_path}")

    # Load raw CSVs using utf-8-sig to safely handle Excel BOMs
    shipments_raw = pd.read_csv(s_path, encoding="utf-8-sig")
    notes_raw = pd.read_csv(n_path, encoding="utf-8-sig")

    quality_report: Dict[str, Any] = {
        "raw_shipments_count": len(shipments_raw),
        "raw_notes_count": len(notes_raw),
        "discarded_shipments_count": 0,
        "discard_reasons": {},
        "warnings": [],
        "route_type_consistency": "verified",
        "date_range": {},
        "unique_routes": []
    }

    # 1. Schema Validation
    missing_shipment_cols = REQUIRED_SHIPMENT_COLUMNS - set(shipments_raw.columns)
    if missing_shipment_cols:
        raise ValueError(f"Shipment CSV missing mandatory columns: {sorted(missing_shipment_cols)}")

    missing_note_cols = REQUIRED_NOTE_COLUMNS - set(notes_raw.columns)
    if missing_note_cols:
        raise ValueError(f"Context notes CSV missing mandatory columns: {sorted(missing_note_cols)}")

    # 2. Type conversions and numeric hygiene
    s_clean = shipments_raw.copy()
    for col in ["quantity_tonnes", "distance_km", "freight_cost_inr"]:
        s_clean[col] = pd.to_numeric(s_clean[col], errors="coerce")

    s_clean["shipment_date"] = pd.to_datetime(s_clean["shipment_date"], errors="coerce")

    # Audit invalid rows
    null_mask = s_clean[list(REQUIRED_SHIPMENT_COLUMNS)].isnull().any(axis=1)
    neg_mask = (
        (s_clean["quantity_tonnes"] <= 0) |
        (s_clean["distance_km"] <= 0) |
        (s_clean["freight_cost_inr"] < 0)
    )

    invalid_mask = null_mask | neg_mask
    discarded_count = int(invalid_mask.sum())
    quality_report["discarded_shipments_count"] = discarded_count
    if discarded_count > 0:
        quality_report["discard_reasons"]["null_fields"] = int(null_mask.sum())
        quality_report["discard_reasons"]["non_positive_values"] = int(neg_mask.sum())

    s_clean = s_clean[~invalid_mask].copy()

    # Canonical route name and Monday calendar week
    s_clean["route"] = [
        format_route_name(o, d) for o, d in zip(s_clean["origin"], s_clean["destination"])
    ]
    s_clean["week_of"] = compute_monday_week(s_clean["shipment_date"])
    s_clean["tonne_km"] = s_clean["quantity_tonnes"] * s_clean["distance_km"]

    # Verify route_type consistency per route
    route_type_map = s_clean.groupby("route")["route_type"].nunique()
    inconsistent = route_type_map[route_type_map > 1]
    if not inconsistent.empty:
        quality_report["warnings"].append(
            f"Routes with multiple route_types detected: {inconsistent.to_dict()}"
        )
        quality_report["route_type_consistency"] = "warning"

    quality_report["unique_routes"] = sorted(s_clean["route"].unique().tolist())
    quality_report["date_range"] = {
        "min_date": s_clean["shipment_date"].min().strftime("%Y-%m-%d"),
        "max_date": s_clean["shipment_date"].max().strftime("%Y-%m-%d"),
        "min_week_of": s_clean["week_of"].min().strftime("%Y-%m-%d"),
        "max_week_of": s_clean["week_of"].max().strftime("%Y-%m-%d"),
    }

    # 3. Clean notes
    n_clean = notes_raw.copy()
    n_clean["date"] = pd.to_datetime(n_clean["date"], errors="coerce")
    n_clean = n_clean.dropna(subset=["note_id", "date", "applies_to", "note"]).copy()
    n_clean["note_id"] = n_clean["note_id"].astype(str).str.strip()
    n_clean["applies_to"] = n_clean["applies_to"].astype(str).str.strip()
    n_clean["note"] = n_clean["note"].astype(str).str.strip()

    return s_clean, n_clean, quality_report

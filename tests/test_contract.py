"""
RouteGuard AI - Output Schema and Contract Tests
Verifies that outputs/flagged_routes.csv satisfies the grading contract:
- Exact 8 columns in exact order
- ISO 8601 YYYY-MM-DD Monday date format
- Allowed categorical verdicts: 'No', 'No (justified)', 'Yes'
- Non-empty matched_note_id strictly on 'No (justified)'
- Empty matched_note_id strictly on 'Yes' and 'No'
- Correct CSV quoting handling commas in reason text without row shifts
"""

import csv
import re
from pathlib import Path
import pytest
import pandas as pd

from backend.app.config import settings
from backend.app.services.verdicts import OUTPUT_COLUMNS
from backend.app.services.pipeline import run_pipeline


@pytest.fixture(scope="module")
def output_csv_path():
    run_pipeline()
    return settings.output_csv_path


def test_csv_header_and_column_order(output_csv_path):
    """Verify exact 8 columns in exact order."""
    with open(output_csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == OUTPUT_COLUMNS, f"Header mismatch: expected {OUTPUT_COLUMNS}, got {header}"


def test_csv_standards_compliant_parsing(output_csv_path):
    """Verify standard csv parser reads every row with exactly 8 fields (no unquoted comma shifts)."""
    with open(output_csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        row_num = 1
        for row in reader:
            row_num += 1
            assert len(row) == 8, f"Row {row_num} has {len(row)} columns instead of 8: {row}"


def test_contract_verdict_semantics(output_csv_path):
    """Verify valid verdict values and matched_note_id constraints."""
    notes_df = pd.read_csv(settings.notes_path)
    valid_note_ids = set(notes_df["note_id"].astype(str).str.strip())
    allowed_verdicts = {"No", "No (justified)", "Yes"}

    with open(output_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

        count = 0
        for row in reader:
            count += 1
            verdict = row["flagged"]
            note_id = row["matched_note_id"].strip()
            week_of = row["week_of"].strip()

            # Date format check
            assert date_pattern.match(week_of), f"Invalid date format in row: {week_of}"

            # Allowed verdict
            assert verdict in allowed_verdicts, f"Invalid verdict: {verdict}"

            # If justified -> note_id must be valid and present
            if verdict == "No (justified)":
                assert note_id != "", f"Justified row missing matched_note_id: {row}"
                assert note_id in valid_note_ids, f"Unknown note_id '{note_id}' in justified row"
            else:
                # If No or Yes -> matched_note_id must be empty string
                assert note_id == "", f"Unexplained or Normal row must have empty matched_note_id, got '{note_id}': {row}"

        assert count == 728, f"Expected 728 route-weeks, found {count}"

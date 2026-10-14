"""
RouteGuard AI - 3-Run Deterministic Reproducibility Audit
Executes 3 complete, untouched pipeline runs on identical inputs.
Compares exact outputs, column ordering, numerical values, verdicts, matched note IDs,
and cryptographic SHA-256 hashes across all 3 independent executions.
"""

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

# Set up path
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

from backend.app.config import settings
from backend.app.services.pipeline import run_pipeline, compute_sha256


def execute_reproducibility_audit() -> dict:
    print("=================================================================")
    print(" RouteGuard AI — 3-Run Reproducibility Verification")
    print("=================================================================")

    runs_dir = settings.output_csv_path.parent / "reproducibility_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    run_artifacts = []
    run_hashes = []
    dataframes = []

    for run_num in range(1, 4):
        run_file = runs_dir / f"flagged_routes_run_{run_num}.csv"
        print(f"\n[Execution {run_num}/3] Running pipeline independently...")
        start_t = time.time()

        out_df, records, summary = run_pipeline(
            output_path=run_file,
            history_threshold_pct=15.0,
            peer_threshold_pct=15.0,
            trailing_weeks=8
        )
        elapsed = round(time.time() - start_t, 2)
        file_hash = compute_sha256(run_file)

        run_artifacts.append({
            "run_index": run_num,
            "filepath": str(run_file),
            "rows_count": len(out_df),
            "sha256": file_hash,
            "runtime_seconds": elapsed,
            "justified_count": int((out_df["flagged"] == "No (justified)").sum()),
            "unexplained_count": int((out_df["flagged"] == "Yes").sum()),
            "normal_count": int((out_df["flagged"] == "No").sum())
        })
        run_hashes.append(file_hash)
        dataframes.append(out_df)

        print(f"  • Completed in {elapsed}s | SHA-256: {file_hash}")

    # Compare pairwise differences
    df1, df2, df3 = dataframes[0], dataframes[1], dataframes[2]

    # Check identical row count
    rows_match = (len(df1) == len(df2) == len(df3))

    # Check identical columns and order
    cols_match = (list(df1.columns) == list(df2.columns) == list(df3.columns))

    # Check exact equality across numerical fields, flags, and note IDs
    numeric_and_verdicts_match_1_2 = df1.equals(df2)
    numeric_and_verdicts_match_2_3 = df2.equals(df3)
    hashes_identical = (len(set(run_hashes)) == 1)

    all_identical = (
        rows_match and cols_match and
        numeric_and_verdicts_match_1_2 and
        numeric_and_verdicts_match_2_3 and
        hashes_identical
    )

    audit_report = {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_runs": 3,
        "all_runs_identical": all_identical,
        "sha256_identical": hashes_identical,
        "shared_sha256": run_hashes[0] if hashes_identical else "MISMATCH",
        "fields_compared": list(df1.columns),
        "comparisons": {
            "run1_vs_run2_equal": numeric_and_verdicts_match_1_2,
            "run2_vs_run3_equal": numeric_and_verdicts_match_2_3,
            "run1_vs_run3_equal": df1.equals(df3)
        },
        "runs": run_artifacts,
        "verdict_summary": {
            "total_route_weeks": len(df1),
            "normal_route_weeks": int((df1["flagged"] == "No").sum()),
            "justified_anomalies": int((df1["flagged"] == "No (justified)").sum()),
            "unexplained_anomalies": int((df1["flagged"] == "Yes").sum())
        },
        "conclusion": (
            "PERFECT DETERMINISTIC REPRODUCIBILITY CONFIRMED. "
            "All three independent runs on untouched inputs yielded identical numerical baselines, "
            "verdicts, matched note IDs, plain-English reasons, and byte-for-byte matching SHA-256 digests."
            if all_identical else "REPRODUCIBILITY MISMATCH DETECTED."
        )
    }

    # Save machine-readable report
    rep_file = settings.reproducibility_report_path
    rep_file.parent.mkdir(parents=True, exist_ok=True)
    with open(rep_file, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)

    print("\n-----------------------------------------------------------------")
    print(f"Reproducibility Status: {'PASSED (100% Identical)' if all_identical else 'FAILED'}")
    print(f"Common SHA-256 Digest:  {run_hashes[0]}")
    print(f"Report saved to:        {rep_file}")
    print("=================================================================\n")

    return audit_report


if __name__ == "__main__":
    execute_reproducibility_audit()

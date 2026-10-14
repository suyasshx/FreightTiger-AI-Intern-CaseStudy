"""
RouteGuard AI - Command Line Interface (CLI)
Enables standalone batch execution of the Freight Cost Intelligence pipeline.
Generates the exact graded output CSV contract: outputs/flagged_routes.csv.
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
WORKSPACE_DIR = Path(__file__).resolve().parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

from backend.app.config import settings
from backend.app.services.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="RouteGuard AI - Evidence-Grounded Freight Cost Intelligence CLI"
    )
    parser.add_argument(
        "--shipments",
        type=str,
        default=str(settings.shipments_path),
        help="Path to shipment_records.csv"
    )
    parser.add_argument(
        "--notes",
        type=str,
        default=str(settings.notes_path),
        help="Path to context_notes.csv"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(settings.output_csv_path),
        help="Path to generated output CSV (default: outputs/flagged_routes.csv)"
    )
    parser.add_argument(
        "--history-threshold",
        type=float,
        default=settings.history_threshold_pct,
        help="Percentage cost rise vs own history to trigger anomaly candidate (default: 15.0)"
    )
    parser.add_argument(
        "--peer-threshold",
        type=float,
        default=settings.peer_threshold_pct,
        help="Percentage cost rise vs similar routes to trigger anomaly candidate (default: 15.0)"
    )
    parser.add_argument(
        "--trailing-weeks",
        type=int,
        default=settings.trailing_history_weeks,
        help="Trailing calendar weeks for history rolling average (default: 8)"
    )

    args = parser.parse_args()

    print("=================================================================")
    print(" RouteGuard AI — Freight Cost Intelligence Pipeline")
    print("=================================================================")
    print(f"Shipments Path:       {args.shipments}")
    print(f"Context Notes Path:   {args.notes}")
    print(f"Output CSV Path:      {args.output}")
    print(f"History Threshold:    +{args.history_threshold}%")
    print(f"Peer Threshold:       +{args.peer_threshold}%")
    print(f"Trailing Window:      {args.trailing_weeks} weeks strictly preceding")
    print("-----------------------------------------------------------------")

    output_df, records, summary = run_pipeline(
        shipments_path=Path(args.shipments),
        notes_path=Path(args.notes),
        output_path=Path(args.output),
        history_threshold_pct=args.history_threshold,
        peer_threshold_pct=args.peer_threshold,
        trailing_weeks=args.trailing_weeks
    )

    print("\nExecution Summary:")
    print(f"  • Total Route-Weeks Analyzed:     {summary['total_route_weeks']}")
    print(f"  • Normal Route-Weeks:             {summary['normal_route_weeks']}")
    print(f"  • Evidence-Supported (Justified): {summary['justified_anomalies']}")
    print(f"  • Unexplained (Requires Review):  {summary['unexplained_anomalies']}")
    print(f"  • Execution Runtime:              {summary['runtime_seconds']:.2f} seconds")
    print(f"  • Output SHA-256 Digest:          {summary['sha256']}")
    print(f"\nSuccessfully written to: {args.output}")
    print("=================================================================\n")


if __name__ == "__main__":
    main()

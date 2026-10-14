"""
RouteGuard AI - Configuration Module
Centralized configuration for thresholds, paths, model settings, and execution modes.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field

# Base workspace paths
WORKSPACE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = WORKSPACE_DIR / "data"
OUTPUTS_DIR = WORKSPACE_DIR / "outputs"
EVALUATION_DIR = WORKSPACE_DIR / "evaluation"
CHROMA_DIR = WORKSPACE_DIR / "chroma_db"

# Ensure essential directories exist
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
EVALUATION_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseModel):
    # Data Paths
    shipments_path: Path = DATA_DIR / "shipment_records.csv"
    notes_path: Path = DATA_DIR / "context_notes.csv"
    sample_output_path: Path = DATA_DIR / "sample_output_format_v2.csv"
    output_csv_path: Path = OUTPUTS_DIR / "flagged_routes.csv"
    cost_log_path: Path = EVALUATION_DIR / "cost_log.json"
    reproducibility_report_path: Path = EVALUATION_DIR / "reproducibility_report.json"
    eval_report_path: Path = EVALUATION_DIR / "eval_report.json"

    # Algorithmic Thresholds
    history_threshold_pct: float = Field(
        default=15.0,
        description="Percentage threshold increase vs own history baseline to trigger anomaly candidate"
    )
    peer_threshold_pct: float = Field(
        default=15.0,
        description="Percentage threshold increase vs same-week same-type peer baseline"
    )
    trailing_history_weeks: int = Field(
        default=8,
        description="Number of strictly preceding observed calendar weeks for history rolling average"
    )

    # Retrieval and RAG Configuration
    embedding_model_name: str = "all-MiniLM-L6-v2"
    chroma_db_dir: Path = CHROMA_DIR
    top_k_candidates: int = 3

    # LLM & QA Assistant
    llm_provider: str = os.getenv("LLM_PROVIDER", "none")  # 'none', 'openai', 'ollama'
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_temperature: float = 0.0

    model_config = {"arbitrary_types_allowed": True}


settings = Settings()

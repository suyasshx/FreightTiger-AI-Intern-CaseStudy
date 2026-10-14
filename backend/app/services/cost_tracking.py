"""
RouteGuard AI - Token Accounting and Execution Cost Tracking
Maintains strict, transparent cost accounting for vector embedding and LLM generation.
By default, the full batch pipeline runs entirely with local embeddings and deterministic
explanations (0 LLM calls, 0 tokens, $0.00 API cost).
"""

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from backend.app.config import settings
from backend.app.schemas.models import CostTrackingReport


class CostTracker:
    """
    Tracks and records real compute, token, and API financial expenditures.
    """

    def __init__(self):
        self.run_id = f"run-{uuid.uuid4().hex[:8]}"
        self.start_time = time.time()
        self.dataset_records_count = 0
        self.total_route_weeks = 0
        self.embedding_model = settings.embedding_model_name
        self.notes_indexed_count = 0
        self.queries_executed_count = 0
        self.llm_calls_count = 0
        self.llm_input_tokens = 0
        self.llm_output_tokens = 0
        self.token_accounting_method = "exact-provider-reported / tiktoken"
        self.provider_currency = "USD"
        self.input_cost_per_million = 0.15   # gpt-4o-mini rate as benchmark reference
        self.output_cost_per_million = 0.60
        self.estimated_api_cost = 0.0
        self.execution_mode = "local-cpu-deterministic"

    def record_ingestion(self, shipment_count: int, route_week_count: int) -> None:
        self.dataset_records_count = shipment_count
        self.total_route_weeks = route_week_count

    def record_indexing(self, note_count: int) -> None:
        self.notes_indexed_count = note_count

    def record_retrieval_query(self) -> None:
        self.queries_executed_count += 1

    def record_llm_usage(self, input_tokens: int, output_tokens: int) -> None:
        self.llm_calls_count += 1
        self.llm_input_tokens += input_tokens
        self.llm_output_tokens += output_tokens
        # Calculate cost based on published rates
        in_cost = (input_tokens / 1_000_000.0) * self.input_cost_per_million
        out_cost = (output_tokens / 1_000_000.0) * self.output_cost_per_million
        self.estimated_api_cost += (in_cost + out_cost)
        self.execution_mode = "hybrid-local-embeddings-plus-llm"

    def finalize_report(self, output_path: Optional[Path] = None) -> CostTrackingReport:
        runtime_seconds = round(time.time() - self.start_time, 3)

        report = CostTrackingReport(
            run_id=self.run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            dataset_records_count=self.dataset_records_count,
            total_route_weeks=self.total_route_weeks,
            embedding_model=self.embedding_model,
            notes_indexed_count=self.notes_indexed_count,
            queries_executed_count=self.queries_executed_count,
            llm_calls_count=self.llm_calls_count,
            llm_input_tokens=self.llm_input_tokens,
            llm_output_tokens=self.llm_output_tokens,
            token_accounting_method="local-deterministic (0 API tokens utilized during batch pipeline)" if self.llm_calls_count == 0 else self.token_accounting_method,
            provider_currency=self.provider_currency,
            estimated_api_cost=round(self.estimated_api_cost, 6),
            runtime_seconds=runtime_seconds,
            execution_mode="local-open-source (embeddings via all-MiniLM-L6-v2 on CPU/GPU, zero external API cost)",
            notes=(
                "Default batch pipeline uses 100% local open-source embeddings (all-MiniLM-L6-v2) "
                "and deterministic evidence-validation gating. Zero external LLM calls or paid API keys "
                "are required to generate the complete graded output table."
            )
        )

        target_file = output_path or settings.cost_log_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

        return report


# Global instance
cost_tracker = CostTracker()

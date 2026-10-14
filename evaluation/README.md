# RouteGuard AI — Evaluation and Verification Report

**Evaluated At**: 2026-10-14T09:24:53.456934+00:00  
**Pipeline Execution Mode**: Local Open-Source Embeddings (`all-MiniLM-L6-v2`) + Hard Gate Engine  
**Execution Time**: 15.5s

---

## 1. Executive Evaluation Scorecard

| Metric | Score | Status | Benchmark / Target |
|---|---|---|---|
| **Evidence Gating Accuracy** | **100.0%** | PASS | 100% on labeled known cases |
| **Retrieval Top-1 Precision** | **100.0%** | PASS | Exact semantic match |
| **Retrieval Top-3 Recall** | **100.0%** | PASS | Comprehensive candidate pool |
| **Golden Sample Exact Matches** | **100.0%** (3/3) | PASS | sample_output_format_v2.csv |
| **False Justification Rate** | **0.0%** | PASS | 0 invalid notes accepted |
| **3-Run Reproducibility Match** | **100.0%** | PASS | Identical SHA-256 hashes |

---

## 2. Hard Evidence Gate Audit (Notes N001–N010)

| Note ID | Corridor | Week | Expected | Decision | Status | Rationale |
|---|---|---|---|---|---|---|
| `N001` | Chennai-Bangalore | 2025-02-24 | PASS | PASS | **PASS** | N001 valid flooding start week |
| `N001` | Chennai-Bangalore | 2025-03-03 | PASS | PASS | **PASS** | N001 valid flooding week 2 |
| `N001` | Chennai-Bangalore | 2025-03-10 | REJECT | REJECT | **PASS** | N001 post-flooding (roads passable Mar 9) |
| `N001` | Mumbai-Pune | 2025-02-24 | REJECT | REJECT | **PASS** | N001 corridor mismatch |
| `N002` | Ahmedabad-Mumbai | 2025-01-20 | PASS | PASS | **PASS** | N002 regional festival surcharge week |
| `N002` | Ahmedabad-Mumbai | 2025-02-17 | REJECT | REJECT | **PASS** | N002 post-festival week |
| `N003` | Delhi-Jaipur | 2025-05-05 | PASS | PASS | **PASS** | N003 nationwide diesel price hike (modest rise) |
| `N004` | All Routes | 2024-03-11 | REJECT | REJECT | **PASS** | N004 toll plaza (routes not part of dataset) |
| `N005` | Mumbai-Delhi | 2024-07-29 | REJECT | REJECT | **PASS** | N005 maintenance (costs not significantly affected) |
| `N006` | All Routes | 2025-09-22 | REJECT | REJECT | **PASS** | N006 stable demand with no disruptions |
| `N007` | Delhi-Jaipur | 2024-05-20 | REJECT | REJECT | **PASS** | N007 road resurfacing improvements |
| `N008` | Kolkata-Bhubaneswar | 2025-06-09 | REJECT | REJECT | **PASS** | N008 normal freight movement |
| `N009` | Chennai-Bangalore | 2025-03-17 | REJECT | REJECT | **PASS** | N009 flood repair completion (recovery) |
| `N010` | All Routes | 2025-10-27 | REJECT | REJECT | **PASS** | N010 fleet tracking costs absorbed by transporters |

---

## 3. Threshold Sensitivity Analysis

How anomaly candidate volume responds to varying percentage thresholds:

| Threshold (%) | Total Candidates | History Trigger Only | Peer Trigger Only | Both Triggered | % of Network |
|---|---|---|---|---|---|
| **+5.0%** | 219 | 17 | 169 | 33 | 30.08% |
| **+10.0%** | 90 | 1 | 82 | 7 | 12.36% |
| **+12.0%** | 52 | 0 | 45 | 7 | 7.14% |
| **+15.0%** | 27 | 0 | 21 | 6 | 3.71% |
| **+20.0%** | 20 | 1 | 14 | 5 | 2.75% |
| **+25.0%** | 13 | 3 | 9 | 1 | 1.79% |
| **+30.0%** | 10 | 1 | 8 | 1 | 1.37% |

---

## 4. Evaluation Methodology and Limitations

1. **Separation of Concerns**: Mathematical metrics are evaluated independently of semantic RAG gating.
2. **Deterministic Reproducibility**: Zero non-deterministic LLM calls exist in the core grading pipeline.
3. **Traceability**: All accepted justifications link to original records in `context_notes.csv`.

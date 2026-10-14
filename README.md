# RouteGuard AI — Evidence-Grounded Freight Cost Intelligence Platform

**FreightTiger Software Engineering Intern (AI) — 24-Hour Challenge Submission**  
**Author:** AI Software Engineering Intern Candidate  
**Project:** RouteGuard AI  
**Status:** 100% Production Ready | 28/28 Pytest Tests Passing | Bit-for-Bit Deterministic Reproducibility  

---

## 1. Executive Summary & Business Problem

In freight transportation, companies pay logistics service providers (LSPs) and fleet operators to transport freight across regional and interstate highway corridors. Over time, freight costs quietly creep upward:
- **Legitimate Cost Rises:** Severe weather events (e.g., monsoon flooding in Chennai forcing 140km highway detours), statutory toll revisions, festival demand surges, or diesel price adjustments.
- **Unjustified Billing Creep:** Rate inflation without operational justification, carrier collusion, or billing errors that slip past manual spot-check audits.

**RouteGuard AI** is an intelligent auditing platform that:
1. Ingests raw multi-drop shipment logs and tracks weekly freight cost per tonne-kilometer across directional corridors.
2. Compares weekly rates against **zero-lookahead trailing 8-week historical baselines** and **same-week same-haul peer baselines**.
3. Detects anomalous cost spikes ($\ge +15.0\%$).
4. Evaluates unstructured contextual notes using **local vector retrieval (RAG)** bounded by **Six Hard Evidence Gates** (rejecting irrelevant routes, expired timeframes, non-causal descriptions, absorbed costs, and disproportionate claims).
5. Emits an exact, standards-compliant 8-column audit CSV (`outputs/flagged_routes.csv`) and serves an operational analytics command center with natural-language Q&A.

---

## 2. System Architecture

```text
                                       Raw Input Data
                                 ┌─────────────────────────┐
                                 │  shipment_records.csv   │
                                 │    context_notes.csv    │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │   Data Ingestion & QC   │
                                 │ (Monday Week Alignment) │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │ Weighted Weekly Metrics │
                                 │   Cost per Tonne-Km     │
                                 └────────────┬────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
        ┌───────────────────────────┐                   ┌───────────────────────────┐
        │ Zero-Lookahead History    │                   │ Same-Week Peer Baseline   │
        │ Trailing 8 Calendar Weeks │                   │ Same Haul, Self-Excluded  │
        └─────────────┬─────────────┘                   └─────────────┬─────────────┘
                      │                                               │
                      └───────────────────────┬───────────────────────┘
                                              ▼
                                ┌───────────────────────────┐
                                │ Anomaly Candidate Filter  │
                                │ (vs_hist or vs_peer ≥15%) │
                                └─────────────┬─────────────┘
                                              │
                                              ▼
                                ┌───────────────────────────┐
                                │ Hybrid RAG Note Retrieval │
                                │ ChromaDB + all-MiniLM-L6  │
                                └─────────────┬─────────────┘
                                              │
                                              ▼
                                ┌───────────────────────────┐
                                │  Six Hard Evidence Gates  │
                                │ Route • Time • Causality  │
                                │ Direction • Mag • Trace   │
                                └─────────────┬─────────────┘
                                              │
                                              ▼
                                ┌───────────────────────────┐
                                │ Deterministic Verdict &   │
                                │ Grounded Explanation Gen  │
                                └─────────────┬─────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
        ┌───────────────────────────┐                   ┌───────────────────────────┐
        │  outputs/flagged_routes   │                   │ FastAPI + React Dashboard │
        │    (Exact CSV Contract)   │                   │ (Visual Command Center)   │
        └───────────────────────────┘                   └───────────────────────────┘
```

---

## 3. Mathematical Foundations & Baselines

All calculations follow the exact grading contract specified in the FreightTiger brief.

### 3.1 Route Definition & Directionality
Routes are grouped strictly by directional `origin-destination` pairs and the provided `route_type` (`Short`, `Medium`, `Long`):
- `Mumbai-Pune` (ascending the Bhor Ghat) is treated independently from `Pune-Mumbai` (descending).
- We do **not** derive synthetic length buckets or combine opposite traffic flows.

### 3.2 Monday-Start Calendar Weeks
Weeks run strictly Monday through Sunday. The `week_of` field records the Monday date in ISO `YYYY-MM-DD` format:

`week_of = shipment_date - timedelta(weekday)`

*(For example, Sunday `2025-03-09` is assigned to Monday `2025-03-03`).*

### 3.3 Cost per Tonne-Kilometre Formulation
To avoid distortion from small, high-rate consignments, we compute the volume-weighted metric across all shipments in that route-week:

`cost_per_tonne_km = SUM(freight_cost_inr) / SUM(quantity_tonnes * distance_km)`

Zero or negative quantities and distances are guarded against during ingestion.

### 3.4 Own-History Baseline (Zero-Lookahead Trailing 8 Weeks)
For route $R$ in week $W_t$, the historical baseline is calculated from observed weekly costs strictly inside the preceding 8-calendar-week window $[W_{t-8}, W_{t-1}]$:
- **No Lookahead:** Current week $W_t$ and future weeks $W_{t+k}$ are strictly excluded (`df.shift(1)`).
- **Handling Incomplete History:** If fewer than 8 prior weeks exist (e.g., during the initial weeks of the dataset), we calculate the arithmetic mean of all available prior observed weeks in that window. We **never** pad with synthetic data or extrapolate.
- **Brand New Routes:** If 0 prior weeks exist (Week 1), `vs_own_history` is marked unavailable (`None`).

`vs_own_history (%) = ((cost - Baseline_hist) / Baseline_hist) * 100`

### 3.5 Similar-Route Peer Baseline (Self-Excluded)
For route $R_i$ of haul type $H$ in week $W_t$, the peer baseline is the arithmetic mean across all **other** routes of the same haul type in that exact same calendar week:

`Baseline_peer(route, week) = average cost of all OTHER routes with the same haul type in that same week`

- Route $R_i$ is strictly excluded from its own peer average to prevent self-dilution.
- If no peer routes exist in that haul tier during that week, the comparison is marked unavailable.

`vs_similar_routes (%) = ((cost - Baseline_peer) / Baseline_peer) * 100`

### 3.6 Anomaly Policy & Threshold Rationale
- **Default Threshold:** $\ge +15.0\%$ increase against either `vs_own_history` or `vs_similar_routes`.
- **Rationale:** Road freight spot rates in India naturally fluctuate by $\pm 3\text{--}8\%$ week-to-week due to fuel micro-adjustments and truck availability. A 15% threshold isolates genuine disruptions (flood detours, festival demand spikes) and aligns with the illustrative examples in the case brief (`+35.5%`, `+29.5%`, `+23.6%`).
- Missing baselines are never treated as infinite increases. Costs lower than baseline (negative deltas) are never marked as positive anomalies.

---

## 4. Contextual RAG & The Six Hard Evidence Gates

A common failure mode in LLM applications is relying purely on vector similarity. If a route spikes by 25% and vector search retrieves a note stating *"Freight demand was stable and no disruptions occurred"*, naive RAG might classify the anomaly as "justified".

RouteGuard AI indexes all 10 context notes in a local ChromaDB vector store using `sentence-transformers/all-MiniLM-L6-v2`. Every candidate note must pass **Six Factual Validation Gates**:

| Gate | Purpose & Logic | Rejection Example |
|---|---|---|
| **1. Route Scope** | Note must match target route or explicitly apply to `All`. | Note N004 (NH-48 bypass not in dataset) rejected for dataset corridors. |
| **2. Temporal Window** | Anomaly week must overlap note's stated event window. | Note N002 (Jan 20 festival) rejected for September anomaly. |
| **3. Causal Support** | Note must describe a plausible cost-increasing event. | Note N005 (Maintenance with no cost effect) rejected. |
| **4. Negative Filter** | Rejects notes indicating normalcy, recovery, or absorbed expenses. | Note N006/N008 (Stable demand) and N010 (Costs absorbed) rejected. |
| **5. Magnitude Check** | Rejects minor ~5% fuel notes from justifying massive 30%+ spikes. | Note N003 (5-7% diesel hike) cannot justify a 40% standalone surge. |
| **6. Traceability** | ID must exist in supplied dataset; reason must cite exact ID. | Synthesized or hallucinated note IDs are immediately blocked. |

### Note Semantic Verification Reference:
- **N001:** Chennai-Bangalore flooding (2025-02-24 to 2025-03-08) -> **ACCEPTED** for Chennai-Bangalore during those 2 weeks.
- **N002:** Ahmedabad-Mumbai festival surcharge (week of 2025-01-20) -> **ACCEPTED** for Ahmedabad-Mumbai for that week.
- **N003:** Nationwide diesel price revision (~5-7% starting 2025-05-05) -> Verified against network rates; within-threshold rates are not flagged.
- **N004:** Toll plaza changes on non-dataset routes -> **REJECTED** for all dataset routes.
- **N005:** Mumbai-Delhi maintenance with no cost effect -> **REJECTED**.
- **N006 / N008:** Stable freight demand with no major disruptions -> **REJECTED**.
- **N007:** Delhi-Jaipur highway improvements -> **REJECTED** (infrastructure improvements reduce turnaround times, not raise costs).
- **N009:** Chennai-Bangalore flood recovery and normalization -> **REJECTED** as justification for price increases.
- **N010:** AIS-140 GPS compliance absorbed by transporters -> **REJECTED** (costs absorbed without rate increases).

---

## 5. Output CSV Contract (`outputs/flagged_routes.csv`)

The generated output satisfies the exact 8-column contract:
1. `route`: Origin-destination string (e.g. `Mumbai-Pune`)
2. `week_of`: Monday date in ISO `YYYY-MM-DD` format
3. `cost_per_tonne_km`: Numeric cost rounded to 2 decimal places (e.g. `3.29`)
4. `vs_own_history`: Readable percentage string (e.g. `+29.5%` or `N/A`)
5. `vs_similar_routes`: Readable percentage string (e.g. `+22.5%` or `N/A`)
6. `flagged`: Categorical verdict string: `No`, `No (justified)`, or `Yes`
7. `matched_note_id`: Grounded note ID (e.g. `N002`) or **blank** if unexplained/normal
8. `reason`: Plain-English, evidence-backed explanation

### Sample Output Verification Against Golden Rows:
```csv
route,week_of,cost_per_tonne_km,vs_own_history,vs_similar_routes,flagged,matched_note_id,reason
Delhi-Jaipur,2024-11-11,4.17,+35.5%,+21.0%,Yes,,"Cost is +35.5% vs own 8-week history and +21.0% vs similar Short routes this week. No contextual note justifies this increase; requires review."
Ahmedabad-Mumbai,2025-01-20,3.29,+29.5%,+22.5%,No (justified),N002,"Cost is +29.5% vs own 8-week history and +22.5% vs similar Medium routes this week. Justified by note N002 (2025-01-20): Temporary festival surcharge in Ahmedabad-Mumbai corridor."
Mumbai-Pune,2025-09-15,3.98,+9.2%,+23.6%,Yes,,"Cost is +23.6% vs similar Short routes this week. Note N006 (2025-09-22) describes stable freight demand and no major disruptions; cost increase is unexplained and requires review."
```

*Total dataset results: 728 route-weeks analyzed (701 Normal, 24 Unexplained Anomalies, 3 Justified Anomalies).*

---

## 6. How We Convinced Ourselves It Was Right

Before submitting, we subjected RouteGuard AI to three layers of validation:

### 1. Automated Test Suite (28 Tests)
```bash
python -m pytest tests/ -v
# 28 passed in 21.24s
```
- **Numerical Edge Cases:** Zero-lookahead rolling window verification, self-exclusion peer baseline tests, boundary checks at exactly 15.0%.
- **Contextual Note Semantic Verification:** Individual test cases asserting that notes N004, N005, N006, N007, N008, N009, and N010 can never justify a cost spike, while N001 and N002 pass only within their exact windows.
- **Golden Sample Integrity:** Verification that Delhi-Jaipur, Ahmedabad-Mumbai, and Mumbai-Pune match the exact semantics of the brief.

### 2. Bit-for-Bit Reproducibility Across 3 Untouched Runs
We executed three independent batch runs from scratch using `evaluation/reproducibility_check.py`:
- **Run 1 SHA-256:** `c59bd40fe8a891d3d43d98439c4597db25b205e9588efa7cd72fd6c6707ecae1`
- **Run 2 SHA-256:** `c59bd40fe8a891d3d43d98439c4597db25b205e9588efa7cd72fd6c6707ecae1`
- **Run 3 SHA-256:** `c59bd40fe8a891d3d43d98439c4597db25b205e9588efa7cd72fd6c6707ecae1`
- **Variance:** **0.00% across all 728 rows, 8 columns, and explanations.**

### 3. Token & Cost Accounting ($0.00 API Cost)
Documented in `evaluation/cost_log.json`:
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (Local PyTorch)
- **Vector Store:** ChromaDB (Local persistent)
- **External LLM Calls:** 0
- **External API Tokens:** 0
- **External API Cost:** **$0.00**
- **Batch Pipeline Execution Time:** ~14.2 seconds on standard CPU

---

## 7. Quickstart Guide

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- *(Optional)* Docker & Docker Compose

### 1. Clone & Set Up Python Environment
```bash
git clone https://github.com/suyasshx/FreightTiger-AI-Intern-CaseStudy.git
cd FreightTiger-AI-Intern-CaseStudy

# Create virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Batch Pipeline (Generate Output CSV)
```bash
python cli.py
# Or with custom anomaly thresholds:
python cli.py --history-threshold 15.0 --peer-threshold 15.0
```
*Output generated at: `outputs/flagged_routes.csv`*

### 3. Run Automated Tests
```bash
python -m pytest tests/ -v
```

### 4. Run Reproducibility Check & Evaluation
```bash
# 3-run bit-for-bit SHA-256 check:
python evaluation/reproducibility_check.py

# Benchmark evaluation harness:
python evaluation/run_evaluation.py
```

### 5. Start the REST API & Documentation
```bash
# Start backend API on http://localhost:8000
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check & Telemetry:** [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **Operational Metrics Endpoint:** [http://localhost:8000/api/overview](http://localhost:8000/api/overview)
- **CSV Download Endpoint:** [http://localhost:8000/api/export/csv](http://localhost:8000/api/export/csv)

### 6. Run with Docker
```bash
docker build -t routeguard-ai .
docker run -p 8000:8000 routeguard-ai
```

---

## 8. Five Core Deliverables Summary

| # | Deliverable | Location in Repository | Status & Verification |
|---|---|---|---|
| **1** | **Working Source Code** | `backend/`, `cli.py`, `tests/` | Complete, modular, type-hinted Python pipeline. All 28 pytest tests passing. |
| **2** | **Final Graded CSV** | [`outputs/flagged_routes.csv`](file:///outputs/flagged_routes.csv) | Exact 8 columns, 728 route-weeks, RFC 4180 compliant, matching golden samples. |
| **3** | **README & Documentation** | `README.md`, `docs/` | Comprehensive formulas, zero-lookahead policy, evidence gates, trade-offs, and limits. |
| **4** | **Reproducibility Evidence** | [`evaluation/reproducibility_report.json`](file:///evaluation/reproducibility_report.json) | 3 untouched runs with identical SHA-256 (`c59bd40fe8a891d3d43d98439c4597db25b205e9588efa7cd72fd6c6707ecae1`). |
| **5** | **Token & Cost Log** | [`evaluation/cost_log.json`](file:///evaluation/cost_log.json) | Full 2,940 shipment run: 0 external LLM calls, 0 tokens, **$0.00 API cost**. |

---

## 9. Repository Structure

```text
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI REST endpoints (/health, /overview, /routes, /qa, /export)
│   │   ├── config.py        # Centralized settings & threshold configurations
│   │   ├── main.py          # FastAPI application entrypoint & API routers
│   │   ├── schemas/         # Pydantic v2 domain schemas (models.py)
│   │   └── services/        # Modular analytical pipeline services
│   │       ├── ingestion.py          # Ingestion, schema QC, Monday week calculation
│   │       ├── weekly_analytics.py   # Volume-weighted cost per tonne-km
│   │       ├── baselines.py          # Zero-lookahead rolling history & peer baselines
│   │       ├── anomaly_detection.py  # Anomaly candidate filtering & sensitivity audits
│   │       ├── note_index.py         # ChromaDB indexing with all-MiniLM-L6-v2
│   │       ├── retrieval.py          # Hybrid semantic + lexical retrieval
│   │       ├── evidence_validation.py# Six hard evidence validation gates
│   │       ├── verdicts.py           # Verdict mapping (No, No (justified), Yes)
│   │       ├── explanations.py       # Deterministic, grounded explanation generator
│   │       ├── qa_assistant.py       # Grounded natural language Q&A assistant
│   │       ├── cost_tracking.py      # Real-time token and compute accounting
│   │       └── pipeline.py           # Unified batch pipeline orchestrator
├── data/                    # Authoritative case study inputs
│   ├── shipment_records.csv # 2,940 raw shipment records
│   ├── context_notes.csv    # 10 contextual disruption notes
│   ├── sample_output_format_v2.csv # Contract reference
│   └── FreightTiger_Intern_CaseStudy.pdf # Original case study brief
├── outputs/
│   ├── flagged_routes.csv   # The official graded 8-column CSV artifact (728 rows)
│   └── reproducibility_runs/ # Independent CSV outputs from Runs 1, 2, and 3
├── evaluation/
│   ├── reproducibility_check.py    # 3-run reproducibility test harness
│   ├── reproducibility_report.json # Hashes and diff analysis (100% match)
│   ├── run_evaluation.py           # Benchmark eval harness
│   ├── eval_report.json            # Metrics report (100% gate accuracy)
│   └── cost_log.json               # Documented $0.00 run cost accounting
├── tests/                   # 28 pytest automated tests
│   ├── test_numerical.py    # Baseline formulas, rolling window, self-exclusion
│   ├── test_evidence.py     # Semantic verification for notes N001–N010
│   ├── test_golden.py       # Exact verification against case study examples
│   ├── test_contract.py     # Schema, column order, and quoting validation
│   └── test_api.py          # FastAPI REST endpoint integration tests
├── docs/
│   ├── ARCHITECTURE.md      # Detailed system architecture & pipeline dataflow
│   ├── WALKTHROUGH.md       # 10-minute presentation script & 18 interview Q&As
│   └── IMPLEMENTATION_STATUS.md # Complete requirement traceability matrix
├── cli.py                   # Standalone batch execution CLI
├── docker-compose.yml       # Containerized orchestration
├── Dockerfile               # Production Python Dockerfile
├── Makefile                 # Developer convenience commands
└── README.md                # Master project documentation
```

---

## 10. Key Trade-Offs & Limitations

1. **Deterministic Rule Gates vs. Generative LLMs:**
   - *Choice:* We chose deterministic Python validation gates over prompting an LLM to decide whether a note justifies an anomaly.
   - *Trade-Off:* Prompting an LLM might produce more varied phrasing, but introduces non-deterministic output, hallucination risk, and API costs. In freight audits, 100% deterministic reproducibility and zero false justifications are paramount.

2. **Volume-Weighted Average vs. Unweighted Ratio Mean:**
   - *Choice:* $\sum \text{Cost} / \sum (\text{Qty} \times \text{Dist})$.
   - *Trade-Off:* Computation requires aggregation before division rather than row-level division, but accurately models commercial freight economics.

3. **Known Limitations:**
   - *Cold-Start Initialization:* Loading PyTorch and ChromaDB introduces a ~3-second cold start on initial run.
   - *Fixed Trailing Window:* The 8-week trailing window cleanly captures recent trends, but an exponential moving average (EMA) could be added to give greater weight to very recent weeks.

---

# RouteGuard AI — Architecture & Technical Design Document

## 1. Executive Overview

**RouteGuard AI** is an evidence-grounded freight transportation cost intelligence platform developed for the **FreightTiger Software Engineering Intern (AI) Case Study**.

Its mission is to identify abnormal transportation cost increases, compare them against rigorous historical and peer benchmarks, search real-world contextual events using Retrieval-Augmented Generation (RAG), and enforce six non-negotiable verification gates before classifying any cost surge as justified or unexplained.

```
+---------------------------------------------------------------------------------------------------+
|                                  ROUTEGUARD AI PLATFORM PIPELINE                                  |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [ Shipment Records CSV ]                                  [ Contextual Notes CSV ]               |
|            |                                                           |                          |
|            v                                                           v                          |
|  +--------------------+                                      +--------------------+               |
|  |  Data Ingestion &  |                                      |  ChromaDB Vector   |               |
|  | Schema Sanitization|                                      |   Index & Hybrid   |               |
|  +--------------------+                                      |  Candidate Pool    |               |
|            |                                                 +--------------------+               |
|            v                                                           |                          |
|  +--------------------+                                                |                          |
|  | Weekly Aggregation |                                                |                          |
|  | (Weighted INR/t-km)|                                                |                          |
|  +--------------------+                                                |                          |
|            |                                                           |                          |
|            v                                                           |                          |
|  +--------------------+                                                |                          |
|  | 8-Wk Zero-Lookahead|                                                |                          |
|  | & Peer Baselines   |                                                |                          |
|  +--------------------+                                                |                          |
|            |                                                           |                          |
|            v                                                           |                          |
|  +--------------------+                                                |                          |
|  | Anomaly Candidate  |                                                |                          |
|  |  Detection (>=15%) |                                                |                          |
|  +--------------------+                                                |                          |
|            |                                                           |                          |
|            | (If candidate)                                            |                          |
|            +--------------------> +---------------------+ <------------+                          |
|                                   |  Hybrid Retrieval   |                                         |
|                                   |  (Top-k Candidates) |                                         |
|                                   +---------------------+                                         |
|                                              |                                                    |
|                                              v                                                    |
|                                   +---------------------+                                         |
|                                   |   6 HARD EVIDENCE   |                                         |
|                                   |  VALIDATION GATES   |                                         |
|                                   +---------------------+                                         |
|                                              |                                                    |
|                      +-----------------------+-----------------------+                            |
|                      | (All 6 Gates Pass)                            | (Any Gate Fails / No Note) |
|                      v                                               v                            |
|          +-----------------------+                       +-----------------------+                |
|          |    No (justified)     |                       |          Yes          |                |
|          | Matched Note: N001/N002                       | Matched Note: [BLANK] |                |
|          | Grounded Explanation  |                       | Unexplained Reason    |                |
|          +-----------------------+                       +-----------------------+                |
|                      |                                               |                            |
|                      +-----------------------+-----------------------+                            |
|                                              |                                                    |
|                                              v                                                    |
|                                   +---------------------+                                         |
|                                   | outputs/flagged_    |                                         |
|                                   |      routes.csv     |                                         |
|                                   +---------------------+                                         |
|                                              |                                                    |
|                   +--------------------------+--------------------------+                         |
|                   |                                                     |                         |
|                   v                                                     v                         |
|        +---------------------+                               +---------------------+              |
|        | FastAPI REST Server |                               | React + TS Command  |              |
|        | (/api/routes, etc.) |                               |   Center Dashboard  |              |
|        +---------------------+                               +---------------------+              |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Mathematical Baseline Formulations

### 2.1 Route Grouping and Calendar Week Formulation
Shipments are partitioned by directional route (`origin-destination`), haul category (`route_type`: Short, Medium, Long), and Monday-start calendar weeks:
$$\text{week\_of} = \text{shipment\_date} - \text{timedelta}(\text{weekday})$$
Weeks run Monday through Sunday. Shipments are assigned to calendar weeks prior to any rolling aggregation.

### 2.2 Weighted Cost per Tonne-Kilometre
Freight cost efficiency cannot be computed as an unweighted mean of individual shipment ratios. RouteGuard AI computes the true physical ratio across shipments $i$ in route-week $w$:
$$\text{cost\_per\_tonne\_km}_w = \frac{\sum_{i \in w} \text{freight\_cost\_inr}_i}{\sum_{i \in w} (\text{quantity\_tonnes}_i \times \text{distance\_km}_i)}$$
Zero quantities or non-positive distances are trapped and audited during ingestion.

### 2.3 Own-History Baseline (Zero Look-Ahead)
For route $r$ in week $t$, the baseline is the arithmetic mean of observed weekly costs in the preceding 8 calendar weeks strictly prior to week $t$:
$$\text{history\_baseline}_{r,t} = \frac{1}{K} \sum_{k=1}^{K} \text{cost\_per\_tonne\_km}_{r, t-k}, \quad 1 \le K \le 8$$
- **Strict Precedence**: Current week $t$ is excluded via `shift(1)`. Future weeks never leak into the past.
- **Available Observation Handling**: If fewer than 8 prior observations exist (e.g. initial weeks), the average of available prior weeks is used without extrapolation or arbitrary padding.
- **Unavailable Baselines**: If $K = 0$ (first observed week), the baseline is marked unavailable (`N/A`).
- **Percentage Shift**:
$$\text{vs\_own\_history\_pct} = \frac{\text{cost\_per\_tonne\_km}_{r,t} - \text{history\_baseline}_{r,t}}{\text{history\_baseline}_{r,t}} \times 100$$

### 2.4 Same-Week Peer Baseline (Strict Self-Exclusion)
For route $r$ of haul category $H$ during week $t$, the peer baseline is the mean cost across all **other** routes sharing category $H$ in week $t$:
$$\text{peer\_baseline}_{r,H,t} = \frac{\sum_{j \in H, j \neq r} \text{cost\_per\_tonne\_km}_{j,t}}{N_H - 1}, \quad N_H > 1$$
The route $r$ is excluded from its own peer average. If $N_H \le 1$, the comparison is marked `N/A`.
$$\text{vs\_similar\_routes\_pct} = \frac{\text{cost\_per\_tonne\_km}_{r,t} - \text{peer\_baseline}_{r,H,t}}{\text{peer\_baseline}_{r,H,t}} \times 100$$

### 2.5 Anomaly Trigger Policy
A route-week becomes an anomaly candidate if EITHER baseline exhibits a positive surge meeting the configured threshold (default 15.0%):
$$\text{Candidate} = (\text{vs\_own\_history\_pct} \ge 15.0\%) \lor (\text{vs\_similar\_routes\_pct} \ge 15.0\%)$$
Negative percentage changes (cost reductions) never trigger anomaly candidacy.

---

## 3. RAG Retrieval & The 6 Hard Evidence Gates

Vector similarity is treated as a candidate discovery heuristic, **never proof of causality**. Every candidate retrieved from ChromaDB must pass six deterministic validation gates:

```
Candidate Context Note
         │
         ▼
[ Gate 1: Route Applicability ] ──── FAIL ──► Disqualified (Route mismatch)
         │ PASS
         ▼
[ Gate 2: Temporal Window ]     ──── FAIL ──► Disqualified (Date mismatch)
         │ PASS
         ▼
[ Gate 3: Causal Mechanism ]    ──── FAIL ──► Disqualified (No cost rise cause)
         │ PASS
         ▼
[ Gate 4: Negative Disqualifier]──── FAIL ──► Disqualified (Normalcy/absorbed)
         │ PASS
         ▼
[ Gate 5: Magnitude Consistency]──── FAIL ──► Disqualified (Spike > stated impact)
         │ PASS
         ▼
[ Gate 6: Traceability Gate ]   ──── FAIL ──► Disqualified (Unverified Note ID)
         │ PASS
         ▼
[ VERIFIED JUSTIFICATION: No (justified) ]
```

### Detailed Gate Specifications

| Gate | Verification Check | Deterministic Rule & Test |
|---|---|---|
| **1. Route Scope** | Corridor alignment | Note `applies_to` must match route or `All Routes`. Notes with exclusions (e.g. N004 "affected routes not in dataset") fail immediately. |
| **2. Temporal Overlap** | Calendar overlap | Week (Monday–Sunday) must overlap stated duration (e.g., N001 Feb 24–Mar 8; N002 week of Jan 20). Post-event dates fail. |
| **3. Causal Mechanism** | Operational cost cause | Note must articulate an active cost-driving mechanism (flooding detours, festival surcharge, fuel hike). |
| **4. Negative Filter** | Disqualifier scan | Rejects notes mentioning "costs unaffected" (N005), "stable demand / no disruptions" (N006), "normal movement" (N008), "road improvements" (N007), "recovery / repairs completed" (N009), or "costs absorbed" (N010). |
| **5. Magnitude Consistency** | Plausibility check | Notes describing modest changes (~5–7% diesel hike) cannot justify extreme unexplained surges (+35%). |
| **6. Traceability** | Dataset authenticity | Note ID must exist in `context_notes.csv`. No synthetic notes permitted. |

---

## 4. Graded Verdict Determination & Contract Integrity

Outputs follow the exact 8-column contract:
`route,week_of,cost_per_tonne_km,vs_own_history,vs_similar_routes,flagged,matched_note_id,reason`

| Verdict Category | Trigger Condition | Matched Note ID Column | Explanation Pattern |
|---|---|---|---|
| **`No`** | Cost within thresholds | `""` (Empty string) | "Weekly cost per tonne-km is within normal historical and peer boundaries." |
| **`No (justified)`** | Candidate passed all 6 gates | `N001` or `N002` (Verified ID) | "Matches note {ID} dated {date}: {real-world cause}. The cost rise has a clear explanation." |
| **`Yes`** | Candidate failed gates or no note found | `""` (Empty string) | "The closest note ({ID}, {date}) mentions {text} -- it does not describe a reason for a cost rise... flagged for review." OR "No matching note found for this route or date range." |

---

## 5. Software Architecture & Module Boundaries

```text
routeguard-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, lifespan, static mount & CORS
│   │   ├── config.py               # Centralized thresholds and paths
│   │   ├── api/
│   │   │   └── routes.py           # REST endpoints (/overview, /routes, /chat, etc.)
│   │   ├── schemas/
│   │   │   └── models.py           # Pydantic domain models
│   │   └── services/
│   │       ├── ingestion.py        # Schema validation & data cleaning
│   │       ├── weekly_analytics.py # Weighted cost per tonne-km
│   │       ├── baselines.py        # Trailing 8-wk & peer baselines
│   │       ├── anomaly_detection.py# Threshold candidate flagging
│   │       ├── note_index.py       # ChromaDB vector collection & local embeddings
│   │       ├── retrieval.py        # Hybrid vector + lexical retrieval
│   │       ├── evidence_validation.py # 6 Hard Evidence Gating Engine
│   │       ├── verdicts.py         # Graded contract table classification
│   │       ├── explanations.py     # Deterministic human-style plain-English generator
│   │       ├── qa_assistant.py     # Grounded Q&A assistant engine
│   │       ├── cost_tracking.py    # Zero-API-cost run accounting
│   │       └── pipeline.py         # End-to-end orchestration
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.tsx          # Navigation header & live status
│   │   │   ├── OperationsOverview.tsx # Real-time KPIs, Recharts trends, corridors
│   │   │   ├── RouteExplorer.tsx   # Filterable table & corridor timeseries chart
│   │   │   ├── EvidenceInspectorModal.tsx # 6-Gate audit breakdown modal
│   │   │   ├── AIAssistant.tsx     # Grounded chat interface with prompt chips
│   │   │   ├── EvaluationView.tsx  # Scorecard, 3-run hashes, sensitivity curve
│   │   │   └── ExportCenter.tsx    # Graded CSV download & threshold simulator
│   │   ├── api/client.ts           # Typed API service
│   │   ├── types/index.ts          # TypeScript domain interfaces
│   │   ├── App.tsx                 # Root application component
│   │   └── index.css               # Dark theme design system
├── tests/
│   ├── test_numerical.py           # Mathematical correctness & zero lookahead
│   ├── test_evidence.py            # Notes N001-N010 & 6 gates
│   ├── test_golden.py              # Exact matches against sample_output_format_v2.csv
│   ├── test_contract.py            # CSV schema and verdict constraints
│   └── test_api.py                 # FastAPI integration tests
├── evaluation/
│   ├── run_evaluation.py           # Comprehensive evaluation harness runner
│   ├── reproducibility_check.py    # 3-run SHA-256 reproducibility check
│   ├── eval_report.json            # Machine-readable scorecard
│   ├── reproducibility_report.json # Cryptographic audit proof
│   └── cost_log.json               # Token and run-cost accounting
├── outputs/
│   └── flagged_routes.csv          # Official graded CSV deliverable
├── cli.py                          # Standalone batch CLI entrypoint
├── Dockerfile                      # Multi-stage container build
├── docker-compose.yml              # Single-command orchestration
└── README.md                       # Comprehensive project documentation
```

---

## 6. Determinism, Security & Performance

1. **Zero Hallucination Guarantee**: All batch justifications are generated via deterministic, evidence-grounded templates directly referencing original text from `context_notes.csv`.
2. **Reproducibility Guarantee**: The vector index and candidate ranking utilize stable tie-breakers (corridor match $\to$ temporal proximity $\to$ note ID). Three independent untouched runs produce identical SHA-256 hashes:
   `c59bd40fe8a891d3d43d98439c4597db25b205e9588efa7cd72fd6c6707ecae1`
3. **Zero Financial API Cost**: The entire batch pipeline uses local open-source embeddings (`all-MiniLM-L6-v2`) on CPU/GPU without recurring external API fees ($0.00).

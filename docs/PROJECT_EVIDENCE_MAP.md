# Project Evidence Map

| Claim | Primary evidence | Evidence type |
|---|---|---|
| Synthetic-only implementation | `src/synthetic_data_generator.py`, `data/sample/`, privacy docs | Source + generated data |
| Fixed seed 20260902 | `src/config.py` | Configuration |
| 150 products / 10 branches / 32 employees | `generation_manifest.json` | Runtime manifest |
| 28 controlled scenarios | `src/config.py`, `expected_scenarios.csv` | Config + ground truth |
| 8 matching levels | `src/config.py`, `src/matching.py`, matching tests | Source + tests |
| Explainable method + confidence | reconciliation output schema | Runtime output |
| 4 reconciliation components | `src/reconciliation.py` | Source |
| 17 reconciliation statuses | `src/config.py` | Configuration |
| Exposure decomposition | `src/exposure.py`, `docs/EXPOSURE_METHODOLOGY.md` | Source + contract |
| 7 anomaly rule families | `src/anomaly_detection.py` | Source |
| CRITICAL anomaly priority escalation | `src/review_queue.py`, regression test | Source + test |
| 2,424 reconciliation lines | `outputs/examples/kpi_summary.csv` | Retained runtime output |
| 1,170 matched / 1,174 exceptions | `kpi_summary.csv` | Retained runtime output |
| 1,182 review-required | `kpi_summary.csv` | Retained runtime output |
| Implemented interactive dashboard | `dashboard/reconciliation_dashboard.html` | Executable artifact |
| SQL analytical coverage | `sql/01_*.sql` through `sql/12_*.sql` | Query layer |
| Power BI runtime implementation | No PBIP/PBIR/TMDL committed | **Not claimed** |
| Power BI design | `docs/powerbi/` | Blueprint only |
| Fraud detection / proven financial loss | No supporting evidence | **Not claimed** |

## Evidence rule

A design document is not treated as runtime evidence. Presentation images are not treated as analytical proof. Runtime claims are tied to executable source, tests, generated manifests, retained outputs or implemented dashboard artifacts.

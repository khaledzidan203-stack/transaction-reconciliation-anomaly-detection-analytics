# Power BI Design Blueprint

The files in this directory are **design specifications**, not runtime implementation evidence.

They document a proposed Power BI layer for the reconciliation platform:

- `POWER_BI_MODEL.md` — conceptual model design;
- `POWER_QUERY_PLAN.md` — ingestion/transformation plan;
- `DAX_MEASURES.md` — proposed measure definitions;
- `DASHBOARD_DESIGN.md` — report/page design;
- `VALIDATION_PLAN.md` — proposed validation procedure.

## Current implementation boundary

This repository currently contains no committed:

- `.pbip` project;
- PBIR report definition;
- TMDL semantic model;
- PBIX runtime artifact;
- retained Power BI Desktop execution log.

Therefore these documents should not be interpreted as proof that the Power BI model or report was built and runtime-validated.

The implemented interactive reporting artifact in the repository is:

`dashboard/reconciliation_dashboard.html`

## Example values

Some Power BI documents include illustrative values used to explain validation procedures. Those values are examples unless they exactly reconcile to the retained runtime outputs in `outputs/examples/`.

Authoritative current example KPIs are stored in:

`outputs/examples/kpi_summary.csv`

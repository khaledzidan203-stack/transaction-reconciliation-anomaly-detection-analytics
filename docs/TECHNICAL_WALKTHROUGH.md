# Technical Walkthrough — 60–90 Seconds

**0–10 seconds — Scope**

This project reconciles two deterministic synthetic transaction systems and converts mismatches into explainable exception intelligence.

**10–25 seconds — Data and governance**

The generator uses fixed seed `20260902`, 150 products, 10 branches, 32 employees and 28 controlled scenarios. Generated files are fingerprinted with SHA-256 so the sample can be reproduced and checked.

**25–45 seconds — Matching**

After normalization, schema checks and master mapping, each Source A line goes through an ordered 8-level matching hierarchy: exact primary ID, barcode, product code, normalized name, fuzzy name, generic-strength equivalent, possible substitute, then unmatched. Every result retains method and confidence.

**45–60 seconds — Reconciliation**

Identity is not treated as the whole result. Quantity, price and amount are evaluated independently using governed tolerances, then combined into one of 17 reconciliation statuses.

**60–75 seconds — Exception intelligence**

The pipeline computes signed/absolute and component exposure, applies seven rule-based anomaly families and creates a prioritized review queue. The current example run produces 2,424 reconciliation lines and 1,182 review-required lines.

**75–90 seconds — Evidence**

The Python engine and pytest suite are executable, the synthetic sample has a committed generation manifest, SQL provides analytical query coverage, and the HTML dashboard is the implemented interactive reporting layer. Power BI documentation is a blueprint only.

## Suggested presentation order

Overview image → matching hierarchy → component reconciliation → exposure/anomalies → review queue → validation evidence.

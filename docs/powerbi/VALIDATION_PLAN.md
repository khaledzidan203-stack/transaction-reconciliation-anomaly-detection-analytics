# Power BI Validation Plan

> Systematic validation procedures to ensure the Power BI report for Transaction Reconciliation & Anomaly Detection Analytics accurately reflects the pipeline output and behaves correctly under all user interactions.

---

## 1. Validation Objectives

| # | Objective | Risk Mitigated |
|---|---|---|
| 1 | Row counts in Power BI match the Python pipeline output | Data loss during ETL |
| 2 | KPI measures produce identical values to Python-computed KPIs | DAX logic errors |
| 3 | Cross-filter and drill-through behave as designed | Broken interactivity, misleading filters |
| 4 | DAX measures return correct results for known inputs | Arithmetic / logic bugs in DAX |
| 5 | Visuals render correctly after data or model changes | Visual regression, broken conditional formatting |
| 6 | Data refresh completes reliably without errors | Stale data, refresh failures |

---

## 2. Data Count Validation

### 2.1 Total Row Counts

Compare row counts in the Power BI model against the CSV file row counts (minus header).

| Table | Validation Query (Power BI) | Expected Source |
|---|---|---|
| `reconciliation_results` | `COUNTROWS('reconciliation_results')` | `wc -l reconciliation_results.csv` minus 1 |
| `product_master` | `COUNTROWS('product_master')` | `wc -l product_master.csv` minus 1 |
| `branch_master` | `COUNTROWS('branch_master')` | `wc -l branch_master.csv` minus 1 |
| `employee_master` | `COUNTROWS('employee_master')` | `wc -l employee_master.csv` minus 1 |

**Procedure:**

1. Run the Python pipeline to generate all CSV outputs.
2. Count rows in each CSV (excluding header).
3. Open Power BI Desktop → **Data view** → select each table → check the row count indicator at the bottom.
4. Alternatively, create a DAX measure:

```dax
Validation Row Count =
    COUNTROWS ( 'reconciliation_results' )
```

5. Compare. **Pass criteria:** Counts match exactly (±0 tolerance).

### 2.2 Filtered Row Counts

Validate that filtered counts align with Python groupby counts:

| Filter | DAX | Python Equivalent |
|---|---|---|
| Matched lines | `CALCULATE(COUNTROWS('reconciliation_results'), 'reconciliation_results'[reconciliation_status]="matched")` | `df[df.reconciliation_status == "matched"].shape[0]` |
| Review required | `CALCULATE(COUNTROWS('reconciliation_results'), 'reconciliation_results'[review_required]=TRUE())` | `df[df.review_required == True].shape[0]` |
| Fuzzy matches | `CALCULATE(COUNTROWS('reconciliation_results'), 'reconciliation_results'[match_method]="fuzzy_name")` | `df[df.match_method == "fuzzy_name"].shape[0]` |

---

## 3. KPI Measure Validation

### 3.1 Match Rate %

**Expected value from Python:**

```python
match_rate = df[df.reconciliation_status == "matched"].shape[0] / df.shape[0]
print(f"Match Rate: {match_rate:.4f}")
```

**Power BI check:**

1. Add a card visual with `Match Rate %` measure.
2. Ensure no slicers are active (all data visible).
3. Compare the displayed percentage to the Python output.

**Pass criteria:** Match within ±0.01% (rounding tolerance).

### 3.2 Exception Rate %

**Expected value from Python:**

```python
exception_rate = df[df.reconciliation_status.isin(["exception", "partial"])].shape[0] / df.shape[0]
```

**Power BI check:** Card visual → `Exception Rate %` → compare.

**Pass criteria:** Match within ±0.01%.

### 3.3 Total Exposure

**Expected value from Python:**

```python
total_exposure = df["absolute_exposure"].sum()
```

**Power BI check:** Card visual → `Total Exposure` → compare.

**Pass criteria:** Match within ±0.01 currency units.

### 3.4 Unresolved Exposure

**Expected value from Python:**

```python
unresolved_exposure = df["unresolved_exposure"].sum()
```

**Power BI check:** Card visual → `Unresolved Exposure` → compare.

**Pass criteria:** Match within ±0.01.

### 3.5 Average Confidence Score

**Expected value from Python:**

```python
avg_confidence = df["confidence_score"].mean()
```

**Power BI check:** Card visual → `Average Confidence Score` → compare.

**Pass criteria:** Match within ±0.001.

### 3.6 Review Queue Count

**Expected value from Python:**

```python
review_count = df[df.review_required == True].shape[0]
```

**Power BI check:** Card visual → `Review Queue Count` → compare.

**Pass criteria:** Exact match (integer).

### 3.7 KPI Summary Table Cross-Check

The `kpi_summary` CSV contains pre-computed KPI values. Use it as an independent reference:

| KPI | kpi_summary Column | Power BI Measure |
|---|---|---|
| Match Rate | `match_rate` | `Match Rate %` |
| Exception Rate | `exception_rate` | `Exception Rate %` |
| Total Exposure | `total_exposure` | `Total Exposure` |
| Avg Confidence | `avg_confidence` | `Average Confidence Score` |

**Procedure:**
1. Load `kpi_summary` into Power BI (already in model as reference table).
2. Create a table visual with both the kpi_summary column and the DAX measure side-by-side.
3. Compare values row-by-row.

---

## 4. Cross-Filter Validation

### 4.1 Branch Filter Propagation

**Test:**
1. On the Executive Summary page, click the bar for **Branch 07** in the "Top 5 Branches by Exposure" chart.
2. Verify that ALL other visuals update:
   - Match Rate % card shows Branch 07's match rate
   - Exception Rate % card shows Branch 07's exception rate
   - Donut chart shows Branch 07's status distribution
   - Exposure by Match Method shows Branch 07's breakdown

**Expected result:** Every visual reflects only Branch 07 data.

**How to verify numerically:**
```python
branch_07_data = df[df.branch_id == 7]
expected_match_rate = branch_07_data[branch_07_data.reconciliation_status == "matched"].shape[0] / branch_07_data.shape[0]
```
Compare the Power BI card value to this Python calculation.

### 4.2 Category Filter Propagation

**Test:**
1. Select a single category (e.g., "Pharmaceuticals") in the Category slicer.
2. Verify all visuals filter to that category.
3. Verify the Branch chart now shows branch exposure **within that category only**.

### 4.3 Multi-Slicer Interaction

**Test:**
1. Select **Branch 03** AND **Category = Pharmaceuticals**.
2. Verify that the Match Rate card shows the intersection of both filters.
3. Clear one slicer, verify the visual expands to include all branches for the remaining category filter.

### 4.4 Cross-Page Filter Consistency

**Test:**
1. On the Executive Summary page, select a branch in the slicer.
2. Navigate to the Detailed Analysis page.
3. Verify the branch filter persists (if using sync slicers) or is cleared (if not synced).
4. Document expected behaviour per design.

### 4.5 Drill-Through Validation

**Test:**
1. On the Anomaly & Review page, right-click a row in the Review Queue Table.
2. Select **Drill through → Reconciliation Detail**.
3. Verify the drill-through page shows only data for `source_a_line_id` of the selected row.
4. Verify all fields (branch, employee, product, statuses, exposures) display the correct values.

**Expected result:** The drill-through page shows exactly one reconciliation record matching the selected line.

**Verify numerically:**
```python
selected_line = "A-00123"
detail = df[df.source_a_line_id == selected_line].iloc[0]
# Compare each field in the drill-through page to this row
```

---

## 5. DAX Measure Unit Tests

Each measure is tested against a known, small dataset to verify arithmetic correctness. Create a **test measure table** in Power BI with hardcoded expected values.

### 5.1 Test Setup

Create a disconnected table `Test_Expectations`:

```dax
Test_Expectations =
DATATABLE (
    "Measure",      STRING,
    "ExpectedValue", DOUBLE,
    {
        { "Match Rate %",       0.924  },
        { "Exception Rate %",   0.051  },
        { "Total Exposure",     47320  },
        { "Unresolved Exposure",12840  },
        { "Avg Confidence",     0.912  },
        { "Review Queue Count", 127    }
    }
)
```

### 5.2 Test Measures

```dax
Test Match Rate =
    VAR Actual = [Match Rate %]
    VAR Expected = LOOKUPVALUE ( Test_Expectations[ExpectedValue], Test_Expectations[Measure], "Match Rate %" )
    VAR Delta = ABS ( Actual - Expected )
    RETURN
        IF ( Delta <= 0.0001, "PASS", "FAIL: " & FORMAT(Actual, "0.0000") & " vs " & FORMAT(Expected, "0.0000") )

Test Exception Rate =
    VAR Actual = [Exception Rate %]
    VAR Expected = LOOKUPVALUE ( Test_Expectations[ExpectedValue], Test_Expectations[Measure], "Exception Rate %" )
    VAR Delta = ABS ( Actual - Expected )
    RETURN
        IF ( Delta <= 0.0001, "PASS", "FAIL: " & FORMAT(Actual, "0.0000") & " vs " & FORMAT(Expected, "0.0000") )

Test Total Exposure =
    VAR Actual = [Total Exposure]
    VAR Expected = LOOKUPVALUE ( Test_Expectations[ExpectedValue], Test_Expectations[Measure], "Total Exposure" )
    VAR Delta = ABS ( Actual - Expected )
    RETURN
        IF ( Delta <= 0.01, "PASS", "FAIL: " & FORMAT(Actual, "#,##0.00") & " vs " & FORMAT(Expected, "#,##0.00") )

Test Unresolved Exposure =
    VAR Actual = [Unresolved Exposure]
    VAR Expected = LOOKUPVALUE ( Test_Expectations[ExpectedValue], Test_Expectations[Measure], "Unresolved Exposure" )
    VAR Delta = ABS ( Actual - Expected )
    RETURN
        IF ( Delta <= 0.01, "PASS", "FAIL: " & FORMAT(Actual, "#,##0.00") & " vs " & FORMAT(Expected, "#,##0.00") )

Test Avg Confidence =
    VAR Actual = [Average Confidence Score]
    VAR Expected = LOOKUPVALUE ( Test_Expectations[ExpectedValue], Test_Expectations[Measure], "Avg Confidence" )
    VAR Delta = ABS ( Actual - Expected )
    RETURN
        IF ( Delta <= 0.001, "PASS", "FAIL: " & FORMAT(Actual, "0.000") & " vs " & FORMAT(Expected, "0.000") )

Test Review Queue Count =
    VAR Actual = [Review Queue Count]
    VAR Expected = LOOKUPVALUE ( Test_Expectations[ExpectedValue], Test_Expectations[Measure], "Review Queue Count" )
    VAR Delta = ABS ( Actual - Expected )
    RETURN
        IF ( Delta <= 1, "PASS", "FAIL: " & Actual & " vs " & Expected )
```

### 5.3 Test Results Table

Create a table visual on a hidden **Test** page:

| Measure | Test Result |
|---|---|
| `Test Match Rate` | PASS / FAIL |
| `Test Exception Rate` | PASS / FAIL |
| `Test Total Exposure` | PASS / FAIL |
| `Test Unresolved Exposure` | PASS / FAIL |
| `Test Avg Confidence` | PASS / FAIL |
| `Test Review Queue Count` | PASS / FAIL |

**Pass criteria:** All measures show `PASS`.

### 5.4 Edge-Case DAX Tests

| Scenario | Test | Expected |
|---|---|---|
| Empty filter context | `[Match Rate %]` with all data | Non-zero value (dataset always has data) |
| Single-row filter | Select one `source_a_line_id` via drill-through | `Match Rate %` = 100% or 0% (single row is either matched or not) |
| Division by zero guard | `[Match Rate %]` when `Total Reconciled Lines = 0` | Returns 0 (DIVIDE with alternate) |
| Blank confidence | Row with `confidence_score = BLANK()` | `AVERAGE` excludes BLANK; verify measure ignores it |

---

## 6. Visual Regression Checks

### 6.1 Visual Rendering Checklist

For each page, verify:

| Check | Method |
|---|---|
| All visuals render without errors | Visual scan — no "couldn't load data" or red error icons |
| Conditional formatting applies correctly | Compare card colours to the rule table in §3 of DASHBOARD_DESIGN.md |
| KPI values display with correct format strings | Currency measures show `#,##0.00`; percentages show `%` |
| Sort order is correct on charts | `match_method_label` sorted by `sort_order`; `month_name` sorted by `month_number` |
| Slicers show all expected values | Branch slicer shows all branches; no missing categories |
| Drill-through menu appears on right-click | Right-click a table row → "Drill through" option is visible |
| Tooltips display on hover | Hover over bar chart → custom tooltip page appears |

### 6.2 Screenshot Comparison

1. Take screenshots of each page after the initial data load (baseline).
2. After any model or measure change, take new screenshots.
3. Visually compare to baseline — or use a diff tool (e.g., PixelMatch) for automated comparison.

**Key areas to check:**
- KPI card values and colours
- Chart axis labels and data points
- Table row counts and cell formatting
- Slicer selection state

### 6.3 Bookmark Validation

| Bookmark | Validation Steps |
|---|---|
| `Default View` | All slicers cleared; all visuals show full dataset |
| `High Exposure Focus` | Status = exception, exposure category = High; verify filtered state |
| `Fuzzy Match Investigation` | On Detailed Analysis page; match_method = fuzzy_name; confidence band slicer active |
| `Review Queue Only` | On Anomaly page; review_required = TRUE; verify only review rows appear |
| `Month-over-Month` | Trend page with MoM comparison overlay |

**Test procedure:**
1. Click each bookmark in the bookmark pane.
2. Verify the expected filter state is applied.
3. Verify all visuals reflect the filtered data.
4. Click back to `Default View` and confirm all filters are cleared.

---

## 7. Refresh Reliability Test

### 7.1 Manual Refresh

| Step | Action | Expected Result |
|---|---|---|
| 1 | Click **Refresh** in Power BI Desktop | Refresh completes with no errors |
| 2 | Check row counts post-refresh | Same as pre-refresh (same CSV files) |
| 3 | Check KPI measures post-refresh | Same values as pre-refresh |
| 4 | Replace CSV files with new synthetic data | Refresh completes; row counts update to new values |
| 5 | Check KPI measures with new data | Values change to reflect new dataset |

### 7.2 Incremental Data Test

1. Generate a new batch of CSV data (append new rows to existing files or replace).
2. Refresh the Power BI model.
3. Verify:
   - New rows appear in the fact table
   - Date dimension extends to cover new date range
   - No duplicate rows introduced

### 7.3 Error Handling During Refresh

| Scenario | Test | Expected Behaviour |
|---|---|---|
| Missing CSV file | Delete or rename `reconciliation_results.csv` before refresh | Power Query returns error; report shows stale data; error logged |
| Malformed CSV row | Add a row with wrong column count to a CSV | Power Query `try...otherwise` returns nulls for that row; other rows load |
| Null transaction_date | Include a row with blank date | Row is filtered out by the date quality guard; row count decreases by 1 |
| Type mismatch | Insert text into a numeric column | Power Query type step fails; error reported clearly |

### 7.4 Service (Power BI Service) Refresh

If the report is published to Power BI Service:

| Test | Action | Expected |
|---|---|---|
| Scheduled refresh | Configure daily refresh; wait 24h | Refresh succeeds; data updated |
| Gateway connection | Configure on-premises data gateway to CSV folder | Gateway connects; refresh succeeds |
| Refresh history | Check Refresh History in Service | Shows success/failure with timestamps |

> **Note:** For this portfolio project, Service refresh testing is optional. Manual Desktop refresh validation is sufficient.

---

## 8. Validation Execution Matrix

| # | Test Category | Test Case | Priority | Automated? | Owner |
|---|---|---|---|---|---|
| 1 | Data Count | Total row count match | P0 | Partial (DAX vs Python) | Analyst |
| 2 | Data Count | Filtered row count match | P0 | Manual | Analyst |
| 3 | KPI Measure | Match Rate % | P0 | DAX test measure | Analyst |
| 4 | KPI Measure | Exception Rate % | P0 | DAX test measure | Analyst |
| 5 | KPI Measure | Total Exposure | P0 | DAX test measure | Analyst |
| 6 | KPI Measure | Unresolved Exposure | P0 | DAX test measure | Analyst |
| 7 | KPI Measure | Average Confidence Score | P1 | DAX test measure | Analyst |
| 8 | KPI Measure | Review Queue Count | P1 | DAX test measure | Analyst |
| 9 | KPI Measure | YTD/MTD variants | P2 | Manual | Analyst |
| 10 | Cross-Filter | Branch filter propagation | P0 | Manual | Analyst |
| 11 | Cross-Filter | Category filter propagation | P0 | Manual | Analyst |
| 12 | Cross-Filter | Multi-slicer interaction | P1 | Manual | Analyst |
| 13 | Cross-Filter | Cross-page consistency | P1 | Manual | Analyst |
| 14 | Cross-Filter | Drill-through correctness | P0 | Manual | Analyst |
| 15 | DAX Unit Test | All test measures PASS | P0 | DAX test measures | Analyst |
| 16 | DAX Unit Test | Edge-case: empty filter | P1 | Manual | Analyst |
| 17 | DAX Unit Test | Edge-case: single row | P1 | Manual | Analyst |
| 18 | DAX Unit Test | Edge-case: division by zero | P0 | Manual | Analyst |
| 19 | Visual Regression | All visuals render | P0 | Visual scan | Analyst |
| 20 | Visual Regression | Conditional formatting | P1 | Visual scan | Analyst |
| 21 | Visual Regression | Sort order correctness | P1 | Visual scan | Analyst |
| 22 | Visual Regression | Bookmark states | P1 | Manual | Analyst |
| 23 | Visual Regression | Screenshot comparison | P2 | Semi-automated | Analyst |
| 24 | Refresh | Manual refresh succeeds | P0 | Manual | Analyst |
| 25 | Refresh | New data loads correctly | P1 | Manual | Analyst |
| 26 | Refresh | Error handling (missing file) | P2 | Manual | Analyst |
| 27 | Refresh | Error handling (malformed row) | P2 | Manual | Analyst |

**Priority definitions:**
- **P0:** Must pass before report is shared with any stakeholder
- **P1:** Must pass before report is published to production / portfolio
- **P2:** Should pass; non-blocking if minor issues found

---

## 9. Validation Log Template

```markdown
## Validation Run — [Date]

| # | Test Case | Result | Actual Value | Expected Value | Notes |
|---|---|---|---|---|---|
| 1 | Total row count | ✅ PASS | 12,847 | 12,847 | |
| 3 | Match Rate % | ✅ PASS | 92.40% | 92.40% | |
| 10 | Branch filter | ✅ PASS | — | — | Branch 07 isolates correctly |
| 14 | Drill-through | ❌ FAIL | — | — | Drill-through shows 0 rows; FK issue? |
| 24 | Manual refresh | ✅ PASS | — | — | 4.2s refresh time |

**Open Issues:**
- #14: Drill-through returns empty. Investigate `source_a_line_id` column in fact table.
```

---

## 10. Acceptance Criteria

The Power BI report is considered **validated** when:

1. **All P0 tests pass** with no open issues.
2. **All P1 tests pass** or have documented workarounds.
3. **KPI measures** match Python pipeline output within defined tolerance.
4. **Cross-filter** behaves correctly for all dimension interactions.
5. **Drill-through** works for all rows in the Review Queue Table.
6. **Manual refresh** completes without errors on the current dataset.
7. **Validation log** is complete and filed.

---

*Document version: 1.0 | Last updated: 2026-09-02 | Project: Transaction Reconciliation & Anomaly Detection Analytics*

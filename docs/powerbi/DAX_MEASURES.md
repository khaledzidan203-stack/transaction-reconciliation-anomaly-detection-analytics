# DAX Measures — Transaction Reconciliation & Anomaly Detection Analytics

> Complete DAX measure library for the Power BI star-schema model. All measures reference the fact table `reconciliation_results` and its surrounding dimensions.

---

## 1. Core KPI Measures

### 1.1 Total Reconciled Lines

```dax
Total Reconciled Lines =
    COUNTROWS ( 'reconciliation_results' )
```

Counts every row in the fact table — represents the total number of reconciled line-pairs (including unmatched).

---

### 1.2 Matched Lines

```dax
Matched Lines =
    CALCULATE (
        [Total Reconciled Lines],
        'reconciliation_results'[reconciliation_status] = "matched"
    )
```

---

### 1.3 Match Rate %

```dax
Match Rate % =
    DIVIDE (
        [Matched Lines],
        [Total Reconciled Lines],
        0
    )
```

**Format:** Percentage, 2 decimal places.

---

### 1.4 Exception Lines

```dax
Exception Lines =
    CALCULATE (
        [Total Reconciled Lines],
        'reconciliation_results'[reconciliation_status] = "exception"
            || 'reconciliation_results'[reconciliation_status] = "partial"
    )
```

---

### 1.5 Exception Rate %

```dax
Exception Rate % =
    DIVIDE (
        [Exception Lines],
        [Total Reconciled Lines],
        0
    )
```

**Format:** Percentage, 2 decimal places.

---

### 1.6 Unmatched A Lines (Source A Only)

```dax
Unmatched A Lines =
    CALCULATE (
        [Total Reconciled Lines],
        'reconciliation_results'[reconciliation_status] = "unmatched_a"
    )
```

---

### 1.7 Unmatched B Lines (Source B Only)

```dax
Unmatched B Lines =
    CALCULATE (
        [Total Reconciled Lines],
        'reconciliation_results'[reconciliation_status] = "unmatched_b"
    )
```

---

## 2. Exposure Measures

### 2.1 Total Exposure

```dax
Total Exposure =
    SUM ( 'reconciliation_results'[absolute_exposure] )
```

**Format:** Currency, 2 decimal places. Represents the total absolute financial discrepancy across all reconciled lines.

---

### 2.2 Signed Exposure

```dax
Signed Exposure =
    SUM ( 'reconciliation_results'[signed_exposure] )
```

**Format:** Currency, 2 decimal places. Positive = net overcharge (Source A > Source B); Negative = net undercharge.

---

### 2.3 Unresolved Exposure

```dax
Unresolved Exposure =
    SUM ( 'reconciliation_results'[unresolved_exposure] )
```

Exposure attributable to unmatched and exception-status lines that have not yet been resolved.

---

### 2.4 Review Exposure

```dax
Review Exposure =
    SUM ( 'reconciliation_results'[review_exposure] )
```

Financial exposure carried by lines flagged `review_required = TRUE`.

---

### 2.5 Quantity Exposure

```dax
Quantity Exposure =
    SUM ( 'reconciliation_results'[quantity_exposure] )
```

---

### 2.6 Price Exposure

```dax
Price Exposure =
    SUM ( 'reconciliation_results'[price_exposure] )
```

---

### 2.7 Amount Exposure

```dax
Amount Exposure =
    SUM ( 'reconciliation_results'[amount_exposure] )
```

---

### 2.8 Exposure per Line (Average)

```dax
Avg Exposure per Line =
    DIVIDE (
        [Total Exposure],
        [Total Reconciled Lines],
        0
    )
```

**Format:** Currency, 2 decimal places.

---

## 3. Confidence & Quality Measures

### 3.1 Average Confidence Score

```dax
Average Confidence Score =
    AVERAGE ( 'reconciliation_results'[confidence_score] )
```

**Format:** Decimal, 2 places. Ranges from 0.0 (no confidence) to 1.0 (exact match).

---

### 3.2 High-Confidence Match Rate %

```dax
High-Confidence Match Rate % =
    VAR HighConfidenceLines =
        CALCULATE (
            [Total Reconciled Lines],
            'reconciliation_results'[confidence_score] >= 0.95
        )
    RETURN
        DIVIDE ( HighConfidenceLines, [Total Reconciled Lines], 0 )
```

Lines matched at ≥ 95% confidence as a proportion of all lines.

---

### 3.3 Low-Confidence Lines Count

```dax
Low-Confidence Lines Count =
    CALCULATE (
        [Total Reconciled Lines],
        'reconciliation_results'[confidence_score] < 0.80
    )
```

Lines below 80% confidence — prime candidates for manual review.

---

## 4. Review Queue Measures

### 4.1 Review Queue Count

```dax
Review Queue Count =
    CALCULATE (
        [Total Reconciled Lines],
        'reconciliation_results'[review_required] = TRUE ()
    )
```

---

### 4.2 Review Queue Rate %

```dax
Review Queue Rate % =
    DIVIDE (
        [Review Queue Count],
        [Total Reconciled Lines],
        0
    )
```

---

### 4.3 Review Queue Exposure

```dax
Review Queue Exposure =
    CALCULATE (
        [Total Exposure],
        'reconciliation_results'[review_required] = TRUE ()
    )
```

---

## 5. Time-Intelligence Measures

> All time-intelligence measures require `date_dim` to be marked as the **Date Table** with `date` as the date column.

### 5.1 Monthly Match Rate Trend

```dax
Monthly Match Rate Trend =
    [Match Rate %]
```

Used in a line chart with `date_dim[month_key]` on the axis. The measure automatically aggregates by the month context from the axis.

---

### 5.2 Match Rate MTD

```dax
Match Rate MTD =
    CALCULATE (
        [Match Rate %],
        DATESMTD ( 'date_dim'[date] )
    )
```

---

### 5.3 Match Rate YTD

```dax
Match Rate YTD =
    CALCULATE (
        [Match Rate %],
        DATESYTD ( 'date_dim'[date] )
    )
```

---

### 5.4 Total Exposure YTD

```dax
Total Exposure YTD =
    CALCULATE (
        [Total Exposure],
        DATESYTD ( 'date_dim'[date] )
    )
```

---

### 5.5 Total Exposure MTD

```dax
Total Exposure MTD =
    CALCULATE (
        [Total Exposure],
        DATESMTD ( 'date_dim'[date] )
    )
```

---

### 5.6 Month-over-Month Exposure Change

```dax
MoM Exposure Change =
    VAR CurrentMonth = [Total Exposure]
    VAR PreviousMonth =
        CALCULATE (
            [Total Exposure],
            PREVIOUSMONTH ( 'date_dim'[date] )
        )
    RETURN
        CurrentMonth - PreviousMonth
```

---

### 5.7 MoM Exposure Change %

```dax
MoM Exposure Change % =
    VAR CurrentMonth = [Total Exposure]
    VAR PreviousMonth =
        CALCULATE (
            [Total Exposure],
            PREVIOUSMONTH ( 'date_dim'[date] )
        )
    RETURN
        DIVIDE ( CurrentMonth - PreviousMonth, PreviousMonth, 0 )
```

**Format:** Percentage, 2 decimal places.

---

## 6. Branch-Dimension Measures

### 6.1 Branch Match Rate

```dax
Branch Match Rate =
    [Match Rate %]
```

Used in a bar chart with `branch_master[branch_name]` on the axis. The measure respects the branch filter context automatically.

---

### 6.2 Branch Exposure Ranking

```dax
Branch Exposure Rank =
    RANKX (
        ALL ( 'branch_master'[branch_name] ),
        [Total Exposure],
        ,
        DESC,
        Dense
    )
```

Returns 1 for the branch with highest total exposure.

---

### 6.3 Branch Review Queue Count

```dax
Branch Review Queue Count =
    CALCULATE (
        [Review Queue Count],
        CROSSFILTER ( 'branch_master'[branch_id], 'reconciliation_results'[branch_id], NONE )
    )
    // Remove CROSSFILTER if single-direction propagation is sufficient
```

In practice, single-direction propagation handles this automatically; the measure is simply `[Review Queue Count]` with `branch_master[branch_name]` on the visual.

---

### 6.4 Top N Branches by Exposure

```dax
Top 5 Branches by Exposure =
    CALCULATE (
        [Total Exposure],
        TOPN (
            5,
            ALL ( 'branch_master'[branch_name] ),
            [Total Exposure], DESC
        )
    )
```

Used as a visual-level filter (Top N) on bar charts.

---

## 7. Category-Dimension Measures

### 7.1 Exposure by Category

```dax
Exposure by Category =
    [Total Exposure]
```

Used with `product_master[category]` or `reconciliation_results[category]` on the axis.

---

### 7.2 Match Rate by Category

```dax
Match Rate by Category =
    [Match Rate %]
```

---

### 7.3 Category Exception Count

```dax
Category Exception Count =
    CALCULATE (
        [Exception Lines],
        VALUES ( 'product_master'[category] )
    )
```

---

### 7.4 Category Average Confidence

```dax
Category Average Confidence =
    AVERAGEX (
        VALUES ( 'product_master'[category] ),
        [Average Confidence Score]
    )
```

---

## 8. Match Method Measures

### 8.1 Count by Match Method

```dax
Count by Match Method =
    [Total Reconciled Lines]
```

Used with `match_method_lookup[match_method_label]` on the axis.

---

### 8.2 Match Method Distribution %

```dax
Match Method Distribution % =
    VAR MethodCount = [Total Reconciled Lines]
    VAR GrandTotal =
        CALCULATE (
            [Total Reconciled Lines],
            ALL ( 'match_method_lookup' )
        )
    RETURN
        DIVIDE ( MethodCount, GrandTotal, 0 )
```

**Format:** Percentage, 2 decimal places.

---

### 8.3 Fuzzy Match Count

```dax
Fuzzy Match Count =
    CALCULATE (
        [Total Reconciled Lines],
        'reconciliation_results'[match_method] = "fuzzy_name"
    )
```

---

### 8.4 Fuzzy Match Avg Confidence

```dax
Fuzzy Match Avg Confidence =
    CALCULATE (
        [Average Confidence Score],
        'reconciliation_results'[match_method] = "fuzzy_name"
    )
```

---

## 9. Composite / Advanced Measures

### 9.1 Exposure Concentration Index

```dax
Exposure Concentration Index =
    VAR TotalExp = [Total Exposure]
    VAR LineCount = [Total Reconciled Lines]
    VAR AvgExp = DIVIDE ( TotalExp, LineCount, 0 )
    VAR StdDevExp =
        SQRT (
            AVERAGEX (
                'reconciliation_results',
                ( 'reconciliation_results'[absolute_exposure] - AvgExp )
                    * ( 'reconciliation_results'[absolute_exposure] - AvgExp )
            )
        )
    RETURN
        DIVIDE ( StdDevExp, AvgExp, 0 )
```

Coefficient of variation of exposure — higher values indicate exposure is concentrated in a few outliers.

---

### 9.2 Reconciliation Health Score

```dax
Reconciliation Health Score =
    VAR MatchWeight = 0.40
    VAR ConfidenceWeight = 0.30
    VAR ExposureWeight = 0.30
    VAR MatchComponent = [Match Rate %]
    VAR ConfidenceComponent = [Average Confidence Score]
    VAR MaxExposure = 1000000  -- adjust to dataset scale
    VAR ExposureComponent =
        MAX (
            0,
            1 - DIVIDE ( [Total Exposure], MaxExposure, 0 )
        )
    RETURN
        ( MatchWeight * MatchComponent )
        + ( ConfidenceWeight * ConfidenceComponent )
        + ( ExposureWeight * ExposureComponent )
```

Composite 0–1 score combining match rate, confidence, and low-exposure. Display as a gauge visual.

---

### 9.3 Unmatched Rate (A + B)

```dax
Unmatched Rate % =
    VAR UnmatchedLines =
        CALCULATE (
            [Total Reconciled Lines],
            'reconciliation_results'[reconciliation_status] = "unmatched_a"
                || 'reconciliation_results'[reconciliation_status] = "unmatched_b"
        )
    RETURN
        DIVIDE ( UnmatchedLines, [Total Reconciled Lines], 0 )
```

---

## 10. Measure Organisation

In Power BI Desktop, organise measures into **display folders** for clean field-panel navigation:

| Display Folder | Measures |
|---|---|
| `KPI\Core` | `Total Reconciled Lines`, `Matched Lines`, `Match Rate %`, `Exception Rate %` |
| `KPI\Exposure` | `Total Exposure`, `Signed Exposure`, `Unresolved Exposure`, `Review Exposure`, `Avg Exposure per Line` |
| `KPI\Confidence` | `Average Confidence Score`, `High-Confidence Match Rate %`, `Low-Confidence Lines Count` |
| `KPI\Review` | `Review Queue Count`, `Review Queue Rate %`, `Review Queue Exposure` |
| `Time Intelligence` | `Match Rate MTD`, `Match Rate YTD`, `Total Exposure YTD`, `Total Exposure MTD`, `MoM Exposure Change`, `MoM Exposure Change %` |
| `Branch` | `Branch Match Rate`, `Branch Exposure Rank` |
| `Category` | `Exposure by Category`, `Match Rate by Category`, `Category Average Confidence` |
| `Match Method` | `Count by Match Method`, `Match Method Distribution %`, `Fuzzy Match Count` |
| `Advanced` | `Exposure Concentration Index`, `Reconciliation Health Score`, `Unmatched Rate %` |

---

## 11. Formatting Standards

| Measure | Format String | Decimal Places |
|---|---|---|
| `Match Rate %` | `0.00%` | 2 |
| `Exception Rate %` | `0.00%` | 2 |
| `Total Exposure` | `#,##0.00` | 2 |
| `Average Confidence Score` | `0.00` | 2 |
| `Review Queue Count` | `#,##0` | 0 |
| `Avg Exposure per Line` | `#,##0.00` | 2 |
| `MoM Exposure Change %` | `0.00%` | 2 |
| `Reconciliation Health Score` | `0.00` | 2 |

---

*Document version: 1.0 | Last updated: 2026-09-02 | Project: Transaction Reconciliation & Anomaly Detection Analytics*

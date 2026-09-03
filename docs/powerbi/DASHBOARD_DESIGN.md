# Dashboard Design — Transaction Reconciliation & Anomaly Detection Analytics

> Page layout, visual selection, interaction behaviour, and styling conventions for the Power BI report.

---

## 1. Report Overview

The Power BI report contains **four pages**, each targeting a distinct analytical persona:

| Page | Audience | Purpose |
|---|---|---|
| **Executive Summary** | Management, CFO | High-level KPI cards, reconciliation status distribution, total exposure snapshot |
| **Detailed Analysis** | Reconciliation Analysts | Match-method drill-down, fuzzy-match investigation, product category breakdown |
| **Anomaly & Review** | Quality Assurance Team | Anomaly heatmap, review queue table with drill-through to line detail |
| **Trend Analysis** | Operations & Finance | Monthly trend lines, branch comparison, time-intelligence measures |

---

## 2. Global Design Conventions

### 2.1 Colour Palette

| Role | Hex | Usage |
|---|---|---|
| **Primary** | `#14532d` | Headers, primary buttons, matched-status accent |
| **Primary Light** | `#22c55e` | Positive KPI indicators, "healthy" gauges |
| **Accent / Warning** | `#d99727` | Partial matches, medium exposure, caution indicators |
| **Danger** | `#b91c1c` | Exceptions, high exposure, critical alerts |
| **Info** | `#2563eb` | Informational highlights, drill-through cues |
| **Unmatched Muted** | `#64748b` | Unmatched A status |
| **Unmatched Purple** | `#8b5cf6` | Unmatched B status |
| **Background** | `#f8fafc` | Page background |
| **Card Background** | `#ffffff` | KPI card tiles |
| **Border** | `#e2e8f0` | Card borders, table outlines |
| **Text Primary** | `#172033` | Body text, titles |
| **Text Muted** | `#637083` | Subtitles, axis labels |

### 2.2 Typography

| Element | Font | Size | Weight |
|---|---|---|---|
| Page title | Segoe UI Semibold | 20 pt | 600 |
| Section header | Segoe UI Semibold | 14 pt | 600 |
| KPI value | Segoe UI Bold | 28 pt | 700 |
| KPI label | Segoe UI Regular | 10 pt | 400 |
| Body / table text | Segoe UI Regular | 10 pt | 400 |
| Axis labels | Segoe UI Regular | 9 pt | 400 |

### 2.3 Cross-Filter Behaviour

| Visual Type | Default Cross-Filter | Override |
|---|---|---|
| Slicers | Filter all visuals on page | None |
| Bar / Column charts | Filter | None |
| Line charts | Filter | None |
| Pie / Donut | Filter | None |
| Maps | Filter | None |
| Tables | Filter | None (except Review Queue — see §4) |

> **Global rule:** Cross-filter remains **Filter** (not Highlight). This ensures clicking a bar in one chart genuinely reduces data in all others.

---

## 3. Page 1 — Executive Summary

### 3.1 Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Logo]  Transaction Reconciliation — Executive Summary             │
│  ┌─────────────── Page Navigator ──────────────────┐  [Date Slicer] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Match    │ │Exception │ │ Total    │ │Unresolved│ │ Review   │ │
│  │ Rate %   │ │ Rate %   │ │ Exposure │ │ Exposure │ │ Queue    │ │
│  │  92.4%   │ │   5.1%   │ │ 47,320   │ │ 12,840   │ │   127    │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│                                                                     │
│  ┌─────────────────────────────┐  ┌────────────────────────────┐    │
│  │                             │  │                            │    │
│  │  Reconciliation Status      │  │  Exposure by Status        │    │
│  │  (Donut Chart)              │  │  (Stacked Bar)             │    │
│  │                             │  │                            │    │
│  │  ○ Matched    92.4%        │  │  ████████ Exception        │    │
│  │  ○ Partial     2.3%        │  │  ██████  Partial           │    │
│  │  ○ Exception   2.8%        │  │  ████    Unmatched A       │    │
│  │  ○ Unmatched A 1.8%        │  │  ██      Unmatched B       │    │
│  │  ○ Unmatched B 0.7%        │  │                            │    │
│  │                             │  │                            │    │
│  └─────────────────────────────┘  └────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────┐  ┌────────────────────────────┐    │
│  │  Exposure by Match Method   │  │  Top 5 Branches by         │    │
│  │  (Horizontal Bar)           │  │  Exposure (Bar)            │    │
│  │                             │  │                            │    │
│  │  Exact   ██                 │  │  Branch 12  ████████████   │    │
│  │  Barcode ████               │  │  Branch 07  ████████      │    │
│  │  Fuzzy   ████████           │  │  Branch 03  ██████        │    │
│  │  Manual  ██████             │  │  Branch 19  ████          │    │
│  │  Unmatch ███████████████    │  │  Branch 01  ███           │    │
│  │                             │  │                            │    │
│  └─────────────────────────────┘  └────────────────────────────┘    │
│                                                                     │
│  [Branch Slicer]  [Category Slicer]  [Match Method Slicer]          │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Visual Specifications

| Visual | Type | Fields | Formatting |
|---|---|---|---|
| Match Rate % | KPI Card | `Match Rate %` | Green if ≥ 90%, amber 70–90%, red < 70% |
| Exception Rate % | KPI Card | `Exception Rate %` | Red if > 5%, amber 2–5%, green < 2% |
| Total Exposure | KPI Card | `Total Exposure` | Currency, conditional: red if > 50K |
| Unresolved Exposure | KPI Card | `Unresolved Exposure` | Currency, red if > 20% of Total Exposure |
| Review Queue | KPI Card | `Review Queue Count` | Integer, amber if > 100 |
| Reconciliation Status | Donut Chart | Legend: `reconciliation_status`, Value: `Total Reconciled Lines` | Colour by `reconciliation_status_lookup[status_color]` |
| Exposure by Status | Stacked Bar | Axis: `reconciliation_status`, Value: `Total Exposure` | Same colour mapping |
| Exposure by Match Method | Horizontal Bar | Axis: `match_method_label` (sorted by `sort_order`), Value: `Total Exposure` | Gradient from green (exact) to red (unmatched) |
| Top 5 Branches | Bar Chart | Axis: `branch_name`, Value: `Total Exposure`, Top N filter = 5 | Solid primary colour |

### 3.3 Slicers

| Slicer | Table | Column | Type | Multi-select |
|---|---|---|---|---|
| Date Range | `date_dim` | `date` | Between (slider) | N/A |
| Branch | `branch_master` | `branch_name` | List | Yes |
| Category | `product_master` | `category` | List | Yes |
| Match Method | `match_method_lookup` | `match_method_label` | List | Yes |

---

## 4. Page 2 — Detailed Analysis

### 4.1 Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Transaction Reconciliation — Detailed Analysis                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────┐  ┌────────────────────────────┐    │
│  │  Match Method Breakdown     │  │  Fuzzy Match Confidence    │    │
│  │  (Stacked Column)           │  │  Distribution (Histogram)  │    │
│  │                             │  │                            │    │
│  │  ▓ Exact  ▒ Barcode         │  │  ▁▂▃▅▇█▇▅▃▂▁             │    │
│  │  ▒ Fuzzy  ░ Manual          │  │  0.5  0.6 0.7 0.8 0.9 1.0│    │
│  │  ░ Unmatched                │  │  confidence_score bins     │    │
│  │  by reconciliation_status   │  │                            │    │
│  └─────────────────────────────┘  └────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────┐  ┌────────────────────────────┐    │
│  │  Product Category Analysis  │  │  Price vs Quantity         │    │
│  │  (Matrix)                   │  │  Difference Scatter        │    │
│  │                             │  │                            │    │
│  │  Category  │Match│Partial│Ex│  │     •                     │    │
│  │  ─────────┼─────┼───────┼──│  │        •  •               │    │
│  │  Pharma    │ 82% │  3%  │5%│  │     •     •               │    │
│  │  Devices   │ 95% │  1%  │2%│  │  •       •   •            │    │
│  │  Consumable│ 78% │  5%  │8%│  │    qty_diff →             │    │
│  │                             │  │                            │    │
│  └─────────────────────────────┘  └────────────────────────────┘    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Fuzzy Match Review Table                                     │   │
│  │  (Table visual — filtered to match_method = fuzzy_name)       │   │
│  │                                                               │   │
│  │  Source A Line │ Product A │ Product B │ Confidence │ Status  │   │
│  │  ──────────────┼───────────┼───────────┼────────────┼──────── │   │
│  │  A-00123       │ Amoxil    │ Amoxy     │ 0.82       │ Review  │   │
│  │  A-00456       │ Panadol   │ Panadole  │ 0.76       │ Review  │   │
│  │                                                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [Branch Slicer]  [Category Slicer]  [Confidence Band Slicer]       │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Visual Specifications

| Visual | Type | Fields | Notes |
|---|---|---|---|
| Match Method Breakdown | Stacked Column | Axis: `match_method_label`, Legend: `reconciliation_status`, Value: `Total Reconciled Lines` | Colour by status |
| Fuzzy Match Confidence Distribution | Column Chart (histogram) | Axis: `confidence_band`, Value: `Total Reconciled Lines` | Filter: `match_method = "fuzzy_name"` |
| Product Category Analysis | Matrix | Rows: `category`, Columns: `reconciliation_status`, Values: `Match Rate %` | Conditional formatting: green→red gradient on values |
| Price vs Quantity Difference Scatter | Scatter Chart | X: `quantity_difference`, Y: `price_difference`, Size: `absolute_exposure`, Details: `product_name` | Tooltips: `source_a_amount`, `source_b_amount` |
| Fuzzy Match Review Table | Table | Columns: `source_a_line_id`, `product_name` (A), `product_name` (B — from Source B), `confidence_score`, `reconciliation_status`, `review_required` | Page-level filter: `match_method = "fuzzy_name"` |

---

## 5. Page 3 — Anomaly & Review

### 5.1 Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Transaction Reconciliation — Anomaly & Review                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────┐  ┌────────────────────────────┐   │
│  │  Anomaly Heatmap             │  │  Review Queue Summary      │   │
│  │  (Matrix — branch × category)│  │  (KPI Cards row)           │   │
│  │                              │  │                            │   │
│  │       Pharma  Devices  Cons  │  │  ┌──────┐ ┌──────┐       │   │
│  │  BR01  ██     █       ████  │  │  │ 127  │ │$12.8K│       │   │
│  │  BR02  ████   ██      ██    │  │  │Queue │ │Expos │       │   │
│  │  BR03  ██     █       █████ │  │  │Count │ │ure   │       │   │
│  │  ...                         │  │  └──────┘ └──────┘       │   │
│  │                              │  │                            │   │
│  └──────────────────────────────┘  └────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Review Queue Table (with drill-through)                     │   │
│  │                                                              │   │
│  │  Line ID  │Branch │Product    │Exposure│Confidence│Status    │   │
│  │  ─────────┼───────┼───────────┼────────┼──────────┼───────── │   │
│  │  A-00123  │BR01   │Amoxil 500│  42.00 │  0.82    │Exception │   │
│  │  A-00456  │BR03   │Panadol   │  18.50 │  0.76    │Partial   │   │
│  │  ...                                                          │   │
│  │                                                              │   │
│  │  ▸ Click a row for drill-through to Reconciliation Detail    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────┐  ┌────────────────────────────┐   │
│  │  Anomaly Type Distribution   │  │  Exposure Aging            │   │
│  │  (Bar Chart)                 │  │  (Bar by days since flag)  │   │
│  │                              │  │                            │   │
│  │  ██████  Price Anomaly       │  │  0–7 days   ██████████    │   │
│  │  █████   Quantity Anomaly    │  │  8–30 days  ██████        │   │
│  │  ████    Amount Anomaly      │  │  31–60 days ███           │   │
│  │  ██      Identity Anomaly    │  │  60+ days   █             │   │
│  │                              │  │                            │   │
│  └──────────────────────────────┘  └────────────────────────────┘   │
│                                                                     │
│  [Branch Slicer]  [Category Slicer]  [Review Required Slicer]       │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Visual Specifications

| Visual | Type | Fields | Notes |
|---|---|---|---|
| Anomaly Heatmap | Matrix | Rows: `branch_name`, Columns: `category`, Values: `COUNTROWS(anomaly_results)` or `Total Exposure` | Conditional formatting: white→yellow→red gradient on cell values |
| Review Queue Summary | KPI Cards | `Review Queue Count`, `Review Queue Exposure` | Side-by-side cards |
| Review Queue Table | Table | `source_a_line_id`, `branch_name`, `product_name`, `absolute_exposure`, `confidence_score`, `reconciliation_status` | **Drill-through enabled** — right-click → "Drill through" → Reconciliation Detail page |
| Anomaly Type Distribution | Bar Chart | Axis: `anomaly_type` from `anomaly_results`, Value: count | Horizontal bars |
| Exposure Aging | Bar Chart | Axis: age bucket (calculated column or bin), Value: `Total Exposure` | Only for `review_required = TRUE` |

### 5.3 Drill-Through Page: Reconciliation Detail

A hidden page used as the drill-through target:

| Field | Source |
|---|---|
| `source_a_line_id` | Drill-through key |
| `source_a_transaction_id` | |
| `branch_name` | From `branch_master` |
| `employee_label` | From `employee_master` |
| `product_name` | From `product_master` |
| `match_method_label` | From `match_method_lookup` |
| `confidence_score` | |
| All status fields | `identity_status`, `quantity_status`, `price_status`, `amount_status` |
| All exposure fields | `signed_exposure`, `absolute_exposure`, `quantity_exposure`, `price_exposure`, `amount_exposure` |
| Source A / B amounts | `source_a_amount`, `source_b_amount` |

Layout: Single card per field, arranged in a 4-column grid. Back button in top-left corner.

---

## 6. Page 4 — Trend Analysis

### 6.1 Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Transaction Reconciliation — Trend Analysis                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Monthly Match Rate Trend                                    │   │
│  │  (Line Chart)                                                │   │
│  │                                                              │   │
│  │  100%┤                                                       │   │
│  │   95%┤ ──────────────────────────●─────── Match Rate %       │   │
│  │   90%┤          ●─────●─────●                                │   │
│  │   85%┤    ●──●                                               │   │
│  │   80%┤ ●─                                                    │   │
│  │       └──┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬──    │   │
│  │        Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct ...  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────┐  ┌────────────────────────────┐   │
│  │  Monthly Exposure Trend      │  │  Monthly Exception Count   │   │
│  │  (Area Chart)                │  │  (Column Chart)            │   │
│  │                              │  │                            │   │
│  │  ▓▓▓▓▓                      │  │  ██                        │   │
│  │  ▓▓▓▓▓▓▓▓▓▓                 │  │  ████                      │   │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓            │  │  ██████                    │   │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓       │  │  ████████                  │   │
│  │                              │  │  ██████████                │   │
│  └──────────────────────────────┘  └────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Branch Comparison — Match Rate & Exposure                    │   │
│  │  (Combo Chart: Bar + Line)                                   │   │
│  │                                                              │   │
│  │  ██████████████████████████████  BR01  ● 92% (line overlay)  │   │
│  │  ████████████████                BR03  ● 88%                 │   │
│  │  █████████████████████████        BR07  ● 94%                │   │
│  │  ████████████████████████████████ BR12  ● 91%                │   │
│  │  Bar = Total Exposure, Line = Match Rate %                   │   │
│  │                                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [Date Range Slicer]  [Region Slicer]  [Branch Slicer]              │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Visual Specifications

| Visual | Type | Fields | Notes |
|---|---|---|---|
| Monthly Match Rate Trend | Line Chart | Axis: `date_dim[month_key]` (sorted), Value: `Match Rate %` | Smooth line, data labels on hover |
| Monthly Exposure Trend | Stacked Area Chart | Axis: `date_dim[month_key]`, Values: `Unresolved Exposure`, `Review Exposure`, rest | Colour: danger tones |
| Monthly Exception Count | Column Chart | Axis: `date_dim[month_key]`, Value: `Exception Lines` | Amber fill |
| Branch Comparison | Combo Chart | Axis: `branch_name`, Bar: `Total Exposure` (left axis), Line: `Match Rate %` (right axis) | Dual axis; bar = currency, line = % |

### 6.3 Time-Intelligence Slicers

| Slicer | Column | Type | Purpose |
|---|---|---|---|
| Date Range | `date_dim[date]` | Relative / Between | Controls all time visuals |
| Region | `branch_master[region]` | Dropdown | Filters branch set |
| Branch | `branch_master[branch_name]` | List | Multi-select for comparison |

---

## 7. Bookmarks

| Bookmark Name | Purpose | What It Captures |
|---|---|---|
| `Default View` | Initial state — all filters cleared | All visuals, no filter selection |
| `High Exposure Focus` | Filter to exception + high exposure | `reconciliation_status = exception`, `exposure_category = High` |
| `Fuzzy Match Investigation` | Detailed Analysis page focused on fuzzy | `match_method = fuzzy_name`, confidence band slicer active |
| `Review Queue Only` | Anomaly page showing only review items | `review_required = TRUE` |
| `Month-over-Month` | Trend page with MoM comparison | Data type = "Selected visuals" for comparison overlay |

**Bookmark settings:**
- Data: **Checked** (preserves filter state)
- Display: **Checked** (preserves visual visibility)
- Current page: **Checked** (preserves which page is active)

---

## 8. Tooltips

Custom report-page tooltips for hover enrichment:

| Tooltip Page | Triggered By | Shows |
|---|---|---|
| `TT_ExposureDetail` | Hovering on exposure bar charts | `Signed Exposure`, `Unresolved Exposure`, `Review Exposure` as mini bar cluster |
| `TT_ConfidenceBreakdown` | Hovering on match method visuals | Confidence band distribution as small stacked bar |
| `TT_BranchSummary` | Hovering on branch charts | `Match Rate %`, `Total Exposure`, `Review Queue Count` for that branch |

Tooltip pages are set to **Page Size → Tooltip (320 × 240 px)** and marked as **Tooltip** type in page settings.

---

## 9. Conditional Formatting Rules

### 9.1 KPI Card Backgrounds

| Measure | Condition | Colour |
|---|---|---|
| Match Rate % | ≥ 90% | `#dcfce7` (green tint) |
| Match Rate % | 70–90% | `#fef9c3` (amber tint) |
| Match Rate % | < 70% | `#fee2e2` (red tint) |
| Exception Rate % | < 2% | Green |
| Exception Rate % | 2–5% | Amber |
| Exception Rate % | > 5% | Red |
| Total Exposure | < 10K | Green |
| Total Exposure | 10K–50K | Amber |
| Total Exposure | > 50K | Red |

### 9.2 Table Cell Formatting

| Column | Rule |
|---|---|
| `reconciliation_status` | Font colour by `reconciliation_status_lookup[status_color]` |
| `confidence_score` | Background gradient: red (0.0) → yellow (0.8) → green (1.0) |
| `absolute_exposure` | Background gradient: white (0) → red (max value) |
| `review_required` | Icon: ⚠ for TRUE, ✓ for FALSE |

### 9.3 Matrix Heatmap

| Measure | Min | Mid | Max | Colours |
|---|---|---|---|---|
| `Total Exposure` | 0 | Median | Max | White → `#fde68a` → `#dc2626` |
| `Exception Lines` | 0 | Median | Max | White → `#fed7aa` → `#b91c1c` |

---

## 10. Responsive Layout Notes

| Breakpoint | Behaviour |
|---|---|
| **Desktop (≥ 1280px)** | Full 2-column layouts as designed |
| **Tablet (768–1279px)** | KPI cards stack to 3 per row; chart pairs stack vertically |
| **Mobile (< 768px)** | KPI cards 2 per row; one chart per row; slicers collapsed into a pane |

> **Tip:** Use Power BI's **Canvas Layout** phone view to define a dedicated mobile layout for each page.

---

## 11. Performance Considerations

| Concern | Mitigation |
|---|---|
| Large tables on report | Limit table rows to **500** with a "Load more" prompt; use page-level filters |
| Too many visuals per page | Maximum **8–10** visuals per page; avoid visual clutter |
| Cross-filter cascades | All relationships are single-direction; no circular paths |
| DAX measure cost | Avoid complex iterators on the fact table in card visuals; prefer `CALCULATE` + filter pushdown |
| Image / custom visual load | Use only native Power BI visuals; no custom visuals from AppSource in this portfolio build |

---

*Document version: 1.0 | Last updated: 2026-09-02 | Project: Transaction Reconciliation & Anomaly Detection Analytics*

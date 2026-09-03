# Power Query M Transformation Plan

> Step-by-step Power Query (M) transformation logic for the Transaction Reconciliation & Anomaly Detection Analytics Power BI model.

---

## 1. Source Connections

All source data is synthetic CSV delivered via a **folder connection**. This allows the pipeline to pick up new data drops without editing queries.

### 1.1 Folder Connection

```m
let
    Source = Folder.Files("D:\data\raw\"),
    // Filter to CSV only
    CsvFiles = Table.SelectRows(Source, each Text.EndsWith([Extension], ".csv")),
    // Combine binaries
    Combined = Csv.Combine(CsvFiles)
in
    Combined
```

### 1.2 Individual File References (Alternative)

If folder connection is not preferred, each table has its own CSV source:

```m
// product_master
Source = Csv.Document(File.Contents("D:\data\raw\product_master.csv"),[Delimiter=",", Columns=9, Encoding=65001, QuoteStyle=QuoteStyle.Csv])

// branch_master
Source = Csv.Document(File.Contents("D:\data\raw\branch_master.csv"),[Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.Csv])

// employee_master
Source = Csv.Document(File.Contents("D:\data\raw\employee_master.csv"),[Delimiter=",", Columns=3, Encoding=65001, QuoteStyle=QuoteStyle.Csv])

// source_a_transaction_headers
Source = Csv.Document(File.Contents("D:\data\raw\source_a_transaction_headers.csv"),[Delimiter=",", Columns=7, Encoding=65001, QuoteStyle=QuoteStyle.Csv])

// source_b_transaction_headers
Source = Csv.Document(File.Contents("D:\data\raw\source_b_transaction_headers.csv"),[Delimiter=",", Columns=7, Encoding=65001, QuoteStyle=QuoteStyle.Csv])

// source_a_transaction_lines
Source = Csv.Document(File.Contents("D:\data\raw\source_a_transaction_lines.csv"),[Delimiter=",", Columns=13, Encoding=65001, QuoteStyle=QuoteStyle.Csv])

// source_b_transaction_lines
Source = Csv.Document(File.Contents("D:\data\raw\source_b_transaction_lines.csv"),[Delimiter=",", Columns=13, Encoding=65001, QuoteStyle=QuoteStyle.Csv])

// reconciliation_results
Source = Csv.Document(File.Contents("D:\data\raw\reconciliation_results.csv"),[Delimiter=",", Columns=24, Encoding=65001, QuoteStyle=QuoteStyle.Csv])

// data_quality_issues
Source = Csv.Document(File.Contents("D:\data\raw\data_quality_issues.csv"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv])

// anomaly_results
Source = Csv.Document(File.Contents("D:\data\raw\anomaly_results.csv"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv])

// review_queue
Source = Csv.Document(File.Contents("D:\data\raw\review_queue.csv"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv])

// kpi_summary
Source = Csv.Document(File.Contents("D:\data\raw\kpi_summary.csv"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv])

// expected_scenarios
Source = Csv.Document(File.Contents("D:\data\raw\expected_scenarios.csv"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv])
```

> **Encoding:** UTF-8 (65001) is the safe default for synthetic data containing Arabic or special characters.

---

## 2. Transformation Steps per Table

### 2.1 `product_master`

```m
let
    Source = Csv.Document(File.Contents("D:\data\raw\product_master.csv"),
        [Delimiter=",", Columns=9, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),

    // Step 1: Promote first row to headers
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),

    // Step 2: Type casting
    Typed = Table.TransformColumnTypes(Promoted, {
        { "product_id",           Int64.Type   },
        { "product_code",         type text    },
        { "barcode",              type text    },
        { "product_name",         type text    },
        { "generic_name",         type text    },
        { "brand",                type text    },
        { "category",             type text    },
        { "strength",             type text    },
        { "reference_unit_price", type number  }
    }),

    // Step 3: Trim whitespace on text columns
    Trimmed = Table.TransformColumns(Typed, {
        { "product_code",   Text.Trim, type text },
        { "barcode",        Text.Trim, type text },
        { "product_name",   Text.Trim, type text },
        { "generic_name",   Text.Trim, type text },
        { "brand",          Text.Trim, type text },
        { "category",       Text.Trim, type text }
    }),

    // Step 4: Remove rows with null product_id (data quality guard)
    Filtered = Table.SelectRows(Trimmed, each [product_id] <> null)

in
    Filtered
```

---

### 2.2 `branch_master`

```m
let
    Source = Csv.Document(File.Contents("D:\data\raw\branch_master.csv"),
        [Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),

    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),

    Typed = Table.TransformColumnTypes(Promoted, {
        { "branch_id",   Int64.Type },
        { "branch_name", type text  },
        { "city",        type text  },
        { "region",      type text  }
    }),

    Trimmed = Table.TransformColumns(Typed, {
        { "branch_name", Text.Trim, type text },
        { "city",        Text.Trim, type text },
        { "region",      Text.Trim, type text }
    })

in
    Trimmed
```

---

### 2.3 `employee_master`

```m
let
    Source = Csv.Document(File.Contents("D:\data\raw\employee_master.csv"),
        [Delimiter=",", Columns=3, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),

    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),

    Typed = Table.TransformColumnTypes(Promoted, {
        { "employee_id",    Int64.Type },
        { "employee_label", type text  },
        { "branch_id",      Int64.Type }
    }),

    Trimmed = Table.TransformColumns(Typed, {
        { "employee_label", Text.Trim, type text }
    })

in
    Trimmed
```

---

### 2.4 `source_a_transaction_headers` / `source_b_transaction_headers`

Both tables share the same schema; only the file path differs.

```m
let
    Source = Csv.Document(File.Contents("D:\data\raw\source_a_transaction_headers.csv"),
        [Delimiter=",", Columns=7, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),

    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),

    // Step 1: Type casting
    Typed = Table.TransformColumnTypes(Promoted, {
        { "transaction_id",   type text    },
        { "branch_id",        Int64.Type   },
        { "employee_id",      Int64.Type   },
        { "transaction_date", type date    },  // requires culture "en-US" if CSV uses MM/DD/YYYY
        { "transaction_type", type text    },
        { "total_amount",     type number  },
        { "source",           type text    }
    }),

    // Step 2: Date parsing fallback — if auto-parse fails
    // ParsedDate = Table.TransformColumns(Typed, {
    //     { "transaction_date", each Date.FromText(_, [Format="yyyy-MM-dd"]), type date }
    // }),

    // Step 3: Add source tag for traceability
    WithSource = Table.AddColumn(Typed, "source_system", each "A"),

    // Step 4: Remove rows with null transaction_id
    Filtered = Table.SelectRows(WithSource, each [transaction_id] <> null)

in
    Filtered
```

> Repeat for Source B, changing the file path and `"source_system"` value to `"B"`.

---

### 2.5 `source_a_transaction_lines` / `source_b_transaction_lines`

```m
let
    Source = Csv.Document(File.Contents("D:\data\raw\source_a_transaction_lines.csv"),
        [Delimiter=",", Columns=13, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),

    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),

    Typed = Table.TransformColumnTypes(Promoted, {
        { "line_id",        type text    },
        { "transaction_id", type text    },
        { "product_id",     Int64.Type   },
        { "product_code",   type text    },
        { "barcode",        type text    },
        { "product_name",   type text    },
        { "generic_name",   type text    },
        { "quantity",       Int64.Type   },
        { "unit_price",     type number  },
        { "amount",         type number  },
        { "reference_id",   type text    },
        { "source",         type text    }
    }),

    // Step 1: Trim text fields
    Trimmed = Table.TransformColumns(Typed, {
        { "product_code", Text.Trim, type text },
        { "barcode",      Text.Trim, type text },
        { "product_name", Text.Trim, type text },
        { "generic_name", Text.Trim, type text }
    }),

    // Step 2: Guard — quantity and amount must be non-negative
    FilteredQuality = Table.SelectRows(Trimmed, each [quantity] >= 0 and [amount] >= 0)

in
    FilteredQuality
```

---

### 2.6 `reconciliation_results` (Fact Table)

This is the **primary fact table** loaded directly from the pipeline output CSV. It already contains all enriched columns.

```m
let
    Source = Csv.Document(File.Contents("D:\data\raw\reconciliation_results.csv"),
        [Delimiter=",", Columns=24, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),

    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),

    // Step 1: Type casting — all columns
    Typed = Table.TransformColumnTypes(Promoted, {
        { "source_a_line_id",         type text     },
        { "source_a_transaction_id",  type text     },
        { "source_b_line_id",         type text     },
        { "source_b_transaction_id",  type text     },
        { "match_method",             type text     },
        { "confidence_score",         type number   },
        { "identity_status",          type text     },
        { "quantity_status",          type text     },
        { "price_status",             type text     },
        { "amount_status",            type text     },
        { "reconciliation_status",    type text     },
        { "review_required",          type logical  },
        { "quantity_difference",      Int64.Type    },
        { "price_difference",         type number   },
        { "amount_difference",        type number   },
        { "source_a_amount",          type number   },
        { "source_b_amount",          type number   },
        { "signed_exposure",          type number   },
        { "absolute_exposure",        type number   },
        { "quantity_exposure",        type number   },
        { "price_exposure",           type number   },
        { "amount_exposure",          type number   },
        { "unresolved_exposure",      type number   },
        { "review_exposure",          type number   }
    }),

    // Step 2: Enrich — add transaction_date from headers
    // (requires merge with source_a_transaction_headers)
    MergedDate = let
        HeadersA = source_a_transaction_headers,  // reference to already-loaded query
        KeyedHeaders = Table.SelectColumns(HeadersA, {"transaction_id", "transaction_date", "branch_id", "employee_id"}),
        Renamed = Table.RenameColumns(KeyedHeaders, {
            {"transaction_id", "source_a_transaction_id"},
            {"transaction_date", "transaction_date"},
            {"branch_id", "branch_id"},
            {"employee_id", "employee_id"}
        }),
        Joined = Table.NestedJoin(
            Typed,
            {"source_a_transaction_id"},
            Renamed,
            {"source_a_transaction_id"},
            "HeaderLookup",
            JoinKind.LeftOuter
        ),
        Expanded = Table.ExpandTableColumn(Joined, "HeaderLookup",
            {"transaction_date", "branch_id", "employee_id"},
            {"transaction_date", "branch_id", "employee_id"}
        )
    in Expanded,

    // Step 3: Enrich — add product_id from source_a_transaction_lines
    MergedProduct = let
        LinesA = source_a_transaction_lines,
        KeyedLines = Table.SelectColumns(LinesA, {"line_id", "product_id", "product_code"}),
        RenamedLines = Table.RenameColumns(KeyedLines, {
            {"line_id", "source_a_line_id"}
        }),
        Joined2 = Table.NestedJoin(
            MergedDate,
            {"source_a_line_id"},
            RenamedLines,
            {"source_a_line_id"},
            "LineLookup",
            JoinKind.LeftOuter
        ),
        Expanded2 = Table.ExpandTableColumn(Joined2, "LineLookup",
            {"product_id"},
            {"product_id"}
        )
    in Expanded2,

    // Step 4: Add calculated column — month_key (YYYYMM)
    WithMonthKey = Table.AddColumn(MergedProduct, "month_key", each
        Text.From(Date.Year([transaction_date])) &
        Text.PadStart(Text.From(Date.Month([transaction_date])), 2, "0")
    ),

    // Step 5: Type the new columns
    FinalTyped = Table.TransformColumnTypes(WithMonthKey, {
        { "transaction_date", type date   },
        { "branch_id",        Int64.Type  },
        { "employee_id",      Int64.Type  },
        { "product_id",       Int64.Type  },
        { "month_key",        type text   }
    }),

    // Step 6: Data quality filter — remove rows missing critical keys
    QualityFiltered = Table.SelectRows(FinalTyped, each
        [source_a_line_id] <> null and
        [reconciliation_status] <> null
    )

in
    QualityFiltered
```

---

## 3. Merge / Join Logic

### 3.1 Fact Enrichment — Headers Merge

**Purpose:** Enrich `reconciliation_results` with `transaction_date`, `branch_id`, and `employee_id` from the Source A transaction headers.

```
reconciliation_results
    LEFT JOIN source_a_transaction_headers
        ON reconciliation_results.source_a_transaction_id = source_a_transaction_headers.transaction_id
```

**Power Query:**

```m
Table.NestedJoin(
    reconciliation_results,
    {"source_a_transaction_id"},
    source_a_transaction_headers,
    {"transaction_id"},
    "HeaderLookup",
    JoinKind.LeftOuter
)
```

> **Why LeftOuter?** Every reconciliation row must survive even if the header lookup fails (data quality issue).

---

### 3.2 Fact Enrichment — Product Merge

**Purpose:** Add `product_id` to the fact for the dimension relationship.

```
reconciliation_results
    LEFT JOIN source_a_transaction_lines
        ON reconciliation_results.source_a_line_id = source_a_transaction_lines.line_id
```

**Power Query:**

```m
Table.NestedJoin(
    reconciliation_results,
    {"source_a_line_id"},
    source_a_transaction_lines,
    {"line_id"},
    "LineLookup",
    JoinKind.LeftOuter
)
```

---

### 3.3 Branch Name Merge (for the fact denormalised label)

If `branch_name` is needed directly in the fact (for quick tooltip display without relying on the relationship):

```m
Table.NestedJoin(
    reconciliation_results,
    {"branch_id"},
    branch_master,
    {"branch_id"},
    "BranchLookup",
    JoinKind.LeftOuter
)
// Expand: branch_name
```

> **Best practice:** Prefer the dimensional relationship over denormalisation. Only add `branch_name` to the fact if a specific visual requires it outside the relationship filter path.

---

## 4. Calculated Columns (Power Query)

### 4.1 `month_key`

```m
Table.AddColumn(PreviousStep, "month_key", each
    Text.From(Date.Year([transaction_date])) &
    Text.PadStart(Text.From(Date.Month([transaction_date])), 2, "0")
)
```

Result: `"202601"`, `"202602"`, etc. Used for sorting and trend grouping.

---

### 4.2 `is_weekend`

```m
Table.AddColumn(PreviousStep, "is_weekend", each
    Date.DayOfWeek([transaction_date], Day.Sunday) >= 5
)
```

Returns `true` for Saturday (5) and Sunday (6).

---

### 4.3 `exposure_category`

```m
Table.AddColumn(PreviousStep, "exposure_category", each
    if [absolute_exposure] = 0 then "None"
    else if [absolute_exposure] <= 50 then "Low"
    else if [absolute_exposure] <= 500 then "Medium"
    else "High"
)
```

Buckets exposure for histogram visuals. Thresholds are configurable.

---

### 4.4 `confidence_band`

```m
Table.AddColumn(PreviousStep, "confidence_band", each
    if [confidence_score] >= 0.95 then "High (≥95%)"
    else if [confidence_score] >= 0.80 then "Medium (80–95%)"
    else if [confidence_score] >= 0.50 then "Low (50–80%)"
    else "Very Low (<50%)"
)
```

---

## 5. Date Dimension Generation

Generated in Power Query to cover the full date range of the fact table:

```m
let
    // Dynamically determine date range from the fact
    FactDates = List.Buffer(
        Table.Column(reconciliation_results, "transaction_date")
    ),
    MinDate = List.Min(FactDates),
    MaxDate = List.Max(FactDates),

    // Generate calendar
    DateList = List.Dates(MinDate, Number.From(MaxDate - MinDate) + 1, #duration(1, 0, 0, 0)),
    DateTable = Table.FromList(DateList, (d) => {d}, {"date"}),
    Typed = Table.TransformColumnTypes(DateTable, {{"date", type date}}),

    // Add attributes
    WithYear = Table.AddColumn(Typed, "year", each Date.Year([date]), Int64.Type),
    WithQuarter = Table.AddColumn(WithYear, "quarter", each "Q" & Text.From(Date.QuarterOfYear([date])), type text),
    WithMonthNum = Table.AddColumn(WithQuarter, "month_number", each Date.Month([date]), Int64.Type),
    WithMonthName = Table.AddColumn(WithMonthNum, "month_name", each Date.ToText([date], "MMM"), type text),
    WithMonthKey = Table.AddColumn(WithMonthName, "month_key", each
        Text.From(Date.Year([date])) & Text.PadStart(Text.From(Date.Month([date])), 2, "0"),
        type text
    ),
    WithDayOfWeek = Table.AddColumn(WithMonthKey, "day_of_week", each Date.ToText([date], "ddd"), type text),
    WithIsWeekend = Table.AddColumn(WithDayOfWeek, "is_weekend", each Date.DayOfWeek([date], Day.Sunday) >= 5, type logical),

    // Fiscal year (assume July start)
    WithFiscalYear = Table.AddColumn(WithIsWeekend, "fiscal_year", each
        if Date.Month([date]) >= 7 then Date.Year([date]) + 1 else Date.Year([date]),
        Int64.Type
    ),
    WithFiscalQuarter = Table.AddColumn(WithFiscalYear, "fiscal_quarter", each
        let
            m = Date.Month([date]),
            fq = if m >= 7 then
                    "FQ" & Text.From(Number.IntegerDivide(m - 7, 3) + 1)
                 else
                    "FQ" & Text.From(Number.IntegerDivide(m + 5, 3))
        in fq,
        type text
    )

in
    WithFiscalQuarter
```

---

## 6. Lookup Table Generation

### 6.1 `match_method_lookup`

```m
let
    Source = #table(
        {"match_method", "match_method_label", "sort_order"},
        {
            {"exact",      "Exact ID Match",    1},
            {"barcode",    "Barcode Match",     2},
            {"fuzzy_name", "Fuzzy Name Match",  3},
            {"manual",     "Manual Review",     4},
            {"unmatched",  "Unmatched",         5}
        }
    ),
    Typed = Table.TransformColumnTypes(Source, {
        {"match_method",      type text},
        {"match_method_label", type text},
        {"sort_order",        Int64.Type}
    })
in
    Typed
```

---

### 6.2 `reconciliation_status_lookup`

```m
let
    Source = #table(
        {"reconciliation_status", "status_label",            "status_color"},
        {
            {"matched",     "Fully Matched",      "#16a34a"},
            {"partial",     "Partial Match",      "#eab308"},
            {"exception",   "Exception",          "#dc2626"},
            {"unmatched_a", "Unmatched (POS)",    "#64748b"},
            {"unmatched_b", "Unmatched (Ref)",    "#8b5cf6"}
        }
    ),
    Typed = Table.TransformColumnTypes(Source, {
        {"reconciliation_status", type text},
        {"status_label",          type text},
        {"status_color",          type text}
    })
in
    Typed
```

---

## 7. Data Quality Filtering

### 7.1 Null Key Guard

Applied to every dimension table to prevent orphan rows:

```m
Table.SelectRows(DimensionTable, each [PrimaryKey] <> null)
```

### 7.2 Negative Amount Guard

Applied to transaction lines and reconciliation amounts:

```m
Table.SelectRows(TransactionLines, each [amount] >= 0 and [quantity] >= 0)
```

### 7.3 Invalid Date Guard

Applied to header tables after date parsing:

```m
Table.SelectRows(Headers, each [transaction_date] <> null and [transaction_date] >= #date(2020, 1, 1))
```

### 7.4 Duplicate Check

For dimension tables, assert uniqueness on the primary key:

```m
// Diagnostic step — not for production ETL, but useful during development
DuplicateCheck = let
    Grouped = Table.Group(product_master, {"product_id"}, {{"Count", each Table.RowCount(_), Int64.Type}}),
    Dups = Table.SelectRows(Grouped, each [Count] > 1)
in
    if Table.RowCount(Dups) > 0 then error "Duplicate product_id found" else product_master
```

---

## 8. Load Strategy

| Table | Load Mode | Reason |
|---|---|---|
| `reconciliation_results` | **Import** | Fact table — needs fast DAX queries; data volume is modest (≤ 50K rows) |
| `product_master` | **Import** | Small dimension (< 1K rows) |
| `branch_master` | **Import** | Tiny dimension (< 50 rows) |
| `employee_master` | **Import** | Small dimension (< 200 rows) |
| `date_dim` | **Import** | Calculated table — always in-memory |
| `match_method_lookup` | **Import** | 5 rows |
| `reconciliation_status_lookup` | **Import** | 5 rows |
| `data_quality_issues` | **Import** | Reference only — not for visuals |
| `anomaly_results` | **Import** | Secondary analysis table |
| `review_queue` | **Import** | Operational reference |

> **Why all Import?** The dataset is synthetic and small enough for full in-memory caching. No DirectQuery or Dual mode is needed.

---

## 9. Query Dependency Graph

```
CSV Files
  ├── product_master.csv ──────────────► product_master
  ├── branch_master.csv ───────────────► branch_master
  ├── employee_master.csv ─────────────► employee_master
  ├── source_a_headers.csv ────────────► source_a_transaction_headers ──┐
  ├── source_b_headers.csv ────────────► source_b_transaction_headers   │
  ├── source_a_lines.csv ──────────────► source_a_transaction_lines ────┤
  ├── source_b_lines.csv ──────────────► source_b_transaction_lines     │
  │                                                                     │
  ├── reconciliation_results.csv ─► reconciliation_results ─────────────┤
  │     ├── LEFT JOIN source_a_transaction_headers (date, branch, emp) ◄┘
  │     ├── LEFT JOIN source_a_transaction_lines (product_id)
  │     ├── AddColumn month_key
  │     ├── AddColumn exposure_category
  │     └── AddColumn confidence_band
  │
  ├── date_dim ◄── generated from reconciliation_results[transaction_date]
  ├── match_method_lookup ◄── hardcoded
  └── reconciliation_status_lookup ◄── hardcoded
```

---

## 10. Refresh Configuration

| Setting | Value |
|---|---|
| Refresh schedule | Manual (portfolio project — no live gateway) |
| Incremental refresh | Not applicable (data volume is small) |
| Error handling | `try ... otherwise` wrappers on date parsing; nulls on failure |
| Query folding | Not applicable (CSV sources do not fold) |

---

*Document version: 1.0 | Last updated: 2026-09-02 | Project: Transaction Reconciliation & Anomaly Detection Analytics*

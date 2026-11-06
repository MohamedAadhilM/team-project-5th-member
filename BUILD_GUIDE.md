# Power BI build guide - Counterfactual Diagnostics (Week 4, Mohamed Aadhil M.)

I could not create a `.pbix` file (it needs Power BI Desktop). Everything else is ready: model tables, Power Query, DAX measures and theme. Building the report takes about 45 minutes.

## 1. Load the data (5 min)
1. Power BI Desktop -> Home -> **Transform data** -> New parameter: name `DataFolder`, type Text, value = the full path of this folder with a trailing `\`.
2. For each block in `load_data.pq.m`: New Source -> Blank Query -> Advanced Editor -> paste -> rename the query to the name in the comment (DimUnit, DimDate, FactCounterfactual, FactFit, FactDonor, FactValidation, MetricSel). Close & Apply.

## 2. Model (5 min)
Relationships (all one-to-many, single direction from Dim to Fact):
- `DimUnit[unit_pool_key]` -> FactCounterfactual, FactFit, FactDonor, FactValidation (same column name)
- `DimDate[week_start]` -> `FactCounterfactual[week_start]`
- `MetricSel` stays disconnected. Mark DimDate as a date table (column `week_start`).
- Hide key columns; set `DimUnit[product_label]` sort-by `product_id`; `DimDate[month]` sort-by `week_start`.
- Add a what-if table: Modeling -> New parameter -> Numeric range 0 to 60 step 1, name `Gap Threshold`, default 10.

## 3. Measures and theme (5 min)
- Home -> Enter data -> blank table named `_Measures`; paste each measure from `measures.dax` (New measure).
- View -> Themes -> Browse for themes -> `theme.json`.
- Format: Actual/Synthetic/Gap/Cumulative Gap as `#,0.0`; `%` measures as 0.0%; `Skill vs Constant` as 0.00.

## 4. Pages and visuals (30 min)

**Page 1 - Executive overview**
- Slicers (sync across pages: View -> Sync slicers): `DimUnit[region_label]` (tile), `DimUnit[product_label]` (dropdown), `DimUnit[pool_label]` (tile, default **Clean donors R07,R08 (frozen)**).
- Cards: `Post Avg Gap`, `Post Avg Gap %`, `Cumulative Gap (End)`, `Fit Grade` (font colour -> Conditional formatting -> Field value -> `Fit Color`).
- Text box / card bound to `Fit Warning` (red banner).
- Line chart: X `DimDate[week_start]`, Y `Actual Revenue`, `Synthetic Revenue`; add a constant line at `Intervention Date` (Analytics pane -> X-axis constant line). Title -> fx -> `Chart Title`.
- Column chart: X `DimDate[week_start]`, Y `Gap`; Columns -> Colours -> fx -> Field value -> `Gap Color`.

**Page 2 - Counterfactual diagnostics**
- Line chart: `Cumulative Gap` by `DimDate[week_start]` (with Analytics -> zero constant line).
- Line chart with **Selected Metric** (slicer on `MetricSel[Metric]`, single select) by week.
- Scatter: X `Pre RMSPE % of Revenue`, Y `Skill vs Constant`, Details `DimUnit[unit_id]`, Colour via `Fit Color`; Analytics -> constant lines at 0.05 and 0.30 (grade B/A thresholds).
- Table: unit_id, `Pre RMSPE (index pts)`, `Skill vs Constant`, `Pre Correlation`, `Fit Grade`, `Post Avg Gap`, `Cumulative Gap (End)` with data bars on skill.
- What-if slicer `Gap Threshold` + card `Weeks Beyond Threshold` (of `Post Weeks`).

**Page 3 - Segment validation (clean pool)**
- Matrix: rows `region_label` > `product_label`; values `Validation Verdict`, `Placebo Rank (of 7)`, `ATT LOO Min`, `ATT LOO Max`; conditional formatting on verdict (contains "Unsupported" -> red).
- Cards: `Segments Grade C`, `Segments Total`, `Sign Stable %`.
- Clustered bar: `FactValidation[ATT_main_clean_pool]` vs `ATT_all6_pool` by unit_id.

**Page 4 - Donors and spillover**
- Stacked bar: Axis `DimUnit[unit_id]`, Legend `FactDonor[donor_region]`, Values `Avg Donor Weight`.
- Card: `Exposed Donor Weight Share`; Table: donor_region, donor_type, `post_mean_network_exposure`.

**Page 5 - Unit detail (drill-through)**
- Add `DimUnit[unit_id]` to Drill-through fields. Reuse the actual-vs-synthetic line chart, cumulative gap, fit cards and `Validation Verdict`. Right-click any unit in Pages 2-3 -> Drill through.

**Tooltip page**: Page size -> Tooltip; add a small line chart (Actual vs Synthetic) and `Fit Grade` card; set it as the tooltip on the scatter and matrix.

## 5. Interactivity checklist
- Cross-filtering between all visuals, synced slicers, drill-through, report-page tooltip.
- Bookmarks (View -> Bookmarks): "Clean pool" and "All-6 pool" (set the pool slicer, add bookmark, uncheck Data); add Buttons (Insert -> Buttons -> Bookmark) on Page 1. Add a "Reset filters" button bound to a bookmark taken with no filters.
- Page-navigation buttons (Insert -> Buttons -> Navigator -> Page navigator).
- Visual interactions: Format -> Edit interactions so the scatter does not filter the cards.

## 6. Reconcile before you show it (must match the Day 5 CSV)
Clean pool, All products, Grade C everywhere:
| Selection | Post Avg Gap | Cumulative Gap (End) |
|---|---|---|
| R01 | 19.45 | 1089.0 |
| R04 | -13.74 | -769.7 |
| R01+R04 average | 2.60 | 145.7 |

`Segments Grade C` = 38 of 42 (all units and both pools; the 4 grade-B units are in the all-6 pool). Clean pool alone: 21 of 21 grade C.

## 7. Message to keep on the page
The synthetic control does not track pre-treatment revenue better than a flat baseline, so gaps are descriptive, not a pricing effect. Show `Fit Warning` on every page.

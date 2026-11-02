// ===== Power Query (M) - paste each block into a Blank Query (Home -> Get Data -> Blank Query -> Advanced Editor) =====
// 1) Create a text parameter named DataFolder, e.g.  C:\Users\you\week4_counterfactual\outputs\powerbi\

// ---- DimUnit
let
    Source = Csv.Document(File.Contents(DataFolder & "DimUnit.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{"unit_pool_key", type text}, {"unit_id", type text}, {"treated_unit", type text}, {"product_id", type text}, {"donor_pool", type text}, {"fit_grade", type text}, {"region_label", type text}, {"product_label", type text}, {"pool_label", type text}})
in
    Typed

// ---- DimDate
let
    Source = Csv.Document(File.Contents(DataFolder & "DimDate.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{"week_start", type date}, {"week_index", Int64.Type}, {"period", type text}, {"weeks_from_intervention", Int64.Type}, {"month", type text}})
in
    Typed

// ---- FactCounterfactual
let
    Source = Csv.Document(File.Contents(DataFolder & "FactCounterfactual.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{"week_start", type date}, {"actual_revenue", type number}, {"synthetic_revenue", type number}, {"gap", type number}, {"cumulative_gap", type number}, {"unit_pool_key", type text}}, "en-US")
in
    Typed

// ---- FactFit
let
    Source = Csv.Document(File.Contents(DataFolder & "FactFit.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{"pre_MSPE_index", type number}, {"pre_RMSPE_index", type number}, {"pre_RMSPE_pct_of_actual", type number}, {"constant_baseline_MSPE", type number}, {"skill_vs_constant", type number}, {"fit_grade", type text}, {"pre_correlation", type number}, {"max_abs_pre_gap", type number}, {"pre_weeks", Int64.Type}, {"post_weeks", Int64.Type}, {"ATT_revenue_per_product_day", type number}, {"ATT_pct_of_counterfactual", type number}, {"cumulative_gap_end", type number}, {"unit_pool_key", type text}}, "en-US")
in
    Typed

// ---- FactDonor
let
    Source = Csv.Document(File.Contents(DataFolder & "FactDonor.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{"donor_region", type text}, {"weight", type number}, {"donor_type", type text}, {"post_mean_network_exposure", type number}, {"max_weight_in_unit", type number}, {"unit_pool_key", type text}}, "en-US")
in
    Typed

// ---- FactValidation
let
    Source = Csv.Document(File.Contents(DataFolder & "FactValidation.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{"skill_vs_constant", type number}, {"ATT_main_clean_pool", type number}, {"ATT_min_leave_one_donor_out", type number}, {"ATT_max_leave_one_donor_out", type number}, {"ATT_all6_pool", type number}, {"sign_stable_across_pools", type logical}, {"placebo_rank_of_7", Int64.Type}, {"placebo_p", type number}, {"max_donor_weight", type number}, {"exposed_donors_used", Int64.Type}, {"verdict", type text}, {"unit_pool_key", type text}}, "en-US")
in
    Typed

// ---- MetricSel
let
    Source = Csv.Document(File.Contents(DataFolder & "MetricSel.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{"Metric", type text}, {"Order", Int64.Type}})
in
    Typed

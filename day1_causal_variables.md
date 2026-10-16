# Day 1 — Define Causal Variables and Assumptions

| | |
|---|---|
| **Member** | Member 5 — Mohamed Aadhil M |
| **Role** | Causal Inference Analyst |
| **Branch** | `feature/causal-dag` |
| **Task (Detailed Plan, commit 5)** | Define treatment, outcome and candidate confounders for the pricing causal question |
| **Expected deliverable** | Documented causal variables and assumptions |
| **Commit message** | `docs: define causal treatment outcome and confounders` |

## 1. Causal question
> Did introducing dynamic pricing in a market change that market's revenue, compared with what its revenue would have been without it?

## 2. Treatment and outcome
| Role | Variable | Definition |
|---|---|---|
| **Treatment** | `dynamic_pricing` | 1 from the week a market goes live with dynamic pricing, otherwise 0 |
| **Outcome** | `log_revenue` | Natural log of weekly gross revenue, so effects read as percentage changes |

*(Column names follow our project panel. If the team's merged dataset names them differently, replace the names here and in the DAG.)*

## 3. Candidate confounders (cause both adoption and revenue)
| Variable | Meaning | Why it is a candidate |
|---|---|---|
| `urban_index` | How urban the market is | Urban markets adopt earlier and sell differently |
| `log_pop` | Market size | Larger markets adopt earlier and earn more |
| `comp_intensity` | Competitive pressure | Competitive markets react sooner and shape competitor prices |
| `comp_gap`, `comp_gap_4w` | Competitor price relative to the market's normal price (weekly and 4-week average) | Rising competitor prices trigger adoption and also lift demand |
| `seasonality` | Calendar pattern | Moves revenue and competitor prices |

## 4. Other variables to classify (decided on Day 3)
| Variable | Initial view |
|---|---|
| `income_z` | Affects revenue only |
| `neighbor_adoption` | Spillover from neighbouring markets onto revenue |
| `log_price` / realised price | Likely a **mediator**: dynamic pricing changes the price, and price changes revenue |
| `local_demand` | **Unobserved** demand that moves competitor prices and revenue |

## 5. Assumptions (draft)
1. **Unconfoundedness:** once the confounders are controlled, no other shared cause of adoption and revenue remains.
2. **No interference (SUTVA):** one market's pricing does not change another's revenue. This is doubtful in a connected marketplace, so spillover is tracked.
3. **Overlap:** markets that never adopted exist and resemble the adopters.
4. **No anticipation:** revenue does not change before go-live.
5. **Consistency:** "dynamic pricing" means the same intervention in every market.

## 6. Plain-words explanation
We want the effect of the new pricing on revenue. But big, urban, competitive markets adopted first and would have earned more anyway. Those shared causes are confounders; ignoring them would credit the pricing with revenue it did not create.

## 7. Submit
- `docs/causal/day1_causal_variables.md` (this file)
- Open a pull request from `feature/causal-dag` into `main`; then set Day 1 to **Confirmed** and paste the commit or PR link in the tracker.

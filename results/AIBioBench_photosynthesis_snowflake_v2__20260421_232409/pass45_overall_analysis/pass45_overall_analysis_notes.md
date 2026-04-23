# AIBioBench Passes 4-5 Overall Analysis

Run analyzed: `AIBioBench_photosynthesis_snowflake_v2__20260421_232409`

Scope: passes 4 and 5 only. This covers 20 Python/pandas queries, 13 models, and 3 repeated attempts per model-query pair.

## Headline Findings

- Overall exact conversion was 3/780 attempts (0.4%).
- Pass 4 produced 3/390 exact attempts, all from one query; pass 5 produced 0/390 exact attempts.
- 19/20 queries had zero exact attempts. The only query with any exact answer was P4 Q10 repairability audit.
- Gemma 4 31B was the only exact converter with 3/60 exact attempts; every other model had zero exact attempts across passes 4-5.
- Pass 5 had a higher mean score than pass 4 (0.548 vs 0.516) because row-set correctness improved (0.757 vs 0.632), but numeric correctness collapsed (0.191 vs 0.490).
- The dominant failure pattern moved from reconciliation/orphan/presentation row-set errors in pass 4 to expression-transform, z-score, coefficient-of-variation, and signal-ranking numeric errors in pass 5.

## Pass-Level Summary

| Pass | Exact Attempts | Queries With Any Exact | Exact-Zero Queries | Mean Score | Row-Set Correctness | Numeric Correctness | Dominant Failure Mode |
|---|---:|---:|---:|---:|---:|---:|---|
| Pass 4 | 3/390 | 1/10 | 9/10 | 0.516 | 0.632 | 0.490 | row_count_mismatch |
| Pass 5 | 0/390 | 0/10 | 10/10 | 0.548 | 0.757 | 0.191 | row_count_mismatch |

## Model Groups

| Group | Models | Interpretation |
|---|---|---|
| Only exact converter | Gemma 4 31B | Only model with any exact conversion across passes 4-5, limited to the pass-4 repairability audit. |
| Top partial-credit operators | Gemma 4 26B, Qwen3 Coder 30B | No exact answers, but strongest partial credit and relatively stable row recovery across both Python passes. |
| Upper-middle row-recovery operators | Qwen3.6, Qwen 2.5 72B, Llama 3 70B | Useful row-set recovery, but exactness collapsed under expression mapping, statistics, and presentation constraints. |
| Row/numeric fragile operators | Mixtral 8x22B, DeepSeek Coder 33B, Command R+, CodeLlama 70B, DBRX, Qwen 2.5 Coder 32B | Some useful table shapes, but failures cluster around row leakage and derived numeric values. |
| Brittle / low-coverage | Phi-4 Mini | Low partial credit with weak row-set and numeric correctness across the Python-heavy phase. |

## Model Ranking

| Model | Exact Attempts | Pass 4 | Pass 5 | Mean Score | Row-Set Correctness | Numeric Correctness | Score Change P4 to P5 | Dominant Failure |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Gemma 4 31B | 3/60 | 3 | 0 | 0.688 | 0.835 | 0.513 | 0.056 | same_count_wrong_values |
| Gemma 4 26B | 0/60 | 0 | 0 | 0.593 | 0.769 | 0.404 | 0.069 | same_count_wrong_values |
| Qwen3 Coder 30B | 0/60 | 0 | 0 | 0.585 | 0.748 | 0.412 | 0.074 | same_count_wrong_values |
| Qwen3.6 | 0/60 | 0 | 0 | 0.557 | 0.702 | 0.398 | 0.032 | same_count_wrong_values |
| Qwen 2.5 72B | 0/60 | 0 | 0 | 0.543 | 0.718 | 0.339 | 0.093 | row_count_mismatch |
| Llama 3 70B | 0/60 | 0 | 0 | 0.527 | 0.708 | 0.312 | 0.046 | row_count_mismatch |
| Mixtral 8x22B | 0/60 | 0 | 0 | 0.517 | 0.667 | 0.360 | 0.014 | row_count_mismatch |
| DeepSeek Coder 33B | 0/60 | 0 | 0 | 0.511 | 0.689 | 0.282 | 0.019 | row_count_mismatch |
| Command R+ | 0/60 | 0 | 0 | 0.509 | 0.674 | 0.285 | 0.016 | same_count_wrong_values |
| CodeLlama 70B | 0/60 | 0 | 0 | 0.503 | 0.650 | 0.306 | -0.020 | row_count_mismatch |
| DBRX | 0/60 | 0 | 0 | 0.484 | 0.661 | 0.317 | 0.021 | row_count_mismatch |
| Qwen 2.5 Coder 32B | 0/60 | 0 | 0 | 0.470 | 0.601 | 0.306 | -0.076 | row_count_mismatch |
| Phi-4 Mini | 0/60 | 0 | 0 | 0.431 | 0.602 | 0.197 | 0.067 | row_count_mismatch |

## Query-Level Takeaways

**Best solvability by exactness and partial score:**

- P4 Q10 `pass4.query10`: 3/39 exact, mean score 0.989, family `repairability_review`.
- P4 Q1 `pass4.query1`: 0/39 exact, mean score 0.849, family `audit_reconciliation`.
- P5 Q8 `pass5.query8`: 0/39 exact, mean score 0.726, family `decision_support`.
- P5 Q7 `pass5.query7`: 0/39 exact, mean score 0.711, family `repeatability_probe`.
- P5 Q4 `pass5.query4`: 0/39 exact, mean score 0.696, family `statistical_summary`.

**Hardest exact-conversion and partial-score queries:**

- P4 Q7 `pass4.query7`: 0/39 exact, mean score 0.000, family `orphan_key_audit`.
- P5 Q9 `pass5.query9`: 0/39 exact, mean score 0.288, family `ranking_and_priority`.
- P4 Q3 `pass4.query3`: 0/39 exact, mean score 0.308, family `decision_support`.
- P5 Q5 `pass5.query5`: 0/39 exact, mean score 0.375, family `decision_support`.
- P4 Q4 `pass4.query4`: 0/39 exact, mean score 0.386, family `decision_support`.

## Query Failure Points

| Query | Family | Exact | Mean Score | Top Failure Points |
|---|---|---:|---:|---|
| P4 Q1 | audit_reconciliation | 0/39 | 0.849 | 37/39: Miscounted unused samples, unused variants, or genes with no variants.; 31/39: Miscounted complete_chain_rows in the reconciliation summary.; 30/39: Miscounted one or more missing sample/variant/gene fact-row categories. |
| P4 Q2 | aggregation_numeric | 0/39 | 0.400 | 39/39: Miscomputed call_count or total_alt_reads.; 39/39: Miscomputed mean_qual.; 36/39: Mapped or averaged expr_ndhb incorrectly. |
| P4 Q3 | decision_support | 0/39 | 0.308 | 39/39: Returned the wrong batch-gene_role group set.; 39/39: Leaked reference, incomplete-chain, or non-gold batch/role groups.; 36/39: Miscomputed non_reference_calls or avg_qual. |
| P4 Q4 | decision_support | 0/39 | 0.386 | 39/39: Returned the wrong shared gene set.; 39/39: Included genes that are not observed in both control and non-control complete-chain rows.; 31/39: Miscomputed total_alt_reads. |
| P4 Q5 | expression_mapping | 0/39 | 0.641 | 39/39: Miscomputed variant_count or call_count.; 39/39: Miscomputed distinct matched sample or tissue counts.; 39/39: Mapped or averaged matched expression incorrectly. |
| P4 Q6 | decision_support | 0/39 | 0.649 | 39/39: Miscomputed mean_log2_marker_expr.; 36/39: Miscomputed burden_genes.; 21/39: Dropped one or more sample_dim rows, usually S5. |
| P4 Q7 | orphan_key_audit | 0/39 | 0.000 | 39/39: Returned the wrong orphan-key row set.; 39/39: Used imprecise source_table labels such as fact_calls instead of fact_calls.sample_id or fact_calls.variant_id.; 39/39: Returned incorrect orphan_type labels. |
| P4 Q8 | presentation_table | 0/39 | 0.471 | 39/39: Returned the wrong non-reference complete-chain call set.; 39/39: Leaked reference, incomplete-chain, or orphan fact rows.; 36/39: Mapped matched_expr_count or log2_matched_expr incorrectly. |
| P4 Q9 | decision_support | 0/39 | 0.471 | 39/39: Miscomputed mean_vaf.; 39/39: Miscomputed mean_matched_expr.; 39/39: Miscomputed call_count or non_reference_rate. |
| P4 Q10 | repairability_review | 3/39 | 0.989 | 31/39: Misclassified call_id 6 / V5; it should be MISSING_GENE and repairable.; 19/39: Set repairable_by_human incorrectly for complete-chain or missing rows.; 5/39: Misclassified call_id 8 / S999; it should be MISSING_SAMPLE and repairable. |
| P5 Q1 | expression_transform | 0/39 | 0.677 | 39/39: Miscomputed one or more log2(expr + 1) marker features.; 39/39: Miscomputed ndh_module_ratio.; 11/39: Returned the wrong sample set for sample_dim-only feature engineering. |
| P5 Q2 | expression_transform | 0/39 | 0.540 | 39/39: Returned the wrong complete-chain matched call set.; 39/39: Mapped matched_expr_count or log2_matched_expr incorrectly.; 39/39: Miscomputed expr_weighted_vaf. |
| P5 Q3 | statistical_summary | 0/39 | 0.408 | 39/39: Returned the wrong condition-gene group set.; 39/39: Leaked incomplete-chain, orphan, or non-gold groups into condition-gene statistics.; 37/39: Miscomputed mean or median matched expression. |
| P5 Q4 | statistical_summary | 0/39 | 0.696 | 39/39: Miscomputed stress/control mean log2 expression.; 39/39: Miscomputed stress-minus-control delta.; 1/39: Returned the wrong marker-gene set. |
| P5 Q5 | decision_support | 0/39 | 0.375 | 36/39: Miscomputed mean_vaf.; 36/39: Miscomputed mean_log2_matched_expr.; 36/39: Miscomputed burden_score. |
| P5 Q6 | statistical_summary | 0/39 | 0.568 | 39/39: Miscomputed marker z-scores, usually from ddof or denominator errors.; 39/39: Miscomputed photosynthesis_expr_z_mean.; 25/39: Returned the wrong sample set for z-score ranking. |
| P5 Q7 | repeatability_probe | 0/39 | 0.711 | 38/39: Miscomputed mean_matched_expr.; 38/39: Miscomputed cv_matched_expr.; 38/39: Miscomputed mean_vaf. |
| P5 Q8 | decision_support | 0/39 | 0.726 | 39/39: Miscomputed non-reference or high/moderate call counts.; 39/39: Miscomputed total_marker_expr or log2_total_marker_expr.; 39/39: Miscomputed photosynthesis_variant_pressure. |
| P5 Q9 | ranking_and_priority | 0/39 | 0.288 | 39/39: Returned the wrong condition-gene signal group set.; 39/39: Leaked reference, incomplete-chain, or orphan groups into signal ranking.; 33/39: Miscomputed mean_log2_matched_expr. |
| P5 Q10 | statistical_summary | 0/39 | 0.491 | 39/39: Miscomputed one or more marker composition shares.; 39/39: Miscomputed marker_imbalance.; 22/39: Returned the wrong sample set for marker composition shares. |

## Interpretation

- Pass 4 exposed failures in reconciliation, orphan-key reporting, final presentation tables, and repairability classification. Only the repairability audit yielded exact answers, and only from Gemma 4 31B.
- Pass 5 shifted from structural table construction to expression-derived statistics. Models often recovered the row identities better than in pass 4, but exact numeric derivations were consistently wrong.
- The main capability gap across passes 4-5 is precise execution of multi-step pandas semantics: complete-chain filtering, expression mapping, log transforms, VAF weighting, population statistics, and derived ranking.
- Model grouping should be interpreted as partial-credit grouping, not exact-answer capability. Except for Gemma 4 31B on P4 Q10, exact conversion disappeared.

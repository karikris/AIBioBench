# AIBioBench Pass 5 Analysis

Run analyzed: `AIBioBench_photosynthesis_snowflake_v2__20260421_232409`

Pass 5 contains ten extreme-hard Python/pandas tasks, each repeated three times across thirteen models. The pass stresses expression transforms, complete-chain matched-expression mapping, population statistics, z-scores, coefficients of variation, signal ranking, and sample-level burden scores.

## Headline Findings

- No model produced an exact answer on pass 5: exact matches were 0/390.
- Gemma 4 31B led on partial credit with mean score 0.716, followed by Gemma 4 26B at 0.628 and Qwen3 Coder 30B at 0.621.
- The strongest query-level scores came from sample-preserving transforms and condition summaries; the weakest were condition-gene signal ranking, pathway burden, and marker composition shares.
- Recurring failure points were wrong numeric derivations after mostly plausible joins: log2 transforms, VAF weighting, population standard deviation, coefficient of variation, and ranking by derived metrics.

## Model Groups

| Group | Models | Why they belong there |
|---|---|---|
| Top partial-credit operators | Gemma 4 31B, Gemma 4 26B, Qwen3 Coder 30B | No exact pass-5 conversions, but best row-set recovery and strongest partial credit on expression/statistical transforms. |
| Upper-middle partial-credit operators | Qwen 2.5 72B, Qwen3.6, Llama 3 70B | Reasonable partial credit, but failures cluster around numeric formulas, population statistics, and ranking order. |
| Row-set fragile partial-credit | Mixtral 8x22B, DeepSeek Coder 33B, Command R+, DBRX, CodeLlama 70B | Some useful table shape recovery, but row-set leakage and expression-derived values remain unstable. |
| Brittle / low-coverage | Phi-4 Mini, Qwen 2.5 Coder 32B | Low partial credit with frequent row-set mismatch and weak numeric derivations. |

## Model Summary

| Model | Exact Attempts | Queries With Any Exact | Mean Score | Mean Cell Accuracy | Mean Row-Set Correctness | Dominant Failure Mode |
|---|---:|---:|---:|---:|---:|---|
| Gemma 4 31B | 0/30 | 0/10 | 0.716 | 0.373 | 0.922 | same_count_wrong_values |
| Gemma 4 26B | 0/30 | 0/10 | 0.628 | 0.349 | 0.843 | same_count_wrong_values |
| Qwen3 Coder 30B | 0/30 | 0/10 | 0.621 | 0.280 | 0.852 | same_count_wrong_values |
| Qwen 2.5 72B | 0/30 | 0/10 | 0.589 | 0.279 | 0.813 | same_count_wrong_values |
| Qwen3.6 | 0/30 | 0/10 | 0.573 | 0.284 | 0.769 | same_count_wrong_values |
| Llama 3 70B | 0/30 | 0/10 | 0.551 | 0.255 | 0.772 | row_count_mismatch |
| Mixtral 8x22B | 0/30 | 0/10 | 0.524 | 0.225 | 0.716 | row_count_mismatch |
| DeepSeek Coder 33B | 0/30 | 0/10 | 0.521 | 0.204 | 0.739 | row_count_mismatch |
| Command R+ | 0/30 | 0/10 | 0.517 | 0.280 | 0.725 | same_count_wrong_values |
| DBRX | 0/30 | 0/10 | 0.494 | 0.192 | 0.716 | row_count_mismatch |
| CodeLlama 70B | 0/30 | 0/10 | 0.493 | 0.272 | 0.681 | row_count_mismatch |
| Phi-4 Mini | 0/30 | 0/10 | 0.464 | 0.198 | 0.696 | row_count_mismatch |
| Qwen 2.5 Coder 32B | 0/30 | 0/10 | 0.432 | 0.243 | 0.595 | row_count_mismatch |

## Query-by-Query Failure Points

| Query | Focus | Exact Attempts | Mean Score | Top failure points |
|---|---|---:|---:|---|
| Q1 | Sample expression features | 0/39 | 0.677 | 39/39: Miscomputed one or more log2(expr + 1) marker features.; 39/39: Miscomputed ndh_module_ratio.; 11/39: Returned the wrong sample set for sample_dim-only feature engineering. |
| Q2 | Expression-weighted VAF | 0/39 | 0.540 | 39/39: Returned the wrong complete-chain matched call set.; 39/39: Mapped matched_expr_count or log2_matched_expr incorrectly.; 39/39: Miscomputed expr_weighted_vaf. |
| Q3 | Condition-gene statistics | 0/39 | 0.408 | 39/39: Returned the wrong condition-gene group set.; 39/39: Leaked incomplete-chain, orphan, or non-gold groups into condition-gene statistics.; 37/39: Miscomputed mean or median matched expression. |
| Q4 | Stress-control log2 delta | 0/39 | 0.696 | 39/39: Miscomputed stress/control mean log2 expression.; 39/39: Miscomputed stress-minus-control delta.; 1/39: Returned the wrong marker-gene set. |
| Q5 | Pathway-tissue burden | 0/39 | 0.375 | 36/39: Miscomputed mean_vaf.; 36/39: Miscomputed mean_log2_matched_expr.; 36/39: Miscomputed burden_score. |
| Q6 | Sample expression z-scores | 0/39 | 0.568 | 39/39: Miscomputed marker z-scores, usually from ddof or denominator errors.; 39/39: Miscomputed photosynthesis_expr_z_mean.; 25/39: Returned the wrong sample set for z-score ranking. |
| Q7 | Condition CV summary | 0/39 | 0.711 | 38/39: Miscomputed mean_matched_expr.; 38/39: Miscomputed cv_matched_expr.; 38/39: Miscomputed mean_vaf. |
| Q8 | Sample variant pressure | 0/39 | 0.726 | 39/39: Miscomputed non-reference or high/moderate call counts.; 39/39: Miscomputed total_marker_expr or log2_total_marker_expr.; 39/39: Miscomputed photosynthesis_variant_pressure. |
| Q9 | Condition-gene signal ranking | 0/39 | 0.288 | 39/39: Returned the wrong condition-gene signal group set.; 39/39: Leaked reference, incomplete-chain, or orphan groups into signal ranking.; 33/39: Miscomputed mean_log2_matched_expr. |
| Q10 | Marker composition shares | 0/39 | 0.491 | 39/39: Miscomputed one or more marker composition shares.; 39/39: Miscomputed marker_imbalance.; 22/39: Returned the wrong sample set for marker composition shares. |

## Short Notes

- **Q1 Sample expression features**: 0/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `expression_transform`.
Issue: 39/39 attempts. Miscomputed one or more log2(expr + 1) marker features. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Miscomputed ndh_module_ratio. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 11/39 attempts. Returned the wrong sample set for sample_dim-only feature engineering. Example models: CodeLlama 70B, DeepSeek Coder 33B, Mixtral 8x22B, Qwen 2.5 Coder 32B.
- **Q2 Expression-weighted VAF**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `expression_transform`.
Issue: 39/39 attempts. Returned the wrong complete-chain matched call set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Mapped matched_expr_count or log2_matched_expr incorrectly. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Miscomputed expr_weighted_vaf. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q3 Condition-gene statistics**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `statistical_summary`.
Issue: 39/39 attempts. Returned the wrong condition-gene group set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Leaked incomplete-chain, orphan, or non-gold groups into condition-gene statistics. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 37/39 attempts. Miscomputed mean or median matched expression. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q4 Stress-control log2 delta**: 0/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `statistical_summary`.
Issue: 39/39 attempts. Miscomputed stress/control mean log2 expression. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Miscomputed stress-minus-control delta. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 1/39 attempts. Returned the wrong marker-gene set. Example models: Llama 3 70B.
- **Q5 Pathway-tissue burden**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `decision_support`.
Issue: 36/39 attempts. Miscomputed mean_vaf. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 36/39 attempts. Miscomputed mean_log2_matched_expr. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 36/39 attempts. Miscomputed burden_score. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q6 Sample expression z-scores**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `statistical_summary`.
Issue: 39/39 attempts. Miscomputed marker z-scores, usually from ddof or denominator errors. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Miscomputed photosynthesis_expr_z_mean. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 25/39 attempts. Returned the wrong sample set for z-score ranking. Example models: CodeLlama 70B, DBRX, DeepSeek Coder 33B, Gemma 4 26B.
- **Q7 Condition CV summary**: 0/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `repeatability_probe`.
Issue: 38/39 attempts. Miscomputed mean_matched_expr. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 38/39 attempts. Miscomputed cv_matched_expr. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 38/39 attempts. Miscomputed mean_vaf. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q8 Sample variant pressure**: 0/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `decision_support`.
Issue: 39/39 attempts. Miscomputed non-reference or high/moderate call counts. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Miscomputed total_marker_expr or log2_total_marker_expr. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Miscomputed photosynthesis_variant_pressure. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q9 Condition-gene signal ranking**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `ranking_and_priority`.
Issue: 39/39 attempts. Returned the wrong condition-gene signal group set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Leaked reference, incomplete-chain, or orphan groups into signal ranking. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 33/39 attempts. Miscomputed mean_log2_matched_expr. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q10 Marker composition shares**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `statistical_summary`.
Issue: 39/39 attempts. Miscomputed one or more marker composition shares. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Miscomputed marker_imbalance. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 22/39 attempts. Returned the wrong sample set for marker composition shares. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.

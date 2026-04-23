# AIBioBench Full Study Overview

Run analyzed: `AIBioBench_photosynthesis_snowflake_v2__20260421_232409`
Benchmark version: `2.0.0`
Provider: `ollama`

Scope: all five passes, 50 queries, 13 models, and 3 repeated attempts per model-query pair.
Models evaluated: 13.

## Executive Summary

- Overall exact conversion was 102/1950 attempts (5.2%).
- 37/50 queries had zero exact answers. Exact-zero queries increased by pass: P1=5/10, P2=6/10, P3=7/10, P4=9/10, P5=10/10.
- Exact attempts fell from 51/390 in pass 1 to 0/390 in pass 5.
- Gemma 4 31B was the clear study-wide leader with 37/150 exact attempts and mean score 0.818.
- The benchmark mostly exposed semantic execution failures, not formatting failures: row-count mismatch and same-count-wrong-values dominated all passes.
- SQL tasks showed measurable exact conversion on join-preservation and audit queries; Python/pandas tasks largely eliminated exact conversion, especially once expression transforms and population statistics were required.

## Pass-Level Results

| Pass | Exact Attempts | Queries With Any Exact | Exact-Zero Queries | Mean Score | Row-Set | Numeric | Cell Accuracy | Dominant Failure |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Pass 1 | 51/390 | 5/10 | 5/10 | 0.761 | 0.864 | 0.639 | 0.602 | same_count_wrong_values |
| Pass 2 | 32/390 | 4/10 | 6/10 | 0.638 | 0.742 | 0.556 | 0.502 | row_count_mismatch |
| Pass 3 | 16/390 | 3/10 | 7/10 | 0.592 | 0.703 | 0.535 | 0.484 | same_count_wrong_values |
| Pass 4 | 3/390 | 1/10 | 9/10 | 0.516 | 0.632 | 0.490 | 0.341 | row_count_mismatch |
| Pass 5 | 0/390 | 0/10 | 10/10 | 0.548 | 0.757 | 0.191 | 0.264 | row_count_mismatch |

## Model Groups

| Group | Models | Interpretation |
|---|---|---|
| Study-wide leader | Gemma 4 31B | Only model with broad exact conversion across SQL passes and any exact conversion in the Python phase. |
| Strong SQL exact converters | Gemma 4 26B, Qwen3.6, Qwen 2.5 72B, Qwen 2.5 Coder 32B | Converted easy and medium SQL tasks, but exactness largely disappeared by hard SQL and Python/pandas passes. |
| Partial-credit / niche survivors | Mixtral 8x22B, Llama 3 70B, Command R+ | Limited exact conversion, but retained useful partial credit across multiple difficulty levels. |
| Low-exactness partial operators | DBRX, Qwen3 Coder 30B | Some row-set recovery and partial scores, but low or absent exact conversion. |
| Brittle / low-coverage | CodeLlama 70B, DeepSeek Coder 33B, Phi-4 Mini | Weak exact conversion and low partial-credit reliability across the full benchmark. |

## Model Ranking

| Model | Exact | P1 | P2 | P3 | P4 | P5 | Mean Score | Row-Set | Numeric | Dominant Failure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Gemma 4 31B | 37/150 | 13 | 12 | 9 | 3 | 0 | 0.818 | 0.921 | 0.701 | same_count_wrong_values |
| Gemma 4 26B | 18/150 | 9 | 6 | 3 | 0 | 0 | 0.674 | 0.787 | 0.581 | same_count_wrong_values |
| Qwen3.6 | 12/150 | 6 | 6 | 0 | 0 | 0 | 0.670 | 0.782 | 0.558 | same_count_wrong_values |
| Qwen 2.5 72B | 11/150 | 7 | 3 | 1 | 0 | 0 | 0.679 | 0.797 | 0.564 | row_count_mismatch |
| Qwen 2.5 Coder 32B | 9/150 | 6 | 3 | 0 | 0 | 0 | 0.597 | 0.719 | 0.497 | row_count_mismatch |
| Mixtral 8x22B | 7/150 | 2 | 2 | 3 | 0 | 0 | 0.631 | 0.753 | 0.512 | row_count_mismatch |
| Llama 3 70B | 3/150 | 3 | 0 | 0 | 0 | 0 | 0.631 | 0.760 | 0.519 | row_count_mismatch |
| CodeLlama 70B | 3/150 | 3 | 0 | 0 | 0 | 0 | 0.511 | 0.649 | 0.329 | row_count_mismatch |
| Command R+ | 1/150 | 1 | 0 | 0 | 0 | 0 | 0.591 | 0.719 | 0.456 | same_count_wrong_values |
| DBRX | 1/150 | 1 | 0 | 0 | 0 | 0 | 0.538 | 0.696 | 0.385 | row_count_mismatch |
| Qwen3 Coder 30B | 0/150 | 0 | 0 | 0 | 0 | 0 | 0.575 | 0.701 | 0.464 | row_count_mismatch |
| DeepSeek Coder 33B | 0/150 | 0 | 0 | 0 | 0 | 0 | 0.527 | 0.675 | 0.365 | row_count_mismatch |
| Phi-4 Mini | 0/150 | 0 | 0 | 0 | 0 | 0 | 0.501 | 0.651 | 0.341 | row_count_mismatch |

## Failure Family Results

| Family | Queries | Exact | Queries With Any Exact | Exact-Zero Queries | Mean Score | Row-Set | Numeric | Dominant Failure |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| outer_join_coverage | 6 | 54/234 | 5/6 | 1/6 | 0.825 | 0.893 | 0.748 | same_count_wrong_values |
| join_key_integrity | 2 | 29/78 | 2/2 | 0/2 | 0.896 | 0.896 | 0.896 | same_count_wrong_values |
| snowflake_traversal | 3 | 7/117 | 2/3 | 1/3 | 0.664 | 0.670 | 0.749 | row_count_mismatch |
| repairability_review | 1 | 3/39 | 1/1 | 0/1 | 0.989 | 0.989 | 0.989 | same_count_wrong_values |
| inner_join_accuracy | 1 | 3/39 | 1/1 | 0/1 | 0.812 | 0.806 | 0.869 | row_count_mismatch |
| decision_support | 11 | 3/429 | 1/11 | 10/11 | 0.535 | 0.684 | 0.323 | row_count_mismatch |
| orphan_key_audit | 3 | 3/117 | 1/3 | 2/3 | 0.275 | 0.331 | 0.827 | same_count_wrong_values |
| audit_reconciliation | 1 | 0/39 | 0/1 | 1/1 | 0.849 | 1.000 | 0.497 | same_count_wrong_values |
| failure_family_audit | 1 | 0/39 | 0/1 | 1/1 | 0.792 | 0.989 | 0.607 | same_count_wrong_values |
| sorting_presentation | 1 | 0/39 | 0/1 | 1/1 | 0.717 | 0.832 | 0.867 | row_count_mismatch |
| repeatability_probe | 1 | 0/39 | 0/1 | 1/1 | 0.711 | 0.910 | 0.246 | same_count_wrong_values |
| expression_mapping | 1 | 0/39 | 0/1 | 1/1 | 0.641 | 0.818 | 0.480 | row_count_mismatch |
| expression_transform | 2 | 0/78 | 0/2 | 2/2 | 0.608 | 0.777 | 0.268 | row_count_mismatch |
| aggregation_numeric | 9 | 0/351 | 0/9 | 9/9 | 0.547 | 0.731 | 0.325 | row_count_mismatch |
| statistical_summary | 4 | 0/156 | 0/4 | 4/4 | 0.541 | 0.809 | 0.091 | same_count_wrong_values |
| presentation_table | 1 | 0/39 | 0/1 | 1/1 | 0.471 | 0.545 | 0.609 | row_count_mismatch |
| ranking_and_priority | 2 | 0/78 | 0/2 | 2/2 | 0.406 | 0.511 | 0.288 | row_count_mismatch |

## Query-Level Takeaways

**Most solvable queries by exact conversion:**

- P1 Q3 `pass1.query3`: 21/39 exact, mean score 0.912, family `outer_join_coverage`.
- P1 Q10 `pass1.query10`: 19/39 exact, mean score 0.792, family `join_key_integrity`.
- P2 Q2 `pass2.query2`: 15/39 exact, mean score 0.846, family `outer_join_coverage`.
- P3 Q1 `pass3.query1`: 10/39 exact, mean score 1.000, family `join_key_integrity`.
- P2 Q3 `pass2.query3`: 9/39 exact, mean score 0.726, family `outer_join_coverage`.
- P1 Q4 `pass1.query4`: 6/39 exact, mean score 0.879, family `outer_join_coverage`.
- P2 Q6 `pass2.query6`: 5/39 exact, mean score 0.580, family `snowflake_traversal`.
- P4 Q10 `pass4.query10`: 3/39 exact, mean score 0.989, family `repairability_review`.

**Hardest queries by exact conversion and partial score:**

- P4 Q7 `pass4.query7`: 0/39 exact, mean score 0.000, family `orphan_key_audit`.
- P5 Q9 `pass5.query9`: 0/39 exact, mean score 0.288, family `ranking_and_priority`.
- P4 Q3 `pass4.query3`: 0/39 exact, mean score 0.308, family `decision_support`.
- P3 Q8 `pass3.query8`: 0/39 exact, mean score 0.308, family `decision_support`.
- P2 Q9 `pass2.query9`: 0/39 exact, mean score 0.375, family `decision_support`.
- P5 Q5 `pass5.query5`: 0/39 exact, mean score 0.375, family `decision_support`.
- P4 Q4 `pass4.query4`: 0/39 exact, mean score 0.386, family `decision_support`.
- P4 Q2 `pass4.query2`: 0/39 exact, mean score 0.400, family `aggregation_numeric`.

## Query Failure Points

| Query | Family | Exact | Mean Score | Top Failure Points |
|---|---|---:|---:|---|
| P1 Q1 | inner_join_accuracy | 3/39 | 0.812 | 25/39: Included orphan sample row S999/call_id 8 that should disappear under the inner join.; 14/39: Dropped call_id 9 even though sample S2 exists and should survive the sample join.; 8/39: Leaked tissue or condition values across rows instead of preserving sample attributes. |
| P1 Q2 | sorting_presentation | 0/39 | 0.717 | 27/39: Included call_id 9 / V999 despite the required inner join to `variant_dim`.; 20/39: Returned the matched row set but not in `qual DESC, call_id ASC` order.; 19/39: Dropped valid matched calls from the joined result. |
| P1 Q3 | outer_join_coverage | 21/39 | 0.912 | 18/39: Did not preserve the unmatched `S999` row cleanly in the left join output.; 9/39: Mixed condition values into tissue/batch fields or used the wrong expression values.; 3/39: Matched the table semantically but serialized numbers/nulls with the wrong types. |
| P1 Q4 | outer_join_coverage | 6/39 | 0.879 | 29/39: Computed the `S2` average incorrectly, often from the wrong row set or over-rounded output.; 10/39: Undercounted `S2` by missing one fact row, usually call_id 9. |
| P1 Q5 | snowflake_traversal | 2/39 | 0.699 | 36/39: Kept unmatched call_id 9 / V999 even though the chain join should remove it.; 31/39: Kept call_id 6 / V5 after the second inner join instead of dropping the incomplete chain.; 14/39: Dropped valid matched rows while traversing the fact -> variant -> gene chain. |
| P1 Q6 | aggregation_numeric | 0/39 | 0.757 | 39/39: Used the wrong row set for average quality per impact bucket.; 32/39: Under-counted high-impact calls by not aggregating both V2 and V3 duplicates.; 18/39: Under-counted the two moderate V1 calls. |
| P1 Q7 | aggregation_numeric | 0/39 | 0.502 | 39/39: Computed tissue averages from the wrong grain instead of fact-call-weighted quality values.; 36/39: Minimum or maximum quality per tissue came from the wrong row set.; 20/39: Included `root` / `S5` even though the task required an inner join to fact rows only. |
| P1 Q8 | aggregation_numeric | 0/39 | 0.742 | 39/39: Used sample counts instead of fact-call counts for one or more conditions.; 38/39: Averaged expression at the wrong grain instead of call-weighting by joined fact rows.; 23/39: Leaked `S5` / `high_light` into the aggregate, inflating the high-light bucket. |
| P1 Q9 | decision_support | 0/39 | 0.795 | 38/39: Missed the high-impact filter/count after joining to `variant_dim`.; 35/39: Used the wrong total-call counts, usually from sample-level counting or leaked rows.; 26/39: Inflated the high-light bucket by leaking unmatched or extra rows. |
| P1 Q10 | join_key_integrity | 19/39 | 0.792 | 9/39: Marked matched variants as `MISSING_VARIANT` instead of `MATCHED`.; 6/39: Matched the audit semantically but serialized identifiers with the wrong types.; 5/39: Nullified `variant_id` for call_id 9 instead of preserving `V999` from the fact table. |
| P2 Q1 | snowflake_traversal | 0/39 | 0.712 | 34/39: Kept call_id 6 / V5 even though the complete four-table inner join should remove it.; 30/39: Kept call_id 8 / S999 even though the sample dimension is missing.; 28/39: Kept call_id 9 / V999 even though the variant/gene chain is incomplete. |
| P2 Q2 | outer_join_coverage | 15/39 | 0.846 | 21/39: Mapped matched variants to the wrong gene symbol or dropped a valid gene symbol.; 14/39: Filled sample attributes for S999 instead of leaving dimension fields null.; 6/39: Failed to leave gene_symbol null for incomplete V5/V999 chain rows. |
| P2 Q3 | outer_join_coverage | 9/39 | 0.726 | 16/39: Dropped the fact-only V999 row from the full outer join.; 14/39: Failed to preserve the coalesced variant_id key for fact-only or matched rows.; 12/39: Dropped the variant-only V6 row from the full outer join. |
| P2 Q4 | aggregation_numeric | 0/39 | 0.553 | 39/39: Computed one or more condition-impact average qualities from the wrong row set.; 34/39: Returned the wrong condition-impact group set.; 30/39: Miscomputed the control/high bucket, especially the two-call count and average. |
| P2 Q5 | aggregation_numeric | 0/39 | 0.489 | 39/39: Computed average VAF from the wrong numerator/denominator or row set.; 36/39: Computed max_qual from the wrong rows.; 24/39: Included incomplete-chain or non-gold genes such as NDHT/PGR1B. |
| P2 Q6 | snowflake_traversal | 5/39 | 0.580 | 32/39: Computed distinct gene counts from the wrong join grain.; 28/39: Computed avg_expr_ndhb over samples instead of complete-chain joined calls.; 23/39: Included root/S5 even though complete inner joins should remove it. |
| P2 Q7 | outer_join_coverage | 0/39 | 0.714 | 36/39: Missed the zero-alt high-impact call for S4.; 36/39: Averaged alt_reads over the wrong subset of rows.; 25/39: Counted non-high or incomplete rows as high-impact calls, often inflating S3. |
| P2 Q8 | aggregation_numeric | 0/39 | 0.560 | 33/39: Computed avg_qual from the wrong row set.; 26/39: Computed total_alt_reads from the wrong row set.; 18/39: Included incomplete-chain genes that should not appear. |
| P2 Q9 | decision_support | 0/39 | 0.375 | 39/39: Miscomputed call_count or distinct_samples.; 39/39: Computed mean VAF from the wrong row set.; 33/39: Returned the wrong condition-pathway group set. |
| P2 Q10 | decision_support | 3/39 | 0.822 | 36/39: Misclassified complete vs incomplete chain calls.; 17/39: Miscomputed total fact calls per sample.; 11/39: Dropped zero-call sample S5 from the sample-preserving coverage screen. |
| P3 Q1 | join_key_integrity | 10/39 | 1.000 | 22/39: Misclassified call_id 6 / V5; it should be MISSING_GENE.; 18/39: Misclassified call_id 9 / V999; it should be MISSING_VARIANT.; 15/39: Misclassified one or more complete-chain calls. |
| P3 Q2 | aggregation_numeric | 0/39 | 0.476 | 39/39: Returned the wrong tissue-gene group set for complete-chain matched rows.; 38/39: Miscomputed call_count or sum_alt_reads.; 38/39: Computed avg_vaf from the wrong numerator/denominator or row set. |
| P3 Q3 | orphan_key_audit | 0/39 | 0.749 | 39/39: Miscomputed total_alt_reads for one or more genes.; 36/39: Miscomputed observed_call_count for one or more genes.; 7/39: Dropped zero-call genes NDHT or PGR1B from the gene-preserving audit. |
| P3 Q4 | aggregation_numeric | 0/39 | 0.449 | 36/39: Returned the wrong set of high-impact condition rows.; 34/39: Miscomputed the control high-impact bucket.; 33/39: Miscomputed the high_light high-impact bucket. |
| P3 Q5 | outer_join_coverage | 3/39 | 0.874 | 36/39: Miscomputed S2 heterozygous calls or non-reference mean quality.; 36/39: Counted reference calls or put genotypes into the wrong class.; 14/39: Included S999 even though sample_dim is the preserving table. |
| P3 Q6 | ranking_and_priority | 0/39 | 0.524 | 36/39: Returned the wrong tissue-gene group set before ranking.; 32/39: Leaked root, incomplete-chain, or non-gold genes into the ranking.; 31/39: Miscomputed total_alt_reads or avg_vaf. |
| P3 Q7 | orphan_key_audit | 3/39 | 0.077 | 36/39: Used dimension-table labels such as gene_dim/sample_dim instead of gene/sample/variant.; 36/39: Dropped or mislabeled one of G4, G5, S5, or V6 in the anti-join audit.; 31/39: Assigned the wrong reason to G4; it should be no_fact_calls_through_variants. |
| P3 Q8 | decision_support | 0/39 | 0.308 | 39/39: Returned the wrong condition-gene_role groups.; 39/39: Leaked reference calls, incomplete chains, or non-gold roles into the non-reference summary.; 28/39: Computed mean_vaf from the wrong row set. |
| P3 Q9 | failure_family_audit | 0/39 | 0.792 | 39/39: Miscomputed complete_chain_calls by condition group.; 36/39: Miscomputed missing_sample, missing_variant, or missing_gene counts. |
| P3 Q10 | decision_support | 0/39 | 0.670 | 39/39: Computed avg_vaf from the wrong non-reference row set.; 39/39: Mapped matched expression counts incorrectly.; 39/39: Computed decision_score incorrectly from avg_vaf and matched expression. |
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

## Study Conclusions

### 1. Exact correctness remains the bottleneck

The best model achieved only 37/150 exact attempts, and the field as a whole achieved 102/1950. Many attempts earned partial credit, but exact reproducibility was rare. This matters because benchmark tasks were deterministic table-returning tasks; a near miss can still be operationally wrong when rows, sort order, or aggregate values must be exact.

### 2. Difficulty exposes different failure regimes

Passes 1-3 primarily test SQL snowflake traversal, joins, preserving-table behavior, aggregation grain, ranking, and audit logic. Exact conversion declines steadily across these passes. Passes 4-5 shift to Python/pandas reconciliation, presentation, expression transforms, z-scores, coefficients of variation, and decision-signal calculations. In those passes, exact conversion effectively disappears.

### 3. Row recovery and numeric correctness diverge

Pass 5 shows the clearest split: row-set correctness rises relative to pass 4, but numeric correctness falls sharply. Models can often identify the right entities while failing the actual derived mathematics. This is important for biological decision support, where rankings and burden scores depend on precise formulas rather than just plausible table shape.

### 4. Failure modes are semantic, not superficial

The dominant failures are `row_count_mismatch` and `same_count_wrong_values`. Invalid JSON, column errors, and type-only issues are secondary. The models generally understand the requested output format but make semantic mistakes in joins, filters, aggregation grain, null handling, complete-chain logic, and derived numeric formulas.

### 5. Model ranking is stable at the top but not uniformly reliable

Gemma 4 31B is the only clear study-wide leader and the only model with exact conversion beyond pass 3. Gemma 4 26B, Qwen3.6, Qwen 2.5 72B, and Qwen 2.5 Coder 32B form a second tier for SQL exactness, but they do not convert the Python-heavy passes. Several other models retain partial credit but should not be treated as exact analytical engines.

### 6. Deployment implication

For these bioinformatics-style table tasks, no model should be used without deterministic validation. The benchmark supports a workflow where models propose code or queries, but row counts, join status, aggregate values, and derived statistics must be checked by executable tests before results are trusted.

### 7. Benchmark implication

The study shows the value of separating exact match, row-set correctness, numeric correctness, sort correctness, and failure families. A single mean score hides the most important operational distinction: some models recover table shape but fail formulas, while others keep formulas plausible but leak or drop rows.

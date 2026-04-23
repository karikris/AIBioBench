# AIBioBench Pass 4 Analysis

Run analyzed: `AIBioBench_photosynthesis_snowflake_v2__20260421_232409`

Pass 4 contains ten extra-hard Python/pandas tasks, each repeated three times across thirteen models. The pressure shifts to reconciliation metrics, expression mapping, orphan-key union reports, presentation tables, and repairability review.

## Headline Findings

- **Gemma 4 31B** led pass 4 with 3/30 exact attempts and exact coverage on 1/10 questions.
- Exact matches nearly disappeared: only 3/390 attempts were exact, and Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9 had zero exact attempts.
- Q10 repairability was the only query with any exact conversion; all analytical, presentation, and orphan-key tasks were exact-zero.
- The largest recurring failures were expression mapping, exact orphan-key labels, complete-chain filtering, and Python table presentation order.

## Model Groups

| Group | Models | Why they belong there |
|---|---|---|
| Only exact converter | Gemma 4 31B | Only model group with any exact pass-4 conversion, limited to the repairability audit. |
| Higher partial-credit operators | Gemma 4 26B, Qwen3 Coder 30B, Qwen3.6 | No exact conversions, but stronger partial credit on reconciliation, burden, and expression-mapping tasks. |
| Middle partial-credit operators | CodeLlama 70B, Mixtral 8x22B, Qwen 2.5 Coder 32B, Llama 3 70B, DeepSeek Coder 33B, Command R+, Qwen 2.5 72B | Some row-set recovery, but presentation, orphan-key, and expression calculations remained unstable. |
| Brittle / low-coverage | DBRX, Phi-4 Mini | Low exactness and low partial credit across most extra-hard Python tasks. |

## Model Summary

| Model | Exact Attempts | Queries With Any Exact | Stable Exact Queries | Mean Score | Mean Cell Accuracy | Dominant Failure Mode |
|---|---:|---:|---:|---:|---:|---|
| Gemma 4 31B | 3/30 | 1/10 | 1/10 | 0.660 | 0.513 | row_count_mismatch |
| Gemma 4 26B | 0/30 | 0/10 | 0/10 | 0.559 | 0.366 | same_count_wrong_values |
| Qwen3 Coder 30B | 0/30 | 0/10 | 0/10 | 0.548 | 0.323 | row_count_mismatch |
| Qwen3.6 | 0/30 | 0/10 | 0/10 | 0.541 | 0.359 | row_count_mismatch |
| CodeLlama 70B | 0/30 | 0/10 | 0/10 | 0.514 | 0.351 | row_count_mismatch |
| Mixtral 8x22B | 0/30 | 0/10 | 0/10 | 0.510 | 0.284 | row_count_mismatch |
| Qwen 2.5 Coder 32B | 0/30 | 0/10 | 0/10 | 0.508 | 0.390 | row_count_mismatch |
| Llama 3 70B | 0/30 | 0/10 | 0/10 | 0.504 | 0.274 | row_count_mismatch |
| DeepSeek Coder 33B | 0/30 | 0/10 | 0/10 | 0.502 | 0.379 | row_count_mismatch |
| Command R+ | 0/30 | 0/10 | 0/10 | 0.501 | 0.335 | row_count_mismatch |
| Qwen 2.5 72B | 0/30 | 0/10 | 0/10 | 0.496 | 0.325 | row_count_mismatch |
| DBRX | 0/30 | 0/10 | 0/10 | 0.473 | 0.252 | same_count_wrong_values |
| Phi-4 Mini | 0/30 | 0/10 | 0/10 | 0.398 | 0.285 | same_count_wrong_values |

## Query-by-Query Failure Points

| Query | Focus | Exact Attempts | Mean Score | Top failure points |
|---|---|---:|---:|---|
| Q1 | Reconciliation metrics | 0/39 | 0.849 | 37/39: Miscounted unused samples, unused variants, or genes with no variants.; 31/39: Miscounted complete_chain_rows in the reconciliation summary.; 30/39: Miscounted one or more missing sample/variant/gene fact-row categories. |
| Q2 | Condition-pathway aggregate | 0/39 | 0.400 | 39/39: Miscomputed call_count or total_alt_reads.; 39/39: Miscomputed mean_qual.; 36/39: Mapped or averaged expr_ndhb incorrectly. |
| Q3 | Batch-role non-reference summary | 0/39 | 0.308 | 39/39: Returned the wrong batch-gene_role group set.; 39/39: Leaked reference, incomplete-chain, or non-gold batch/role groups.; 36/39: Miscomputed non_reference_calls or avg_qual. |
| Q4 | Control/non-control shared genes | 0/39 | 0.386 | 39/39: Returned the wrong shared gene set.; 39/39: Included genes that are not observed in both control and non-control complete-chain rows.; 31/39: Miscomputed total_alt_reads. |
| Q5 | Gene-preserving profile | 0/39 | 0.641 | 39/39: Miscomputed variant_count or call_count.; 39/39: Miscomputed distinct matched sample or tissue counts.; 39/39: Mapped or averaged matched expression incorrectly. |
| Q6 | Sample burden table | 0/39 | 0.649 | 39/39: Miscomputed mean_log2_marker_expr.; 36/39: Miscomputed burden_genes.; 21/39: Dropped one or more sample_dim rows, usually S5. |
| Q7 | Orphan-key report | 0/39 | 0.000 | 39/39: Returned the wrong orphan-key row set.; 39/39: Used imprecise source_table labels such as fact_calls instead of fact_calls.sample_id or fact_calls.variant_id.; 39/39: Returned incorrect orphan_type labels. |
| Q8 | Final presentation table | 0/39 | 0.471 | 39/39: Returned the wrong non-reference complete-chain call set.; 39/39: Leaked reference, incomplete-chain, or orphan fact rows.; 36/39: Mapped matched_expr_count or log2_matched_expr incorrectly. |
| Q9 | Pathway reliability summary | 0/39 | 0.471 | 39/39: Miscomputed mean_vaf.; 39/39: Miscomputed mean_matched_expr.; 39/39: Miscomputed call_count or non_reference_rate. |
| Q10 | Repairability audit | 3/39 | 0.989 | 31/39: Misclassified call_id 6 / V5; it should be MISSING_GENE and repairable.; 19/39: Set repairable_by_human incorrectly for complete-chain or missing rows.; 5/39: Misclassified call_id 8 / S999; it should be MISSING_SAMPLE and repairable. |

## Short Notes

- **Q1 Reconciliation metrics**: 0/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `audit_reconciliation`.
Issue: 37/39 attempts. Miscounted unused samples, unused variants, or genes with no variants. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 31/39 attempts. Miscounted complete_chain_rows in the reconciliation summary. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 30/39 attempts. Miscounted one or more missing sample/variant/gene fact-row categories. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q2 Condition-pathway aggregate**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `aggregation_numeric`.
Issue: 39/39 attempts. Miscomputed call_count or total_alt_reads. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Miscomputed mean_qual. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 36/39 attempts. Mapped or averaged expr_ndhb incorrectly. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q3 Batch-role non-reference summary**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `decision_support`.
Issue: 39/39 attempts. Returned the wrong batch-gene_role group set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Leaked reference, incomplete-chain, or non-gold batch/role groups. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 36/39 attempts. Miscomputed non_reference_calls or avg_qual. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q4 Control/non-control shared genes**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `decision_support`.
Issue: 39/39 attempts. Returned the wrong shared gene set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Included genes that are not observed in both control and non-control complete-chain rows. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 31/39 attempts. Miscomputed total_alt_reads. Example models: CodeLlama 70B, DBRX, DeepSeek Coder 33B, Gemma 4 26B.
- **Q5 Gene-preserving profile**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `expression_mapping`.
Issue: 39/39 attempts. Miscomputed variant_count or call_count. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Miscomputed distinct matched sample or tissue counts. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Mapped or averaged matched expression incorrectly. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q6 Sample burden table**: 0/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `decision_support`.
Issue: 39/39 attempts. Miscomputed mean_log2_marker_expr. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 36/39 attempts. Miscomputed burden_genes. Example models: Command R+, DBRX, DeepSeek Coder 33B, Gemma 4 26B.
Issue: 21/39 attempts. Dropped one or more sample_dim rows, usually S5. Example models: CodeLlama 70B, Command R+, DBRX, Llama 3 70B.
- **Q7 Orphan-key report**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `orphan_key_audit`.
Issue: 39/39 attempts. Returned the wrong orphan-key row set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Used imprecise source_table labels such as fact_calls instead of fact_calls.sample_id or fact_calls.variant_id. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Returned incorrect orphan_type labels. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q8 Final presentation table**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `presentation_table`.
Issue: 39/39 attempts. Returned the wrong non-reference complete-chain call set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Leaked reference, incomplete-chain, or orphan fact rows. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 36/39 attempts. Mapped matched_expr_count or log2_matched_expr incorrectly. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q9 Pathway reliability summary**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `decision_support`.
Issue: 39/39 attempts. Miscomputed mean_vaf. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Miscomputed mean_matched_expr. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Miscomputed call_count or non_reference_rate. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q10 Repairability audit**: 3/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `repairability_review`.
Issue: 31/39 attempts. Misclassified call_id 6 / V5; it should be MISSING_GENE and repairable. Example models: Command R+, DBRX, DeepSeek Coder 33B, Gemma 4 26B.
Issue: 19/39 attempts. Set repairable_by_human incorrectly for complete-chain or missing rows. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 5/39 attempts. Misclassified call_id 8 / S999; it should be MISSING_SAMPLE and repairable. Example models: DBRX, Gemma 4 26B, Phi-4 Mini.

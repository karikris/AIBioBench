# AIBioBench Pass 3 Analysis

Run analyzed: `AIBioBench_photosynthesis_snowflake_v2__20260421_232409`

Pass 3 contains ten hard SQL tasks, each repeated three times across thirteen models. The pressure shifts to join-status classification, orphan audits, dense ranking, complete-chain non-reference filters, and decision-score arithmetic.

## Headline Findings

- **Gemma 4 31B** led pass 3 with 9/30 exact attempts and exact coverage on 3/10 questions.
- Exact matches were very sparse: only 16/390 attempts were exact, and Q2, Q3, Q4, Q6, Q8, Q9, Q10 had zero exact attempts.
- Q1 had high mean score because most models could preserve the row set, but exactness depended on three edge-row status labels.
- The hardest exactness failures were Q2/Q4/Q6/Q8/Q10 numeric-grain tasks and Q7 anti-join label/reason normalization.

## Model Groups

| Group | Models | Why they belong there |
|---|---|---|
| Broad pass leader | Gemma 4 31B | Only model with stable exact conversions across join-status, genotype, and anti-join audit tasks. |
| Single-skill exact converters | Mixtral 8x22B, Gemma 4 26B | Converted one query reliably, but did not generalize to the aggregate, ranking, or decision-support tasks. |
| Partial-credit operators | Qwen 2.5 72B, Qwen3.6, Qwen3 Coder 30B, Llama 3 70B | Usually found part of the row set, but numeric grain, role grouping, or status classification blocked exact matches. |
| Brittle / low-coverage | Qwen 2.5 Coder 32B, DBRX, Command R+, CodeLlama 70B, DeepSeek Coder 33B, Phi-4 Mini | No exact conversions plus repeated row-set, audit-label, or numeric calculation failures. |

## Model Summary

| Model | Exact Attempts | Queries With Any Exact | Stable Exact Queries | Mean Score | Mean Cell Accuracy | Dominant Failure Mode |
|---|---:|---:|---:|---:|---:|---|
| Gemma 4 31B | 9/30 | 3/10 | 3/10 | 0.867 | 0.701 | same_count_wrong_values |
| Mixtral 8x22B | 3/30 | 1/10 | 1/10 | 0.619 | 0.510 | row_count_mismatch |
| Gemma 4 26B | 3/30 | 1/10 | 1/10 | 0.570 | 0.523 | same_count_wrong_values |
| Qwen 2.5 72B | 1/30 | 1/10 | 0/10 | 0.691 | 0.627 | same_count_wrong_values |
| Qwen3.6 | 0/30 | 0/10 | 0/10 | 0.663 | 0.641 | same_count_wrong_values |
| Qwen3 Coder 30B | 0/30 | 0/10 | 0/10 | 0.656 | 0.524 | same_count_wrong_values |
| Llama 3 70B | 0/30 | 0/10 | 0/10 | 0.647 | 0.507 | row_count_mismatch |
| Qwen 2.5 Coder 32B | 0/30 | 0/10 | 0/10 | 0.567 | 0.488 | same_count_wrong_values |
| DBRX | 0/30 | 0/10 | 0/10 | 0.545 | 0.412 | same_count_wrong_values |
| Command R+ | 0/30 | 0/10 | 0/10 | 0.514 | 0.393 | row_count_mismatch |
| CodeLlama 70B | 0/30 | 0/10 | 0/10 | 0.506 | 0.333 | row_count_mismatch |
| DeepSeek Coder 33B | 0/30 | 0/10 | 0/10 | 0.432 | 0.339 | same_count_wrong_values |
| Phi-4 Mini | 0/30 | 0/10 | 0/10 | 0.417 | 0.295 | row_count_mismatch |

## Query-by-Query Failure Points

| Query | Focus | Exact Attempts | Mean Score | Top failure points |
|---|---|---:|---:|---|
| Q1 | Join-status classification | 10/39 | 1.000 | 22/39: Misclassified call_id 6 / V5; it should be MISSING_GENE.; 18/39: Misclassified call_id 9 / V999; it should be MISSING_VARIANT.; 15/39: Misclassified one or more complete-chain calls. |
| Q2 | Tissue-gene VAF aggregate | 0/39 | 0.476 | 39/39: Returned the wrong tissue-gene group set for complete-chain matched rows.; 38/39: Miscomputed call_count or sum_alt_reads.; 38/39: Computed avg_vaf from the wrong numerator/denominator or row set. |
| Q3 | Gene coverage audit | 0/39 | 0.749 | 39/39: Miscomputed total_alt_reads for one or more genes.; 36/39: Miscomputed observed_call_count for one or more genes.; 7/39: Dropped zero-call genes NDHT or PGR1B from the gene-preserving audit. |
| Q4 | High-impact condition summary | 0/39 | 0.449 | 36/39: Returned the wrong set of high-impact condition rows.; 34/39: Miscomputed the control high-impact bucket.; 33/39: Miscomputed the high_light high-impact bucket. |
| Q5 | Sample genotype classes | 3/39 | 0.874 | 36/39: Miscomputed S2 heterozygous calls or non-reference mean quality.; 36/39: Counted reference calls or put genotypes into the wrong class.; 14/39: Included S999 even though sample_dim is the preserving table. |
| Q6 | Tissue-gene dense ranking | 0/39 | 0.524 | 36/39: Returned the wrong tissue-gene group set before ranking.; 32/39: Leaked root, incomplete-chain, or non-gold genes into the ranking.; 31/39: Miscomputed total_alt_reads or avg_vaf. |
| Q7 | Unused dimension anti-join | 3/39 | 0.077 | 36/39: Used dimension-table labels such as gene_dim/sample_dim instead of gene/sample/variant.; 36/39: Dropped or mislabeled one of G4, G5, S5, or V6 in the anti-join audit.; 31/39: Assigned the wrong reason to G4; it should be no_fact_calls_through_variants. |
| Q8 | Gene-role decision summary | 0/39 | 0.308 | 39/39: Returned the wrong condition-gene_role groups.; 39/39: Leaked reference calls, incomplete chains, or non-gold roles into the non-reference summary.; 28/39: Computed mean_vaf from the wrong row set. |
| Q9 | Failure-family audit | 0/39 | 0.792 | 39/39: Miscomputed complete_chain_calls by condition group.; 36/39: Miscomputed missing_sample, missing_variant, or missing_gene counts. |
| Q10 | Decision-priority candidate table | 0/39 | 0.670 | 39/39: Computed avg_vaf from the wrong non-reference row set.; 39/39: Mapped matched expression counts incorrectly.; 39/39: Computed decision_score incorrectly from avg_vaf and matched expression. |

## Short Notes

- **Q1 Join-status classification**: 10/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `join_key_integrity`.
Issue: 22/39 attempts. Misclassified call_id 6 / V5; it should be MISSING_GENE. Example models: Command R+, DBRX, DeepSeek Coder 33B, Phi-4 Mini.
Issue: 18/39 attempts. Misclassified call_id 9 / V999; it should be MISSING_VARIANT. Example models: CodeLlama 70B, Command R+, DBRX, Phi-4 Mini.
Issue: 15/39 attempts. Misclassified one or more complete-chain calls. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q2 Tissue-gene VAF aggregate**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `aggregation_numeric`.
Issue: 39/39 attempts. Returned the wrong tissue-gene group set for complete-chain matched rows. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 38/39 attempts. Miscomputed call_count or sum_alt_reads. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 38/39 attempts. Computed avg_vaf from the wrong numerator/denominator or row set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q3 Gene coverage audit**: 0/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `orphan_key_audit`.
Issue: 39/39 attempts. Miscomputed total_alt_reads for one or more genes. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 36/39 attempts. Miscomputed observed_call_count for one or more genes. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 7/39 attempts. Dropped zero-call genes NDHT or PGR1B from the gene-preserving audit. Example models: CodeLlama 70B, Command R+, Mixtral 8x22B.
- **Q4 High-impact condition summary**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `aggregation_numeric`.
Issue: 36/39 attempts. Returned the wrong set of high-impact condition rows. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 34/39 attempts. Miscomputed the control high-impact bucket. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 33/39 attempts. Miscomputed the high_light high-impact bucket. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q5 Sample genotype classes**: 3/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `outer_join_coverage`.
Issue: 36/39 attempts. Miscomputed S2 heterozygous calls or non-reference mean quality. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 36/39 attempts. Counted reference calls or put genotypes into the wrong class. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 14/39 attempts. Included S999 even though sample_dim is the preserving table. Example models: DBRX, DeepSeek Coder 33B, Llama 3 70B, Mixtral 8x22B.
- **Q6 Tissue-gene dense ranking**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `ranking_and_priority`.
Issue: 36/39 attempts. Returned the wrong tissue-gene group set before ranking. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 32/39 attempts. Leaked root, incomplete-chain, or non-gold genes into the ranking. Example models: Command R+, DBRX, DeepSeek Coder 33B, Gemma 4 26B.
Issue: 31/39 attempts. Miscomputed total_alt_reads or avg_vaf. Example models: CodeLlama 70B, Command R+, DBRX, Gemma 4 31B.
- **Q7 Unused dimension anti-join**: 3/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `orphan_key_audit`.
Issue: 36/39 attempts. Used dimension-table labels such as gene_dim/sample_dim instead of gene/sample/variant. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 36/39 attempts. Dropped or mislabeled one of G4, G5, S5, or V6 in the anti-join audit. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 31/39 attempts. Assigned the wrong reason to G4; it should be no_fact_calls_through_variants. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q8 Gene-role decision summary**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `decision_support`.
Issue: 39/39 attempts. Returned the wrong condition-gene_role groups. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Leaked reference calls, incomplete chains, or non-gold roles into the non-reference summary. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 28/39 attempts. Computed mean_vaf from the wrong row set. Example models: CodeLlama 70B, Command R+, Gemma 4 26B, Gemma 4 31B.
- **Q9 Failure-family audit**: 0/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `failure_family_audit`.
Issue: 39/39 attempts. Miscomputed complete_chain_calls by condition group. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 36/39 attempts. Miscomputed missing_sample, missing_variant, or missing_gene counts. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q10 Decision-priority candidate table**: 0/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `decision_support`.
Issue: 39/39 attempts. Computed avg_vaf from the wrong non-reference row set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Mapped matched expression counts incorrectly. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Computed decision_score incorrectly from avg_vaf and matched expression. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.

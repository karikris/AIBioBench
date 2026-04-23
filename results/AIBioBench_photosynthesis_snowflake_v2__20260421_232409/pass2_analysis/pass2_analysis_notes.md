# AIBioBench Pass 2 Analysis

Run analyzed: `AIBioBench_photosynthesis_snowflake_v2__20260421_232409`

Pass 2 contains ten medium SQL tasks, each repeated three times across thirteen models. Compared with pass 1, the task pressure shifts from basic joins to full snowflake traversal, full outer join coverage, VAF arithmetic, and sample-preserving coverage counts.

## Headline Findings

- **Gemma 4 31B** led pass 2 with 12/30 exact attempts and exact coverage on 4/10 questions.
- Exact matches were sparse: only 32/390 attempts were exact, and Q1, Q4, Q5, Q7, Q8, Q9 had zero exact attempts.
- The suite mostly broke models on chain completeness, aggregate grain, and preserving the right side of outer joins.
- High partial scores still occurred on Q2/Q10, but exact conversion failed when null handling or complete-vs-incomplete chain counts were off.

## Model Groups

| Group | Models | Why they belong there |
|---|---|---|
| Broad pass leader | Gemma 4 31B | Converted exact answers across four query types and kept high partial credit on the zero-exact aggregation tasks. |
| Strong exact converters | Gemma 4 26B, Qwen3.6 | Solved the easier outer-join cases reliably but did not convert the VAF, pathway, or high-impact aggregates. |
| Partial-credit joiners | Qwen 2.5 72B, Qwen 2.5 Coder 32B, Mixtral 8x22B, Llama 3 70B | Frequently found much of the row set, but row-count, chain-null, or aggregate-grain mistakes prevented exact conversion. |
| Brittle / low-coverage | Qwen3 Coder 30B, Command R+, Phi-4 Mini, DeepSeek Coder 33B, DBRX, CodeLlama 70B | Low exact coverage plus repeated row-count, chain traversal, or numeric aggregation failures. |

## Model Summary

| Model | Exact Attempts | Queries With Any Exact | Stable Exact Queries | Mean Score | Mean Cell Accuracy | Dominant Failure Mode |
|---|---:|---:|---:|---:|---:|---|
| Gemma 4 31B | 12/30 | 4/10 | 4/10 | 0.920 | 0.791 | same_count_wrong_values |
| Gemma 4 26B | 6/30 | 2/10 | 2/10 | 0.789 | 0.581 | row_count_mismatch |
| Qwen3.6 | 6/30 | 2/10 | 2/10 | 0.731 | 0.602 | row_count_mismatch |
| Qwen 2.5 72B | 3/30 | 1/10 | 1/10 | 0.781 | 0.621 | same_count_wrong_values |
| Qwen 2.5 Coder 32B | 3/30 | 1/10 | 1/10 | 0.633 | 0.493 | row_count_mismatch |
| Mixtral 8x22B | 2/30 | 1/10 | 0/10 | 0.701 | 0.545 | same_count_wrong_values |
| Llama 3 70B | 0/30 | 0/10 | 0/10 | 0.654 | 0.411 | row_count_mismatch |
| Qwen3 Coder 30B | 0/30 | 0/10 | 0/10 | 0.598 | 0.524 | row_count_mismatch |
| Command R+ | 0/30 | 0/10 | 0/10 | 0.592 | 0.549 | row_count_mismatch |
| Phi-4 Mini | 0/30 | 0/10 | 0/10 | 0.529 | 0.340 | row_count_mismatch |
| DeepSeek Coder 33B | 0/30 | 0/10 | 0/10 | 0.507 | 0.358 | row_count_mismatch |
| DBRX | 0/30 | 0/10 | 0/10 | 0.441 | 0.339 | row_count_mismatch |
| CodeLlama 70B | 0/30 | 0/10 | 0/10 | 0.415 | 0.371 | row_count_mismatch |

## Query-by-Query Failure Points

| Query | Focus | Exact Attempts | Mean Score | Top failure points |
|---|---|---:|---:|---|
| Q1 | Four-table inner join | 0/39 | 0.712 | 34/39: Kept call_id 6 / V5 even though the complete four-table inner join should remove it.; 30/39: Kept call_id 8 / S999 even though the sample dimension is missing.; 28/39: Kept call_id 9 / V999 even though the variant/gene chain is incomplete. |
| Q2 | Full snowflake left join | 15/39 | 0.846 | 21/39: Mapped matched variants to the wrong gene symbol or dropped a valid gene symbol.; 14/39: Filled sample attributes for S999 instead of leaving dimension fields null.; 6/39: Failed to leave gene_symbol null for incomplete V5/V999 chain rows. |
| Q3 | Variant full outer join | 9/39 | 0.726 | 16/39: Dropped the fact-only V999 row from the full outer join.; 14/39: Failed to preserve the coalesced variant_id key for fact-only or matched rows.; 12/39: Dropped the variant-only V6 row from the full outer join. |
| Q4 | Condition-impact aggregate | 0/39 | 0.553 | 39/39: Computed one or more condition-impact average qualities from the wrong row set.; 34/39: Returned the wrong condition-impact group set.; 30/39: Miscomputed the control/high bucket, especially the two-call count and average. |
| Q5 | Gene VAF aggregate | 0/39 | 0.489 | 39/39: Computed average VAF from the wrong numerator/denominator or row set.; 36/39: Computed max_qual from the wrong rows.; 24/39: Included incomplete-chain or non-gold genes such as NDHT/PGR1B. |
| Q6 | Tissue complete-chain aggregate | 5/39 | 0.580 | 32/39: Computed distinct gene counts from the wrong join grain.; 28/39: Computed avg_expr_ndhb over samples instead of complete-chain joined calls.; 23/39: Included root/S5 even though complete inner joins should remove it. |
| Q7 | Sample high-impact screen | 0/39 | 0.714 | 36/39: Missed the zero-alt high-impact call for S4.; 36/39: Averaged alt_reads over the wrong subset of rows.; 25/39: Counted non-high or incomplete rows as high-impact calls, often inflating S3. |
| Q8 | Gene read-quality aggregate | 0/39 | 0.560 | 33/39: Computed avg_qual from the wrong row set.; 26/39: Computed total_alt_reads from the wrong row set.; 18/39: Included incomplete-chain genes that should not appear. |
| Q9 | Pathway decision summary | 0/39 | 0.375 | 39/39: Miscomputed call_count or distinct_samples.; 39/39: Computed mean VAF from the wrong row set.; 33/39: Returned the wrong condition-pathway group set. |
| Q10 | Sample coverage screen | 3/39 | 0.822 | 36/39: Misclassified complete vs incomplete chain calls.; 17/39: Miscomputed total fact calls per sample.; 11/39: Dropped zero-call sample S5 from the sample-preserving coverage screen. |

## Short Notes

- **Q1 Four-table inner join**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `snowflake_traversal`.
Issue: 34/39 attempts. Kept call_id 6 / V5 even though the complete four-table inner join should remove it. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 30/39 attempts. Kept call_id 8 / S999 even though the sample dimension is missing. Example models: Command R+, DBRX, DeepSeek Coder 33B, Llama 3 70B.
Issue: 28/39 attempts. Kept call_id 9 / V999 even though the variant/gene chain is incomplete. Example models: Command R+, DBRX, DeepSeek Coder 33B, Llama 3 70B.
- **Q2 Full snowflake left join**: 15/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `outer_join_coverage`.
Issue: 21/39 attempts. Mapped matched variants to the wrong gene symbol or dropped a valid gene symbol. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 14/39 attempts. Filled sample attributes for S999 instead of leaving dimension fields null. Example models: CodeLlama 70B, Llama 3 70B, Mixtral 8x22B, Phi-4 Mini.
Issue: 6/39 attempts. Failed to leave gene_symbol null for incomplete V5/V999 chain rows. Example models: CodeLlama 70B, DeepSeek Coder 33B, Mixtral 8x22B.
- **Q3 Variant full outer join**: 9/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `outer_join_coverage`.
Issue: 16/39 attempts. Dropped the fact-only V999 row from the full outer join. Example models: CodeLlama 70B, Command R+, DBRX, Llama 3 70B.
Issue: 14/39 attempts. Failed to preserve the coalesced variant_id key for fact-only or matched rows. Example models: CodeLlama 70B, DBRX, DeepSeek Coder 33B, Llama 3 70B.
Issue: 12/39 attempts. Dropped the variant-only V6 row from the full outer join. Example models: DBRX, Llama 3 70B, Mixtral 8x22B, Phi-4 Mini.
- **Q4 Condition-impact aggregate**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `aggregation_numeric`.
Issue: 39/39 attempts. Computed one or more condition-impact average qualities from the wrong row set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 34/39 attempts. Returned the wrong condition-impact group set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 30/39 attempts. Miscomputed the control/high bucket, especially the two-call count and average. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q5 Gene VAF aggregate**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `aggregation_numeric`.
Issue: 39/39 attempts. Computed average VAF from the wrong numerator/denominator or row set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 36/39 attempts. Computed max_qual from the wrong rows. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 24/39 attempts. Included incomplete-chain or non-gold genes such as NDHT/PGR1B. Example models: Command R+, DBRX, DeepSeek Coder 33B, Gemma 4 26B.
- **Q6 Tissue complete-chain aggregate**: 5/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `snowflake_traversal`.
Issue: 32/39 attempts. Computed distinct gene counts from the wrong join grain. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 28/39 attempts. Computed avg_expr_ndhb over samples instead of complete-chain joined calls. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 23/39 attempts. Included root/S5 even though complete inner joins should remove it. Example models: CodeLlama 70B, Command R+, DBRX, Gemma 4 26B.
- **Q7 Sample high-impact screen**: 0/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `outer_join_coverage`.
Issue: 36/39 attempts. Missed the zero-alt high-impact call for S4. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 36/39 attempts. Averaged alt_reads over the wrong subset of rows. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 25/39 attempts. Counted non-high or incomplete rows as high-impact calls, often inflating S3. Example models: Command R+, DBRX, DeepSeek Coder 33B, Llama 3 70B.
- **Q8 Gene read-quality aggregate**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `aggregation_numeric`.
Issue: 33/39 attempts. Computed avg_qual from the wrong row set. Example models: CodeLlama 70B, DeepSeek Coder 33B, Gemma 4 26B, Gemma 4 31B.
Issue: 26/39 attempts. Computed total_alt_reads from the wrong row set. Example models: CodeLlama 70B, DeepSeek Coder 33B, Gemma 4 26B, Mixtral 8x22B.
Issue: 18/39 attempts. Included incomplete-chain genes that should not appear. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q9 Pathway decision summary**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `decision_support`.
Issue: 39/39 attempts. Miscomputed call_count or distinct_samples. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 39/39 attempts. Computed mean VAF from the wrong row set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 33/39 attempts. Returned the wrong condition-pathway group set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
- **Q10 Sample coverage screen**: 3/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `decision_support`.
Issue: 36/39 attempts. Misclassified complete vs incomplete chain calls. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 17/39 attempts. Miscomputed total fact calls per sample. Example models: CodeLlama 70B, Llama 3 70B, Mixtral 8x22B, Phi-4 Mini.
Issue: 11/39 attempts. Dropped zero-call sample S5 from the sample-preserving coverage screen. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.

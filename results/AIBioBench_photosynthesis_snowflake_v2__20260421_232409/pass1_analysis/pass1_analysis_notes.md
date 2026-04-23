# AIBioBench Pass 1 Analysis

Run analyzed: `AIBioBench_photosynthesis_snowflake_v2__20260421_232409`

Pass 1 in the latest run contains ten easy SQL tasks, each repeated three times across thirteen models. The charts in this folder focus on exact-match conversion, partial-credit behavior, repeatability, and the recurring failure points that kept models from converting high partial scores into exact answers.

## Headline Findings

- **Gemma 4 31B** was the clear leader with 13/30 exact attempts and exact coverage on 5/10 questions.
- Only **Q1, Q3, Q4, Q5, and Q10** produced any exact answers at all; **Q2 and Q6-Q9 were exact-zero questions across the whole field**.
- Several models posted strong mean scores despite weak exact conversion. That means the main gap was often a final join/filter/count/sort decision, not total failure to understand the task.
- Failure patterns split cleanly into structural join mistakes on Q1/Q4/Q5/Q10 and misweighted aggregation mistakes on Q6-Q9.

## Model Groups

| Group | Models | Why they belong there |
|---|---|---|
| Broad pass leader | Gemma 4 31B | Only model family with exact coverage spanning half of the suite and strong partial credit on the remaining aggregation tasks. |
| Strong but narrow exactness | Gemma 4 26B, Qwen 2.5 72B, Qwen 2.5 Coder 32B, Qwen3.6 | Reliable exactness on a few structural tasks, then near-exact rather than exact on the harder aggregation screens. |
| Near-miss operators | Llama 3 70B, Mixtral 8x22B, Command R+ | Often one join/filter/count fix away from correctness, but exact-match brittleness kept them from converting those near misses. |
| Brittle / low-coverage | CodeLlama 70B, DBRX, Phi-4 Mini, DeepSeek Coder 33B, Qwen3 Coder 30B | Low exact coverage plus repeated row-count, type, or schema-level mistakes kept performance unstable. |

## Model Summary

| Model | Exact Attempts | Queries With Any Exact | Stable Exact Queries | Mean Score | Mean Cell Accuracy | Dominant Failure Mode |
|---|---:|---:|---:|---:|---:|---|
| Gemma 4 31B | 13/30 | 5/10 | 3/10 | 0.925 | 0.789 | exact |
| Gemma 4 26B | 9/30 | 3/10 | 3/10 | 0.823 | 0.646 | row_count_mismatch |
| Qwen 2.5 72B | 7/30 | 3/10 | 2/10 | 0.840 | 0.693 | same_count_wrong_values |
| Qwen 2.5 Coder 32B | 6/30 | 2/10 | 2/10 | 0.845 | 0.684 | same_count_wrong_values |
| Qwen3.6 | 6/30 | 2/10 | 2/10 | 0.842 | 0.628 | same_count_wrong_values |
| Llama 3 70B | 3/30 | 1/10 | 1/10 | 0.800 | 0.598 | row_count_mismatch |
| CodeLlama 70B | 3/30 | 1/10 | 1/10 | 0.627 | 0.560 | same_count_wrong_values |
| Mixtral 8x22B | 2/30 | 1/10 | 0/10 | 0.803 | 0.598 | same_count_wrong_values |
| Command R+ | 1/30 | 1/10 | 0/10 | 0.830 | 0.639 | same_count_wrong_values |
| DBRX | 1/30 | 1/10 | 0/10 | 0.735 | 0.490 | row_count_mismatch |
| Phi-4 Mini | 0/30 | 0/10 | 0/10 | 0.694 | 0.418 | row_count_mismatch |
| DeepSeek Coder 33B | 0/30 | 0/10 | 0/10 | 0.676 | 0.494 | row_count_mismatch |
| Qwen3 Coder 30B | 0/30 | 0/10 | 0/10 | 0.450 | 0.587 | row_count_mismatch |

## Query-by-Query Failure Points

| Query | Focus | Exact Attempts | Mean Score | Top failure points |
|---|---|---:|---:|---|
| Q1 | Sample inner join | 3/39 | 0.812 | 25/39: Included orphan sample row S999/call_id 8 that should disappear under the inner join.; 14/39: Dropped call_id 9 even though sample S2 exists and should survive the sample join.; 8/39: Leaked tissue or condition values across rows instead of preserving sample attributes. |
| Q2 | Variant join + qual sort | 0/39 | 0.717 | 27/39: Included call_id 9 / V999 despite the required inner join to `variant_dim`.; 20/39: Returned the matched row set but not in `qual DESC, call_id ASC` order.; 19/39: Dropped valid matched calls from the joined result. |
| Q3 | Sample left join | 21/39 | 0.912 | 18/39: Did not preserve the unmatched `S999` row cleanly in the left join output.; 9/39: Mixed condition values into tissue/batch fields or used the wrong expression values.; 3/39: Matched the table semantically but serialized numbers/nulls with the wrong types. |
| Q4 | Outer join aggregate | 6/39 | 0.879 | 29/39: Computed the `S2` average incorrectly, often from the wrong row set or over-rounded output.; 10/39: Undercounted `S2` by missing one fact row, usually call_id 9. |
| Q5 | Variant to gene chain | 2/39 | 0.699 | 36/39: Kept unmatched call_id 9 / V999 even though the chain join should remove it.; 31/39: Kept call_id 6 / V5 after the second inner join instead of dropping the incomplete chain.; 14/39: Dropped valid matched rows while traversing the fact -> variant -> gene chain. |
| Q6 | Impact aggregate | 0/39 | 0.757 | 39/39: Used the wrong row set for average quality per impact bucket.; 32/39: Under-counted high-impact calls by not aggregating both V2 and V3 duplicates.; 18/39: Under-counted the two moderate V1 calls. |
| Q7 | Tissue qual aggregate | 0/39 | 0.502 | 39/39: Computed tissue averages from the wrong grain instead of fact-call-weighted quality values.; 36/39: Minimum or maximum quality per tissue came from the wrong row set.; 20/39: Included `root` / `S5` even though the task required an inner join to fact rows only. |
| Q8 | Condition expression aggregate | 0/39 | 0.742 | 39/39: Used sample counts instead of fact-call counts for one or more conditions.; 38/39: Averaged expression at the wrong grain instead of call-weighting by joined fact rows.; 23/39: Leaked `S5` / `high_light` into the aggregate, inflating the high-light bucket. |
| Q9 | Condition decision screen | 0/39 | 0.795 | 38/39: Missed the high-impact filter/count after joining to `variant_dim`.; 35/39: Used the wrong total-call counts, usually from sample-level counting or leaked rows.; 26/39: Inflated the high-light bucket by leaking unmatched or extra rows. |
| Q10 | Variant anomaly audit | 19/39 | 0.792 | 9/39: Marked matched variants as `MISSING_VARIANT` instead of `MATCHED`.; 6/39: Matched the audit semantically but serialized identifiers with the wrong types.; 5/39: Nullified `variant_id` for call_id 9 instead of preserving `V999` from the fact table. |

## Short Notes

- **Q1 Sample inner join**: 3/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `inner_join_accuracy`.
Issue: 25/39 attempts. Included orphan sample row S999/call_id 8 that should disappear under the inner join. Example models: Command R+, DBRX, DeepSeek Coder 33B, Llama 3 70B.
Issue: 14/39 attempts. Dropped call_id 9 even though sample S2 exists and should survive the sample join. Example models: CodeLlama 70B, Gemma 4 26B, Mixtral 8x22B, Qwen 2.5 72B.
Issue: 8/39 attempts. Leaked tissue or condition values across rows instead of preserving sample attributes. Example models: CodeLlama 70B, Command R+, DeepSeek Coder 33B, Phi-4 Mini.
- **Q2 Variant join + qual sort**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `sorting_presentation`.
Issue: 27/39 attempts. Included call_id 9 / V999 despite the required inner join to `variant_dim`. Example models: Command R+, DBRX, DeepSeek Coder 33B, Llama 3 70B.
Issue: 20/39 attempts. Returned the matched row set but not in `qual DESC, call_id ASC` order. Example models: Command R+, DBRX, DeepSeek Coder 33B, Gemma 4 26B.
Issue: 19/39 attempts. Dropped valid matched calls from the joined result. Example models: CodeLlama 70B, DeepSeek Coder 33B, Mixtral 8x22B, Phi-4 Mini.
- **Q3 Sample left join**: 21/39 exact, dominant failure mode `exact`. Primary family: `outer_join_coverage`.
Issue: 18/39 attempts. Did not preserve the unmatched `S999` row cleanly in the left join output. Example models: CodeLlama 70B, Command R+, DBRX, Llama 3 70B.
Issue: 9/39 attempts. Mixed condition values into tissue/batch fields or used the wrong expression values. Example models: DBRX, DeepSeek Coder 33B, Llama 3 70B, Phi-4 Mini.
Issue: 3/39 attempts. Matched the table semantically but serialized numbers/nulls with the wrong types. Example models: Qwen3 Coder 30B.
- **Q4 Outer join aggregate**: 6/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `outer_join_coverage`.
Issue: 29/39 attempts. Computed the `S2` average incorrectly, often from the wrong row set or over-rounded output. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 10/39 attempts. Undercounted `S2` by missing one fact row, usually call_id 9. Example models: DBRX, Mixtral 8x22B, Phi-4 Mini, Qwen 2.5 Coder 32B.
- **Q5 Variant to gene chain**: 2/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `snowflake_traversal`.
Issue: 36/39 attempts. Kept unmatched call_id 9 / V999 even though the chain join should remove it. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 31/39 attempts. Kept call_id 6 / V5 after the second inner join instead of dropping the incomplete chain. Example models: Command R+, DBRX, DeepSeek Coder 33B, Gemma 4 26B.
Issue: 14/39 attempts. Dropped valid matched rows while traversing the fact -> variant -> gene chain. Example models: CodeLlama 70B, Command R+, DBRX, Phi-4 Mini.
- **Q6 Impact aggregate**: 0/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `aggregation_numeric`.
Issue: 39/39 attempts. Used the wrong row set for average quality per impact bucket. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 32/39 attempts. Under-counted high-impact calls by not aggregating both V2 and V3 duplicates. Example models: CodeLlama 70B, DBRX, DeepSeek Coder 33B, Gemma 4 26B.
Issue: 18/39 attempts. Under-counted the two moderate V1 calls. Example models: Command R+, DBRX, DeepSeek Coder 33B, Gemma 4 26B.
- **Q7 Tissue qual aggregate**: 0/39 exact, dominant failure mode `row_count_mismatch`. Primary family: `aggregation_numeric`.
Issue: 39/39 attempts. Computed tissue averages from the wrong grain instead of fact-call-weighted quality values. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 36/39 attempts. Minimum or maximum quality per tissue came from the wrong row set. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 20/39 attempts. Included `root` / `S5` even though the task required an inner join to fact rows only. Example models: Command R+, DBRX, DeepSeek Coder 33B, Gemma 4 26B.
- **Q8 Condition expression aggregate**: 0/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `aggregation_numeric`.
Issue: 39/39 attempts. Used sample counts instead of fact-call counts for one or more conditions. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 38/39 attempts. Averaged expression at the wrong grain instead of call-weighting by joined fact rows. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 23/39 attempts. Leaked `S5` / `high_light` into the aggregate, inflating the high-light bucket. Example models: CodeLlama 70B, DBRX, Gemma 4 26B, Gemma 4 31B.
- **Q9 Condition decision screen**: 0/39 exact, dominant failure mode `same_count_wrong_values`. Primary family: `decision_support`.
Issue: 38/39 attempts. Missed the high-impact filter/count after joining to `variant_dim`. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 35/39 attempts. Used the wrong total-call counts, usually from sample-level counting or leaked rows. Example models: CodeLlama 70B, Command R+, DBRX, DeepSeek Coder 33B.
Issue: 26/39 attempts. Inflated the high-light bucket by leaking unmatched or extra rows. Example models: CodeLlama 70B, DBRX, DeepSeek Coder 33B, Gemma 4 26B.
- **Q10 Variant anomaly audit**: 19/39 exact, dominant failure mode `exact`. Primary family: `join_key_integrity`.
Issue: 9/39 attempts. Marked matched variants as `MISSING_VARIANT` instead of `MATCHED`. Example models: CodeLlama 70B, DBRX, Phi-4 Mini.
Issue: 6/39 attempts. Matched the audit semantically but serialized identifiers with the wrong types. Example models: DeepSeek Coder 33B, Qwen3 Coder 30B.
Issue: 5/39 attempts. Nullified `variant_id` for call_id 9 instead of preserving `V999` from the fact table. Example models: Mixtral 8x22B, Phi-4 Mini.

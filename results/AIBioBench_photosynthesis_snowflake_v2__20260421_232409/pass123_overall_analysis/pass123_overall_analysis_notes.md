# AIBioBench Passes 1-3 Overall Analysis

Run analyzed: `AIBioBench_photosynthesis_snowflake_v2__20260421_232409`

Scope: passes 1, 2, and 3 only. This covers 30 SQL queries, 13 models, and 3 repeated attempts per model-query pair.

## Headline Findings

- Overall exact conversion was 99/1170 attempts (8.5%).
- Exact matches dropped monotonically by pass: 51/390 in pass 1, 32/390 in pass 2, and 16/390 in pass 3.
- 18/30 queries had zero exact attempts. Exact-zero queries increased from 5/10 in pass 1 to 6/10 in pass 2 and 7/10 in pass 3.
- Gemma 4 31B was the clear cross-pass leader with 34/90 exact attempts and exact matches in all three passes.
- The primary degradation was not invalid output. Models usually returned plausible tables but failed on row-set boundaries, join preservation, aggregation grain, or exact sort/type semantics.

## Pass-Level Summary

| Pass | Exact Attempts | Queries With Any Exact | Exact-Zero Queries | Mean Score | Mean Cell Accuracy | Dominant Failure Mode |
|---|---:|---:|---:|---:|---:|---|
| Pass 1 | 51/390 | 5/10 | 5/10 | 0.761 | 0.602 | same_count_wrong_values |
| Pass 2 | 32/390 | 4/10 | 6/10 | 0.638 | 0.502 | row_count_mismatch |
| Pass 3 | 16/390 | 3/10 | 7/10 | 0.592 | 0.484 | same_count_wrong_values |

## Model Groups

| Group | Models | Interpretation |
|---|---|---|
| Dominant cross-pass leader | Gemma 4 31B | Only model with high exact conversion across all three SQL passes and the smallest pass-1 to pass-3 exactness decay. |
| Strong but difficulty-sensitive exact converters | Gemma 4 26B, Qwen3.6, Qwen 2.5 72B, Qwen 2.5 Coder 32B | Converted easy/medium structural tasks, but exactness fell sharply as hard joins, audits, and ranking appeared. |
| Near-miss or niche hard-query operators | Mixtral 8x22B, Llama 3 70B, Command R+ | Often retained useful partial credit or a narrow hard-query skill, but exact conversion was sparse. |
| Brittle / low-exactness operators | CodeLlama 70B, DBRX, Qwen3 Coder 30B, Phi-4 Mini, DeepSeek Coder 33B | Low or zero exact conversion with repeated row-set, join-chain, and aggregation-grain failures. |

## Model Ranking

| Model | Exact Attempts | Pass 1 | Pass 2 | Pass 3 | Mean Score | Score Drop P1 to P3 | Dominant Failure |
|---|---:|---:|---:|---:|---:|---:|---|
| Gemma 4 31B | 34/90 | 13 | 12 | 9 | 0.904 | 0.059 | same_count_wrong_values |
| Gemma 4 26B | 18/90 | 9 | 6 | 3 | 0.727 | 0.252 | row_count_mismatch |
| Qwen3.6 | 12/90 | 6 | 6 | 0 | 0.745 | 0.179 | same_count_wrong_values |
| Qwen 2.5 72B | 11/90 | 7 | 3 | 1 | 0.770 | 0.149 | same_count_wrong_values |
| Qwen 2.5 Coder 32B | 9/90 | 6 | 3 | 0 | 0.682 | 0.278 | same_count_wrong_values |
| Mixtral 8x22B | 7/90 | 2 | 2 | 3 | 0.707 | 0.184 | same_count_wrong_values |
| Llama 3 70B | 3/90 | 3 | 0 | 0 | 0.700 | 0.153 | row_count_mismatch |
| CodeLlama 70B | 3/90 | 3 | 0 | 0 | 0.516 | 0.120 | row_count_mismatch |
| Command R+ | 1/90 | 1 | 0 | 0 | 0.646 | 0.317 | same_count_wrong_values |
| DBRX | 1/90 | 1 | 0 | 0 | 0.574 | 0.190 | same_count_wrong_values |
| Qwen3 Coder 30B | 0/90 | 0 | 0 | 0 | 0.568 | -0.206 | row_count_mismatch |
| Phi-4 Mini | 0/90 | 0 | 0 | 0 | 0.547 | 0.277 | row_count_mismatch |
| DeepSeek Coder 33B | 0/90 | 0 | 0 | 0 | 0.538 | 0.243 | row_count_mismatch |

## Query-Level Takeaways

**Best exact-conversion queries:**

- P1 Q3 `pass1.query3`: 21/39 exact, mean score 0.912, family `outer_join_coverage`.
- P1 Q10 `pass1.query10`: 19/39 exact, mean score 0.792, family `join_key_integrity`.
- P2 Q2 `pass2.query2`: 15/39 exact, mean score 0.846, family `outer_join_coverage`.
- P3 Q1 `pass3.query1`: 10/39 exact, mean score 1.000, family `join_key_integrity`.
- P2 Q3 `pass2.query3`: 9/39 exact, mean score 0.726, family `outer_join_coverage`.

**Hardest exact-conversion queries:**

- P3 Q8 `pass3.query8`: 0/39 exact, mean score 0.308, family `decision_support`.
- P2 Q9 `pass2.query9`: 0/39 exact, mean score 0.375, family `decision_support`.
- P3 Q4 `pass3.query4`: 0/39 exact, mean score 0.449, family `aggregation_numeric`.
- P3 Q2 `pass3.query2`: 0/39 exact, mean score 0.476, family `aggregation_numeric`.
- P2 Q5 `pass2.query5`: 0/39 exact, mean score 0.489, family `aggregation_numeric`.

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

## Interpretation

- Pass 1 mainly separated models on basic join preservation and simple aggregation grain. Even easy tasks exposed exact-match brittleness: half the queries had zero exact attempts.
- Pass 2 raised the cost of snowflake traversal and preserving-table logic. Exactness concentrated in a few join-coverage tasks, while decision-support aggregates stayed exact-zero.
- Pass 3 moved failures toward hard join-status classification, anti-join/orphan logic, dense ranking, and decision-priority aggregation. Some models preserved high partial scores, but exact conversion largely collapsed.
- Across all three passes, row-count mismatch and same-count-wrong-values dominate. That means the benchmark is mostly measuring semantic boundary errors rather than JSON validity or execution-format failures.

# AIBioBench Queries

Source: `benchmark_cases.jsonl`

Benchmark: `AIBioBench_photosynthesis_snowflake_v4`

Total queries: 50

## Pass 1

### Query 1: `pass1.query1`

- Difficulty: `easy`
- Language: `sql`
- Primary failure family: `inner_join_accuracy`

```text
Inner join fact_calls to sample_dim on sample_id.
Return: call_id, sample_id, tissue, condition, genotype
Sort by call_id ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 8 data rows and exactly these columns in this order: call_id, sample_id, tissue, condition, genotype.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by call_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_id; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses call_id; follow the prompt's sort direction and tie-breakers exactly.
- For the sample inner join only, call_id 8/S999 must be removed, but call_id 9/S2 must remain because S2 exists in sample_dim.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q1_included_orphan_s999, 64% of attempts): Included orphan sample row S999/call_id 8 that should disappear under the inner join. Check this explicitly before finalizing.
- Previous v3 failure warning (q1_dropped_call9, 36% of attempts): Dropped call_id 9 even though sample S2 exists and should survive the sample join. Check this explicitly before finalizing.
- Previous v3 failure warning (q1_attribute_leakage, 21% of attempts): Leaked tissue or condition values across rows instead of preserving sample attributes. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 1 and end with last row key/value 9 for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 2: `pass1.query2`

- Difficulty: `easy`
- Language: `sql`
- Primary failure family: `sorting_presentation`

```text
Inner join fact_calls to variant_dim on variant_id.
Return: call_id, variant_id, variant_class, impact, qual
Sort by qual descending, then call_id ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 8 data rows and exactly these columns in this order: call_id, variant_id, variant_class, impact, qual.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by call_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_id, qual; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses qual, call_id; follow the prompt's sort direction and tie-breakers exactly.
- For the variant inner join only, call_id 9/V999 must be removed, but call_id 6/V5 remains because V5 exists in variant_dim.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q2_included_v999, 64% of attempts): Included call_id 9 / V999 despite the required inner join to `variant_dim`. Check this explicitly before finalizing.
- Previous v3 failure warning (q2_dropped_matched_calls, 48% of attempts): Dropped valid matched calls from the joined result. Check this explicitly before finalizing.
- Previous v3 failure warning (q2_wrong_sort, 45% of attempts): Returned the matched row set but not in `qual DESC, call_id ASC` order. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 1 and end with last row key/value 8 for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 3: `pass1.query3`

- Difficulty: `easy`
- Language: `sql`
- Primary failure family: `outer_join_coverage`

```text
Left join fact_calls to sample_dim on sample_id.
Return: call_id, sample_id, tissue, batch, expr_ndhb
Keep all fact rows.
Sort by call_id ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 9 data rows and exactly these columns in this order: call_id, sample_id, tissue, batch, expr_ndhb.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by call_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_id, expr_ndhb; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses call_id; follow the prompt's sort direction and tie-breakers exactly.
- Fact-preserving logic must keep every fact_calls row unless the prompt later applies an explicit filter; preserve fact-side keys such as V999/S999 and put NULLs only in missing dimension attributes.
- Expression summaries must use the marker column named in the prompt and the correct grain: sample-only tasks average samples, joined tasks average the joined sample-call rows.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q3_bad_unmatched_row, 26% of attempts): Did not preserve the unmatched `S999` row cleanly in the left join output. Check this explicitly before finalizing.
- Previous v3 failure warning (q3_attribute_mixup, 26% of attempts): Mixed condition values into tissue/batch fields or used the wrong expression values. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 1 and end with last row key/value 9 for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 4: `pass1.query4`

- Difficulty: `easy`
- Language: `sql`
- Primary failure family: `outer_join_coverage`

```text
Use a RIGHT JOIN from fact_calls to sample_dim, or an equivalent reversed LEFT JOIN.
Return one row per sample with:
sample_id, tissue, call_count, avg_qual
Include samples with zero calls.
Sort by sample_id ascending.
Round avg_qual to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 5 data rows and exactly these columns in this order: sample_id, tissue, call_count, avg_qual.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by sample_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_count, avg_qual; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses sample_id; follow the prompt's sort direction and tie-breakers exactly.
- For sample-preserving output, produce one row per sample_dim sample; zero-call or zero-burden samples still need count 0 and NULL/rounded derived values as requested.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Quality statistics must use qual values from the correctly joined/filter-preserved fact rows; compute min/max/mean after the row boundary is correct.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q4_s2_avg_wrong, 79% of attempts): Computed the `S2` average incorrectly, often from the wrong row set or over-rounded output. Check this explicitly before finalizing.
- Previous v3 failure warning (q4_s2_undercounted, 36% of attempts): Undercounted `S2` by missing one fact row, usually call_id 9. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'S1' and end with last row key/value 'S5' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 5: `pass1.query5`

- Difficulty: `easy`
- Language: `sql`
- Primary failure family: `snowflake_traversal`

```text
Inner join fact_calls to variant_dim, then to gene_dim.
Return: call_id, variant_id, gene_symbol, pathway
Sort by call_id ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 7 data rows and exactly these columns in this order: call_id, variant_id, gene_symbol, pathway.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by call_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_id; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses call_id; follow the prompt's sort direction and tie-breakers exactly.
- For a fact -> variant -> gene chain without sample_dim, drop V5/G999 and V999, but do not drop call_id 8 solely because S999 is not in sample_dim.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q5_kept_call6, 81% of attempts): Kept call_id 6 / V5 after the second inner join instead of dropping the incomplete chain. Check this explicitly before finalizing.
- Previous v3 failure warning (q5_kept_call9, 81% of attempts): Kept unmatched call_id 9 / V999 even though the chain join should remove it. Check this explicitly before finalizing.
- Previous v3 failure warning (q5_dropped_matched_rows, 52% of attempts): Dropped valid matched rows while traversing the fact -> variant -> gene chain. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 1 and end with last row key/value 8 for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 6: `pass1.query6`

- Difficulty: `easy`
- Language: `sql`
- Primary failure family: `aggregation_numeric`

```text
Inner join fact_calls to variant_dim.
Count calls by impact and also compute average qual.
Return: impact, call_count, avg_qual
Sort by call_count descending, then impact ascending.
Round avg_qual to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 4 data rows and exactly these columns in this order: impact, call_count, avg_qual.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by impact; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_count, avg_qual; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses call_count, impact; follow the prompt's sort direction and tie-breakers exactly.
- For the variant inner join only, call_id 9/V999 must be removed, but call_id 6/V5 remains because V5 exists in variant_dim.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Quality statistics must use qual values from the correctly joined/filter-preserved fact rows; compute min/max/mean after the row boundary is correct.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q6_avg_wrong, 93% of attempts): Used the wrong row set for average quality per impact bucket. Check this explicitly before finalizing.
- Previous v3 failure warning (q6_high_undercount, 64% of attempts): Under-counted high-impact calls by not aggregating both V2 and V3 duplicates. Check this explicitly before finalizing.
- Previous v3 failure warning (q6_moderate_undercount, 55% of attempts): Under-counted the two moderate V1 calls. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'high' and end with last row key/value 'modifier' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 7: `pass1.query7`

- Difficulty: `easy`
- Language: `sql`
- Primary failure family: `aggregation_numeric`

```text
Inner join fact_calls to sample_dim.
Compute average, minimum, and maximum qual by tissue.
Return: tissue, avg_qual, min_qual, max_qual
Sort by avg_qual descending.
Round avg_qual to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 2 data rows and exactly these columns in this order: tissue, avg_qual, min_qual, max_qual.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by tissue; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: avg_qual, min_qual, max_qual; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses avg_qual; follow the prompt's sort direction and tie-breakers exactly.
- For the sample inner join only, call_id 8/S999 must be removed, but call_id 9/S2 must remain because S2 exists in sample_dim.
- Quality statistics must use qual values from the correctly joined/filter-preserved fact rows; compute min/max/mean after the row boundary is correct.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q7_misweighted_avg, 100% of attempts): Computed tissue averages from the wrong grain instead of fact-call-weighted quality values. Check this explicitly before finalizing.
- Previous v3 failure warning (q7_wrong_extrema, 98% of attempts): Minimum or maximum quality per tissue came from the wrong row set. Check this explicitly before finalizing.
- Previous v3 failure warning (q7_included_root, 52% of attempts): Included `root` / `S5` even though the task required an inner join to fact rows only. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'young_leaf' and end with last row key/value 'mature_leaf' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 8: `pass1.query8`

- Difficulty: `easy`
- Language: `sql`
- Primary failure family: `aggregation_numeric`

```text
Inner join fact_calls to sample_dim.
For each condition, compute:
- call_count
- avg_expr_pgr5
Return: condition, call_count, avg_expr_pgr5
Sort by condition ascending.
Round avg_expr_pgr5 to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 3 data rows and exactly these columns in this order: condition, call_count, avg_expr_pgr5.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by condition; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_count, avg_expr_pgr5; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses condition; follow the prompt's sort direction and tie-breakers exactly.
- For the sample inner join only, call_id 8/S999 must be removed, but call_id 9/S2 must remain because S2 exists in sample_dim.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Expression summaries must use the marker column named in the prompt and the correct grain: sample-only tasks average samples, joined tasks average the joined sample-call rows.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q8_sample_counts, 100% of attempts): Used sample counts instead of fact-call counts for one or more conditions. Check this explicitly before finalizing.
- Previous v3 failure warning (q8_expr_misweighted, 100% of attempts): Averaged expression at the wrong grain instead of call-weighting by joined fact rows. Check this explicitly before finalizing.
- Previous v3 failure warning (q8_high_light_leak, 62% of attempts): Leaked `S5` / `high_light` into the aggregate, inflating the high-light bucket. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'control' and end with last row key/value 'high_light' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 9: `pass1.query9`

- Difficulty: `easy`
- Language: `sql`
- Primary failure family: `decision_support`

```text
Decision screen for sample quality.
Inner join fact_calls to sample_dim and variant_dim.
For each condition, compute:
- total_calls
- avg_qual
- high_impact_calls where impact = 'high'
Return: condition, total_calls, avg_qual, high_impact_calls
Sort by condition ascending.
Round avg_qual to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 3 data rows and exactly these columns in this order: condition, total_calls, avg_qual, high_impact_calls.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by condition; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: total_calls, avg_qual, high_impact_calls; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses condition; follow the prompt's sort direction and tie-breakers exactly.
- Apply the high-impact filter only to rows whose joined variant_dim impact is exactly 'high'.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Quality statistics must use qual values from the correctly joined/filter-preserved fact rows; compute min/max/mean after the row boundary is correct.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q9_wrong_total_calls, 98% of attempts): Used the wrong total-call counts, usually from sample-level counting or leaked rows. Check this explicitly before finalizing.
- Previous v3 failure warning (q9_high_impact_miss, 95% of attempts): Missed the high-impact filter/count after joining to `variant_dim`. Check this explicitly before finalizing.
- Previous v3 failure warning (q9_high_light_leak, 79% of attempts): Inflated the high-light bucket by leaking unmatched or extra rows. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'control' and end with last row key/value 'high_light' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 10: `pass1.query10`

- Difficulty: `easy`
- Language: `sql`
- Primary failure family: `join_key_integrity`

```text
Simple anomaly audit.
Left join fact_calls to variant_dim on variant_id.
Return: call_id, variant_id, impact, variant_match_status
Set variant_match_status to MATCHED when variant_dim matched, else MISSING_VARIANT.
Keep all fact rows.
Sort by call_id ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 9 data rows and exactly these columns in this order: call_id, variant_id, impact, variant_match_status.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by call_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_id; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses call_id; follow the prompt's sort direction and tie-breakers exactly.
- Fact-preserving logic must keep every fact_calls row unless the prompt later applies an explicit filter; preserve fact-side keys such as V999/S999 and put NULLs only in missing dimension attributes.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q10_false_missing_variant, 29% of attempts): Marked matched variants as `MISSING_VARIANT` instead of `MATCHED`. Check this explicitly before finalizing.
- Previous v3 failure warning (q10_nullified_v999, 7% of attempts): Nullified `variant_id` for call_id 9 instead of preserving `V999` from the fact table. Check this explicitly before finalizing.
- Previous v3 failure warning (q10_dropped_call9, 5% of attempts): Dropped the unmatched call_id 9 row despite the required left join. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 1 and end with last row key/value 9 for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

## Pass 2

### Query 1: `pass2.query1`

- Difficulty: `medium`
- Language: `sql`
- Primary failure family: `snowflake_traversal`

```text
Inner join across all four tables:
fact_calls -> sample_dim
fact_calls -> variant_dim -> gene_dim
Return: call_id, sample_id, tissue, gene_symbol, impact, genotype
Sort by call_id ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 6 data rows and exactly these columns in this order: call_id, sample_id, tissue, gene_symbol, impact, genotype.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by call_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_id; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses call_id; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q1_kept_call6, 93% of attempts): Kept call_id 6 / V5 even though the complete four-table inner join should remove it. Check this explicitly before finalizing.
- Previous v3 failure warning (q1_dropped_valid_calls, 55% of attempts): Dropped one or more valid complete-chain calls. Check this explicitly before finalizing.
- Previous v3 failure warning (q1_kept_call8, 52% of attempts): Kept call_id 8 / S999 even though the sample dimension is missing. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 1 and end with last row key/value 7 for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 2: `pass2.query2`

- Difficulty: `medium`
- Language: `sql`
- Primary failure family: `outer_join_coverage`

```text
Left join fact_calls across the full snowflake.
Return: call_id, sample_id, plant_line_id, tissue, variant_id, gene_symbol
Keep all fact rows.
Sort by call_id ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 9 data rows and exactly these columns in this order: call_id, sample_id, plant_line_id, tissue, variant_id, gene_symbol.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by call_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_id; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses call_id; follow the prompt's sort direction and tie-breakers exactly.
- Fact-preserving logic must keep every fact_calls row unless the prompt later applies an explicit filter; preserve fact-side keys such as V999/S999 and put NULLs only in missing dimension attributes.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q2_wrong_gene_mapping, 43% of attempts): Mapped matched variants to the wrong gene symbol or dropped a valid gene symbol. Check this explicitly before finalizing.
- Previous v3 failure warning (q2_bad_sample_nulls, 33% of attempts): Filled sample attributes for S999 instead of leaving dimension fields null. Check this explicitly before finalizing.
- Previous v3 failure warning (q2_bad_chain_nulls, 10% of attempts): Failed to leave gene_symbol null for incomplete V5/V999 chain rows. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 1 and end with last row key/value 9 for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 3: `pass2.query3`

- Difficulty: `medium`
- Language: `sql`
- Primary failure family: `outer_join_coverage`

```text
Perform a FULL OUTER JOIN between fact_calls and variant_dim on variant_id.
Return:
- variant_id as the coalesced key
- call_id
- sample_id
- impact
Sort by variant_id ascending, then call_id ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 10 data rows and exactly these columns in this order: variant_id, call_id, sample_id, impact.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by variant_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_id; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses variant_id, call_id; follow the prompt's sort direction and tie-breakers exactly.
- FULL OUTER JOIN must include matched rows, fact-only V999, and variant-only V6; use a coalesced variant_id key and do not drop either side-only row.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q3_wrong_impact, 50% of attempts): Assigned an incorrect impact value in the full outer result. Check this explicitly before finalizing.
- Previous v3 failure warning (q3_missing_v999, 40% of attempts): Dropped the fact-only V999 row from the full outer join. Check this explicitly before finalizing.
- Previous v3 failure warning (q3_missing_v6, 38% of attempts): Dropped the variant-only V6 row from the full outer join. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'V1' and end with last row key/value 'V999' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 4: `pass2.query4`

- Difficulty: `medium`
- Language: `sql`
- Primary failure family: `aggregation_numeric`

```text
Inner join fact_calls to sample_dim and variant_dim.
Count calls by condition and impact, and compute average qual.
Return: condition, impact, call_count, avg_qual
Sort by condition ascending, then impact ascending.
Round avg_qual to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 6 data rows and exactly these columns in this order: condition, impact, call_count, avg_qual.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by condition, impact; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_count, avg_qual; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses condition, impact; follow the prompt's sort direction and tie-breakers exactly.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Quality statistics must use qual values from the correctly joined/filter-preserved fact rows; compute min/max/mean after the row boundary is correct.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q4_avg_wrong, 90% of attempts): Computed one or more condition-impact average qualities from the wrong row set. Check this explicitly before finalizing.
- Previous v3 failure warning (q4_wrong_group_set, 88% of attempts): Returned the wrong condition-impact group set. Check this explicitly before finalizing.
- Previous v3 failure warning (q4_control_high_wrong, 86% of attempts): Miscomputed the control/high bucket, especially the two-call count and average. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'control' and end with last row key/value 'high_light' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 5: `pass2.query5`

- Difficulty: `medium`
- Language: `sql`
- Primary failure family: `aggregation_numeric`

```text
Inner join fact_calls to variant_dim and gene_dim.
Compute VAF = alt_reads / total_reads.
Return average VAF and maximum qual by gene_symbol.
Columns: gene_symbol, avg_vaf, max_qual
Sort by avg_vaf descending, then gene_symbol ascending.
Round avg_vaf to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 3 data rows and exactly these columns in this order: gene_symbol, avg_vaf, max_qual.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by gene_symbol; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: avg_vaf, max_qual; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses avg_vaf, gene_symbol; follow the prompt's sort direction and tie-breakers exactly.
- For a fact -> variant -> gene chain without sample_dim, drop V5/G999 and V999, but do not drop call_id 8 solely because S999 is not in sample_dim.
- Quality statistics must use qual values from the correctly joined/filter-preserved fact rows; compute min/max/mean after the row boundary is correct.
- Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.
- Use alt_reads from the filtered fact rows; include zero alt_reads when the row satisfies the filter, especially for high-impact/reference boundary cases.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q5_wrong_vaf, 100% of attempts): Computed average VAF from the wrong numerator/denominator or row set. Check this explicitly before finalizing.
- Previous v3 failure warning (q5_wrong_max_qual, 93% of attempts): Computed max_qual from the wrong rows. Check this explicitly before finalizing.
- Previous v3 failure warning (q5_leaked_unmatched_gene, 29% of attempts): Included incomplete-chain or non-gold genes such as NDHT/PGR1B. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'PGR5' and end with last row key/value 'NDHK' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 6: `pass2.query6`

- Difficulty: `medium`
- Language: `sql`
- Primary failure family: `snowflake_traversal`

```text
Use complete inner joins across all four tables.
For each tissue, compute:
- distinct_genes
- avg_expr_ndhb
Return: tissue, distinct_genes, avg_expr_ndhb
Sort by tissue ascending.
Round avg_expr_ndhb to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 2 data rows and exactly these columns in this order: tissue, distinct_genes, avg_expr_ndhb.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by tissue; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: distinct_genes, avg_expr_ndhb; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses tissue; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- For distinct counts, count distinct values only after the required joins and filters have been applied.
- Expression summaries must use the marker column named in the prompt and the correct grain: sample-only tasks average samples, joined tasks average the joined sample-call rows.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q6_wrong_distinct_genes, 83% of attempts): Computed distinct gene counts from the wrong join grain. Check this explicitly before finalizing.
- Previous v3 failure warning (q6_wrong_expr_average, 74% of attempts): Computed avg_expr_ndhb over samples instead of complete-chain joined calls. Check this explicitly before finalizing.
- Previous v3 failure warning (q6_included_root, 50% of attempts): Included root/S5 even though complete inner joins should remove it. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'mature_leaf' and end with last row key/value 'young_leaf' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 7: `pass2.query7`

- Difficulty: `medium`
- Language: `sql`
- Primary failure family: `outer_join_coverage`

```text
Use sample_dim as the preserving table.
For each sample, count high-impact calls and compute average alt_reads among only high-impact calls.
Return: sample_id, tissue, high_impact_call_count, avg_alt_reads_high
Include samples with zero high-impact calls.
Sort by high_impact_call_count descending, then sample_id ascending.
Round avg_alt_reads_high to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 5 data rows and exactly these columns in this order: sample_id, tissue, high_impact_call_count, avg_alt_reads_high.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by sample_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: high_impact_call_count, avg_alt_reads_high; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses high_impact_call_count, sample_id; follow the prompt's sort direction and tie-breakers exactly.
- sample_dim is the preserving table: include S1-S5, keep zero-count samples such as S5, and never include orphan fact key S999 as a sample row.
- For sample-preserving output, produce one row per sample_dim sample; zero-call or zero-burden samples still need count 0 and NULL/rounded derived values as requested.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Use alt_reads from the filtered fact rows; include zero alt_reads when the row satisfies the filter, especially for high-impact/reference boundary cases.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q7_missed_zero_alt_high, 100% of attempts): Missed the zero-alt high-impact call for S4. Check this explicitly before finalizing.
- Previous v3 failure warning (q7_wrong_alt_average, 100% of attempts): Averaged alt_reads over the wrong subset of rows. Check this explicitly before finalizing.
- Previous v3 failure warning (q7_counted_non_high, 57% of attempts): Counted non-high or incomplete rows as high-impact calls, often inflating S3. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'S1' and end with last row key/value 'S5' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 8: `pass2.query8`

- Difficulty: `medium`
- Language: `sql`
- Primary failure family: `aggregation_numeric`

```text
Inner join fact_calls to variant_dim and gene_dim.
For each gene_symbol, compute:
- total_alt_reads
- avg_qual
- max_alt_reads
Return: gene_symbol, total_alt_reads, avg_qual, max_alt_reads
Sort by total_alt_reads descending, then gene_symbol ascending.
Round avg_qual to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 3 data rows and exactly these columns in this order: gene_symbol, total_alt_reads, avg_qual, max_alt_reads.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by gene_symbol; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: total_alt_reads, avg_qual, max_alt_reads; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses total_alt_reads, gene_symbol; follow the prompt's sort direction and tie-breakers exactly.
- For a fact -> variant -> gene chain without sample_dim, drop V5/G999 and V999, but do not drop call_id 8 solely because S999 is not in sample_dim.
- Quality statistics must use qual values from the correctly joined/filter-preserved fact rows; compute min/max/mean after the row boundary is correct.
- Use alt_reads from the filtered fact rows; include zero alt_reads when the row satisfies the filter, especially for high-impact/reference boundary cases.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q8_wrong_avg_qual, 93% of attempts): Computed avg_qual from the wrong row set. Check this explicitly before finalizing.
- Previous v3 failure warning (q8_wrong_alt_total, 79% of attempts): Computed total_alt_reads from the wrong row set. Check this explicitly before finalizing.
- Previous v3 failure warning (q8_dropped_gene, 21% of attempts): Dropped one of the expected gene symbols. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'NDHB' and end with last row key/value 'PGR5' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 9: `pass2.query9`

- Difficulty: `medium`
- Language: `sql`
- Primary failure family: `decision_support`

```text
Decision-oriented pathway summary.
Use complete inner joins across all four tables.
For each condition and pathway, compute:
- call_count
- mean_vaf where VAF = alt_reads / total_reads
- distinct_samples
Return: condition, pathway, call_count, mean_vaf, distinct_samples
Sort by condition ascending, then pathway ascending.
Round mean_vaf to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 3 data rows and exactly these columns in this order: condition, pathway, call_count, mean_vaf, distinct_samples.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by condition, pathway; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_count, mean_vaf, distinct_samples; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses condition, pathway; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.
- Use alt_reads from the filtered fact rows; include zero alt_reads when the row satisfies the filter, especially for high-impact/reference boundary cases.
- For distinct counts, count distinct values only after the required joins and filters have been applied.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q9_wrong_counts, 100% of attempts): Miscomputed call_count or distinct_samples. Check this explicitly before finalizing.
- Previous v3 failure warning (q9_wrong_vaf, 100% of attempts): Computed mean VAF from the wrong row set. Check this explicitly before finalizing.
- Previous v3 failure warning (q9_wrong_group_set, 81% of attempts): Returned the wrong condition-pathway group set. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'control' and end with last row key/value 'high_light' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 10: `pass2.query10`

- Difficulty: `medium`
- Language: `sql`
- Primary failure family: `decision_support`

```text
Coverage screen with sample_dim as the preserving table.
Left join sample_dim to fact_calls, then to variant_dim and gene_dim.
For each sample, compute:
- total_fact_calls
- complete_chain_calls
- incomplete_chain_calls
Return: sample_id, tissue, total_fact_calls, complete_chain_calls, incomplete_chain_calls
Sort by sample_id ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 5 data rows and exactly these columns in this order: sample_id, tissue, total_fact_calls, complete_chain_calls, incomplete_chain_calls.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by sample_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: total_fact_calls, complete_chain_calls, incomplete_chain_calls; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses sample_id; follow the prompt's sort direction and tie-breakers exactly.
- sample_dim is the preserving table: include S1-S5, keep zero-count samples such as S5, and never include orphan fact key S999 as a sample row.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q10_wrong_chain_counts, 86% of attempts): Misclassified complete vs incomplete chain calls. Check this explicitly before finalizing.
- Previous v3 failure warning (q10_wrong_total_calls, 21% of attempts): Miscomputed total fact calls per sample. Check this explicitly before finalizing.
- Previous v3 failure warning (q10_missing_s5, 17% of attempts): Dropped zero-call sample S5 from the sample-preserving coverage screen. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'S1' and end with last row key/value 'S5' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

## Pass 3

### Query 1: `pass3.query1`

- Difficulty: `hard`
- Language: `sql`
- Primary failure family: `join_key_integrity`

```text
Left join fact_calls across the full snowflake and classify each fact row into one join_status using this logic:
- COMPLETE_CHAIN: sample, variant, and gene all matched
- MISSING_SAMPLE: sample missing but variant and gene matched
- MISSING_GENE: variant matched but gene missing
- MISSING_VARIANT: variant missing
Return: call_id, sample_id, variant_id, join_status
Sort by call_id ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 9 data rows and exactly these columns in this order: call_id, sample_id, variant_id, join_status.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by call_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_id; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses call_id; follow the prompt's sort direction and tie-breakers exactly.
- Fact-preserving logic must keep every fact_calls row unless the prompt later applies an explicit filter; preserve fact-side keys such as V999/S999 and put NULLs only in missing dimension attributes.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q1_complete_chain_status_wrong, 43% of attempts): Misclassified one or more complete-chain calls. Check this explicitly before finalizing.
- Previous v3 failure warning (q1_call6_status_wrong, 33% of attempts): Misclassified call_id 6 / V5; it should be MISSING_GENE. Check this explicitly before finalizing.
- Previous v3 failure warning (q1_call8_status_wrong, 26% of attempts): Misclassified call_id 8 / S999; it should be MISSING_SAMPLE. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 1 and end with last row key/value 9 for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 2: `pass3.query2`

- Difficulty: `hard`
- Language: `sql`
- Primary failure family: `aggregation_numeric`

```text
Using only complete-chain matched rows, group by tissue and gene_symbol.
Compute:
- call_count
- sum_alt_reads
- avg_vaf where VAF = alt_reads / total_reads
- max_qual
Return: tissue, gene_symbol, call_count, sum_alt_reads, avg_vaf, max_qual
Sort by tissue ascending, then gene_symbol ascending.
Round avg_vaf to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 4 data rows and exactly these columns in this order: tissue, gene_symbol, call_count, sum_alt_reads, avg_vaf, max_qual.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by tissue, gene_symbol; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_count, sum_alt_reads, avg_vaf, max_qual; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses tissue, gene_symbol; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Quality statistics must use qual values from the correctly joined/filter-preserved fact rows; compute min/max/mean after the row boundary is correct.
- Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.
- Use alt_reads from the filtered fact rows; include zero alt_reads when the row satisfies the filter, especially for high-impact/reference boundary cases.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q2_wrong_counts_or_alt, 86% of attempts): Miscomputed call_count or sum_alt_reads. Check this explicitly before finalizing.
- Previous v3 failure warning (q2_wrong_vaf, 86% of attempts): Computed avg_vaf from the wrong numerator/denominator or row set. Check this explicitly before finalizing.
- Previous v3 failure warning (q2_wrong_group_set, 74% of attempts): Returned the wrong tissue-gene group set for complete-chain matched rows. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'mature_leaf' and end with last row key/value 'young_leaf' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 3: `pass3.query3`

- Difficulty: `hard`
- Language: `sql`
- Primary failure family: `orphan_key_audit`

```text
Start from gene_dim and left join to variant_dim, then fact_calls.
Return one row per gene with:
gene_symbol, pathway, observed_call_count, total_alt_reads
Count matched fact rows per gene.
Include genes with zero observed calls.
Sort by observed_call_count descending, then gene_symbol ascending.
Round total_alt_reads to 3 decimals if needed.

Task-specific guidance for v4:
- Expected output contract: return exactly 5 data rows and exactly these columns in this order: gene_symbol, pathway, observed_call_count, total_alt_reads.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by gene_symbol; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: observed_call_count, total_alt_reads; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses observed_call_count, gene_symbol; follow the prompt's sort direction and tie-breakers exactly.
- gene_dim is the preserving gene table: include real genes from gene_dim, including genes with zero observed calls, but do not invent an output gene for orphan variant gene_id G999.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Use alt_reads from the filtered fact rows; include zero alt_reads when the row satisfies the filter, especially for high-impact/reference boundary cases.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q3_wrong_observed_count, 98% of attempts): Miscomputed observed_call_count for one or more genes. Check this explicitly before finalizing.
- Previous v3 failure warning (q3_wrong_total_alt, 90% of attempts): Miscomputed total_alt_reads for one or more genes. Check this explicitly before finalizing.
- Previous v3 failure warning (q3_leaked_unknown_gene, 24% of attempts): Included a non-gold gene such as G999. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'NDHB' and end with last row key/value 'PGR1B' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 4: `pass3.query4`

- Difficulty: `hard`
- Language: `sql`
- Primary failure family: `aggregation_numeric`

```text
Inner join fact_calls to sample_dim and variant_dim.
Filter to impact = 'high'.
For each condition, compute:
- high_impact_call_count
- avg_qual
- avg_alt_reads
Return: condition, high_impact_call_count, avg_qual, avg_alt_reads
Sort by condition ascending.
Round decimal outputs to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 2 data rows and exactly these columns in this order: condition, high_impact_call_count, avg_qual, avg_alt_reads.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by condition; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: high_impact_call_count, avg_qual, avg_alt_reads; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses condition; follow the prompt's sort direction and tie-breakers exactly.
- Apply the high-impact filter only to rows whose joined variant_dim impact is exactly 'high'.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Quality statistics must use qual values from the correctly joined/filter-preserved fact rows; compute min/max/mean after the row boundary is correct.
- Use alt_reads from the filtered fact rows; include zero alt_reads when the row satisfies the filter, especially for high-impact/reference boundary cases.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q4_control_bucket_wrong, 100% of attempts): Miscomputed the control high-impact bucket. Check this explicitly before finalizing.
- Previous v3 failure warning (q4_wrong_group_set, 88% of attempts): Returned the wrong set of high-impact condition rows. Check this explicitly before finalizing.
- Previous v3 failure warning (q4_included_non_high_condition, 83% of attempts): Included a condition that has no high-impact joined calls, usually drought. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'control' and end with last row key/value 'high_light' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 5: `pass3.query5`

- Difficulty: `hard`
- Language: `sql`
- Primary failure family: `outer_join_coverage`

```text
Using sample_dim as the preserving table, count genotype classes per sample.
Compute:
- heterozygous_calls where genotype = '0/1'
- homozygous_alt_calls where genotype = '1/1'
- mean_nonref_qual over only non-reference calls where genotype in ('0/1','1/1')
Return: sample_id, heterozygous_calls, homozygous_alt_calls, mean_nonref_qual
Include samples with zero calls.
Sort by sample_id ascending.
Round mean_nonref_qual to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 5 data rows and exactly these columns in this order: sample_id, heterozygous_calls, homozygous_alt_calls, mean_nonref_qual.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by sample_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: heterozygous_calls, homozygous_alt_calls, mean_nonref_qual; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses sample_id; follow the prompt's sort direction and tie-breakers exactly.
- sample_dim is the preserving table: include S1-S5, keep zero-count samples such as S5, and never include orphan fact key S999 as a sample row.
- For sample-preserving output, produce one row per sample_dim sample; zero-call or zero-burden samples still need count 0 and NULL/rounded derived values as requested.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q5_s2_nonref_wrong, 86% of attempts): Miscomputed S2 heterozygous calls or non-reference mean quality. Check this explicitly before finalizing.
- Previous v3 failure warning (q5_counted_reference_or_wrong_class, 86% of attempts): Counted reference calls or put genotypes into the wrong class. Check this explicitly before finalizing.
- Previous v3 failure warning (q5_included_s999, 29% of attempts): Included S999 even though sample_dim is the preserving table. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'S1' and end with last row key/value 'S5' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 6: `pass3.query6`

- Difficulty: `hard`
- Language: `sql`
- Primary failure family: `ranking_and_priority`

```text
Using only complete-chain matched rows, compute total_alt_reads and avg_vaf by tissue and gene_symbol.
Within each tissue, rank genes by total_alt_reads descending using dense rank.
Return: tissue, gene_symbol, total_alt_reads, avg_vaf, rank_in_tissue
Sort by tissue ascending, then rank_in_tissue ascending, then gene_symbol ascending.
Round avg_vaf to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 4 data rows and exactly these columns in this order: tissue, gene_symbol, total_alt_reads, avg_vaf, rank_in_tissue.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by tissue; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: total_alt_reads, avg_vaf, rank_in_tissue; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses tissue, rank_in_tissue, gene_symbol; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.
- Use alt_reads from the filtered fact rows; include zero alt_reads when the row satisfies the filter, especially for high-impact/reference boundary cases.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q6_wrong_totals_or_vaf, 79% of attempts): Miscomputed total_alt_reads or avg_vaf. Check this explicitly before finalizing.
- Previous v3 failure warning (q6_wrong_group_set, 76% of attempts): Returned the wrong tissue-gene group set before ranking. Check this explicitly before finalizing.
- Previous v3 failure warning (q6_leaked_root_or_incomplete, 50% of attempts): Leaked root, incomplete-chain, or non-gold genes into the ranking. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'mature_leaf' and end with last row key/value 'young_leaf' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 7: `pass3.query7`

- Difficulty: `hard`
- Language: `sql`
- Primary failure family: `orphan_key_audit`

```text
Find unused dimension rows across both branches using anti-join logic.
Return: object_type, object_id, reason
Use these rules:
- sample_dim rows with no fact_calls => no_fact_calls
- variant_dim rows with no fact_calls => no_fact_calls
- gene_dim rows with variants but no fact_calls through those variants => no_fact_calls_through_variants
- gene_dim rows with no variants at all => no_variants_attached
Sort by object_type ascending, then object_id ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 4 data rows and exactly these columns in this order: object_type, object_id, reason.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by object_type; do not duplicate, omit, or relabel those keys.
- Sort-order scoring uses object_type, object_id; follow the prompt's sort direction and tie-breakers exactly.
- Previous v3 failure warning (q7_object_type_labels_wrong, 93% of attempts): Used dimension-table labels such as gene_dim/sample_dim instead of gene/sample/variant. Check this explicitly before finalizing.
- Previous v3 failure warning (q7_missing_expected_object, 93% of attempts): Dropped or mislabeled one of G4, G5, S5, or V6 in the anti-join audit. Check this explicitly before finalizing.
- Previous v3 failure warning (q7_g4_reason_wrong, 74% of attempts): Assigned the wrong reason to G4; it should be no_fact_calls_through_variants. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'gene' and end with last row key/value 'variant' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 8: `pass3.query8`

- Difficulty: `hard`
- Language: `sql`
- Primary failure family: `decision_support`

```text
Using complete-chain matched rows only, filter to non-reference calls where genotype <> '0/0'.
Group by condition and gene_role.
Return: condition, gene_role, non_reference_call_count, mean_vaf
Sort by condition ascending, then gene_role ascending.
Round mean_vaf to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 3 data rows and exactly these columns in this order: condition, gene_role, non_reference_call_count, mean_vaf.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by condition, gene_role; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: non_reference_call_count, mean_vaf; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses condition, gene_role; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Apply the non-reference filter exactly as genotype <> '0/0'; do not count 0/0 reference calls in non-reference summaries.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q8_wrong_group_set, 83% of attempts): Returned the wrong condition-gene_role groups. Check this explicitly before finalizing.
- Previous v3 failure warning (q8_leaked_reference_or_incomplete, 83% of attempts): Leaked reference calls, incomplete chains, or non-gold roles into the non-reference summary. Check this explicitly before finalizing.
- Previous v3 failure warning (q8_wrong_vaf, 83% of attempts): Computed mean_vaf from the wrong row set. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'control' and end with last row key/value 'high_light' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 9: `pass3.query9`

- Difficulty: `hard`
- Language: `sql`
- Primary failure family: `failure_family_audit`

```text
Failure-family audit for operational review.
Left join fact_calls across the full snowflake.
Create condition_group = condition when sample matched, else 'UNMATCHED_SAMPLE'.
For each condition_group, compute:
- complete_chain_calls
- missing_sample_calls
- missing_variant_calls
- missing_gene_calls
Return: condition_group, complete_chain_calls, missing_sample_calls, missing_variant_calls, missing_gene_calls
Sort by condition_group ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 4 data rows and exactly these columns in this order: condition_group, complete_chain_calls, missing_sample_calls, missing_variant_calls, missing_gene_calls.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by condition_group; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: complete_chain_calls, missing_sample_calls, missing_variant_calls, missing_gene_calls; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses condition_group; follow the prompt's sort direction and tie-breakers exactly.
- Fact-preserving logic must keep every fact_calls row unless the prompt later applies an explicit filter; preserve fact-side keys such as V999/S999 and put NULLs only in missing dimension attributes.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- For ratios/shares, use the exact denominator in the prompt for each row; calculate all component shares first, then derive imbalance or ratios from those components.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q9_wrong_missing_status_counts, 100% of attempts): Miscomputed missing_sample, missing_variant, or missing_gene counts. Check this explicitly before finalizing.
- Previous v3 failure warning (q9_wrong_complete_counts, 100% of attempts): Miscomputed complete_chain_calls by condition group. Check this explicitly before finalizing.
- Previous v3 failure warning (q9_missing_condition_group, 12% of attempts): Dropped one of UNMATCHED_SAMPLE, control, drought, or high_light. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'UNMATCHED_SAMPLE' and end with last row key/value 'high_light' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

### Query 10: `pass3.query10`

- Difficulty: `hard`
- Language: `sql`
- Primary failure family: `decision_support`

```text
Decision-priority candidate table.
Using complete-chain matched rows only, filter to non-reference calls where genotype <> '0/0'.
Map matched expression counts using:
- NDHB -> expr_ndhb
- NDHK -> expr_ndhk
- PGR5 -> expr_pgr5
For each gene_symbol, compute:
- non_reference_calls
- avg_vaf
- avg_matched_expr
- decision_score = avg_vaf * avg_matched_expr
Return: gene_symbol, non_reference_calls, avg_vaf, avg_matched_expr, decision_score
Sort by decision_score descending, then gene_symbol ascending.
Round decimals to 3 places.

Task-specific guidance for v4:
- Expected output contract: return exactly 3 data rows and exactly these columns in this order: gene_symbol, non_reference_calls, avg_vaf, avg_matched_expr, decision_score.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by gene_symbol; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: non_reference_calls, avg_vaf, avg_matched_expr, decision_score; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses decision_score, gene_symbol; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Apply the non-reference filter exactly as genotype <> '0/0'; do not count 0/0 reference calls in non-reference summaries.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.
- Matched expression must use gene_symbol mapping NDHB -> expr_ndhb, NDHK -> expr_ndhk, PGR5 -> expr_pgr5, and NULL for all other genes; do not average the wrong marker column.
- Expression summaries must use the marker column named in the prompt and the correct grain: sample-only tasks average samples, joined tasks average the joined sample-call rows.
- Compute composite decision/burden/pressure scores from the already-correct intermediate metrics; do not recompute them from rounded display values unless the prompt explicitly says so.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q10_wrong_vaf, 100% of attempts): Computed avg_vaf from the wrong non-reference row set. Check this explicitly before finalizing.
- Previous v3 failure warning (q10_wrong_decision_score, 100% of attempts): Computed decision_score incorrectly from avg_vaf and matched expression. Check this explicitly before finalizing.
- Previous v3 failure warning (q10_wrong_expression, 76% of attempts): Mapped matched expression counts incorrectly. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'NDHB' and end with last row key/value 'NDHK' for the first returned column.
- For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.
```

## Pass 4

### Query 1: `pass4.query1`

- Difficulty: `extra_hard`
- Language: `python`
- Primary failure family: `audit_reconciliation`

```text
Using pandas, create a reconciliation summary with exactly these metrics:
- fact_rows_total
- complete_chain_rows
- fact_rows_missing_sample
- fact_rows_missing_variant
- fact_rows_missing_gene
- unused_samples
- unused_variants
- genes_with_no_variants
Return: metric, value
Preserve this exact row order.

Task-specific guidance for v4:
- Expected output contract: return exactly 8 data rows and exactly these columns in this order: metric, value.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by metric; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: value; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses metric; follow the prompt's sort direction and tie-breakers exactly.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q1_unused_dimension_wrong, 79% of attempts): Miscounted unused samples, unused variants, or genes with no variants. Check this explicitly before finalizing.
- Previous v3 failure warning (q1_missing_status_wrong, 67% of attempts): Miscounted one or more missing sample/variant/gene fact-row categories. Check this explicitly before finalizing.
- Previous v3 failure warning (q1_complete_chain_wrong, 52% of attempts): Miscounted complete_chain_rows in the reconciliation summary. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'fact_rows_total' and end with last row key/value 'genes_with_no_variants' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 2: `pass4.query2`

- Difficulty: `extra_hard`
- Language: `python`
- Primary failure family: `aggregation_numeric`

```text
Using pandas and complete-chain matched rows only, group by condition and pathway.
Compute:
- call_count
- total_alt_reads
- mean_qual
- avg_expr_ndhb
Return: condition, pathway, call_count, total_alt_reads, mean_qual, avg_expr_ndhb
Sort by condition ascending, then total_alt_reads descending, then pathway ascending.
Round decimal outputs to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 3 data rows and exactly these columns in this order: condition, pathway, call_count, total_alt_reads, mean_qual, avg_expr_ndhb.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by condition, pathway; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_count, total_alt_reads, mean_qual, avg_expr_ndhb; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses condition, total_alt_reads, pathway; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Quality statistics must use qual values from the correctly joined/filter-preserved fact rows; compute min/max/mean after the row boundary is correct.
- Use alt_reads from the filtered fact rows; include zero alt_reads when the row satisfies the filter, especially for high-impact/reference boundary cases.
- Expression summaries must use the marker column named in the prompt and the correct grain: sample-only tasks average samples, joined tasks average the joined sample-call rows.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q2_wrong_counts_or_alt, 100% of attempts): Miscomputed call_count or total_alt_reads. Check this explicitly before finalizing.
- Previous v3 failure warning (q2_wrong_quality, 100% of attempts): Miscomputed mean_qual. Check this explicitly before finalizing.
- Previous v3 failure warning (q2_wrong_expression, 100% of attempts): Mapped or averaged expr_ndhb incorrectly. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'control' and end with last row key/value 'high_light' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 3: `pass4.query3`

- Difficulty: `extra_hard`
- Language: `python`
- Primary failure family: `decision_support`

```text
Using pandas and complete-chain non-reference rows only where genotype <> '0/0', group by batch and gene_role.
Compute:
- non_reference_calls
- avg_qual
- max_vaf
- mean_expr_pgr5
Return: batch, gene_role, non_reference_calls, avg_qual, max_vaf, mean_expr_pgr5
Sort by batch ascending, then gene_role ascending.
Round decimal outputs to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 2 data rows and exactly these columns in this order: batch, gene_role, non_reference_calls, avg_qual, max_vaf, mean_expr_pgr5.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by batch, gene_role; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: non_reference_calls, avg_qual, max_vaf, mean_expr_pgr5; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses batch, gene_role; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Apply the non-reference filter exactly as genotype <> '0/0'; do not count 0/0 reference calls in non-reference summaries.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Quality statistics must use qual values from the correctly joined/filter-preserved fact rows; compute min/max/mean after the row boundary is correct.
- Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.
- Expression summaries must use the marker column named in the prompt and the correct grain: sample-only tasks average samples, joined tasks average the joined sample-call rows.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q3_wrong_counts_or_quality, 86% of attempts): Miscomputed non_reference_calls or avg_qual. Check this explicitly before finalizing.
- Previous v3 failure warning (q3_wrong_group_set, 81% of attempts): Returned the wrong batch-gene_role group set. Check this explicitly before finalizing.
- Previous v3 failure warning (q3_leaked_extra_group, 81% of attempts): Leaked reference, incomplete-chain, or non-gold batch/role groups. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'B1' and end with last row key/value 'B2' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 4: `pass4.query4`

- Difficulty: `extra_hard`
- Language: `python`
- Primary failure family: `decision_support`

```text
Using pandas and complete-chain matched rows only, find genes observed in both:
- control
- at least one non-control condition
Return:
- gene_symbol
- control_calls
- non_control_calls
- total_alt_reads
Sort by total_alt_reads descending, then gene_symbol ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 1 data rows and exactly these columns in this order: gene_symbol, control_calls, non_control_calls, total_alt_reads.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by gene_symbol; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: control_calls, non_control_calls, total_alt_reads; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses total_alt_reads, gene_symbol; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Use alt_reads from the filtered fact rows; include zero alt_reads when the row satisfies the filter, especially for high-impact/reference boundary cases.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q4_wrong_gene_set, 100% of attempts): Returned the wrong shared gene set. Check this explicitly before finalizing.
- Previous v3 failure warning (q4_leaked_non_shared_gene, 100% of attempts): Included genes that are not observed in both control and non-control complete-chain rows. Check this explicitly before finalizing.
- Previous v3 failure warning (q4_wrong_counts, 48% of attempts): Miscomputed control_calls or non_control_calls. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'NDHB' and end with last row key/value 'NDHB' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 5: `pass4.query5`

- Difficulty: `extra_hard`
- Language: `python`
- Primary failure family: `expression_mapping`

```text
Using pandas, start from gene_dim and left join to variant_dim, then fact_calls, then sample_dim.
Return one row per gene with:
- gene_symbol
- variant_count
- call_count
- distinct_matched_sample_count
- distinct_tissue_count
- avg_matched_expression
For distinct_matched_sample_count, count only sample_dim matches and exclude orphan fact sample keys.
For avg_matched_expression, use the matched expression mapping from the instructions and average across matched sample-call rows only.
Sort by gene_symbol ascending.
Round avg_matched_expression to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 5 data rows and exactly these columns in this order: gene_symbol, variant_count, call_count, distinct_matched_sample_count, distinct_tissue_count, avg_matched_expression.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by gene_symbol; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: variant_count, call_count, distinct_matched_sample_count, distinct_tissue_count, avg_matched_expression; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses gene_symbol; follow the prompt's sort direction and tie-breakers exactly.
- gene_dim is the preserving gene table: include real genes from gene_dim, including genes with zero observed calls, but do not invent an output gene for orphan variant gene_id G999.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- For distinct counts, count distinct values only after the required joins and filters have been applied.
- Matched expression must use gene_symbol mapping NDHB -> expr_ndhb, NDHK -> expr_ndhk, PGR5 -> expr_pgr5, and NULL for all other genes; do not average the wrong marker column.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q5_wrong_sample_or_tissue_count, 88% of attempts): Miscomputed distinct matched sample or tissue counts. Check this explicitly before finalizing.
- Previous v3 failure warning (q5_wrong_expression, 88% of attempts): Mapped or averaged matched expression incorrectly. Check this explicitly before finalizing.
- Previous v3 failure warning (q5_wrong_variant_or_call_count, 81% of attempts): Miscomputed variant_count or call_count. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'NDHB' and end with last row key/value 'PGR5' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 6: `pass4.query6`

- Difficulty: `extra_hard`
- Language: `python`
- Primary failure family: `decision_support`

```text
Using pandas, compute sample-level burden.
Use complete-chain matched rows only, filter to non-reference calls where genotype <> '0/0' and impact IN ('high', 'moderate').
For each sample in sample_dim, compute:
- burden_genes = count of distinct genes meeting that rule
- mean_log2_marker_expr = mean(log2(expr_ndhb+1), log2(expr_pgr5+1), log2(expr_ndhk+1))
Return: sample_id, tissue, burden_genes, mean_log2_marker_expr
Include samples with zero burden.
Sort by burden_genes descending, then sample_id ascending.
Round mean_log2_marker_expr to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 5 data rows and exactly these columns in this order: sample_id, tissue, burden_genes, mean_log2_marker_expr.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by sample_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: burden_genes, mean_log2_marker_expr; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses burden_genes, sample_id; follow the prompt's sort direction and tie-breakers exactly.
- sample_dim is the preserving table: include S1-S5, keep zero-count samples such as S5, and never include orphan fact key S999 as a sample row.
- For sample-preserving output, produce one row per sample_dim sample; zero-call or zero-burden samples still need count 0 and NULL/rounded derived values as requested.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Apply the non-reference filter exactly as genotype <> '0/0'; do not count 0/0 reference calls in non-reference summaries.
- For high/moderate burden filters, include only joined variants with impact exactly 'high' or 'moderate'; exclude low, modifier, missing, and unmatched variants.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- For distinct counts, count distinct values only after the required joins and filters have been applied.
- Expression summaries must use the marker column named in the prompt and the correct grain: sample-only tasks average samples, joined tasks average the joined sample-call rows.
- Use numpy.log2(x + 1) or SQL-equivalent log2(x + 1) exactly; apply +1 before the log transform and round only the final displayed value.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q6_wrong_log2_expr, 100% of attempts): Miscomputed mean_log2_marker_expr. Check this explicitly before finalizing.
- Previous v3 failure warning (q6_wrong_burden, 98% of attempts): Miscomputed burden_genes. Check this explicitly before finalizing.
- Previous v3 failure warning (q6_missing_sample, 45% of attempts): Dropped one or more sample_dim rows, usually S5. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'S1' and end with last row key/value 'S5' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 7: `pass4.query7`

- Difficulty: `extra_hard`
- Language: `python`
- Primary failure family: `orphan_key_audit`

```text
Using pandas, build a single orphan-key report using concat/union-style logic.
Return: source_table, key_value, orphan_type
Include:
- fact_calls.sample_id values missing in sample_dim
- fact_calls.variant_id values missing in variant_dim
- variant_dim.gene_id values missing in gene_dim
- sample_dim.sample_id rows unused by fact_calls
- variant_dim.variant_id rows unused by fact_calls
- gene_dim.gene_id rows with no variants attached
Sort by source_table ascending, then key_value ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 6 data rows and exactly these columns in this order: source_table, key_value, orphan_type.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by source_table; do not duplicate, omit, or relabel those keys.
- Sort-order scoring uses source_table, key_value; follow the prompt's sort direction and tie-breakers exactly.
- Previous v3 failure warning (q7_wrong_orphan_row_set, 100% of attempts): Returned the wrong orphan-key row set. Check this explicitly before finalizing.
- Previous v3 failure warning (q7_wrong_source_table, 100% of attempts): Used imprecise source_table labels such as fact_calls instead of fact_calls.sample_id or fact_calls.variant_id. Check this explicitly before finalizing.
- Previous v3 failure warning (q7_wrong_orphan_type, 100% of attempts): Returned incorrect orphan_type labels. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'fact_calls.sample_id' and end with last row key/value 'variant_dim.variant_id' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 8: `pass4.query8`

- Difficulty: `extra_hard`
- Language: `python`
- Primary failure family: `presentation_table`

```text
Using pandas, produce a final presentation table for all non-reference complete-chain calls only.
Filter to genotype <> '0/0'.
Return these columns in this exact order:
call_id, plant_line_id, tissue, condition, gene_symbol, pathway, variant_id, impact, genotype, alt_reads, total_reads, vaf, matched_expr_count, log2_matched_expr, qual
Use the matched expression mapping from the instructions.
Sort by:
condition ascending,
tissue ascending,
gene_symbol ascending,
variant_id ascending,
call_id ascending.
Round vaf and log2_matched_expr to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 4 data rows and exactly these columns in this order: call_id, plant_line_id, tissue, condition, gene_symbol, pathway, variant_id, impact, genotype, alt_reads, total_reads, vaf, matched_expr_count, log2_matched_expr, qual.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by call_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_id, alt_reads, total_reads, vaf, matched_expr_count, log2_matched_expr, qual; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses condition, tissue, gene_symbol, variant_id, call_id; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Apply the non-reference filter exactly as genotype <> '0/0'; do not count 0/0 reference calls in non-reference summaries.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.
- Use alt_reads from the filtered fact rows; include zero alt_reads when the row satisfies the filter, especially for high-impact/reference boundary cases.
- Matched expression must use gene_symbol mapping NDHB -> expr_ndhb, NDHK -> expr_ndhk, PGR5 -> expr_pgr5, and NULL for all other genes; do not average the wrong marker column.
- Use numpy.log2(x + 1) or SQL-equivalent log2(x + 1) exactly; apply +1 before the log transform and round only the final displayed value.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q8_wrong_row_set, 90% of attempts): Returned the wrong non-reference complete-chain call set. Check this explicitly before finalizing.
- Previous v3 failure warning (q8_wrong_expression_or_log, 90% of attempts): Mapped matched_expr_count or log2_matched_expr incorrectly. Check this explicitly before finalizing.
- Previous v3 failure warning (q8_leaked_reference_or_incomplete, 83% of attempts): Leaked reference, incomplete-chain, or orphan fact rows. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 4 and end with last row key/value 2 for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 9: `pass4.query9`

- Difficulty: `extra_hard`
- Language: `python`
- Primary failure family: `decision_support`

```text
Using pandas and complete-chain matched rows only, build a pathway reliability summary.
For each pathway, compute:
- call_count
- non_reference_rate where genotype <> '0/0'
- mean_vaf
- mean_matched_expr
Return: pathway, call_count, non_reference_rate, mean_vaf, mean_matched_expr
Sort by non_reference_rate descending, then pathway ascending.
Round decimals to 3 places.

Task-specific guidance for v4:
- Expected output contract: return exactly 2 data rows and exactly these columns in this order: pathway, call_count, non_reference_rate, mean_vaf, mean_matched_expr.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by pathway; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_count, non_reference_rate, mean_vaf, mean_matched_expr; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses non_reference_rate, pathway; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Apply the non-reference filter exactly as genotype <> '0/0'; do not count 0/0 reference calls in non-reference summaries.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.
- Matched expression must use gene_symbol mapping NDHB -> expr_ndhb, NDHK -> expr_ndhk, PGR5 -> expr_pgr5, and NULL for all other genes; do not average the wrong marker column.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q9_wrong_vaf, 100% of attempts): Miscomputed mean_vaf. Check this explicitly before finalizing.
- Previous v3 failure warning (q9_wrong_expression, 100% of attempts): Miscomputed mean_matched_expr. Check this explicitly before finalizing.
- Previous v3 failure warning (q9_wrong_counts_or_rate, 100% of attempts): Miscomputed call_count or non_reference_rate. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'cyclic_electron_flow' and end with last row key/value 'chloroplast_NDH_complex' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 10: `pass4.query10`

- Difficulty: `extra_hard`
- Language: `python`
- Primary failure family: `repairability_review`

```text
Using pandas, create a repairability audit over all fact rows.
Left join fact_calls across the full snowflake and classify join_status using:
- COMPLETE_CHAIN
- MISSING_SAMPLE
- MISSING_GENE
- MISSING_VARIANT
Set repairable_by_human = True only for MISSING_SAMPLE and MISSING_GENE.
Return: call_id, sample_id, variant_id, join_status, repairable_by_human
Sort by call_id ascending.

Task-specific guidance for v4:
- Expected output contract: return exactly 9 data rows and exactly these columns in this order: call_id, sample_id, variant_id, join_status, repairable_by_human.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by call_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_id; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses call_id; follow the prompt's sort direction and tie-breakers exactly.
- Fact-preserving logic must keep every fact_calls row unless the prompt later applies an explicit filter; preserve fact-side keys such as V999/S999 and put NULLs only in missing dimension attributes.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q10_repairable_flags_wrong, 57% of attempts): Set repairable_by_human incorrectly for complete-chain or missing rows. Check this explicitly before finalizing.
- Previous v3 failure warning (q10_call6_status_wrong, 40% of attempts): Misclassified call_id 6 / V5; it should be MISSING_GENE and repairable. Check this explicitly before finalizing.
- Previous v3 failure warning (q10_call9_repairability_wrong, 24% of attempts): Misclassified call_id 9 / V999 repairability; MISSING_VARIANT is not human-repairable. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 1 and end with last row key/value 9 for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

## Pass 5

### Query 1: `pass5.query1`

- Difficulty: `extreme_hard`
- Language: `python`
- Primary failure family: `expression_transform`

```text
Using pandas and sample_dim only, compute these expression features for every sample:
- log2_expr_ndhb = log2(expr_ndhb + 1)
- log2_expr_pgr5 = log2(expr_pgr5 + 1)
- log2_expr_ndhk = log2(expr_ndhk + 1)
- ndh_module_ratio = (expr_ndhb + expr_ndhk) / (expr_ndhb + expr_pgr5 + expr_ndhk)
Return: sample_id, tissue, log2_expr_ndhb, log2_expr_pgr5, log2_expr_ndhk, ndh_module_ratio
Sort by sample_id ascending.
Round all derived decimals to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 5 data rows and exactly these columns in this order: sample_id, tissue, log2_expr_ndhb, log2_expr_pgr5, log2_expr_ndhk, ndh_module_ratio.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by sample_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: log2_expr_ndhb, log2_expr_pgr5, log2_expr_ndhk, ndh_module_ratio; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses sample_id; follow the prompt's sort direction and tie-breakers exactly.
- Use sample_dim only: return the five real sample_dim rows S1-S5 exactly once; do not join to fact_calls or introduce S999.
- Expression summaries must use the marker column named in the prompt and the correct grain: sample-only tasks average samples, joined tasks average the joined sample-call rows.
- Use numpy.log2(x + 1) or SQL-equivalent log2(x + 1) exactly; apply +1 before the log transform and round only the final displayed value.
- For ratios/shares, use the exact denominator in the prompt for each row; calculate all component shares first, then derive imbalance or ratios from those components.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q1_wrong_log2_transform, 93% of attempts): Miscomputed one or more log2(expr + 1) marker features. Check this explicitly before finalizing.
- Previous v3 failure warning (q1_wrong_ratio, 93% of attempts): Miscomputed ndh_module_ratio. Check this explicitly before finalizing.
- Previous v3 failure warning (q1_wrong_sample_set, 24% of attempts): Returned the wrong sample set for sample_dim-only feature engineering. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'S1' and end with last row key/value 'S5' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 2: `pass5.query2`

- Difficulty: `extreme_hard`
- Language: `python`
- Primary failure family: `expression_transform`

```text
Using pandas and complete-chain matched rows only, map matched expression by gene_symbol using the standard mapping.
Compute:
- matched_expr_count
- log2_matched_expr = log2(matched_expr_count + 1)
- vaf = alt_reads / total_reads
- expr_weighted_vaf = vaf * log2_matched_expr
Return: call_id, gene_symbol, matched_expr_count, log2_matched_expr, vaf, expr_weighted_vaf
Sort by call_id ascending.
Round derived decimals to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 6 data rows and exactly these columns in this order: call_id, gene_symbol, matched_expr_count, log2_matched_expr, vaf, expr_weighted_vaf.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by call_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: call_id, matched_expr_count, log2_matched_expr, vaf, expr_weighted_vaf; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses call_id; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.
- Use alt_reads from the filtered fact rows; include zero alt_reads when the row satisfies the filter, especially for high-impact/reference boundary cases.
- Matched expression must use gene_symbol mapping NDHB -> expr_ndhb, NDHK -> expr_ndhk, PGR5 -> expr_pgr5, and NULL for all other genes; do not average the wrong marker column.
- Use numpy.log2(x + 1) or SQL-equivalent log2(x + 1) exactly; apply +1 before the log transform and round only the final displayed value.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q2_wrong_call_set, 100% of attempts): Returned the wrong complete-chain matched call set. Check this explicitly before finalizing.
- Previous v3 failure warning (q2_wrong_expr_mapping, 93% of attempts): Mapped matched_expr_count or log2_matched_expr incorrectly. Check this explicitly before finalizing.
- Previous v3 failure warning (q2_wrong_weighted_vaf, 93% of attempts): Miscomputed expr_weighted_vaf. Check this explicitly before finalizing.
- Previous v3 failure warning (q2_leaked_incomplete_or_orphan, 74% of attempts): Leaked incomplete-chain, orphan, or non-gold calls into the weighted VAF table. Check this explicitly before finalizing.
- Previous v3 failure warning (q2_wrong_vaf, 19% of attempts): Miscomputed VAF. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 1 and end with last row key/value 7 for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 3: `pass5.query3`

- Difficulty: `extreme_hard`
- Language: `python`
- Primary failure family: `statistical_summary`

```text
Using pandas and complete-chain matched rows only, group by condition and gene_symbol.
Compute:
- n_calls
- mean_matched_expr
- median_matched_expr
- pop_std_matched_expr using ddof=0
Return: condition, gene_symbol, n_calls, mean_matched_expr, median_matched_expr, pop_std_matched_expr
Sort by condition ascending, then gene_symbol ascending.
Round decimal outputs to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 4 data rows and exactly these columns in this order: condition, gene_symbol, n_calls, mean_matched_expr, median_matched_expr, pop_std_matched_expr.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by condition, gene_symbol; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: n_calls, mean_matched_expr, median_matched_expr, pop_std_matched_expr; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses condition, gene_symbol; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Matched expression must use gene_symbol mapping NDHB -> expr_ndhb, NDHK -> expr_ndhk, PGR5 -> expr_pgr5, and NULL for all other genes; do not average the wrong marker column.
- Use population statistics with ddof=0 for standard deviation, z-scores, and coefficient of variation; sample standard deviation will score wrong.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q3_wrong_mean_or_median, 93% of attempts): Miscomputed mean or median matched expression. Check this explicitly before finalizing.
- Previous v3 failure warning (q3_wrong_group_set, 90% of attempts): Returned the wrong condition-gene group set. Check this explicitly before finalizing.
- Previous v3 failure warning (q3_wrong_count, 88% of attempts): Miscomputed n_calls. Check this explicitly before finalizing.
- Previous v3 failure warning (q3_wrong_pop_std, 88% of attempts): Miscomputed population standard deviation. Check this explicitly before finalizing.
- Previous v3 failure warning (q3_leaked_incomplete_or_orphan, 83% of attempts): Leaked incomplete-chain, orphan, or non-gold groups into condition-gene statistics. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'control' and end with last row key/value 'high_light' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 4: `pass5.query4`

- Difficulty: `extreme_hard`
- Language: `python`
- Primary failure family: `statistical_summary`

```text
Using pandas and sample_dim only, define:
- stress_group = 'stress' for conditions high_light or drought
- stress_group = 'control' for condition control
For each gene marker (NDHB, NDHK, PGR5), compute:
- stress_mean_log2
- control_mean_log2
- delta_log2_stress_minus_control
Use:
- NDHB from expr_ndhb
- NDHK from expr_ndhk
- PGR5 from expr_pgr5
Apply log2(x + 1) before averaging.
Return: gene_symbol, stress_mean_log2, control_mean_log2, delta_log2_stress_minus_control
Sort by gene_symbol ascending.
Round decimal outputs to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 3 data rows and exactly these columns in this order: gene_symbol, stress_mean_log2, control_mean_log2, delta_log2_stress_minus_control.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by gene_symbol; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: stress_mean_log2, control_mean_log2, delta_log2_stress_minus_control; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses gene_symbol; follow the prompt's sort direction and tie-breakers exactly.
- Use sample_dim only: return the five real sample_dim rows S1-S5 exactly once; do not join to fact_calls or introduce S999.
- Expression summaries must use the marker column named in the prompt and the correct grain: sample-only tasks average samples, joined tasks average the joined sample-call rows.
- Use numpy.log2(x + 1) or SQL-equivalent log2(x + 1) exactly; apply +1 before the log transform and round only the final displayed value.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q4_wrong_stress_or_control_mean, 100% of attempts): Miscomputed stress/control mean log2 expression. Check this explicitly before finalizing.
- Previous v3 failure warning (q4_wrong_delta, 100% of attempts): Miscomputed stress-minus-control delta. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'NDHB' and end with last row key/value 'PGR5' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 5: `pass5.query5`

- Difficulty: `extreme_hard`
- Language: `python`
- Primary failure family: `decision_support`

```text
Using pandas and complete-chain non-reference rows only where genotype <> '0/0', group by pathway and tissue.
Compute:
- non_reference_calls
- mean_vaf
- mean_log2_matched_expr
- burden_score = sum(vaf * log2(matched_expr_count + 1))
Return: pathway, tissue, non_reference_calls, mean_vaf, mean_log2_matched_expr, burden_score
Sort by pathway ascending, then tissue ascending.
Round decimal outputs to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 2 data rows and exactly these columns in this order: pathway, tissue, non_reference_calls, mean_vaf, mean_log2_matched_expr, burden_score.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by pathway, tissue; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: non_reference_calls, mean_vaf, mean_log2_matched_expr, burden_score; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses pathway, tissue; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Apply the non-reference filter exactly as genotype <> '0/0'; do not count 0/0 reference calls in non-reference summaries.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.
- Matched expression must use gene_symbol mapping NDHB -> expr_ndhb, NDHK -> expr_ndhk, PGR5 -> expr_pgr5, and NULL for all other genes; do not average the wrong marker column.
- Use numpy.log2(x + 1) or SQL-equivalent log2(x + 1) exactly; apply +1 before the log transform and round only the final displayed value.
- Compute composite decision/burden/pressure scores from the already-correct intermediate metrics; do not recompute them from rounded display values unless the prompt explicitly says so.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q5_wrong_group_set, 88% of attempts): Returned the wrong pathway-tissue group set. Check this explicitly before finalizing.
- Previous v3 failure warning (q5_leaked_ref_or_incomplete, 81% of attempts): Leaked reference, incomplete-chain, or orphan rows into pathway burden. Check this explicitly before finalizing.
- Previous v3 failure warning (q5_wrong_log2_expr, 81% of attempts): Miscomputed mean_log2_matched_expr. Check this explicitly before finalizing.
- Previous v3 failure warning (q5_wrong_burden, 81% of attempts): Miscomputed burden_score. Check this explicitly before finalizing.
- Previous v3 failure warning (q5_wrong_vaf, 79% of attempts): Miscomputed mean_vaf. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'chloroplast_NDH_complex' and end with last row key/value 'cyclic_electron_flow' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 6: `pass5.query6`

- Difficulty: `extreme_hard`
- Language: `python`
- Primary failure family: `statistical_summary`

```text
Using pandas and sample_dim only, compute population z-scores for each expression marker:
- z_ndhb from expr_ndhb
- z_pgr5 from expr_pgr5
- z_ndhk from expr_ndhk
Use population standard deviation with ddof=0.
Then compute:
- photosynthesis_expr_z_mean = mean(z_ndhb, z_pgr5, z_ndhk)
Return: sample_id, z_ndhb, z_pgr5, z_ndhk, photosynthesis_expr_z_mean
Sort by photosynthesis_expr_z_mean descending, then sample_id ascending.
Round decimal outputs to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 5 data rows and exactly these columns in this order: sample_id, z_ndhb, z_pgr5, z_ndhk, photosynthesis_expr_z_mean.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by sample_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: z_ndhb, z_pgr5, z_ndhk, photosynthesis_expr_z_mean; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses photosynthesis_expr_z_mean, sample_id; follow the prompt's sort direction and tie-breakers exactly.
- Use sample_dim only: return the five real sample_dim rows S1-S5 exactly once; do not join to fact_calls or introduce S999.
- Expression summaries must use the marker column named in the prompt and the correct grain: sample-only tasks average samples, joined tasks average the joined sample-call rows.
- Use population statistics with ddof=0 for standard deviation, z-scores, and coefficient of variation; sample standard deviation will score wrong.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q6_wrong_zscore, 93% of attempts): Miscomputed marker z-scores, usually from ddof or denominator errors. Check this explicitly before finalizing.
- Previous v3 failure warning (q6_wrong_z_mean, 93% of attempts): Miscomputed photosynthesis_expr_z_mean. Check this explicitly before finalizing.
- Previous v3 failure warning (q6_wrong_sample_set, 52% of attempts): Returned the wrong sample set for z-score ranking. Check this explicitly before finalizing.
- Previous v3 failure warning (q6_wrong_sort, 17% of attempts): Returned z-score rows in the wrong order. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'S1' and end with last row key/value 'S5' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 7: `pass5.query7`

- Difficulty: `extreme_hard`
- Language: `python`
- Primary failure family: `repeatability_probe`

```text
Using pandas and complete-chain matched rows only, create a condition-level integrative summary.
For each condition, compute:
- distinct_genes_observed
- mean_matched_expr
- cv_matched_expr = population_std(matched_expr_count, ddof=0) / mean(matched_expr_count)
- mean_vaf
Return: condition, distinct_genes_observed, mean_matched_expr, cv_matched_expr, mean_vaf
Sort by condition ascending.
Round decimal outputs to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 3 data rows and exactly these columns in this order: condition, distinct_genes_observed, mean_matched_expr, cv_matched_expr, mean_vaf.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by condition; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: distinct_genes_observed, mean_matched_expr, cv_matched_expr, mean_vaf; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses condition; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.
- For distinct counts, count distinct values only after the required joins and filters have been applied.
- Matched expression must use gene_symbol mapping NDHB -> expr_ndhb, NDHK -> expr_ndhk, PGR5 -> expr_pgr5, and NULL for all other genes; do not average the wrong marker column.
- Use population statistics with ddof=0 for standard deviation, z-scores, and coefficient of variation; sample standard deviation will score wrong.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q7_wrong_mean_expr, 93% of attempts): Miscomputed mean_matched_expr. Check this explicitly before finalizing.
- Previous v3 failure warning (q7_wrong_cv, 93% of attempts): Miscomputed cv_matched_expr. Check this explicitly before finalizing.
- Previous v3 failure warning (q7_wrong_vaf, 93% of attempts): Miscomputed mean_vaf. Check this explicitly before finalizing.
- Previous v3 failure warning (q7_wrong_gene_count, 83% of attempts): Miscomputed distinct_genes_observed. Check this explicitly before finalizing.
- Previous v3 failure warning (q7_wrong_sort, 7% of attempts): Returned condition CV rows in the wrong order. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'control' and end with last row key/value 'high_light' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 8: `pass5.query8`

- Difficulty: `extreme_hard`
- Language: `python`
- Primary failure family: `decision_support`

```text
Using pandas, compute a plant-photosynthesis burden table at sample level.
Start from sample_dim and left join in complete-chain non-reference calls where genotype <> '0/0'.
For each sample, compute:
- non_reference_complete_chain_calls
- high_or_moderate_nonref_calls where impact IN ('high','moderate')
- total_marker_expr = expr_ndhb + expr_pgr5 + expr_ndhk
- log2_total_marker_expr = log2(total_marker_expr + 1)
- photosynthesis_variant_pressure = high_or_moderate_nonref_calls * log2_total_marker_expr
Return:
sample_id, tissue, non_reference_complete_chain_calls, high_or_moderate_nonref_calls, total_marker_expr, log2_total_marker_expr, photosynthesis_variant_pressure
Include samples with zero calls.
Sort by photosynthesis_variant_pressure descending, then sample_id ascending.
Round decimal outputs to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 5 data rows and exactly these columns in this order: sample_id, tissue, non_reference_complete_chain_calls, high_or_moderate_nonref_calls, total_marker_expr, log2_total_marker_expr, photosynthesis_variant_pressure.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by sample_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: non_reference_complete_chain_calls, high_or_moderate_nonref_calls, total_marker_expr, log2_total_marker_expr, photosynthesis_variant_pressure; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses photosynthesis_variant_pressure, sample_id; follow the prompt's sort direction and tie-breakers exactly.
- sample_dim is the preserving table: include S1-S5, keep zero-count samples such as S5, and never include orphan fact key S999 as a sample row.
- For sample-preserving output, produce one row per sample_dim sample; zero-call or zero-burden samples still need count 0 and NULL/rounded derived values as requested.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Apply the non-reference filter exactly as genotype <> '0/0'; do not count 0/0 reference calls in non-reference summaries.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Expression summaries must use the marker column named in the prompt and the correct grain: sample-only tasks average samples, joined tasks average the joined sample-call rows.
- Use numpy.log2(x + 1) or SQL-equivalent log2(x + 1) exactly; apply +1 before the log transform and round only the final displayed value.
- Compute composite decision/burden/pressure scores from the already-correct intermediate metrics; do not recompute them from rounded display values unless the prompt explicitly says so.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q8_wrong_marker_expr, 98% of attempts): Miscomputed total_marker_expr or log2_total_marker_expr. Check this explicitly before finalizing.
- Previous v3 failure warning (q8_wrong_pressure, 98% of attempts): Miscomputed photosynthesis_variant_pressure. Check this explicitly before finalizing.
- Previous v3 failure warning (q8_wrong_counts, 79% of attempts): Miscomputed non-reference or high/moderate call counts. Check this explicitly before finalizing.
- Previous v3 failure warning (q8_wrong_sort, 50% of attempts): Returned sample pressure rows in the wrong order. Check this explicitly before finalizing.
- Previous v3 failure warning (q8_wrong_sample_set, 24% of attempts): Returned the wrong sample set for the preserving sample-level burden table. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'S1' and end with last row key/value 'S5' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 9: `pass5.query9`

- Difficulty: `extreme_hard`
- Language: `python`
- Primary failure family: `ranking_and_priority`

```text
Using pandas and complete-chain non-reference rows only where genotype <> '0/0', build a condition-by-gene decision summary.
Compute:
- non_reference_calls
- mean_vaf
- mean_log2_matched_expr
- expression_weighted_signal = mean_vaf * mean_log2_matched_expr
Return: condition, gene_symbol, non_reference_calls, mean_vaf, mean_log2_matched_expr, expression_weighted_signal
Sort by expression_weighted_signal descending, then gene_symbol ascending, then condition ascending.
Round decimal outputs to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 3 data rows and exactly these columns in this order: condition, gene_symbol, non_reference_calls, mean_vaf, mean_log2_matched_expr, expression_weighted_signal.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by condition, gene_symbol; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: non_reference_calls, mean_vaf, mean_log2_matched_expr, expression_weighted_signal; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses expression_weighted_signal, gene_symbol, condition; follow the prompt's sort direction and tie-breakers exactly.
- A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.
- Apply the non-reference filter exactly as genotype <> '0/0'; do not count 0/0 reference calls in non-reference summaries.
- Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.
- Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.
- Matched expression must use gene_symbol mapping NDHB -> expr_ndhb, NDHK -> expr_ndhk, PGR5 -> expr_pgr5, and NULL for all other genes; do not average the wrong marker column.
- Use numpy.log2(x + 1) or SQL-equivalent log2(x + 1) exactly; apply +1 before the log transform and round only the final displayed value.
- Compute composite decision/burden/pressure scores from the already-correct intermediate metrics; do not recompute them from rounded display values unless the prompt explicitly says so.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q9_wrong_log2_expr, 86% of attempts): Miscomputed mean_log2_matched_expr. Check this explicitly before finalizing.
- Previous v3 failure warning (q9_wrong_signal, 86% of attempts): Miscomputed expression_weighted_signal. Check this explicitly before finalizing.
- Previous v3 failure warning (q9_wrong_vaf, 83% of attempts): Miscomputed mean_vaf. Check this explicitly before finalizing.
- Previous v3 failure warning (q9_wrong_group_set, 81% of attempts): Returned the wrong condition-gene signal group set. Check this explicitly before finalizing.
- Previous v3 failure warning (q9_leaked_ref_or_incomplete, 74% of attempts): Leaked reference, incomplete-chain, or orphan groups into signal ranking. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'high_light' and end with last row key/value 'control' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

### Query 10: `pass5.query10`

- Difficulty: `extreme_hard`
- Language: `python`
- Primary failure family: `statistical_summary`

```text
Using pandas and sample_dim only, compute marker composition shares and imbalance.
For each sample, compute:
- ndhb_share = expr_ndhb / (expr_ndhb + expr_pgr5 + expr_ndhk)
- pgr5_share = expr_pgr5 / (expr_ndhb + expr_pgr5 + expr_ndhk)
- ndhk_share = expr_ndhk / (expr_ndhb + expr_pgr5 + expr_ndhk)
- marker_imbalance = max(share) - min(share)
Return: sample_id, condition, ndhb_share, pgr5_share, ndhk_share, marker_imbalance
Sort by marker_imbalance descending, then sample_id ascending.
Round decimal outputs to 3 decimals.

Task-specific guidance for v4:
- Expected output contract: return exactly 5 data rows and exactly these columns in this order: sample_id, condition, ndhb_share, pgr5_share, ndhk_share, marker_imbalance.
- Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.
- Row identity is scored by sample_id; do not duplicate, omit, or relabel those keys.
- Numeric columns checked for tolerance are: ndhb_share, pgr5_share, ndhk_share, marker_imbalance; compute them from the correct joined/filter row set before rounding.
- Sort-order scoring uses marker_imbalance, sample_id; follow the prompt's sort direction and tie-breakers exactly.
- Use sample_dim only: return the five real sample_dim rows S1-S5 exactly once; do not join to fact_calls or introduce S999.
- Expression summaries must use the marker column named in the prompt and the correct grain: sample-only tasks average samples, joined tasks average the joined sample-call rows.
- For ratios/shares, use the exact denominator in the prompt for each row; calculate all component shares first, then derive imbalance or ratios from those components.
- Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.
- Previous v3 failure warning (q10_wrong_shares, 100% of attempts): Miscomputed one or more marker composition shares. Check this explicitly before finalizing.
- Previous v3 failure warning (q10_wrong_imbalance, 100% of attempts): Miscomputed marker_imbalance. Check this explicitly before finalizing.
- Previous v3 failure warning (q10_wrong_sort, 60% of attempts): Returned marker-share rows in the wrong order. Check this explicitly before finalizing.
- Previous v3 failure warning (q10_wrong_sample_set, 40% of attempts): Returned the wrong sample set for marker composition shares. Check this explicitly before finalizing.
- Previous v3 failure warning (q10_wrong_condition, 5% of attempts): Mismapped sample condition labels. Check this explicitly before finalizing.
- Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.
- The sorted final table should start with first row key/value 'S4' and end with last row key/value 'S5' for the first returned column.
- For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.
```

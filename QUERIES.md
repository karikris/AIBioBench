# AIBioBench Queries

Source: `benchmark_cases.jsonl`

Benchmark: `AIBioBench_photosynthesis_snowflake_v5`

Prompt strategy: v5 uses the v2/v3 base query text in this file plus model-specific runtime addenda from `query_engineering_registry/v5/model_query_guidance.json`.

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
```

### Query 2: `pass1.query2`

- Difficulty: `easy`
- Language: `sql`
- Primary failure family: `sorting_presentation`

```text
Inner join fact_calls to variant_dim on variant_id.
Return: call_id, variant_id, variant_class, impact, qual
Sort by qual descending, then call_id ascending.
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
```

### Query 5: `pass1.query5`

- Difficulty: `easy`
- Language: `sql`
- Primary failure family: `snowflake_traversal`

```text
Inner join fact_calls to variant_dim, then to gene_dim.
Return: call_id, variant_id, gene_symbol, pathway
Sort by call_id ascending.
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
```

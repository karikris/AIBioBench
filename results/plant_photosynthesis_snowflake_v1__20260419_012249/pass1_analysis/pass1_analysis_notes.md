# AIBioBench Pass 1 Analysis

Pass 1 contains eight easy SQL-style tasks over the shared plant/variant dataset. The scoring is all-or-nothing exact table matching, so near misses receive zero score.

## Model Summary

| Model | Exact | Accuracy | Mean Cell Accuracy | Row Count Match | Wall Time | Mean Gen TPS |
|---|---:|---:|---:|---:|---:|---:|
| Gemma 31B 64k | 3/8 | 37.5% | 72.0% | 75.0% | 370.4s | 3.48 |
| Gemma 31B 256k | 3/8 | 37.5% | 72.0% | 75.0% | 428.5s | 3.09 |
| Gemma 26B 256k | 2/8 | 25.0% | 60.9% | 50.0% | 89.6s | 15.36 |
| Gemma 26B 64k | 2/8 | 25.0% | 60.1% | 50.0% | 81.2s | 15.16 |
| Qwen Coder 30B 64k | 1/8 | 12.5% | 61.1% | 50.0% | 93.7s | 17.34 |
| Qwen 36B 64k | 1/8 | 12.5% | 60.8% | 62.5% | 168.8s | 11.86 |
| Qwen 36B 256k | 1/8 | 12.5% | 56.5% | 62.5% | 204.6s | 9.45 |
| Qwen Coder 30B 256k | 0/8 | 0.0% | 57.0% | 62.5% | 139.3s | 13.04 |
| Phi4 Mini 128k | 0/8 | 0.0% | 33.2% | 25.0% | 85.7s | 19.29 |

## Case Summary

| Query | Exact Models | Mean Cell Accuracy | Row Count Mismatches | Same Count But Wrong | Dominant Failure |
|---|---:|---:|---:|---:|---|
| QUERY1 | 2/9 | 82.9% | 7 | 0 | row_count_mismatch |
| QUERY2 | 0/9 | 36.8% | 6 | 3 | row_count_mismatch |
| QUERY3 | 7/9 | 94.1% | 1 | 1 | exact |
| QUERY4 | 4/9 | 90.2% | 1 | 4 | exact |
| QUERY5 | 0/9 | 55.6% | 9 | 0 | row_count_mismatch |
| QUERY6 | 0/9 | 58.9% | 3 | 6 | same_count_wrong_values |
| QUERY7 | 0/9 | 6.5% | 4 | 5 | same_count_wrong_values |
| QUERY8 | 0/9 | 49.4% | 0 | 9 | same_count_wrong_values |

## Query Notes

- **QUERY1**: Inner join on sample_dim; common failure was including orphan S999 or dropping call_id 9 because V999 has no variant row.
- **QUERY2**: Inner join on variant_dim plus qual DESC sort; common failures were sorting by call_id, including V999, or treating unmatched V999 as a joined row.
- **QUERY3**: Left join to sample_dim; mostly solved, except one type-only failure from string call_id values and one model that invented/misplaced rows.
- **QUERY4**: Right join / reversed left join; failures were aggregate arithmetic around S2 and zero-call sample handling.
- **QUERY5**: Inner join fact_calls -> variant_dim -> gene_dim; common failure was leaking V5/G999 or V999 rows that should be removed by the second inner join.
- **QUERY6**: Aggregate by impact after variant join; failures were mostly missed duplicate high-impact V2/V3 calls or bad averages.
- **QUERY7**: Aggregate by tissue after sample join; every model missed the weighted-by-call aggregate and/or included root/S5.
- **QUERY8**: Aggregate by condition after sample join; every model missed fact-row weighting and often included S5/high_light leakage.
